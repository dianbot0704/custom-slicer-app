# Native Libraries

This directory is for native shared libraries (`.so` files) required by the Aim backend.

## Usage

Copy your native library file here. By default, the loader expects:

```
_native/AimPosition312.so
```

You can rename your file to match, or modify `src/aigcamera/_native_loader.py` to use a different filename.

## Git

All `.so` files are gitignored. Do not commit native libraries to the repository.
