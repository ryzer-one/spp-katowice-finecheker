from __future__ import annotations

import time
from typing import Any, Dict
import sys
import os
import shutil
import tempfile

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException
    HAS_SELENIUM = True
except Exception:  # pragma: no cover - import guarded by runtime env
    HAS_SELENIUM = False


class KatowiceSeleniumChecker:
    def __init__(self, headless: bool = True, verbose: bool = False):
        if not HAS_SELENIUM:
            raise ImportError("Selenium is required. Install with: pip install selenium")

        self.headless = headless
        self.verbose = verbose
        self.driver = None
        self.setup_driver()

    def log(self, msg: str) -> None:
        if self.verbose:
            print(msg, file=sys.stderr, flush=True)

    def setup_driver(self) -> None:
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Ensure a unique, writable user data dir in containers
        user_data_dir = tempfile.mkdtemp(prefix="chrome-user-data-")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--disk-cache-dir=/tmp/chrome-cache")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")

        # Prefer system chromedriver to avoid Selenium Manager cache
        service = None
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService  # type: ignore

            exe = shutil.which("chromedriver")
            if os.path.exists("/usr/bin/chromedriver"):
                exe = "/usr/bin/chromedriver"
            if exe:
                service = ChromeService(executable_path=exe)
        except Exception:
            service = None

        self.log("Launching Chromium WebDriver (headless=%s)" % self.headless)
        if service is not None:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Fallback: let Selenium Manager resolve, may need writable cache
            # Users can set SELENIUM_MANAGER_CACHE to a writable path
            self.driver = webdriver.Chrome(options=chrome_options)

    def check_license_plate(self, license_plate: str) -> Dict[str, Any]:
        if not self.driver:
            return {
                "license_plate": license_plate,
                "status": "error",
                "message": "WebDriver not initialized",
            }

        try:
            self.log("Navigating to website...")
            self.driver.get("https://spp.katowice.eu/finechecksimple")

            wait = WebDriverWait(self.driver, 10)

            cookie_selectors = [
                "//button[contains(text(), 'Zaakceptuj wszystkie')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'wszystkie')]",
                "//vaadin-button[contains(text(), 'Zaakceptuj')]",
                "//button[@class='primary']",
                "//button[contains(@class, 'cookie')]",
                "//div[contains(@class, 'cookie')]//button",
            ]

            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    self.log(f"Accepted cookies with selector: {selector}")
                    cookie_button.click()
                    time.sleep(2)
                    break
                except TimeoutException:
                    continue

            # Find the license plate input field
            input_field = None
            selectors = [
                "//input[@type='text']",
                "//input[contains(@placeholder, 'rejestr')]",
                "//input[contains(@name, 'rejestr')]",
                "//input[contains(@id, 'rejestr')]",
                "//input[contains(@class, 'textbox')]",
                "//textbox",
                "//vaadin-text-field//input",
                "//input",
            ]
            for selector in selectors:
                try:
                    input_field = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    self.log(f"Found input field with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            if not input_field:
                raise Exception("Could not find input field")

            time.sleep(2)
            try:
                input_field.click()
                time.sleep(1)
                input_field.clear()
                input_field.send_keys(license_plate)
                self.log(f"Entered license plate: {license_plate}")
            except Exception:
                self.driver.execute_script("arguments[0].value = arguments[1];", input_field, license_plate)
                self.log("Filled license plate using JavaScript fallback")

            # Click search
            search_button = None
            button_selectors = [
                "//button[contains(text(), 'Szukaj')]",
                "//button[contains(text(), 'Search')]",
                "//vaadin-button[contains(text(), 'Szukaj')]",
                "//vaadin-button",
                "//button[@type='submit']",
                "//button",
            ]
            for selector in button_selectors:
                try:
                    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    self.log(f"Found search button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            if not search_button:
                raise Exception("Could not find search button")

            time.sleep(1)
            try:
                search_button.click()
                self.log("Clicked search button")
            except Exception:
                self.driver.execute_script("arguments[0].click();", search_button)
                self.log("Clicked search via JavaScript fallback")

            time.sleep(3)
            self.log("Parsing results...")
            page_source = self.driver.page_source
            return self._parse_results(page_source, license_plate)

        except TimeoutException as e:
            return {
                "license_plate": license_plate,
                "status": "timeout",
                "message": f"Timeout waiting for page elements: {e}",
            }
        except Exception as e:  # noqa: BLE001
            return {
                "license_plate": license_plate,
                "status": "error",
                "message": f"Error during check: {e}",
            }

    def _parse_results(self, page_source: str, license_plate: str) -> Dict[str, Any]:
        try:
            if "Nie naliczono opłaty dodatkowej" in page_source:
                return {
                    "license_plate": license_plate,
                    "status": "success",
                    "has_fines": False,
                    "message": "No additional fees found",
                    "details": "Nie naliczono opłaty dodatkowej za postój Twojego pojazdu",
                    "reminder": "Remember to check again after 48 hours from suspected parking violation",
                }
            elif any(
                phrase in page_source for phrase in ["naliczono opłatę", "opłata dodatkowa"]
            ):
                return {
                    "license_plate": license_plate,
                    "status": "success",
                    "has_fines": True,
                    "message": "Additional fees found!",
                    "details": "Fines detected - check the website for payment information",
                }
            elif "błąd" in page_source.lower() or "nieprawidłowy" in page_source.lower():
                return {
                    "license_plate": license_plate,
                    "status": "error",
                    "has_fines": None,
                    "message": "Invalid license plate or system error",
                }
            else:
                return {
                    "license_plate": license_plate,
                    "status": "unknown",
                    "has_fines": None,
                    "message": "Could not determine result",
                }
        except Exception as e:  # noqa: BLE001
            return {
                "license_plate": license_plate,
                "status": "parse_error",
                "message": f"Error parsing results: {e}",
            }

    def close(self) -> None:
        if self.driver:
            self.driver.quit()

    def __enter__(self):  # noqa: D401
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: D401
        self.close()
