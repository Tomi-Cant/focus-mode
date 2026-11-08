"""Generate stable, factual highlight and lowlight messages."""

from __future__ import annotations

import hashlib
import random
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping


def format_minutes(value) -> str:
    minutes = max(0, int(round(float(value))))
    hours, remainder = divmod(minutes, 60)
    if hours and remainder:
        return f"{hours}h {remainder}m"
    if hours:
        return f"{hours}h"
    return f"{remainder}m"


TEMPLATES = {
    "average_shift_high": [
        "{subject} is down to {current} a day lately, below the usual {baseline}.",
        "Daily {subject} time is {current} lately, compared with {baseline} normally.",
        "{subject} now averages {current} a day, down from the usual {baseline}.",
    ],
    "average_shift_low": [
        "{subject} is taking more of your day: {current} on average over the last {days} days, against your usual {baseline}.",
        "Daily {subject} time is {current} lately, compared with the usual {baseline}.",
        "{subject} averages {current} over the last {days} days, up from {baseline} normally.",
    ],
    "trend_down": [
        "{subject} time has decreased on {days} consecutive days, from {start} to {end}.",
        "Your {subject} time moved from {start} to {end} over {days} days in a row.",
        "{subject} is down across {days} consecutive days, ending at {end}.",
    ],
    "trend_up": [
        "{subject} time has risen on {days} consecutive days, from {start} to {end}.",
        "{subject} increased over {days} days in a row, moving from {start} to {end}.",
        "{subject} is up across {days} consecutive days, ending at {end}.",
    ],
    "late_night_high": [
        "{subject} time after 10 PM is {current}% lately, down from {baseline}%.",
        "Late-night {subject} use is {current}% of your time, compared with {baseline}%.",
        "After 10 PM, {subject} accounts for {current}% lately, from {baseline}% previously.",
    ],
    "late_night_low": [
        "{subject} time after 10 PM accounts for {current}% this {period}, compared with {baseline}% normally.",
        "{current}% of {subject} time landed after 10 PM this {period}, versus {baseline}% normally.",
        "Late-night {subject} time is {current}% this {period}, against the usual {baseline}%.",
    ],
    "streak_high": [
        "{days} days in a row under your usual {subject} time.",
        "{subject} stayed below its usual time for {days} consecutive days.",
        "The last {days} days were under the usual {subject} time.",
    ],
    "streak_low": [
        "{days} days in a row above your usual {subject} time.",
        "{subject} stayed above its usual time for {days} consecutive days.",
        "The last {days} days were above the usual {subject} time.",
    ],
    "category_high": [
        "{category} time is {current} a day lately, {difference} below usual.",
        "{category} averages {current} daily, {difference} under the usual amount.",
        "Daily {category} time is {current}, with a {difference} decrease from usual.",
    ],
    "category_low": [
        "{category} is at {current} a day lately, {difference} above usual.",
        "Daily {category} time is {current}, {difference} higher than usual.",
        "{category} averages {current} a day, with {difference} added over usual.",
    ],
    "ban_attempts_high": [
        "Attempts to open blocked apps fell from {previous} to {current}.",
        "Blocked-app attempts changed from {previous} to {current}.",
        "There were {current} attempts to open blocked apps, down from {previous}.",
    ],
    "ban_attempts_low": [
        "You tried to open blocked apps {current} times this {period}, up from {previous} the {comparison_period}.",
        "Blocked-app attempts increased from {previous} to {current} this {period}.",
        "This {period} had {current} attempts to open blocked apps, compared with {previous} the {comparison_period}.",
    ],
}

INSIGHT_LABELS = {
    "average_shift_high": "Average Shift Down",
    "average_shift_low": "Average Shift Up",
    "trend_down": "Trend Down",
    "trend_up": "Trend Up",
    "late_night_high": "Late Night Down",
    "late_night_low": "Late Night Up",
    "streak_high": "Below-Average Streak",
    "streak_low": "Above-Average Streak",
    "category_high": "Category Trend Down",
    "category_low": "Category Trend Up",
    "ban_attempts_high": "Ban Attempts Down",
    "ban_attempts_low": "Ban Attempts Up",
}


def _template_values(insight_type: str, data: Mapping) -> dict[str, str]:
    subject = str(data.get("subject") or data.get("category") or "")
    values = dict(data)
    values["subject"] = subject
    values["category"] = subject
    if "current" in data and "current_minutes" not in insight_type:
        pass
    for key in ("current", "baseline", "start", "end", "difference", "previous"):
        if key in data and isinstance(data[key], (int, float)):
            unit = data.get("unit", "minutes")
            if insight_type.startswith("late_night") or unit == "percent":
                values[key] = str(data[key])
            elif unit == "count":
                values[key] = str(int(data[key]))
            elif key == "current" and insight_type.startswith("late_night"):
                values[key] = str(data[key])
            else:
                values[key] = format_minutes(data[key])
    values.setdefault("period", "week")
    values.setdefault("comparison_period", "week before")
    values.setdefault("days", str(data.get("days", "")))
    values.setdefault("current", str(data.get("current", "")))
    values.setdefault("previous", str(data.get("previous", "")))
    return {key: str(value) for key, value in values.items()}


