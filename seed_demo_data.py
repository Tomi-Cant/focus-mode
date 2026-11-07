"""Seed Focused Up with one week of fake gamer usage (too much Minecraft, some Overwatch).

Usage:
    python seed_demo_data.py                  # writes into the real Focused Up DB (backs it up first)
    python seed_demo_data.py --db demo.db     # write to another file (tables are created if missing)
    python seed_demo_data.py --no-samples     # only daily_usage + app_settings, skip raw samples
    python seed_demo_data.py --end 2026-11-07 # last day of the week (default: today)

Everything comes from one list of fake sessions, so daily_usage and the raw samples agree.
Re-running replaces the seeded dates instead of duplicating them.
"""

import argparse
import os
import random
import shutil
import sqlite3
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

SAMPLE_SECONDS = 10       # spacing of foreground samples (matches the sampler loop)
SNAPSHOT_SECONDS = 300    # spacing of "what is open" snapshots (every 5 minutes)
MAX_END = 23 * 60 + 50    # every session ends by 23:50 so nothing crosses midnight

MC = "Minecraft.Windows.exe"   # change to "javaw.exe" if your tracker sees Java Minecraft
OW = "Overwatch.exe"

# Categories as the app would store them in app_settings
CATEGORIES = {
    MC: "game",
    OW: "game",
    "Discord.exe": "social",
    "chrome.exe": "browser",
    "Spotify.exe": "other",
    "Code.exe": "work",
}

# Foreground plan: (app, usual start HH:MM, min minutes, max minutes, weekdays it happens)
# Monday = 0 ... Sunday = 6. Start times and lengths get random jitter below.
WEEKDAYS = {0, 1, 2, 3, 4}
WEEKEND = {5, 6}
PLAN = [
    ("chrome.exe",  "08:30", 25, 45,  WEEKDAYS),
    ("Code.exe",    "09:15", 50, 90,  {0, 2}),               # a little schoolwork on Mon/Wed
    ("chrome.exe",  "12:30", 20, 35,  WEEKDAYS),
    ("Discord.exe", "15:30", 15, 30,  WEEKDAYS),
    ("chrome.exe",  "10:30", 30, 50,  WEEKEND),
    # Weekday evenings: Minecraft in two long blocks, Overwatch squeezed in on Tue/Thu
    (MC,            "17:30", 100, 140, WEEKDAYS),
    (OW,            "19:45", 65, 95,  {1, 3}),
    ("chrome.exe",  "19:45", 10, 20,  {0, 2, 4}),
    (MC,            "21:15", 110, 160, WEEKDAYS),
    # Weekends: marathon Minecraft sessions, Overwatch ~1 hour
    (MC,            "12:45", 200, 250, WEEKEND),
    ("Discord.exe", "16:45", 15, 25,  WEEKEND),
    (OW,            "17:15", 70, 100, {5}),
    (OW,            "17:15", 40, 60,  {6}),
    (MC,            "19:00", 180, 240, WEEKEND),
]

# Apps that sit open in the background: (app, opens, closes, weekdays)
BACKGROUND = [
    ("chrome.exe",  "08:00", "23:30", WEEKDAYS),   # open almost all day, like a real browser
    ("chrome.exe",  "10:00", "23:30", WEEKEND),
    ("Discord.exe", "11:00", "23:45", set(range(7))),
    ("Spotify.exe", "17:00", "23:30", {0, 1, 3, 4, 5, 6}),
]


def hm(text):
    """'17:30' -> minutes since midnight."""
    hour, minute = text.split(":")
    return int(hour) * 60 + int(minute)


def build_day(day, rng):
    """Return (foreground_blocks, open_windows) for one date, in minutes since midnight."""
    weekday = day.weekday()
    entries = sorted(
        (e for e in PLAN if weekday in e[4]), key=lambda e: hm(e[1])
    )

    blocks = []   # (app, start_min, end_min), never overlapping
    cursor = 0
    for app, start, lo, hi, _ in entries:
        # Jitter the start, but never begin before the previous block ended
        begin = max(hm(start) + rng.randint(-10, 10), cursor + rng.randint(1, 5))
        end = min(begin + rng.randint(lo, hi), MAX_END)
        if end - begin >= 5:
            blocks.append((app, begin, end))
            cursor = end

    # Open windows: explicit background times, otherwise first-to-last use of the app
    windows = {}
    for app, opens, closes, days in BACKGROUND:
        if weekday in days:
            windows[app] = (hm(opens), hm(closes))
    for app, begin, end in blocks:
        old_start, old_end = windows.get(app, (begin - 3, end + 3))
        windows[app] = (min(old_start, begin - 3), max(old_end, end + 3))
    # Clamp to the day
    windows = {a: (max(0, s), min(24 * 60 - 1, e)) for a, (s, e) in windows.items()}
    return blocks, windows


