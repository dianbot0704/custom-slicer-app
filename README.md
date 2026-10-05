# AksaratorApp by Aksarator

Customized version of Slicer

_This project is in active development and may change from version to version without notice,_

## Table of contents

- [Features](#features)
- [Development](#development)

## Features

_List key features_

## Development

- [Contributing](CONTRIBUTING.md)
- [Building](BUILD.md)
- [Automated application verification](scripts/verification/README.md)
- [AIGCamera source](#aigcamera-source)

After building on Linux, run the UI smoke check without manual navigation:

```bash
./scripts/verify-app.py
```

The check uses synthetic data and isolated settings. It produces an HTML report, JSON results, screenshots, and logs under `out/verification/`. Camera and DICOM connections are disabled. See the [verification guide](scripts/verification/README.md) for coverage and limits.

## AIGCamera source

The `aigcamera` Python package is pulled from its upstream repo and stored under `Python/`.
It is not tracked as a submodule yet.

```bash
mkdir -p Python
git clone https://github.com/alwint3r/aigcamera Python/aigcamera
```

To update later:

```bash
git -C Python/aigcamera pull
```

![AksaratorApp by Aksarator](Applications/AksaratorApp/Resources/Images/LogoFull.png?raw=true)
