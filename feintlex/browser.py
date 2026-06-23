from __future__ import annotations

import logging
import os
import shutil
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path


LOGGER = logging.getLogger("feintlex.browser")

DEFAULT_BROWSER = "brave"
DEFAULT_MODE = "fullscreen"
VALID_MODES = {"fullscreen", "maximized", "normal", "kiosk"}
DEFAULT_BROWSER_NAMES = {"default", "system", "browser"}
BRAVE_PATHS = (
    Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
    Path(r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
)
BRAVE_COMMANDS = ("brave.exe", "brave", "brave-browser")


@dataclass(frozen=True)
class BrowserLaunchPlan:
    url: str
    mode: str
    use_brave: bool
    executable: str | None
    args: list[str]
    fallback_reason: str | None = None


def normalize_browser_mode(mode: str | None = None) -> str:
    selected = (mode or os.environ.get("FEINT_BROWSER_MODE") or DEFAULT_MODE).strip().lower()
    if selected not in VALID_MODES:
        return DEFAULT_MODE
    return selected


def find_brave_executable() -> str | None:
    override = os.environ.get("FEINT_BROWSER_PATH")
    if override and Path(override).exists():
        return str(Path(override))

    for path in BRAVE_PATHS:
        if path.exists():
            return str(path)

    for command in BRAVE_COMMANDS:
        found = shutil.which(command)
        if found:
            return found

    return None


def brave_args_for_url(url: str, mode: str | None = None) -> list[str]:
    selected_mode = normalize_browser_mode(mode)
    args = ["--new-window"]
    if selected_mode == "fullscreen":
        args.append("--start-fullscreen")
    elif selected_mode == "maximized":
        args.append("--start-maximized")
    elif selected_mode == "kiosk":
        args.append("--kiosk")
    args.append(url)
    return args


def get_feint_browser_launch_plan(url: str, mode: str | None = None) -> BrowserLaunchPlan:
    selected_mode = normalize_browser_mode(mode)
    selected_browser = (os.environ.get("FEINT_BROWSER") or DEFAULT_BROWSER).strip().lower()
    if selected_browser in DEFAULT_BROWSER_NAMES:
        return BrowserLaunchPlan(
            url=url,
            mode=selected_mode,
            use_brave=False,
            executable=None,
            args=[],
            fallback_reason=f"FEINT_BROWSER={selected_browser}",
        )

    brave = find_brave_executable()
    if brave:
        return BrowserLaunchPlan(
            url=url,
            mode=selected_mode,
            use_brave=True,
            executable=brave,
            args=brave_args_for_url(url, selected_mode),
        )

    return BrowserLaunchPlan(
        url=url,
        mode=selected_mode,
        use_brave=False,
        executable=None,
        args=[],
        fallback_reason="Brave executable was not found.",
    )


def open_in_feint_browser(url: str, mode: str | None = None) -> bool:
    plan = get_feint_browser_launch_plan(url, mode)
    try:
        if plan.use_brave and plan.executable:
            subprocess.Popen(
                [plan.executable, *plan.args],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True

        LOGGER.warning("Brave unavailable; falling back to default browser.", extra={"reason": plan.fallback_reason})
        return bool(webbrowser.open(url))
    except Exception as exc:
        LOGGER.warning("Browser launch failed.", extra={"error_type": type(exc).__name__})
        return False