def render_insight(insight_type: str, data: Mapping, date) -> str:
    """Render one deterministic template using only values in data."""
    templates = TEMPLATES.get(insight_type)
    if not templates:
        raise KeyError(f"Unknown insight type: {insight_type}")
    seed = f"{date.isoformat() if hasattr(date, 'isoformat') else date}:{data.get('subject') or data.get('category') or ''}:{insight_type}"
    choice = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % len(templates)
    values = _template_values(insight_type, data)
    try:
        return templates[choice].format(**values)
    except KeyError as error:
        raise ValueError(f"Missing insight data: {error.args[0]}") from error


def message_numbers(message: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?%|\d+", message)


def message_numbers_are_supported(message: str, data: Mapping) -> bool:
    numbers = [number.rstrip("%") for number in message_numbers(message)]
    supported = set()
    for key, value in data.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            supported.add(str(int(value)) if float(value).is_integer() else str(value))
            if key not in {"days", "current", "baseline", "start", "end", "difference", "previous"}:
                continue
            minutes = int(value)
            hours, remainder = divmod(minutes, 60)
            if hours:
                supported.add(str(hours))
                if remainder:
                    supported.add(str(remainder))
            else:
                supported.add(str(remainder))
    supported.update(re.findall(r"\b\d+\b", " ".join(str(value) for value in data.values())))
    return all(number in supported for number in numbers)


def _daily_rows(connection, process_name):
    return [
        (date, float(minutes))
        for date, minutes in connection.execute(
            """
            SELECT date, fg_minutes FROM daily_usage
            WHERE process_name = ?
            ORDER BY date ASC
            """,
            (process_name,),
        ).fetchall()
    ]


def _eligible_trend(values):
    if len(values) < 3:
        return None
    recent = values[-3:]
    change = recent[-1] - recent[0]
    significant = abs(change) >= 45
    percent_shift = abs(change) >= max(45, recent[0] * 0.15)
    if (
        recent[0] < recent[1] < recent[2]
        and significant
        and percent_shift
    ):
        return recent, "trend_up"
    if (
        recent[0] > recent[1] > recent[2]
        and significant
        and percent_shift
    ):
        return recent, "trend_down"
    return None


def _friendly_subject(process_name):
    try:
        from suggestion_ui import humanize_application_name
        return humanize_application_name(process_name)
    except Exception:
        return process_name.removesuffix(".exe").replace("_", " ").replace(".", " ").title()


def generate_insights(database_path=None, date=None, maximum=2):
    """Select available highlight and lowlight candidates with stable random choice."""
    database_path = Path(database_path) if database_path else Path(
        __import__("os").environ["LOCALAPPDATA"]
    ) / "Focused Up" / "usage.db"
    date = date or datetime.now().date()
    today = date.isoformat()
    highlights = []
    lowlights = []

    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        processes = [
            row["process_name"]
            for row in connection.execute(
                """
                SELECT DISTINCT process_name FROM daily_usage
                WHERE date >= date(?, '-13 days')
                """,
                (today,),
            ).fetchall()
        ]

        for process_name in processes:
            rows = _daily_rows(connection, process_name)
            if len(rows) < 5:
                continue
            subject = _friendly_subject(process_name)
            recent = [minutes for _, minutes in rows[-3:]]
            baseline_rows = rows[-7:-3]
            baseline = (
                sum(minutes for _, minutes in baseline_rows) / len(baseline_rows)
                if baseline_rows
                else sum(minutes for _, minutes in rows[:-3])
                / max(1, len(rows[:-3]))
            )
            current = sum(recent) / 3
            average_change = abs(current - baseline)
            if (
                current <= baseline * 0.85
                and average_change >= 45
            ):
                highlights.append(
                    ("average_shift_high", {
                        "subject": subject, "current": current,
                        "baseline": baseline,
                    })
                )
            elif (
                current >= baseline * 1.15
                and average_change >= 45
            ):
                lowlights.append(
                    ("average_shift_low", {
                        "subject": subject, "current": current,
                        "baseline": baseline, "days": 3,
                    })
                )

            trend = _eligible_trend([minutes for _, minutes in rows[-3:]])
            if trend:
                trend_values, trend_type = trend
                if trend_type == "trend_down":
                    highlights.append((trend_type, {
                        "subject": subject, "days": 3,
                        "start": trend_values[0], "end": trend_values[-1],
                    }))
                else:
                    lowlights.append((trend_type, {
                        "subject": subject, "days": 3,
                        "start": trend_values[0], "end": trend_values[-1],
                    }))

            streak_values = [minutes for _, minutes in rows[-3:]]
            if (
                all(value < baseline * 0.85 for value in streak_values)
                and all(baseline - value >= 45 for value in streak_values)
            ):
                highlights.append(("streak_high", {"subject": subject, "days": 3}))
            elif (
                all(value > baseline * 1.15 for value in streak_values)
                and all(value - baseline >= 45 for value in streak_values)
            ):
                lowlights.append(("streak_low", {"subject": subject, "days": 3}))

            after_ten = connection.execute(
                """
                SELECT COUNT(*) FROM samples
                WHERE process_name = ?
                    AND idle = 0
                    AND substr(ts, 1, 10) >= date(?, '-6 days')
                    AND CAST(substr(ts, 12, 2) AS INTEGER) >= 22
                """,
                (process_name, today),
            ).fetchone()[0]
            total = connection.execute(
                """
                SELECT COUNT(*) FROM samples
                WHERE process_name = ?
                    AND idle = 0
                    AND substr(ts, 1, 10) >= date(?, '-6 days')
                """,
                (process_name, today),
            ).fetchone()[0]
            if total >= 30:
                late_percent = round(after_ten * 100 / total)
                if late_percent <= 10 and late_percent + 15 <= 100:
                    highlights.append(("late_night_high", {
                        "subject": subject, "current": late_percent,
                        "baseline": late_percent + 15,
                    }))
                elif late_percent >= 25:
                    lowlights.append(("late_night_low", {
                        "subject": subject, "current": late_percent,
                        "baseline": late_percent - 15, "period": "week",
                    }))

        category_totals = connection.execute(
            """
            SELECT s.category, AVG(d.fg_minutes)
            FROM daily_usage d
            JOIN app_settings s ON lower(s.process_name) = lower(d.process_name)
            WHERE d.date >= date(?, '-6 days')
            GROUP BY s.category
            """,
            (today,),
        ).fetchall()
        for category, current in category_totals:
            if not category or category == "uncategorized":
                continue
            baseline_row = connection.execute(
                """
                SELECT AVG(d.fg_minutes)
                FROM daily_usage d
                JOIN app_settings s ON lower(s.process_name) = lower(d.process_name)
                WHERE s.category = ?
                    AND d.date < date(?, '-6 days')
                    AND d.date >= date(?, '-13 days')
                """,
                (category, today, today),
            ).fetchone()
            if not baseline_row or baseline_row[0] is None:
                continue
            baseline = float(baseline_row[0])
            current = float(current)
            difference = abs(current - baseline)
            if difference < 45 or difference < baseline * 0.15:
                continue
            if current < baseline:
                highlights.append(("category_high", {
                    "category": category.title(), "current": current,
                    "difference": difference,
                }))
            else:
                lowlights.append(("category_low", {
                    "category": category.title(), "current": current,
                    "difference": difference,
                }))

        ban_counts = []
        for days, label in ((7, "week"), (14, "two weeks")):
            cutoff = (datetime.combine(date, datetime.min.time(), tzinfo=timezone.utc) - timedelta(days=days)).isoformat()
            ban_counts.append(connection.execute(
                "SELECT COUNT(*) FROM ban_attempts WHERE ts >= ?",
                (cutoff,),
            ).fetchone()[0] if "ban_attempts" in {
                row["name"] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            } else 0)
        if ban_counts[0] >= 3:
            previous = max(0, ban_counts[1] - ban_counts[0])
            percent_change = abs(ban_counts[0] - previous)
            significant = (
                previous == 0
                and ban_counts[0] >= 1
                or previous > 0
                and percent_change / previous >= 0.15
            )
            if ban_counts[0] < previous and significant:
                highlights.append(("ban_attempts_high", {
                    "previous": previous, "current": ban_counts[0], "unit": "count",
                }))
            elif ban_counts[0] > previous and significant:
                lowlights.append(("ban_attempts_low", {
                    "previous": previous, "current": ban_counts[0],
                    "period": "week", "comparison_period": "week before",
                    "unit": "count",
                }))

    seed = int(hashlib.sha256(f"{today}:insights".encode()).hexdigest()[:12], 16)
    rng = random.Random(seed)
    rng.shuffle(highlights)
    rng.shuffle(lowlights)

    def render(candidates):
        messages = []
        used = set()
        for insight_type, data in candidates:
            message = render_insight(insight_type, data, date)
            if message in used:
                continue
            used.add(message)
            messages.append({
                "label": INSIGHT_LABELS[insight_type],
                "message": message,
            })
            if len(messages) >= maximum:
                break
        return messages

    return {"highlights": render(highlights), "lowlights": render(lowlights)}
