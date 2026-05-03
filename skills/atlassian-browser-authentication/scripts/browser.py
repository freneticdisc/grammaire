#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#  "platformdirs",
#  "playwright"
# ]
# requires-python = ">=3.12"
# ///
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from json import dumps
from os import environ
from platform import system
from subprocess import run
from sys import executable, exit, stderr
from urllib.parse import urlparse

from platformdirs import user_state_path
from playwright.sync_api import Error, sync_playwright

p = ArgumentParser()
p.add_argument("url")
p.add_argument("--force", action="store_true")
args = p.parse_args()

cache_dir = user_state_path(appname="atlassian", ensure_exists=True)
platform = system().lower()
state_file = cache_dir / f"{sha256(urlparse(args.url).netloc.encode()).hexdigest()}.json"
timeout = 1000 * 600
ttl = 28800

stderr.write(f"application state directory is {cache_dir}\n")
stderr.write(f"the platform is {platform}\n")
if state_file.exists() and not args.force:
    mtime = datetime.fromtimestamp(state_file.stat().st_mtime, tz=timezone.utc)
    if mtime + timedelta(seconds=ttl) > datetime.now(timezone.utc):
        stderr.write("\nsession state has time to live")
        print(dumps({"state_file": str(state_file)}, indent=2))
        exit()

with sync_playwright() as playwright:
    try:
        context = playwright.chromium.launch_persistent_context(
            channel="chrome",
            headless=False,
            ignore_default_args=["--disable-component-update"],
            user_data_dir=str(cache_dir / "data" / "chrome")
        )
    except Error as error:
        stderr.write("unable to locate a browser using channel chrome\n")
        try:
            context = playwright.chromium.launch_persistent_context(
                channel="chromium",
                headless=False,
                ignore_default_args=["--disable-component-update"],
                user_data_dir=str(cache_dir / "data" / "chromium")
            )
        except Error as error:
            stderr.write("unable to locate a browser using channel chromium\n")
            try:
                context = playwright.chromium.launch_persistent_context(
                    channel="msedge",
                    headless=False,
                    ignore_default_args=["--disable-component-update"],
                    user_data_dir=str(cache_dir / "data" / "msedge")
                )
            except Error as error:
                stderr.write("unable to locate a browser using channel msedge\n")
                stderr.write("unable to locate or launch a local browser\n")
                stderr.write("installing and starting the bundled chromium browser\n")
                environ["PLAYWRIGHT_BROWSERS_PATH"] = str(cache_dir / "browsers")
                run([executable, "-m", "playwright", "install", "chromium"], check=True)
                context = playwright.chromium.launch_persistent_context(
                    headless=False,
                    ignore_default_args=["--disable-component-update"],
                    user_data_dir=str(cache_dir / "data" / "chromium")
                )
    page = context.pages[0] if context.pages else context.new_page()
    try:
        page.goto(args.url)
        page.wait_for_selector(
            'meta[id="atlassian-token"], meta[name="ajs-atl-token"]',
            state="attached",
            timeout=timeout
        )
        stderr.write("saving browser storage state\n")
        context.storage_state(path=str(state_file))
        print(dumps({"state_file": str(state_file)}, indent=2))
    finally:
        page.close()
        context.close()
