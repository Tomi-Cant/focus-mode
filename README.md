# Focused Up

Focused Up helps you make room for work, study, and the things that matter by keeping distracting apps out of the way.

## Focused Up usage database

The new Focused Up database layer stores its SQLite database at
`%LOCALAPPDATA%\Focused Up\usage.db`. On initialization, it imports existing
schedule data from `%LOCALAPPDATA%\Focused Up\blacklist.json` and app settings
from `%LOCALAPPDATA%\Focused Up\config.json`. Original schedule fields and
unknown settings are retained in the database so the migration does not discard
data that is not represented by the new rule columns.

## What you can do

- **Create focus schedules** for the times and days that work for you.
- **Choose which apps to block** during each scheduled focus period.
- **Set a daily time allowance** for selected apps before they are blocked.
- **Pick a replacement app or website** to open when a blocked app gets in the way. Choose a set order or let Focused Up pick one for you.
- **Choose what happens when a focus period starts or ends**, such as opening an app or website, sleeping your PC, or shutting it down.
- **Turn schedules on or off** and update them whenever your routine changes.

## How to run

1. `pip install pyinstaller` (with python installed on your device) {skip if already installed}

```cmd
pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "Focused Up" initialize_app.py
```

```cmd
pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "FocusedUpScript" main.py
```

2. Put `focused_up_logo.ico` `StartProcess.bat` and `SilentRun.vbs` into the `dist` folder, this is resposible for the persistence of the scheduler when the device shuts off or errors (will not work without it).
3. Open the `dist` folder and run `Focused Up.exe`.
4. On first launch, approve the administrator permission request so Focused Up can complete setup and run your schedules automatically.
5. Choose whether to add a desktop shortcut, if prompted. Setup then opens Focused Up so you can create your schedules.

After setup, Focused Up automatically opens and you can start creating your schedules.

## Updating versions (optional)

If you plan to make edits to the repository you will need to run:
`pip install pyinstaller` (with python installed on your device) {skip if already installed}
`pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "Focused Up" initialize_app.py`
`pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "FocusedUpScript" main.py`
for the main app and the script respectively and also update the version number in `initialize_app.py`

Focused Up is designed to help you stay focused while keeping your schedule and preferences in your hands.

## Optional Services

Warning Times and all triggered voicelines can be found at <https://tomibanjoko.gumroad.com/l/FocusedUpAddons>
