from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from feintlex import browser


def test_find_brave_executable_prefers_environment_path(tmp_path, monkeypatch):
    brave = tmp_path / "brave.exe"
    brave.write_text("", encoding="utf-8")
    monkeypatch.setenv("FEINT_BROWSER_PATH", str(brave))

    assert browser.find_brave_executable() == str(brave)


def test_brave_launch_plan_defaults_to_fullscreen(tmp_path, monkeypatch):
    brave = tmp_path / "brave.exe"
    brave.write_text("", encoding="utf-8")
    monkeypatch.setenv("FEINT_BROWSER_PATH", str(brave))
    monkeypatch.delenv("FEINT_BROWSER_MODE", raising=False)
    monkeypatch.delenv("FEINT_BROWSER", raising=False)

    plan = browser.get_feint_browser_launch_plan("http://127.0.0.1:8044/dashboard")

    assert plan.use_brave is True
    assert plan.executable == str(brave)
    assert plan.mode == "fullscreen"
    assert plan.args == ["--new-window", "--start-fullscreen", "http://127.0.0.1:8044/dashboard"]


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("maximized", ["--new-window", "--start-maximized", "http://localhost"]),
        ("normal", ["--new-window", "http://localhost"]),
        ("kiosk", ["--new-window", "--kiosk", "http://localhost"]),
        ("unsupported", ["--new-window", "--start-fullscreen", "http://localhost"]),
    ],
)
def test_brave_args_for_url_modes(mode, expected):
    assert browser.brave_args_for_url("http://localhost", mode) == expected


def test_open_in_feint_browser_uses_brave_without_opening_default(tmp_path, monkeypatch):
    brave = tmp_path / "brave.exe"
    brave.write_text("", encoding="utf-8")
    popen = Mock()
    default_open = Mock()
    monkeypatch.setenv("FEINT_BROWSER_PATH", str(brave))
    monkeypatch.setattr(browser.subprocess, "Popen", popen)
    monkeypatch.setattr(browser.webbrowser, "open", default_open)

    assert browser.open_in_feint_browser("http://127.0.0.1:8044/dashboard") is True
    popen.assert_called_once_with(
        [str(brave), "--new-window", "--start-fullscreen", "http://127.0.0.1:8044/dashboard"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    default_open.assert_not_called()


def test_open_in_feint_browser_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("FEINT_BROWSER_PATH", raising=False)
    monkeypatch.delenv("FEINT_BROWSER", raising=False)
    monkeypatch.setattr(browser, "BRAVE_PATHS", ())
    monkeypatch.setattr(browser.shutil, "which", lambda command: None)
    default_open = Mock(return_value=True)
    monkeypatch.setattr(browser.webbrowser, "open", default_open)

    assert browser.open_in_feint_browser("http://127.0.0.1:8044/dashboard") is True
    default_open.assert_called_once_with("http://127.0.0.1:8044/dashboard")


def test_powershell_browser_helper_builds_fullscreen_brave_plan(tmp_path):
    powershell = shutil.which("powershell")
    if powershell is None:
        pytest.skip("PowerShell is not available.")

    brave = tmp_path / "brave.exe"
    brave.write_text("", encoding="utf-8")
    helper = Path(__file__).resolve().parents[1] / "scripts" / "feint_browser.ps1"
    command = (
        f"$env:FEINT_BROWSER_PATH = '{brave}'; "
        f". '{helper}'; "
        "$plan = Get-FeintBrowserLaunchPlan -Url 'http://127.0.0.1:8044/dashboard'; "
        "$plan | ConvertTo-Json -Compress"
    )

    result = subprocess.run(
        [powershell, "-NoProfile", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
    )

    plan = json.loads(result.stdout)
    assert plan["Browser"] == "brave"
    assert plan["FilePath"] == str(brave)
    assert plan["Mode"] == "fullscreen"
    assert plan["Arguments"] == ["--new-window", "--start-fullscreen", "http://127.0.0.1:8044/dashboard"]
