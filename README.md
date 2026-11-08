# Focused Up

Focused Up helps you make room for work, study, and the things that matter by keeping distracting apps out of the way.

## Technical features

Focused Up is a Windows desktop app written in Python with a tkinter interface. It is built as four separate programs that share state only through a local SQLite database, so enforcement and tracking keep working even when the main window is closed.

| Program | Role |
|---|---|
| `Focused Up` (`initialize_app.py`) | Setup wizard, schedule editor and settings |
| `FocusedUpScript` (`main.py`) | Runs in the background and closes blocked apps on schedule |
| `FocusedUpSampler` (`sampler.py`) | Always-on process that records app usage |
| `FocusedUpUsageScheduler` (`usage_scheduler.py`) | Periodic task for daily processing |

## Enforcement
- Schedules have start and end times, active days, a blocked-app list and an optional daily time allowance
- Configurable actions on start and finish (open an app or website, sleep or shut down the PC), with replacement apps or sites opened in a set order or at random
- Registered with Windows Task Scheduler during setup and launched silently through `SilentRun.vbs` and `StartProcess.bat`, so it restarts after shutdowns or errors

## Usage tracking and habit analysis
- Records the foreground app and a snapshot of open apps, and ignores idle time using the Win32 `GetLastInputInfo` API
- Time asleep or hibernating is discarded instead of counted as usage
- Baselines use the median and median absolute deviation over recent days, so one unusual day doesn't skew results
- Analysis looks at habits over several days (foreground time, time open, sessions per day, late-night use), not one-off spikes **[confirm]**
- Suggestions and highlights/lowlights come from these baselines and trends **[confirm]**

## Data storage
- Everything is stored in SQLite at `%LOCALAPPDATA%\Focused Up\usage.db`. Initialization creates empty tables and does not import schedule or configuration records from JSON
- `ban_rules` stores schedules and `app_config` stores application settings and other JSON-backed configuration. Existing databases are migrated to the current rule and pending-change schemas
- Usage lives in `samples` (raw activity) and `daily_usage` (per-app daily totals)
- Schedule edits are buffered and committed at the next day rollover, while the app applies them immediately **[confirm]**
- Write-ahead logging lets the background programs and the UI use the database at the same time **[confirm]**

## Installer
- Setup wizard with administrator elevation, installation to Program Files and an optional desktop shortcut
- Version check on launch, so setup only reruns after an upgrade
- Packaged with PyInstaller (`--onedir`, `--windowed`)
## What you can do

- **Create focus schedules** for the times and days that work for you.
- **Choose which apps to block** during each scheduled focus period.
- **Set a daily time allowance** for selected apps before they are blocked.
- **Pick a replacement app or website** to open when a blocked app gets in the way. Choose a set order or let Focused Up pick one for you.
- **Choose what happens when a focus period starts or ends**, such as opening an app or website, sleeping your PC, or shutting it down.
- **Turn schedules on or off** and update them whenever your routine changes.
- **

## How to run

Install dependencies and PyInstaller:

```cmd
pip install -r requirements.txt
```

Build the setup application, main application, sampler, and usage scheduler:

```cmd
pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "Focused Up" initialize_app.py
pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "FocusedUpScript" main.py
pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "FocusedUpSampler" sampler.py
pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "FocusedUpUsageScheduler" usage_scheduler.py
```

2. Put `focused_up_logo.ico`, `StartProcess.bat`, and `SilentRun.vbs` in the
   `dist` folder. They support persistence after shutdowns or errors.
3. Open the `dist` folder and run `Focused Up.exe`.
4. On first launch, approve the administrator permission request so setup can
   install the application and scheduled tasks.
5. Choose whether to create a desktop shortcut when prompted.

After setup, Focused Up automatically opens and you can start creating your schedules.

## Updating versions (optional)

Rebuild all executables after making application changes and update the current
version in `initialize_app.py` before distributing a new release.

Focused Up is designed to help you stay focused while keeping your schedule and preferences in your hands.

