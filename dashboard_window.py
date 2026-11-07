"""Standalone Tkinter dashboard window.

The caller is responsible for fetching the user's record from the database and
passing it to :func:`open_dashboard_window`.  Keeping database access outside
the UI makes this window reusable with any database layer.

Expected ``user_data`` shape::

    {
        "name": "Alex",
        "suggestions": [
            {
                "title": "Take a short reset",
                "body": "A ten-minute walk may help you regain focus.",
                "tag": "Wellbeing",
            }
        ],
        "highlights": ["Completed 4 focus sessions", "Best streak: 6 days"],
        "lowlights": ["Two goals are overdue", "Focus dipped after 3 PM"],
    }
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Mapping, Sequence
from tkinter import messagebox
from typing import Any


COLORS = {
    "background": "#F5F4EF",
    "surface": "#FFFFFF",
    "ink": "#17201D",
    "muted": "#66706C",
    "border": "#DDE2DD",
    "green": "#176B4A",
    "green_soft": "#DDEFE5",
    "red": "#A94343",
    "red_soft": "#F8E5E1",
    "amber": "#E8B84F",
    "amber_soft": "#FFF3CF",
    "nav": "#12221C",
}

FONT = "Arial"

DEFAULT_DATA: dict[str, Any] = {
    "name": "there",
    "suggestions": [
        {
            "title": "Build on your strongest hour",
            "body": (
                "Your best results tend to happen early in the day. Consider "
                "protecting that time for your most important task."
            ),
            "tag": "Personal insight",
        },
        {
            "title": "Try a lighter afternoon",
            "body": (
                "Your energy has been lower after 3 PM. Move one demanding "
                "task earlier and leave routine work for later."
            ),
            "tag": "Suggested adjustment",
        },
    ],
    "highlights": [
        "You completed more planned tasks than last week.",
        "Your morning focus sessions were consistently strong.",
    ],
    "lowlights": [
        "Two goals have not been updated recently.",
        "Afternoon focus was below your usual average.",
    ],
}


def _as_string_list(value: Any) -> list[str]:
    """Return clean display strings from common database result shapes."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence):
        results: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                text = item.get("text") or item.get("title") or item.get("label")
            else:
                text = item
            if text is not None and str(text).strip():
                results.append(str(text).strip())
        return results
    return [str(value)]


def _normalise_suggestions(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []

    suggestions: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, Mapping):
            title = str(item.get("title") or "Suggestion")
            body = str(item.get("body") or item.get("text") or "")
            tag = str(item.get("tag") or item.get("category") or "For you")
        else:
            title, body, tag = "Suggestion", str(item), "For you"
        if body.strip() or title.strip():
            suggestion = {"title": title, "body": body, "tag": tag}
            for key in ("id", "process_name", "type", "features_json"):
                if isinstance(item, Mapping) and item.get(key) is not None:
                    suggestion[key] = str(item[key])
            suggestions.append(suggestion)
    return suggestions


