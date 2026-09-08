# Native Libraries

This directory holds proprietary native artifacts required by the Aim backend.

The loader expects:

- Linux: `_native/AimPosition312.so`
- Windows: `_native/AimPosition312.pyd` and `_native/libusb0.dll`

On Windows, the AimPosition extension also requires Npcap to provide `wpcap.dll`. The application SuperBuild can
stage the Windows files directly from the vendor ZIP archive, so they do not need to be copied into this source tree.
Pass the archive to `build.py configure --aimposition-archive <archive.zip>`.

For Linux development, copy the shared object from the repository root with:

```text
python setup_aigcamera.py /path/to/aimposition
```

Do not commit proprietary native libraries or vendor archives to the repository.
