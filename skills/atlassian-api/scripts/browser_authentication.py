#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#  "httpx",
#  "playwright",
#  "python-dotenv"
# ]
# requires-python = ">=3.12"
# ///
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from json import dumps
from logging import NOTSET, basicConfig, error, info, warning
from os import environ
from pathlib import Path
from platform import system
from subprocess import run
from sys import argv
from time import sleep
from traceback import format_exc

from playwright._impl._errors import TargetClosedError
from playwright.sync_api import sync_playwright

basicConfig(level=NOTSET, format="%(levelname)s %(message)s")
if len(argv) > 1 and (url := argv[1]):
    force = bool(argv[2]) if len(argv) > 2 else False
    app_dir = Path().home() / ".atlassian-api"
    info(f"application state directory is {app_dir}")
    browsers: dict[str, list[tuple[str, str]]] = {
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
    results = None
    sleep_duration = 5
    state_file = app_dir / f"{sha256(url.encode()).hexdigest()}.json"
    results = {"state_file": str(state_file), "success": True}
    system = system().lower()
    token_ttl = 3600 * 8

    info(f"the platform is {system}")
    if state_file.is_file() and not force:
        info("session state file exists")
        modified = datetime.fromtimestamp(state_file.stat().st_mtime, tz=timezone.utc)
        info(f"session state file was last updated on {modified}")
        if modified + timedelta(seconds=token_ttl) > datetime.now(timezone.utc):
            info("session state has time to live")
            print(dumps(results, indent=2))
            exit()
        else:
            warning("session state has expired")
    info("creating new session state")
    browser, channel, path = None, None, None
    for c, p in browsers.get(system):
        if p and (p := Path(p)).exists() and p.is_file():
            info(f"found a browser: channel {c}, path: {p}")
            channel, path = c, p
            break
    info(f"selected browser {channel} at {path}")

    with sync_playwright() as playwright:
        if path:
            try:
                match channel:
                    case "chrome" | "edge":
                        browser = playwright.chromium.launch(executable_path=path, headless=False)
                    case "firefox":
                        browser = playwright.firefox.launch(executable_path=path, headless=False)
                    case _:
                        error("no supported local browser found")
            except Exception as e:
                error(f"the local browser could not be used: {e}")
        if not browser:
            info("installing playwright chromium")
            environ["PLAYWRIGHT_BROWSERS_PATH"] = str(app_dir / "browsers")
            run(["playwright", "install", "chromium"], check=True)
            browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        try:
            if len(argv) > 1 and (url := argv[1]):
                info(f"loading page {url}")
                page.goto(url)
                while True:
                    try:
                        if page.query_selector(
                                'meta[id="atlassian-token"]'
                        ) or page.query_selector(
                            'meta[name="ajs-atl-token"]'
                        ):
                            info("login completion detected via meta tag")
                            state_file.parent.mkdir(exist_ok=True, parents=True)
                            info("saving storage state")
                            context.storage_state(path=str(state_file))
                            break
                        info("waiting for meta tag...")
                        sleep(sleep_duration)
                    except TargetClosedError:
                        raise RuntimeError(f"the browser window was closed prematurely")
                    except:
                        info(format_exc())
        except Exception as e:
            print(dumps(
                {"error_message": f"could not complete the authentication flow: {e}", "success": False},
                indent=2
            ))
            exit(1)
        finally:
            page.close()
            context.close()
            browser.close()
else:
    print(dumps({"error_message": "no url was provided as the first argument", "success": False}, indent=2))
    exit(1)

if __name__ == "__main__":
    print(dumps(results, indent=2))