class DashboardWindow:
    """Controller for a dashboard rendered in its own Tkinter window."""

    def __init__(
        self,
        parent: tk.Misc | None,
        user_data: Mapping[str, Any] | None,
        *,
        on_accept: Callable[[Mapping[str, str]], None] | None = None,
        on_dismiss: Callable[[Mapping[str, str]], None] | None = None,
        on_ignore: Callable[[Mapping[str, str]], None] | None = None,
        on_manual_mode: Callable[[], None] | None = None,
        on_audio_settings: Callable[[], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self._owns_root = parent is None
        self.window = tk.Tk() if self._owns_root else tk.Toplevel(parent)
        self.window.title("Your dashboard")
        self.window.geometry("980x780")
        self.window.minsize(760, 650)
        self.window.configure(bg=COLORS["background"])

        incoming = dict(user_data or {})
        self.name = str(incoming.get("name") or DEFAULT_DATA["name"])
        self.suggestions = _normalise_suggestions(
            incoming.get("suggestions", DEFAULT_DATA["suggestions"])
        )
        self.highlights = _as_string_list(
            incoming.get(
                "highlights",
                incoming.get("high_points", DEFAULT_DATA["highlights"]),
            )
        )
        self.lowlights = _as_string_list(
            incoming.get(
                "lowlights",
                incoming.get("low_points", DEFAULT_DATA["lowlights"]),
            )
        )
        self.on_accept = on_accept
        self.on_dismiss = on_dismiss
        self.on_ignore = on_ignore
        self.on_manual_mode = on_manual_mode
        self.on_audio_settings = on_audio_settings
        self.on_close = on_close
        self.suggestion_index = 0

        self._build_scroll_area()
        self._build_header()
        self._build_suggestions()
        self._build_insights()
        self._build_footer_actions()
        self._refresh_suggestion()

        self.window.bind("<Left>", lambda _event: self._change_suggestion(-1))
        self.window.bind("<Right>", lambda _event: self._change_suggestion(1))
        self.window.protocol("WM_DELETE_WINDOW", self._close_window)
        self.window.after_idle(self._update_scroll_region)

    def _build_scroll_area(self) -> None:
        self.canvas = tk.Canvas(
            self.window,
            bg=COLORS["background"],
            highlightthickness=0,
            borderwidth=0,
        )
        scrollbar = tk.Scrollbar(
            self.window, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self.canvas, bg=COLORS["background"])
        self.content.columnconfigure(0, weight=1)
        self.content_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind("<Configure>", lambda _event: self._update_scroll_region())
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(
                self.content_window, width=event.width
            ),
        )
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda event: self.canvas.yview_scroll(int(-event.delta / 120), "units"),
        )

    def _build_header(self) -> None:
        header = tk.Frame(self.content, bg=COLORS["background"])
        header.grid(row=0, column=0, sticky="ew", padx=48, pady=(38, 22))
        header.columnconfigure(0, weight=1)

        tk.Label(
            header,
            text=f"Good to see you, {self.name}",
            bg=COLORS["background"],
            fg=COLORS["ink"],
            font=(FONT, 24, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text="Here is a clear view of what is working and where to adjust.",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=(FONT, 11),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(7, 0))

    def _build_suggestions(self) -> None:
        section = tk.Frame(self.content, bg=COLORS["background"])
        section.grid(row=1, column=0, sticky="ew", padx=48)
        section.columnconfigure(1, weight=1)

        tk.Label(
            section,
            text="Suggestions",
            bg=COLORS["background"],
            fg=COLORS["ink"],
            font=(FONT, 16, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        self.previous_button = self._icon_button(
            section, "<", lambda: self._change_suggestion(-1)
        )
        self.previous_button.grid(row=1, column=0, padx=(0, 16))

        card = tk.Frame(
            section,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=28,
            pady=24,
        )
        self.suggestion_card = card
        card.grid(row=1, column=1, sticky="ew")
        card.columnconfigure(0, weight=1)

        top_line = tk.Frame(card, bg=COLORS["surface"])
        self.suggestion_top_line = top_line
        top_line.grid(row=0, column=0, sticky="ew")
        top_line.columnconfigure(0, weight=1)
        self.suggestion_tag = tk.Label(
            top_line,
            bg=COLORS["amber_soft"],
            fg="#6E5217",
            font=(FONT, 9, "bold"),
            padx=10,
            pady=4,
        )
        self.suggestion_tag.grid(row=0, column=0, sticky="w")
        self.suggestion_count = tk.Label(
            top_line,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT, 9),
        )
        self.suggestion_count.grid(row=0, column=1, sticky="e")

        self.suggestion_title = tk.Label(
            card,
            bg=COLORS["surface"],
            fg=COLORS["ink"],
            font=(FONT, 17, "bold"),
            anchor="w",
            justify="left",
        )
        self.suggestion_title.grid(row=1, column=0, sticky="ew", pady=(18, 8))
        self.suggestion_body = tk.Label(
            card,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT, 11),
            anchor="w",
            justify="left",
            wraplength=610,
        )
        self.suggestion_body.grid(row=2, column=0, sticky="ew")

        actions = tk.Frame(card, bg=COLORS["surface"])
        self.suggestion_actions = actions
        actions.grid(row=3, column=0, sticky="w", pady=(22, 0))
        self.accept_button = self._button(
            actions, "Accept", self._accept_suggestion, primary=True
        )
        self.accept_button.configure(pady=10)
        self.accept_button.pack(side="left")
        self.dismiss_button = self._button(
            actions, "Dismiss", self._dismiss_suggestion
        )
        self.dismiss_button.pack(side="left")
        self.enlarge_button = self._button(
            actions, "Ignore 3 days", self._ignore_suggestion
        )
        self.enlarge_button.pack(side="left")

        self.next_button = self._icon_button(
            section, ">", lambda: self._change_suggestion(1)
        )
        self.next_button.grid(row=1, column=2, padx=(16, 0))

    def _build_insights(self) -> None:
        section = tk.Frame(self.content, bg=COLORS["background"])
        section.grid(row=2, column=0, sticky="ew", padx=48, pady=(30, 0))
        section.columnconfigure(0, weight=1, uniform="insights")
        section.columnconfigure(1, weight=1, uniform="insights")

        tk.Label(
            section,
            text="Your week at a glance",
            bg=COLORS["background"],
            fg=COLORS["ink"],
            font=(FONT, 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self._insight_card(
            section,
            "High points",
            "What is going well",
            self.highlights,
            COLORS["green"],
            COLORS["green_soft"],
        ).grid(row=1, column=0, sticky="nsew", padx=(0, 7))
        self._insight_card(
            section,
            "Low points",
            "Where there is room to improve",
            self.lowlights,
            COLORS["red"],
            COLORS["red_soft"],
        ).grid(row=1, column=1, sticky="nsew", padx=(7, 0))

    def _insight_card(
        self,
        parent: tk.Misc,
        title: str,
        subtitle: str,
        items: list[str],
        accent: str,
        accent_soft: str,
    ) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=22,
            pady=20,
        )
        card.columnconfigure(1, weight=1)
        marker = tk.Label(
            card,
            text="+" if title == "High points" else "-",
            bg=accent_soft,
            fg=accent,
            width=2,
            font=(FONT, 12, "bold"),
        )
        marker.grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, 10))
        tk.Label(
            card,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["ink"],
            font=(FONT, 13, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")
        tk.Label(
            card,
            text=subtitle,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT, 9),
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", pady=(2, 13))

        display_items = items or ["No data available yet."]
        for index, item in enumerate(display_items, start=2):
            tk.Label(
                card,
                text="•",
                bg=COLORS["surface"],
                fg=accent,
                font=(FONT, 12, "bold"),
            ).grid(row=index, column=0, sticky="n", pady=3)
            tk.Label(
                card,
                text=item,
                bg=COLORS["surface"],
                fg=COLORS["ink"],
                font=(FONT, 10),
                justify="left",
                anchor="nw",
                wraplength=280,
            ).grid(row=index, column=1, sticky="ew", pady=3)
        return card

    def _build_footer_actions(self) -> None:
        footer = tk.Frame(self.content, bg=COLORS["background"])
        footer.grid(row=3, column=0, pady=(26, 44))

        self._button(
            footer, "Open manual mode", self._open_manual_mode, primary=True
        ).pack(side="left", padx=6)
        self._button(
            footer, "Audio settings", self._open_audio_settings
        ).pack(side="left", padx=6)

    def _button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        primary: bool = False,
    ) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg="#AEB3AF",
            fg="#FFFFFF",
            activebackground="#AEB3AF",
            activeforeground="#000000",
            relief="flat",
            borderwidth=0,
            highlightbackground=COLORS["border"],
            highlightthickness=0 if primary else 1,
            cursor="hand2",
            font=(FONT, 10, "bold"),
            padx=8,
            pady=9,
            width=14,
        )
        button.bind("<Enter>", lambda _event: button.configure(bg="#AEB3AF", fg="#000000"))
        button.bind("<Leave>", lambda _event: button.configure(bg="#AEB3AF", fg="#FFFFFF"))
        return button

    def _icon_button(
        self, parent: tk.Misc, text: str, command: Callable[[], None]
    ) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg="#AEB3AF",
            fg="#FFFFFF",
            activebackground="#AEB3AF",
            activeforeground="#000000",
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=(FONT, 20, "bold"),
            width=2,
        )
        button.bind("<Enter>", lambda _event: button.configure(bg="#AEB3AF", fg="#000000"))
        button.bind("<Leave>", lambda _event: button.configure(bg="#AEB3AF", fg="#FFFFFF"))
        return button

    def _refresh_suggestion(self) -> None:
        has_suggestions = bool(self.suggestions)
        state = tk.NORMAL if has_suggestions else tk.DISABLED
        for button in (
            self.accept_button,
            self.dismiss_button,
            self.enlarge_button,
        ):
            button.configure(state=state)

        if not has_suggestions:
            self.previous_button.grid_remove()
            self.next_button.grid_remove()
            self.accept_button.grid_remove()
            self.dismiss_button.grid_remove()
            self.enlarge_button.grid_remove()
            empty_background = "#E8EAE8"
            self.suggestion_card.configure(
                bg=empty_background,
                highlightbackground="#D2D6D2",
            )
            for widget in (
                self.suggestion_top_line,
                self.suggestion_tag,
                self.suggestion_count,
                self.suggestion_title,
                self.suggestion_body,
            ):
                widget.configure(bg=empty_background)
            self.suggestion_tag.configure(
                text="UP TO DATE",
                fg=COLORS["muted"],
                bg="#D9DDD9",
            )
            self.suggestion_title.configure(
                text="No suggestions right now",
                fg=COLORS["muted"],
            )
            self.suggestion_body.configure(
                text="New suggestions will appear as more user data becomes available.",
                fg=COLORS["muted"],
            )
            self.suggestion_count.configure(text="0 of 0")
            return

        self.suggestion_card.configure(
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
        )
        for widget in (
            self.suggestion_top_line,
            self.suggestion_tag,
            self.suggestion_count,
            self.suggestion_title,
            self.suggestion_body,
        ):
            widget.configure(bg=COLORS["surface"] if widget is not self.suggestion_tag else COLORS["amber_soft"])
        self.suggestion_tag.configure(fg="#6E5217")
        self.suggestion_title.configure(fg=COLORS["ink"])
        self.suggestion_body.configure(fg=COLORS["muted"])
        self.suggestion_count.configure(fg=COLORS["muted"])
        self.previous_button.grid()
        self.next_button.grid()
        self.accept_button.pack(side="left")
        self.dismiss_button.pack(side="left")
        self.enlarge_button.pack(side="left")

        self.suggestion_index %= len(self.suggestions)
        suggestion = self.suggestions[self.suggestion_index]
        self.suggestion_tag.configure(text=suggestion["tag"].upper())
        self.suggestion_title.configure(text=suggestion["title"])
        self.suggestion_body.configure(text=suggestion["body"])
        self.suggestion_count.configure(
            text=f"{self.suggestion_index + 1} of {len(self.suggestions)}"
        )

    def _change_suggestion(self, amount: int) -> None:
        if self.suggestions:
            self.suggestion_index = (
                self.suggestion_index + amount
            ) % len(self.suggestions)
            self._refresh_suggestion()

    def _current_suggestion(self) -> dict[str, str] | None:
        if not self.suggestions:
            return None
        return self.suggestions[self.suggestion_index]

    def _accept_suggestion(self) -> None:
        suggestion = self._current_suggestion()
        if suggestion is None:
            return
        if self.on_accept:
            self.on_accept(suggestion)
        messagebox.showinfo(
            "Suggestion accepted",
            f'"{suggestion["title"]}" has been added to your plan.',
            parent=self.window,
        )

    def _dismiss_suggestion(self) -> None:
        suggestion = self._current_suggestion()
        if suggestion is None:
            return
        if self.on_dismiss:
            self.on_dismiss(suggestion)
        self.suggestions.pop(self.suggestion_index)
        if self.suggestions:
            self.suggestion_index %= len(self.suggestions)
        else:
            self.suggestion_index = 0
        self._refresh_suggestion()

    def _ignore_suggestion(self) -> None:
        suggestion = self._current_suggestion()
        if suggestion is None:
            return
        if self.on_ignore:
            self.on_ignore(suggestion)
        self.suggestions.pop(self.suggestion_index)
        if self.suggestions:
            self.suggestion_index %= len(self.suggestions)
        else:
            self.suggestion_index = 0
        self._refresh_suggestion()

    def _show_details(self) -> None:
        suggestion = self._current_suggestion()
        if suggestion is None:
            return

        detail = tk.Toplevel(self.window)
        detail.title(suggestion["title"])
        detail.geometry("520x330")
        detail.minsize(440, 280)
        detail.configure(bg=COLORS["surface"])
        detail.transient(self.window)
        detail.grab_set()
        detail.columnconfigure(0, weight=1)
        detail.rowconfigure(1, weight=1)

        tk.Label(
            detail,
            text=suggestion["title"],
            bg=COLORS["surface"],
            fg=COLORS["ink"],
            font=(FONT, 19, "bold"),
            anchor="w",
            wraplength=440,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=32, pady=(30, 12))
        tk.Label(
            detail,
            text=suggestion["body"],
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT, 11),
            anchor="nw",
            justify="left",
            wraplength=440,
        ).grid(row=1, column=0, sticky="nsew", padx=32)
        self._button(detail, "Close", detail.destroy, primary=True).grid(
            row=2, column=0, sticky="e", padx=32, pady=26
        )

    def _open_manual_mode(self) -> None:
        if self.on_manual_mode:
            self.on_manual_mode()
            return
        messagebox.showinfo(
            "Manual mode",
            "Connect this button with your manual mode callback.",
            parent=self.window,
        )

    def _open_audio_settings(self) -> None:
        if self.on_audio_settings:
            self.on_audio_settings()
            return
        messagebox.showinfo(
            "Audio settings",
            "Connect this button with your audio settings callback.",
            parent=self.window,
        )

    def _close_window(self) -> None:
        self.window.destroy()
        if self.on_close is not None:
            self.on_close()

    def _update_scroll_region(self) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def show(self) -> "DashboardWindow":
        """Display the window and start Tk only when no parent was supplied."""
        self.window.focus_set()
        if self._owns_root:
            self.window.mainloop()
        return self


def open_dashboard_window(
    parent: tk.Misc | None = None,
    user_data: Mapping[str, Any] | None = None,
    *,
    on_accept: Callable[[Mapping[str, str]], None] | None = None,
    on_dismiss: Callable[[Mapping[str, str]], None] | None = None,
    on_ignore: Callable[[Mapping[str, str]], None] | None = None,
    on_manual_mode: Callable[[], None] | None = None,
    on_audio_settings: Callable[[], None] | None = None,
    on_close: Callable[[], None] | None = None,
) -> DashboardWindow:
    """Open the dashboard as a root window or as a child ``Toplevel``.

    Pass the existing app window as ``parent``. If ``parent`` is omitted, this
    function creates a root window and runs its event loop for standalone use.
    Database records should be converted to the documented ``user_data`` shape
    before this function is called.
    """
    return DashboardWindow(
        parent,
        user_data,
        on_accept=on_accept,
        on_dismiss=on_dismiss,
        on_ignore=on_ignore,
        on_manual_mode=on_manual_mode,
        on_audio_settings=on_audio_settings,
        on_close=on_close,
    ).show()


if __name__ == "__main__":
    open_dashboard_window(user_data=DEFAULT_DATA)
