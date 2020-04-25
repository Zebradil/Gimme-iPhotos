# Gimme-iPhotos

[![PyPI](https://img.shields.io/pypi/v/gimme-iphotos.svg)](https://pypi.python.org/pypi/gimme-iphotos)
[![PyPI](https://img.shields.io/pypi/l/gimme-iphotos.svg)](https://opensource.org/licenses/MIT)

Download media files from iCloud.

This tool uses [pyicloud] to synchronize photos and videos from iCloud to your
local machine.

## Features

- Downloads media files from iCloud in parallel (might be beneficial on small files and wide bandwidth)
- Keeps local collection in sync with iCloud by:
  - skipping files which exist locally
  - removing local files which were removed from the cloud
- Reads configuration from ini-file
- Stores password in keychain (provided by [pyicloud])
- Supports two-factor authentication
- Shows nice progress bars (thanks to [tqdm])

## Installation

```sh
$ pip3 install gimme-iphotos
```

or

```sh
$ docker pull zebradil/gimme-iphotos
```

## Usage

```
$ gimme-iphotos --help
usage: gimme-iphotos [-h] [-c CONFIG] [-v] [-u USERNAME] [-p PASSWORD] [-d DESTINATION] [-o] [-r] [-n PARALLEL]

Downloads media files from iCloud

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file. It's ini-like file (see configparser module docs), must contain [main] section. Keys are fully-named arguments, except help, config and verbose.
                        Values specified using command line arguments take precedence over values from a provided config file.
  -v, --verbose
  -u USERNAME, --username USERNAME
                        iCloud username (email). Can be specified interactively if not set.
  -p PASSWORD, --password PASSWORD
                        iCloud password. Can be specified interactively if not set.
  -d DESTINATION, --destination DESTINATION
                        Destination directory. Can be specified interactively if not set.
  -o, --overwrite       Overwrite existing files. Default: false.
  -r, --remove          Remove missing files. Default: false.
  -n PARALLEL, --num-parallel-downloads PARALLEL
                        Max number of concurrent downloads. Increase this number if bandwidth is not fully utilized. Default: 3
```

Using config file:

```sh
$ cat john.cfg
[main]
username = john.doe@example.com
password = not-secure123
destination = /home/john/Photos
remove = True

$ gimme-iphotos -c john.cfg
```

Overriding config file:

```sh
$ gimme-iphotos -c john.cfg --destination /tmp/icloud
```

Without config file:

```sh
$ # Password will be requested interactively
$ gimme-iphotos -u john.doe@rexample.com --destination /tmp/icloud
Enter iCloud password for john.doe@rexample.com:
```

### Docker

The CLI is the same but requires mounting destination directory and config file (if needed).

```sh
$ docker run -it \
    -v <destination>:/somedir \
    -v ${PWD}/john.cfg:/app/ \
    zebradil/gimme-iphotos -c john.cfg 
```

## License

Licensed under the [MIT License].

By [German Lashevich].

[MIT License]: https://github.com/zebradil/Gimme-iPhotos/blob/master/LICENSE
[pyicloud]: https://github.com/picklepete/pyicloud
[tqdm]: https://github.com/tqdm/tqdm
[German Lashevich]: https://github.com/zebradil
