#!/usr/bin/env python3
"""
Katowice Fine Checker using Selenium WebDriver
This is the most reliable approach for JavaScript-heavy sites
"""

import argparse
import json
import time
import sys
import os

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False


class KatowiceSeleniumChecker:
    def __init__(self, headless=True):
        if not HAS_SELENIUM:
            raise ImportError("Selenium is required. Install with: pip install selenium")
        
        self.headless = headless
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Make sure chromedriver is installed and in PATH")
            print("Install with: sudo apt-get install chromium-chromedriver")
            print("Or download from: https://chromedriver.chromium.org/")
            raise
    
    def check_license_plate(self, license_plate):
        """Check license plate for fines"""
        if not self.driver:
            return {
                'license_plate': license_plate,
                'status': 'error',
                'message': 'WebDriver not initialized'
            }
        
        try:
            print(f"Navigating to website...")
            self.driver.get('https://spp.katowice.eu/finechecksimple')
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            
            # Handle cookies popup if present - try multiple approaches
            cookie_handled = False
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
                    cookie_button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, selector)))
                    cookie_button.click()
                    print(f"Accepted cookies with selector: {selector}")
                    cookie_handled = True
                    time.sleep(2)
                    break
                except TimeoutException:
                    continue
            
            if not cookie_handled:
                print("No cookie popup found or could not handle it")
                # Try to close any overlays with JavaScript
                try:
                    self.driver.execute_script("""
                        var overlays = document.querySelectorAll('vaadin-dialog-overlay, .overlay, [role="dialog"]');
                        overlays.forEach(function(overlay) {
                            if (overlay.style) overlay.style.display = 'none';
                            if (overlay.remove) overlay.remove();
                        });
                    """)
                    print("Attempted to remove overlays with JavaScript")
                    time.sleep(1)
                except:
                    pass
            
            # Find the license plate input field - try multiple approaches
            print("Looking for input field...")
            input_field = None
            
            # Try different selectors to find the input field
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
                    print(f"Found input field with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not input_field:
                raise Exception("Could not find input field")
            
            # Wait a bit more for the field to be ready
            time.sleep(2)
            
            # Try to interact with the input field
            try:
                input_field.click()
                time.sleep(1)
                input_field.clear()
                input_field.send_keys(license_plate)
                print(f"Entered license plate: {license_plate}")
            except Exception as e:
                print(f"Error with input field interaction: {e}")
                # Try using JavaScript as fallback
                self.driver.execute_script("arguments[0].value = arguments[1];", input_field, license_plate)
                print(f"Used JavaScript to enter license plate: {license_plate}")
            
            # Find and click search button
            print("Looking for search button...")
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
                    print(f"Found search button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not search_button:
                raise Exception("Could not find search button")
            
            # Try to click the search button
            try:
                time.sleep(1)
                search_button.click()
                print("Clicked search button")
            except Exception as e:
                print(f"Error clicking button: {e}")
                # Use JavaScript as fallback
                self.driver.execute_script("arguments[0].click();", search_button)
                print("Used JavaScript to click search button")
            
            # Wait for results
            time.sleep(3)
            
            # Get page content after search
            page_source = self.driver.page_source
            
            return self._parse_results(page_source, license_plate)
            
        except TimeoutException as e:
            return {
                'license_plate': license_plate,
                'status': 'timeout',
                'message': f'Timeout waiting for page elements: {e}'
            }
        except Exception as e:
            return {
                'license_plate': license_plate,
                'status': 'error',
                'message': f'Error during check: {e}'
            }
    
    def _parse_results(self, page_source, license_plate):
        """Parse the results from page source"""
        try:
            # Look for the key messages
            if 'Nie naliczono opłaty dodatkowej' in page_source:
                return {
                    'license_plate': license_plate,
                    'status': 'success',
                    'has_fines': False,
                    'message': 'No additional fees found',
                    'details': 'Nie naliczono opłaty dodatkowej za postój Twojego pojazdu',
                    'reminder': 'Remember to check again after 48 hours from suspected parking violation'
                }
            
            elif any(phrase in page_source for phrase in ['naliczono opłatę', 'opłata dodatkowa']):
                return {
                    'license_plate': license_plate,
                    'status': 'success', 
                    'has_fines': True,
                    'message': 'Additional fees found!',
                    'details': 'Fines detected - check the website for payment information'
                }
            
            elif 'błąd' in page_source.lower() or 'nieprawidłowy' in page_source.lower():
                return {
                    'license_plate': license_plate,
                    'status': 'error',
                    'has_fines': None,
                    'message': 'Invalid license plate or system error'
                }
            
            else:
                # Take a screenshot for debugging if not headless
                if not self.headless:
                    screenshot_path = f"debug_screenshot_{license_plate}.png"
                    self.driver.save_screenshot(screenshot_path)
                    print(f"Screenshot saved: {screenshot_path}")
                
                return {
                    'license_plate': license_plate,
                    'status': 'unknown',
                    'has_fines': None,
                    'message': 'Could not determine result - check screenshot or run in non-headless mode'
                }
        
        except Exception as e:
            return {
                'license_plate': license_plate,
                'status': 'parse_error',
                'message': f'Error parsing results: {e}'
            }
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def install_selenium():
    """Helper function to install selenium"""
    print("Selenium not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    print("Selenium installed. Please also install chromedriver:")
    print("sudo apt-get install chromium-chromedriver")
    print("or download from: https://chromedriver.chromium.org/")


def main():
    parser = argparse.ArgumentParser(description='Katowice parking fine checker using Selenium')
    parser.add_argument('license_plate', help='License plate to check')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--no-headless', action='store_true', help='Run browser in visible mode')
    parser.add_argument('--install-selenium', action='store_true', help='Install selenium')
    
    args = parser.parse_args()
    
    if args.install_selenium:
        install_selenium()
        return
    
    if not HAS_SELENIUM:
        print("❌ Selenium not available")
        print("Install with: python selenium_fine_checker.py --install-selenium")
        print("Or manually: pip install selenium")
        print("Also install: sudo apt-get install chromium-chromedriver")
        return
    
    license_plate = args.license_plate.upper().strip()
    headless = not args.no_headless
    
    print(f"🔍 Checking license plate: {license_plate}")
    print(f"🖥️  Mode: {'Headless' if headless else 'Visible'}")
    print("-" * 50)
    
    try:
        with KatowiceSeleniumChecker(headless=headless) as checker:
            result = checker.check_license_plate(license_plate)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n" + "=" * 60)
            print(f"🚗 RESULT FOR: {result['license_plate']}")
            print("=" * 60)
            
            status_emoji = {
                'success': '✅',
                'error': '❌', 
                'timeout': '⏰',
                'unknown': '❓',
                'parse_error': '🔧'
            }
            
            print(f"{status_emoji.get(result['status'], '❓')} Status: {result['status']}")
            
            if 'has_fines' in result:
                fine_status = result['has_fines']
                if fine_status is True:
                    print("💰 Has fines: YES")
                elif fine_status is False:
                    print("✅ Has fines: NO")
                else:
                    print("❓ Has fines: UNKNOWN")
            
            print(f"📝 Message: {result['message']}")
            
            if 'details' in result:
                print(f"📋 Details: {result['details']}")
            
            if 'reminder' in result:
                print(f"⚠️  Reminder: {result['reminder']}")
            
            print("=" * 60)
    
    except Exception as e:
        error_result = {
            'license_plate': license_plate,
            'status': 'fatal_error',
            'message': str(e)
        }
        
        if args.json:
            print(json.dumps(error_result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    main()