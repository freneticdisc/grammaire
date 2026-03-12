#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#  "cyclopts",
#  "playwright"
# ]
# requires-python = ">=3.12"
# ///
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from os import environ
from pathlib import Path
from platform import system
from subprocess import run
from sys import exit
from typing import Annotated, Optional

from cyclopts.core import App
from cyclopts.parameter import Parameter
from playwright.sync_api import sync_playwright

from variables import APP_DIR, BROWSERS_CACHE

BROWSERS = {
    "darwin": [
        ("chrome", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ("chrome", f"{Path.home()}/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ("edge", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        ("edge", f"{Path.home()}/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        ("firefox", "/Applications/Firefox.app/Contents/MacOS/firefox"),
        ("firefox", f"{Path.home()}/Applications/Firefox.app/Contents/MacOS/firefox")
    ],
    "linux": [
        ("chrome", "google-chrome"),
        ("chrome", "google-chrome-stable"),
        ("chrome", "chromium"),
        ("chrome", "chromium-browser"),
        ("edge", "microsoft-edge"),
        ("edge", "microsoft-edge-stable"),
        ("firefox", "firefox"),
        ("firefox", "firefox-esr")
    ],
    "windows": [
        ("chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("chrome", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ("edge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ("edge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ("firefox", r"C:\Program Files\Mozilla Firefox\firefox.exe"),
        ("firefox", r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe")
    ],
}
STATE_FILE = None
TIMEOUT = 1000 * 600
TTL = 28800

application = App(exit_on_error=False, print_error=False)


def error(msg: str) -> None:
    application.console.print_json(
        data={"error_message": msg, "success": False},
        indent=2,
        sort_keys=True
    )
    exit(1)


def log(msg: str, log_locals: bool = False) -> None:
    application.error_console.log(msg, log_locals=log_locals)


def success() -> None:
    application.console.print_json(data={"state_file": str(STATE_FILE)}, indent=2, sort_keys=True)
    exit()


@application.default
def default(
        url: str,
        force: Annotated[Optional[bool], Parameter(negative="")] = False
):
    global STATE_FILE
    platform = system().lower()
    log(f"application state directory is {APP_DIR}")
    log(f"the platform is {platform}")

    STATE_FILE = APP_DIR / f"{sha256(url.encode()).hexdigest()}.json"
    if STATE_FILE.exists() and not force:
        mtime = datetime.fromtimestamp(STATE_FILE.stat().st_mtime, tz=timezone.utc)
        if mtime + timedelta(seconds=TTL) > datetime.now(timezone.utc):
            log("session state has time to live")
            success()

    with sync_playwright() as playwright:
        try:
            browser = None
            for channel, path in BROWSERS.get(platform):
                if path and (path := Path(path)).exists() and path.is_file():
                    match channel:
                        case "chrome" | "edge":
                            browser = playwright.chromium.launch(executable_path=path, headless=False)
                        case "firefox":
                            browser = playwright.firefox.launch(executable_path=path, headless=False)
                        case _:
                            raise RuntimeError("no supported local browser found")
        except:
            log("unable to locate or launch a local browser")
            log("installing and starting the bundled chromium browser")
            environ["PLAYWRIGHT_BROWSERS_PATH"] = str(BROWSERS_CACHE)
            run(["playwright", "install", "chromium"], check=True)
            browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url)
            page.wait_for_selector(
                'meta[id="atlassian-token"], meta[name="ajs-atl-token"]',
                state="attached",
                timeout=TIMEOUT
            )
            log("saving browser storage state")
            APP_DIR.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(STATE_FILE))
            success()
        finally:
            page.close()
            context.close()
            browser.close()
    log("something went wrong", log_locals=True)
    error("an unknown error has occurred")


if __name__ == "__main__":
    try:
        application()
    except Exception as ex:
        error(str(ex))
