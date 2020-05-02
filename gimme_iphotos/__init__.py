#!/usr/bin/env python3
import argparse
import logging
import sys

from .downloader import DownloaderApp


def get_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Downloads media files from iCloud",
        argument_default=argparse.SUPPRESS,
    )

    # Command line only arguments
    parser.add_argument(
        "-c",
        "--config",
        help="""
            Configuration file.
            It's ini-like file (see configparser module docs), must contain [main] section.
            Keys are fully-named arguments, except help, config and verbose.
            Values specified using command line arguments take precedence over values from a provided config file.
        """,
        type=argparse.FileType("r"),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="""
            Increase verbosity. Can be specified multiple times.  Use -vvvv to get maximum verbosity.""",
    )

    # Arguments suitable for configuration file
    parser.add_argument(
        "-u",
        "--username",
        help="iCloud username (email). Can be specified interactively if not set.",
    )
    parser.add_argument(
        "-p",
        "--password",
        help="iCloud password. Can be specified interactively if not set.",
    )
    parser.add_argument(
        "-d",
        "--destination",
        help="Destination directory. Can be specified interactively if not set.",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Overwrite existing files. Default: false.",
    )
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove missing files. Default: false.",
    )
    parser.add_argument(
        "-n",
        "--num-parallel-downloads",
        dest="parallel",
        type=int,
        help="Max number of concurrent downloads. Increase this number if bandwidth is not fully utilized. Default: 3",
    )

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
