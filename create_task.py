# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025   
import os
import shlex
import sys
from pathlib import Path


def _quote_desktop_arg(value):
    escaped = (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("`", "\\`")
    )
    return f'"{escaped}"'


def create_desktop_entry(script_path, entry_path, name, script_args=""):
    script_path = Path(script_path).resolve()
    entry_path = Path(entry_path)
    entry_path.parent.mkdir(parents=True, exist_ok=True)

    command = [sys.executable, str(script_path), *shlex.split(script_args)]
    entry_path.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={name}\n"
        f"Exec={' '.join(_quote_desktop_arg(arg) for arg in command)}\n"
        f"Path={script_path.parent}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n",
        encoding="utf-8",
    )
    entry_path.chmod(0o755)
    return True


def create_autostart_entry(task_name, script_path, script_args=""):
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    entry_path = config_home / "autostart" / f"{task_name}.desktop"
    return create_desktop_entry(script_path, entry_path, "Focused Up", script_args)


if __name__ == "__main__":
    create_autostart_entry("FocusedUp", Path.cwd() / "FocusedUpScript.exe")