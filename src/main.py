#!/usr/bin/env python3
import argparse
import logging
import sys

from downloader import DownloaderApp


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
        "-o", "--overwrite", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument(
        "-r", "--remove", action="store_true", help="Remove missing files"
    )
    parser.add_argument("-n", "--num-parallel-downloads", dest="parallel", type=int)

    return parser.parse_args()


def main():
    try:
        args = get_cli_args()
        logging.basicConfig(level=logging.CRITICAL)
        DownloaderApp(vars(args)).run()
        return 0
    except KeyboardInterrupt:
        print("\nAborting.")
        return 1
    except Exception as err:
        logging.critical(err)
        return 1


if __name__ == "__main__":
    sys.exit(main())
