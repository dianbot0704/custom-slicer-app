# Run AksaratorApp as a Linux kiosk

The machine logs in automatically and shows only AksaratorApp, fullscreen. If the application exits or crashes, it starts again.

There are three parts:

| Part | File | Does |
| --- | --- | --- |
| Application kiosk mode | `Applications/AksaratorApp/qAksaratorAppMainWindow.cxx` | `--kiosk` locks the main window. |
| Kiosk session | `aksarator-kiosk-session`, `aksarator-kiosk.desktop` | Starts the application as the whole X session and starts it again when it exits. |
| X server lock | `10-aksarator-kiosk.conf` | Turns off console switching (Ctrl+Alt+F*n*) and Ctrl+Alt+Backspace. |

## Application kiosk mode

Start the application with `--kiosk`, or set `AKSARATOR_KIOSK=1`. Slicer keeps `--kiosk` when it restarts itself.

In kiosk mode the main window:

- opens fullscreen and goes back to fullscreen if something leaves it (F11, minimize, window manager keys);
- hides Slicer's menu bar, status bar, toolbars, Python console and error log; the module panel stays and cannot be closed, moved or floated;
- removes the keyboard shortcuts of Slicer's own actions, such as Ctrl+3 (Python console), Ctrl+0 (error log), Ctrl+F (module finder) and Ctrl+Left/Right (switch module); shortcuts that modules create themselves are kept;
- refuses to close from Alt+F4, the window manager or File > Exit. An exit the application asks for itself still works: the landing page power button and Ctrl+Q (`slicer.app.exit()`), and restart (Ctrl+R);
- does not load files dropped on the window.

Scripted modules can read the state as `slicer.util.mainWindow().kioskMode` and listen to the `kioskModeChanged(bool)` signal.

### Unlock for maintenance

Press **Ctrl+Alt+Shift+K** and confirm. The window leaves fullscreen and Slicer's menus, toolbars and shortcuts come back. IntraopPlanner may hide Slicer's UI again; Ctrl+Shift+H shows it. Restart the application to lock it again.

To ask for a PIN instead of a confirmation, store the SHA-256 of the PIN in the kiosk user's settings file, `~/.config/Aksarator/AksaratorApp.ini`:

```bash
printf '%s' '<pin>' | sha256sum
```

```ini
[Kiosk]
UnlockPinSha256=<the 64 hex characters printed above>
# Optional, a Qt key sequence; the default is Ctrl+Alt+Shift+K
UnlockShortcut=Ctrl+Alt+Shift+K
```

The PIN only keeps operators out of the maintenance UI. It is not a security boundary: the hash is unsalted, and a short PIN can be recovered from it by anyone who can read the settings file.

### Try it on a development machine

```bash
./build/Slicer-build/AksaratorApp --kiosk
```

Alt+F4 does not close the window. Exit with the landing page power button or Ctrl+Q, or unlock first with Ctrl+Alt+Shift+K.

## Install the kiosk session

These steps are written for Ubuntu with GDM or LightDM. They have not yet been run on a target machine.

1. Install the application, for example extract the package to `/opt/AksaratorApp`, so that the launcher is `/opt/AksaratorApp/AksaratorApp`.

2. Create a user for the kiosk. Do not add it to the `sudo` group.

   ```bash
   sudo useradd --create-home --shell /bin/bash aksarator
   ```

3. Install the session files:

   ```bash
   sudo install -m 755 scripts/kiosk/linux/aksarator-kiosk-session /usr/local/bin/
   sudo install -m 644 scripts/kiosk/linux/aksarator-kiosk.desktop /usr/share/xsessions/
   sudo install -m 644 scripts/kiosk/linux/10-aksarator-kiosk.conf /etc/X11/xorg.conf.d/
   ```

   The X server file applies to every session on the machine.

4. Optional: install a minimal window manager. Dialogs are placed and focused more reliably with one. The session starts `matchbox-window-manager` when it is installed.

   ```bash
   sudo apt install matchbox-window-manager
   ```

5. Optional: create `/etc/aksarator/kiosk.conf`, owned by root. The session script sources it.

   ```bash
   # Launcher, if it is not /opt/AksaratorApp/AksaratorApp
   AKSARATOR_APP=/opt/AksaratorApp/AksaratorApp
   # Normal exit (landing page power button): restart, poweroff or logout
   AKSARATOR_KIOSK_ON_EXIT=poweroff
   # Window manager command, or none
   AKSARATOR_KIOSK_WM="matchbox-window-manager -use_titlebar no"
   ```

6. Log in automatically to the kiosk session.

   GDM, `/etc/gdm3/custom.conf`:

   ```ini
   [daemon]
   AutomaticLoginEnable=true
   AutomaticLogin=aksarator
   ```

   and `/var/lib/AccountsService/users/aksarator` (older releases use `XSession=` instead of `Session=`):

   ```ini
   [User]
   Session=aksarator-kiosk
   ```

   LightDM, `/etc/lightdm/lightdm.conf.d/50-aksarator-kiosk.conf`:

   ```ini
   [Seat:*]
   autologin-user=aksarator
   autologin-session=aksarator-kiosk
   ```

7. Reboot.

The session writes the application output and its own messages to `~aksarator/.local/state/aksarator-kiosk/session.log`. The file is rotated at 10 MB.

## How the session restarts the application

| The application | The session |
| --- | --- |
| crashes or exits with a nonzero status | starts it again after 2 seconds. After 5 crashes in a row, each within 30 seconds of starting, it waits 60 seconds first. |
| exits with status 0 (power button, Ctrl+Q) | applies `AKSARATOR_KIOSK_ON_EXIT`: `restart` (default), `poweroff` or `logout`. |
| restarts itself (Ctrl+R) | waits for the new copy to exit, then starts the application again. |

`logout` ends the session. GDM then usually shows the login screen instead of logging in again, which gives a technician a way to log in with another account.

## Known gaps

- IntraopPlanner's Ctrl+Shift+H shows Slicer's UI, including the View menu and from there the Python console, even in kiosk mode. The module should ignore it while `slicer.util.mainWindow().kioskMode` is true. The application already cancels the module's F11.
- After a restart (Ctrl+R) the session cannot see the new copy's exit status, so a power button exit after that restarts the application instead of applying `AKSARATOR_KIOSK_ON_EXIT`.
- Not covered here: disabling automatic OS updates and reboots, hiding the mouse cursor on touch screens (for example `unclutter`), and filesystem protection against power loss.

## Windows

`--kiosk` works the same on Windows. Windows needs its own session part: Shell Launcher v2 (Windows Enterprise, Education or IoT Enterprise) can run `AksaratorApp.exe --kiosk` instead of Explorer and restart it when it exits.