def daily_rows(day, blocks, windows):
    """One daily_usage row per app: (date, process, fg_minutes, open_minutes)."""
    foreground = {}
    for app, begin, end in blocks:
        foreground[app] = foreground.get(app, 0) + (end - begin)
    rows = []
    for app, (start, end) in windows.items():
        rows.append((day.isoformat(), app, float(foreground.get(app, 0)), float(end - start)))
    return rows


def sample_rows(day, blocks, windows):
    """Raw samples: foreground every 10 s, plus a 5-minute snapshot of every open app."""
    midnight = datetime.combine(day, time())
    stamp = lambda secs: (midnight + timedelta(seconds=secs)).isoformat(timespec="seconds")
    rows = []

    # Foreground samples: one row per interval while the app is in front
    for app, begin, end in blocks:
        for secs in range(begin * 60, end * 60, SAMPLE_SECONDS):
            rows.append((stamp(secs), app, 1, 0))

    # Open-app snapshots: always is_foreground=0, so foreground time is only ever counted
    # from the 10-second samples above and can't be double counted
    for secs in range(0, 24 * 3600, SNAPSHOT_SECONDS):
        for app, (start, end) in windows.items():
            if start * 60 <= secs < end * 60:
                rows.append((stamp(secs), app, 0, 0))
    return rows


def default_db_path():
    try:
        import db  # the app's own module, if it's next to this script
        return Path(db.get_database_path())
    except Exception:
        return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def ensure_tables(path):
    """Make sure the schema exists; reuse the app's init_db() when possible."""
    with sqlite3.connect(path) as conn:
        have = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if {"samples", "daily_usage", "app_settings"} <= have:
        return
    try:
        import db
        db.init_db(path)
    except Exception as error:
        sys.exit(f"Tables are missing and db.init_db() failed ({error}). Run db.py first.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", help="database file (default: the app's usage.db)")
    parser.add_argument("--end", help="last day of the week, YYYY-MM-DD (default: today)")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--no-samples", action="store_true", help="skip raw samples")
    parser.add_argument("--seed", type=int, default=7, help="change for a different-looking week")
    args = parser.parse_args()

    path = Path(args.db) if args.db else default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup)   # safety net before touching real data
        print(f"Backed up existing database to {backup}")
    ensure_tables(path)

    end_day = date.fromisoformat(args.end) if args.end else date.today()
    days = [end_day - timedelta(days=n) for n in range(args.days - 1, -1, -1)]
    rng = random.Random(args.seed)   # fixed seed, so the data is the same every run

    all_daily, all_samples = [], []
    for day in days:
        blocks, windows = build_day(day, rng)
        all_daily += daily_rows(day, blocks, windows)
        if not args.no_samples:
            all_samples += sample_rows(day, blocks, windows)

    first, last = days[0].isoformat(), days[-1].isoformat()
    with sqlite3.connect(path) as conn:
        # Replace the seeded date range so re-running never duplicates rows
        conn.execute("DELETE FROM daily_usage WHERE date BETWEEN ? AND ?", (first, last))
        conn.executemany(
            "INSERT INTO daily_usage (date, process_name, fg_minutes, open_minutes) VALUES (?, ?, ?, ?)",
            all_daily,
        )
        if not args.no_samples:
            conn.execute(
                "DELETE FROM samples WHERE ts >= ? AND ts < ?",
                (first, (days[-1] + timedelta(days=1)).isoformat()),
            )
            conn.executemany(
                "INSERT INTO samples (ts, process_name, is_foreground, idle) VALUES (?, ?, ?, ?)",
                all_samples,
            )
        # Categories only for apps that have no setting yet, so user choices are never overwritten
        conn.executemany(
            "INSERT OR IGNORE INTO app_settings (process_name, category, excluded) VALUES (?, ?, 0)",
            [
                (process_name.casefold(), category)
                for process_name, category in CATEGORIES.items()
            ],
        )

    print(f"Seeded {first} to {last} into {path}")
    print(f"  daily_usage rows: {len(all_daily)}   samples rows: {len(all_samples)}")
    print("\nForeground hours per day:")
    for day in days:
        todays = {r[1]: r[2] for r in all_daily if r[0] == day.isoformat()}
        mc, ow = todays.get(MC, 0) / 60, todays.get(OW, 0) / 60
        print(f"  {day} {day.strftime('%a')}  Minecraft {mc:4.1f}h   Overwatch {ow:4.1f}h")


if __name__ == "__main__":
    main()
