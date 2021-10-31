#!/usr/bin/env python3
import argparse
import logging
import sys
from argparse import RawTextHelpFormatter

import click

from .downloader import DownloaderApp


def get_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Downloads media files from iCloud",
        argument_default=argparse.SUPPRESS,
        formatter_class=RawTextHelpFormatter,
    )

    # Command line only arguments
    parser.add_argument(
        "-c",
        "--config",
        help="Configuration file.\n"
        + "It's ini-like file (see configparser module docs), must contain [main] section.\n"
        + "Keys are fully-named arguments, except help, config and verbose.\n"
        + "Values specified using command line arguments take precedence over values from a provided config file.",
        type=argparse.FileType("r"),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity. Can be specified multiple times.\n"
        + "Use -vvvv to get maximum verbosity.",
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
        help="Max number of concurrent downloads.\n"
        + "Increase this number if bandwidth is not fully utilized. Default: 3",
    )
    parser.add_argument(
        "-g",
        "--group",
        action="store_true",
        dest="group_by_year_month",
        help="Group the photos into year and month directories.",
    )
    parser.add_argument(
        "--zero-pad",
        action="store_true",
        dest="group_by_year_month_zero_pad",
        help="Zero pad months when grouping photos.",
    )

    return parser.parse_args()


def main():
    try:
        args = get_cli_args()
        logging.basicConfig(level=logging.CRITICAL)
        DownloaderApp(vars(args)).run()
        return 0
    except (KeyboardInterrupt, click.exceptions.Abort):
        print("\nAborting.")
        return 1
    except Exception as err:
        logging.critical(err, exc_info=True)
        return 1
