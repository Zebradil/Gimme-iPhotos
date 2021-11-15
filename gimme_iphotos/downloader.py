import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, wait
from configparser import ConfigParser
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Set, Union

import click
from colorama import Fore
from pyicloud import PyiCloudService
from pyicloud.utils import get_password
from tqdm import tqdm

from .utils import Copy

# TODO option to create config file from cli arguments
# TODO consider using click library instead of argparse as it is used anyways


class DownloaderApp:
    DEFAULTS = {
        "username": None,
        "password": None,
        "destination": None,
        "overwrite": False,
        "remove": False,
        "group_by_year_month": False,
        "group_by_year_month_zero_pad": False,
        "parallel": 3,
    }

    def __init__(self, args: Dict[str, Any] = {}):
        self.logger = logging.getLogger("app")
        self.logger.setLevel(self._verbosity_to_logging_level(args.get("verbose", 0)))

        self.config = self.get_config(args, self.DEFAULTS)
        self.logger.debug(
            "Configuration: %s",
            {
                **self.config,
                "password": "******"
                if self.config["password"]
                else self.config["password"],
            },
        )

    def get_config(
        self, args: Dict[str, Any], defaults: Dict[str, Union[str, bool, None]]
    ) -> Dict[str, Union[str, bool, None]]:
        config = {**defaults}

        if "config" in args:
            cfgp = ConfigParser()
            cfgp.read_file(args["config"])

            if "main" not in cfgp:
                raise Exception("Config must contain section [main]")

            for key, value in cfgp["main"].items():
                if key in config:
                    config[key] = value
                else:
                    logging.warning('Unknown configuration key "%s" — skipping', key)

        # Override values by command line arguments
        for key in config:
            if key in args:
                self.logger.debug(
                    "Configuration key '%s' is override from cli arguments", key
                )
                config[key] = args[key]

        # Ensure required configuration values are set
        if not config["username"]:
            config["username"] = input("Specify username: ")

        if not config["password"]:
            config["password"] = get_password(config["username"])

        if config["destination"]:
            config["destination"] = os.path.abspath(config["destination"])

        while True:
            isset = bool(config["destination"])
            isdir = isset and os.path.isdir(config["destination"])
            writeable = isset and os.access(config["destination"], os.W_OK | os.X_OK)

            if isset and isdir and writeable:
                break

            reason = ""
            if not isset:
                reason = "Destination is not set. "
            elif not isdir:
                reason = "Destination is not a directory. "
            elif not writeable:
                reason = "Destination is not writeable. "
            config["destination"] = os.path.abspath(
                input(f"{reason}Specify destination directory: ")
            )

        return config

    def run(self) -> None:
        config = self.config

        api = self.connect_to_icloud(config)

        icloud_photos = self.download_photos(
            api, config["destination"], config["overwrite"], config["parallel"],
        )

        if config["remove"]:
            self.remove_missing(config["destination"], icloud_photos)

    def connect_to_icloud(
        self, config: Dict[str, Union[str, bool, None]]
    ) -> PyiCloudService:
        self.logger.info("Connecting to iCloud…")
        if config["password"] == "":
            api = PyiCloudService(config["username"])
        else:
            api = PyiCloudService(config["username"], config["password"])

        if api.requires_2sa:
            print("Two-step authentication required.")

            if click.confirm(
                "Have you received authentication request on any of your devices?"
            ):
                verification_function = lambda code: api.validate_2fa_code(code)
            else:
                print("Fallback to SMS verification.")
                print("Your trusted devices are:")
                devices = api.trusted_devices
                for i, device in enumerate(devices):
                    print(
                        "  {}: {}".format(
                            i,
                            device.get(
                                "deviceName",
                                "SMS to {}".format(device.get("phoneNumber")),
                            ),
                        )
                    )
                device = click.prompt("Which device would you like to use?", default=0)
                device = devices[device]
                if not api.send_verification_code(device):
                    raise Exception("Failed to send verification code")
                verification_function = lambda code: api.validate_verification_code(
                    device, code
                )

            verified = False
            while not verified:
                code = click.prompt("Please enter validation code")
                verified = verification_function(code)
                self.logger.debug("Verification result: %s", verified)
                if verified:
                    print("Succeed")
                else:
                    print(
                        "Failed to verify verification code, retry (Ctrl-C to cancel)"
                    )

        return api

    def download_photos(
        self,
        api: PyiCloudService,
        destination: str,
        overwrite_existing: bool,
        parallel: int = 3,
    ) -> Set[str]:
        print(
            "Downloading all photos into '{}' while {} existing…".format(
                destination, "overwriting" if overwrite_existing else "skipping"
            )
        )

        downloaded_count = 0
        overwritten_count = 0
        skipped_count = 0
        total_count = 0
        icloud_photos = set()
        collection = tqdm(
            api.photos.all,
            desc="Total",
            bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET),
            disable=self.logger.level <= logging.INFO,
        )
        # FIXME Cancelling doesn't work well with ThreadPoolExecutor. I didn't find a way to cancel tasks if they're
        # already running. Maybe it makes sense using lower level of threading API.
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            try:
                downloads = []
                for photo in collection:
                    total_count += 1
                    filename = self.name_photo(photo, icloud_photos, destination)
                    icloud_photos.add(filename)
                    if os.path.isfile(filename):
                        if not overwrite_existing:
                            skipped_count += 1
                            self.logger.debug("Skipping existing '%s'", photo.filename)
                            continue
                        else:
                            overwritten_count += 1
                            self.logger.debug(
                                "Overwriting existing '%s'", photo.filename
                            )
                    downloads.append(
                        executor.submit(
                            self.download_photo, photo, filename, destination
                        )
                    )
                    downloaded_count += 1
                wait(downloads)
            except KeyboardInterrupt as stop:
                print("Stopping tasks")
                # Make an attempt to cancel all tasks and wait for the rest which were not cancelled
                wait([feature for feature in downloads if not feature.cancel()])
                raise stop

        print(
            "Downloaded: {} | Skipped: {} | Overwritten: {} | Total: {}".format(
                downloaded_count, skipped_count, overwritten_count, total_count
            )
        )

        self.logger.debug("icloud_photos: %s", icloud_photos)

        return icloud_photos

    def name_photo(self, photo, icloud_photos: set, destination: str) -> str:
        if self.config["group_by_year_month_zero_pad"]:
            month_format = "%02d"
        else:
            month_format = "%d"

        if self.config["group_by_year_month"]:
            if photo.asset_date:
                destination_directory = os.path.join(
                    destination,
                    "%04d" % photo.asset_date.year,
                    month_format % photo.asset_date.month,
                )
            else:
                destination_directory = os.path.join(destination, "NO_DATE")
            filename = os.path.join(destination_directory, photo.filename)
        else:
            filename = os.path.join(destination, photo.filename)

        if filename in icloud_photos:
            """If the filename has already been encountered try to
            rename it like so:
                img.jpg -> img 2.jpg -> img 3.jpg ...
            Photos are ordered by date added so this works across runs.
            Maximum rename attempts is arbitrarily set at 100.
            """
            root, ext = os.path.splitext(filename)
            for i in range(2, 102):
                new_filename = f"{root} {i}{ext}"
                if new_filename not in icloud_photos:
                    filename = new_filename
                    break
            else:
                raise (Exception(f"Exceeded 100 files with the name {filename}."))
        return filename

    def download_photo(self, photo, filename: str, temp_file_dir: str) -> None:
        download = photo.download()
        tmp_prefix = os.path.join(temp_file_dir, os.path.basename(filename)) + "."
        with NamedTemporaryFile(mode="wb", prefix=tmp_prefix, delete=False) as fdst:
            self.logger.debug("Downloading '%s' to '%s'", photo.filename, fdst.name)
            try:
                self._copyfileobj(download.raw, fdst.file, photo.size, photo.filename)
            except KeyboardInterrupt as stop:
                # FIXME Apart from KeyboardInterrupt there might be more reasons to do cleanup
                self.logger.debug(
                    "Downloading interrupted, removing temporary file %s", fdst.name
                )
                os.unlink(fdst.name)
                raise stop
            self.logger.debug(
                "Downloading is completed, renaming '%s' → '%s'", fdst.name, filename
            )
            os.renames(fdst.name, filename)
            self.logger.debug("Set modification date to %s", photo.created)
            os.utime(filename, (time.time(), photo.created.timestamp()))

    def remove_missing(self, destination: str, icloud_photos: Set[str]) -> None:
        print("Checking for missing photos…", end=" ")
        photos_for_removal = set()
        for entry in os.scandir(destination):
            if entry.is_file(follow_symlinks=False) and entry.path not in icloud_photos:
                self.logger.debug("'%s' is considered for removal", entry.name)
                photos_for_removal.add(entry)

        if not photos_for_removal:
            print("Nothing to do.")
            return

        print("Missing photos ({}):".format(len(photos_for_removal)))
        for entry in photos_for_removal:
            print("\t{}".format(entry.name))

        if click.confirm("Proceed with removal?"):
            for entry in photos_for_removal:
                os.unlink(entry.path)
                print(".", end="", flush=True)
            print("\nRemoved {} files".format(len(photos_for_removal)))
        else:
            self.logger.info("Abort removal of missing photos")

    def _copyfileobj(self, fsrc, fdst, size: int = 0, desc: str = ""):
        with tqdm(
            desc=desc,
            total=size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            leave=False,
            disable=self.logger.level <= logging.INFO or size <= 0,
        ) as t:
            Copy.fileobj(fsrc, fdst, t.update)

    @staticmethod
    def _verbosity_to_logging_level(verbosity: int) -> int:
        """
        Converts verbosity (the number of -v arguments) to logging level.
        The maximum level is CRITICAL
        The minimum level is DEBUG
        The default level is ERROR
        """
        if verbosity == 0:
            return logging.ERROR

        level = logging.CRITICAL - verbosity * 10

        if level < logging.DEBUG:
            return logging.DEBUG

        return min(level, logging.CRITICAL)
