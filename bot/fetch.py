#!/usr/bin/env python3
"""Coleta seguidores scrapando a página do perfil com cookie (sem API)."""

from __future__ import annotations

import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_store import append_snapshot, get_last_snapshot, init_csv
from profiles import PROFILES

COOKIES_FILE = Path(__file__).parent.parent / ".cookies"

CHROME_CANDIDATES = (
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/snap/bin/chromium",
    "/usr/bin/google-chrome",
)
CHROMEDRIVER_CANDIDATES = ("/usr/bin/chromedriver",)


def load_cookie_header() -> str:
    if COOKIES_FILE.is_file():
        cookie = COOKIES_FILE.read_text(encoding="utf-8").strip()
        if cookie:
            return cookie
    env = (os.environ.get("INSTAGRAM_COOKIES") or "").strip()
    if env:
        return env
    raise RuntimeError("Cookie obrigatório em .cookies (ou INSTAGRAM_COOKIES)")


def parse_cookie_pairs(cookie_header: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for part in cookie_header.split(";"):
        part = part.strip()
        if "=" in part:
            name, value = part.split("=", 1)
            pairs[name.strip()] = value.strip()
    return pairs


def parse_count(raw: str) -> int:
    raw = raw.strip().lower().replace(" ", "").replace("\u00a0", "")
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else 0


def _first_existing(paths: tuple[str, ...]) -> str | None:
    for path in paths:
        if path and os.path.isfile(path):
            return path
    return None


def create_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--lang=en-US")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.page_load_strategy = "eager"

    chrome_bin = (
        os.environ.get("CHROME_BIN")
        or _first_existing(CHROME_CANDIDATES)
        or shutil.which("chromium-browser")
        or shutil.which("chromium")
        or shutil.which("google-chrome")
    )
    if not chrome_bin:
        raise WebDriverException("Chromium não encontrado")
    opts.binary_location = chrome_bin

    driver_path = (
        os.environ.get("CHROMEDRIVER")
        or _first_existing(CHROMEDRIVER_CANDIDATES)
        or shutil.which("chromedriver")
    )
    service = Service(driver_path) if driver_path else Service()
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(25)
    driver.set_script_timeout(20)
    return driver


def inject_cookies(driver: webdriver.Chrome, cookie_header: str) -> None:
    driver.get("https://www.instagram.com/")
    time.sleep(1)
    driver.delete_all_cookies()
    for name, value in parse_cookie_pairs(cookie_header).items():
        driver.add_cookie(
            {
                "name": name,
                "value": value,
                "domain": ".instagram.com",
                "path": "/",
            }
        )
    driver.get("https://www.instagram.com/")
    time.sleep(1)
    if "/accounts/login" in driver.current_url:
        raise ValueError("Cookie inválido/expirado — Instagram pediu login")


def extract_followers(driver: webdriver.Chrome) -> int | None:
    # Contagem exata no atributo title do span de seguidores
    for el in driver.find_elements(By.CSS_SELECTOR, "span[title]"):
        title = (el.get_attribute("title") or "").strip()
        text = (el.text or "").strip()
        if not re.fullmatch(r"[\d.,\s]+", title):
            continue
        # O texto visível costuma ser abreviado (1.9M); o title tem o número cheio
        if text and re.search(r"[kmb]$", text, re.I):
            return parse_count(title)
        parent = el.find_element(By.XPATH, "./ancestor::li[1]|./ancestor::a[1]|./..")
        blob = (parent.text or "").lower()
        if "follower" in blob or "seguidor" in blob:
            return parse_count(title)

    # Fallback: qualquer span[title] numérico “grande” na área de métricas
    candidates = []
    for el in driver.find_elements(By.CSS_SELECTOR, "header span[title], section span[title]"):
        title = (el.get_attribute("title") or "").strip()
        if re.fullmatch(r"[\d.,\s]+", title):
            candidates.append(parse_count(title))
    if candidates:
        return max(candidates)
    return None


def fetch_followers(driver: webdriver.Chrome, username: str) -> int:
    url = f"https://www.instagram.com/{username}/"
    driver.get(url)
    if "/accounts/login" in driver.current_url:
        raise ValueError(f"@{username}: redirecionou para login (cookie)")

    WebDriverWait(driver, 18).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "header, main, span[title]"))
    )

    try:
        WebDriverWait(driver, 12).until(lambda d: extract_followers(d) is not None)
    except TimeoutException:
        pass

    count = extract_followers(driver)
    if count is None or count <= 0:
        raise ValueError(f"@{username}: não achou contagem exata na página")
    return count


def main():
    init_csv()
    cookie_header = load_cookie_header()
    ts = datetime.now(timezone.utc).isoformat()
    errors: list[str] = []

    driver = None
    try:
        driver = create_driver()
        inject_cookies(driver, cookie_header)

        for profile in PROFILES:
            username = profile["username"]
            try:
                followers = fetch_followers(driver, username)
            except Exception as e:
                msg = str(e)
                errors.append(msg)
                print(f"ERRO {msg}", file=sys.stderr)
                continue

            last = get_last_snapshot(username)
            delta = followers - last["followers"] if last else 0
            # Ignora baseline suja de aproximações (ex.: 2_000_000)
            if last and last["followers"] > 0:
                ratio = abs(delta) / last["followers"]
                if ratio > 0.15 and last["followers"] % 100_000 == 0:
                    delta = 0

            append_snapshot(username, followers, delta, ts=ts)
            sign = "+" if delta >= 0 else ""
            print(
                f"[{ts}] @{username} ({profile['display_name']}): "
                f"{followers:,} seguidores ({sign}{delta})"
            )
            time.sleep(1.2)
    finally:
        if driver:
            driver.quit()

    if errors and len(errors) == len(PROFILES):
        sys.exit(1)


if __name__ == "__main__":
    main()
