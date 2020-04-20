#!/usr/bin/env python3
import argparse
import logging
import os
import shutil
import sys
from configparser import ConfigParser
from getpass import getpass
from typing import Dict, Iterable, Set, Union

import click
from pyicloud import PyiCloudService
from pyicloud.utils import get_password
from tqdm import tqdm

# TODO option to create config fiel from cli arguments
# TODO consider using click library instead of argparse as it is used anyways


class DownloaderApp:
    DEFAULTS = {
        "username": None,
        "password": None,
        "destination": None,
        "skip": True,
        "remove": False,
    }

    def __init__(self, args: argparse.Namespace):
        self.logger = logging.getLogger("app")
        level = logging.CRITICAL - args.verbose * 10
        if level < logging.DEBUG:
            level = logging.ERROR
        else:
            level = min(level, logging.CRITICAL)
        self.logger.setLevel(level)

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
        self, args: argparse.Namespace, defaults: Dict[str, Union[str, bool, None]]
    ) -> Dict[str, Union[str, bool, None]]:
        config = {**defaults}

        if hasattr(args, "config"):
            cfgp = ConfigParser()
            cfgp.read_file(args.config)

            if "main" not in cfgp:
                raise Exception("Config must contain section [main]")

            for key, value in cfgp["main"].items():
                if key in config:
                    config[key] = value
                else:
                    logging.warning('Unknown configuration key "%s" — skipping', key)

        # Override values by command line arguments
        for key in config:
            if hasattr(args, key):
                self.logger.debug(
                    "Configuration key '%s' is override from cli arguments", key
                )
                config[key] = getattr(args, key)

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

        icloud_photos = self.download_photos(api, config["destination"], config["skip"])

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
            print("Two-step authentication required. Your trusted devices are:")

            devices = api.trusted_devices
            for i, device in enumerate(devices):
                print(
                    "  %s: %s"
                    % (
                        i,
                        device.get(
                            "deviceName", "SMS to %s" % device.get("phoneNumber")
                        ),
                    )
                )

            device = click.prompt("Which device would you like to use?", default=0)
            device = devices[device]
            if not api.send_verification_code(device):
                raise Exception("Failed to send verification code")

            # TODO consider retry in case of a typo
            code = click.prompt("Please enter validation code")
            if not api.validate_verification_code(device, code):
                raise Exception("Failed to verify verification code")

        return api

    def download_photos(
        self, api: PyiCloudService, destination: str, skip_existing: bool,
    ) -> Set[str]:
        self.logger.info(
            "Downloading all photos into '%s' while %s existing…",
            destination,
            "skipping" if skip_existing else "overwriting",
        )

        downloaded_count = 0
        skipped_count = 0
        total_count = 0
        icloud_photos = set()
        for photo in self._iterator(api.photos.all):
            total_count += 1
            filename = os.path.join(destination, photo.filename)
            icloud_photos.add(filename)
            if skip_existing and os.path.isfile(filename):
                skipped_count += 1
                self.logger.debug("Skipping existing '%s'", photo.filename)
                continue
            download = photo.download()
            with open(filename, "wb") as fdst:
                self.logger.debug("Downloading '%s'", photo.filename)
                shutil.copyfileobj(download.raw, fdst)
            downloaded_count += 1

        self.logger.info(
            "Downloaded: %s | Skipped: %s | Total: %s",
            downloaded_count,
            skipped_count,
            total_count,
        )

        self.logger.debug("icloud_photos: %s", icloud_photos)

        return icloud_photos

    def remove_missing(self, destination: str, icloud_photos: Set[str]) -> None:
        self.logger.info("Removing missing photos…")
        photos_for_removal = set()
        for entry in os.scandir(destination):
            if entry.is_file(follow_symlinks=False) and entry.path not in icloud_photos:
                self.logger.debug("'%s' is considered for removal", entry.name)
                photos_for_removal.add(entry)
        print("Missing photos ({}):".format(len(photos_for_removal)))
        for entry in photos_for_removal:
            print("\t{}".format(entry.name))
        if click.confirm("Proceed with removal?"):
            for entry in photos_for_removal:
                os.unlink(entry.path)
            self.logger.info("Removed %s files", len(photos_for_removal))
        else:
            self.logger.info("Abort removal of missing photos")

    def _iterator(self, iterable: Iterable) -> Iterable:
        return tqdm(iterable) if self.logger.level > logging.INFO else iterable

    @staticmethod
    def get_cli_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Fetch media from iCloud", argument_default=argparse.SUPPRESS
        )

        # Command line only arguments
        parser.add_argument(
            "-c", "--config", help="Configuration file", type=argparse.FileType("r")
        )
        parser.add_argument("-v", "--verbose", action="count", default=0)

        # Arguments suitable for configuration file
        parser.add_argument("-u", "--username")
        parser.add_argument("-p", "--password")
        parser.add_argument("-d", "--destination", help="Destination directory")
        parser.add_argument(
            "-s", "--skip", action="store_true", help="Skip existing files"
        )
        parser.add_argument(
            "-r", "--remove", action="store_true", help="Remove missing files"
        )

        return parser.parse_args()


def main():
    try:
        args = DownloaderApp.get_cli_args()
        logging.basicConfig(level=logging.INFO)
        DownloaderApp(args).run()
        return 0
    except Exception as err:
        logging.critical(err)
        return 1


if __name__ == "__main__":
    sys.exit(main())
