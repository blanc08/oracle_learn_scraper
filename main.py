import csv
import logging
import os
import time
from urllib.parse import urljoin

# Web Scraping libraries
from bs4 import BeautifulSoup
from seleniumwire import webdriver  # Import from seleniumwire
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.remote.webelement import WebElement

import retrying

from utils import make_output_dir, parse_m3u8
from dotenv import load_dotenv
import argparse

# Logger
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Scraping:
    def __init__(self, web_driver: webdriver.Chrome, base_url):
        # Prepare output dir in case not exist
        make_output_dir()

        self.driver = web_driver
        self.base_url = base_url
        self.items = []
        self.course_links = []
        self.csv_base_path = os.path.join(os.path.curdir, "output/csv")

        self.authentication()

    def prepase_output_directories(self):
        """
        Preparing output directories if not exist
        """
        os.makedirs("output/csv", exist_ok=True)
        os.makedirs("output/m3u8", exist_ok=True)
        os.makedirs("output/videos", exist_ok=True)

    @retrying.retry(
        stop_max_attempt_number=3,
        wait_fixed=2000,
        retry_on_exception=lambda e: isinstance(
            e, (NoSuchElementException, TimeoutException)
        ),
    )
    def authentication(self):
        """Authenticate with Oracle Learn website with retry mechanism"""
        logger.warning("authenticating")

        self.driver.get(
            "https://mylearn.oracle.com/arrivals-gate?access_t=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE1NTE4YmQ1LTE3ZDktNDAzZS04OWYxLWZkNjFmYjAwYzk3NCIsImZpcnN0TmFtZSI6IkJlbmhhcmRpIiwibGFzdE5hbWUiOiJDaGFuZHJhIiwiZW1haWwiOiJiZW5oYXJkaS5jaGFuZHJhQG1ldHJvZGF0YS5jby5pZCIsImxlZ2FjeUd1aWQiOiIwRTgwNjI2QjBBRUQ1MDNDRTA1MEU2MEFEMTdGMTlERCIsInBlcm1pc3Npb25zIjpbInN0dWRlbnRfcHJvZmlsZSIsIm5vdGlmaWNhdGlvbiIsImludGVncmF0aW9uIl0sImxlYXJuZXJSb2xlUHJvZmlsZUlkIjoiMWMwZmNjNDMtNTFiNy00NDRmLWI2OTAtOTFmZTU4NGM0MjkzIiwiaW5kZXhlcyI6WyJtbHByb2RfY29udGVudF9vdV9pbmRleCIsIm1scHJvZF9jb250ZW50X2Zvb2RuYmV2X2luZGV4IiwibWxwcm9kX2NvbnRlbnRfcHJvZHVjdF9zdXBwb3J0X2luZGV4Il0sImNvbnRlbnRPd25lcnMiOlt7ImlkIjoiMTlmZDIwN2YtYjdlNC00MzdlLWIyOTYtM2M4Njc1ZGUwOWZkIiwibmFtZSI6Ik9VIiwibGVnYWN5TGVhcm5Pd25lcklkIjoxLCJsYWJlbCI6Ik9VIn0seyJpZCI6Ijg3ZGVjM2JmLTAxNmMtNGM5Ni05ZDVjLTE2MmM0ODhkOTJhNCIsIm5hbWUiOiJGT09ETkJFViIsImxlZ2FjeUxlYXJuT3duZXJJZCI6OCwibGFiZWwiOiJGT09ETkJFViJ9LHsiaWQiOiJmMGViMWNkMS1iMGIzLTRmODgtODVmZi05ZDFmOTk3ZmRmMmQiLCJuYW1lIjoiUFJPRFVDVF9TVVBQT1JUIiwibGVnYWN5TGVhcm5Pd25lcklkIjo2LCJsYWJlbCI6IlBST0RVQ1RfU1VQUE9SVCJ9LHsiaWQiOiJkMWM5M2IwYi1jY2M3LTRmNWYtYjVkMy05OThmZDBjZDM0Y2QiLCJuYW1lIjoiSE9TUElUQUxJVFkiLCJsZWdhY3lMZWFybk93bmVySWQiOjcsImxhYmVsIjoiSE9TUElUQUxJVFkifV0sImlhdCI6MTc0MDI5Mzg3NiwiZXhwIjoxNzQwMjk1MDc2fQ.bFUGpvFFuT0ZTHCb8iKS-sYIG0NUf6GjTRVCGrYIuA4&goTo=https%3A%2F%2Fmylearn.oracle.com%2Fou%2Fhome"
        )

        # Wait for page to be loaded completely
        time.sleep(5)

        # Log current URL to debug
        logger.warning(f"Current URL: {self.driver.current_url}")

        # Take a screenshot for debugging (optional)
        self.driver.save_screenshot("login_page.png")
        logger.warning("Saved screenshot as login_page.png")

        # Use explicit wait instead of implicit
        wait = WebDriverWait(self.driver, 20)

        try:
            # Try multiple selectors for the username field
            selectors = [
                (By.ID, "idcs-signin-basic-signin-form-username"),
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name='username']"),
            ]

            username_field = None
            for selector_type, selector_value in selectors:
                try:
                    logger.warning(
                        f"Trying to find username field with {selector_type}: {selector_value}"
                    )
                    username_field = wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    if username_field:
                        logger.warning(
                            f"Found username field with {selector_type}: {selector_value}"
                        )
                        break
                except (NoSuchElementException, TimeoutException):
                    continue

            if not username_field:
                raise NoSuchElementException(
                    "Could not find username field with any of the known selectors"
                )

            load_dotenv()
            username = os.getenv("EMAIL")
            username_field.clear()
            username_field.send_keys(username)
            logger.warning(f"Entered username: {username}")

            # Try multiple selectors for the continue button
            button_selectors = [
                (By.ID, "idcs-signin-basic-signin-form-submit"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (
                    By.XPATH,
                    "//button[contains(text(), 'Continue') or contains(text(), 'Next')]",
                ),
            ]

            continue_button = None
            for selector_type, selector_value in button_selectors:
                try:
                    logger.warning(
                        f"Trying to find continue button with {selector_type}: {selector_value}"
                    )
                    continue_button = wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    if continue_button:
                        logger.warning(
                            f"Found continue button with {selector_type}: {selector_value}"
                        )
                        break
                except (NoSuchElementException, TimeoutException):
                    continue

            if not continue_button:
                raise NoSuchElementException(
                    "Could not find continue button with any of the known selectors"
                )

            continue_button.click()
            logger.warning("Clicked continue button")

            # Wait for password field
            time.sleep(3)

            # Try multiple selectors for the password field
            password_selectors = [
                (By.ID, "idcs-auth-pwd-input|input"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[name='password']"),
            ]

            password_field = None
            for selector_type, selector_value in password_selectors:
                try:
                    logger.warning(
                        f"Trying to find password field with {selector_type}: {selector_value}"
                    )
                    password_field = wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    if password_field:
                        logger.warning(
                            f"Found password field with {selector_type}: {selector_value}"
                        )
                        break
                except (NoSuchElementException, TimeoutException):
                    continue

            if not password_field:
                raise NoSuchElementException(
                    "Could not find password field with any of the known selectors"
                )

            password = os.getenv("PASSWORD")
            password_field.clear()
            password_field.send_keys(password)
            logger.warning("Entered password")

            # Try multiple selectors for the login button
            login_button_selectors = [
                (By.ID, "idcs-mfa-mfa-auth-user-password-submit-button"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (
                    By.XPATH,
                    "//button[contains(text(), 'Sign In') or contains(text(), 'Login')]",
                ),
            ]

            login_button = None
            for selector_type, selector_value in login_button_selectors:
                try:
                    logger.warning(
                        f"Trying to find login button with {selector_type}: {selector_value}"
                    )
                    login_button = wait.until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    if login_button:
                        logger.warning(
                            f"Found login button with {selector_type}: {selector_value}"
                        )
                        break
                except (NoSuchElementException, TimeoutException):
                    continue

            if not login_button:
                raise NoSuchElementException(
                    "Could not find login button with any of the known selectors"
                )

            login_button.click()
            logger.warning("Login button clicked")

            # Wait longer for login to complete
            time.sleep(20)

            # Verify we're logged in by checking URL or some element that should be present after login
            if "mylearn.oracle.com/ou/home" not in self.driver.current_url:
                logger.warning(
                    f"Login might have failed. Current URL: {self.driver.current_url}"
                )
                self.driver.save_screenshot("login_failed.png")

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            self.driver.save_screenshot("login_error.png")
            raise

    def parse(self):
        """
        Parse an items for given path name
        """

        logger.info(f"Parsing items from path {self.base_url}")
        self.driver.get(self.base_url)

        wait_chapters = WebDriverWait(self.driver, 60)
        wait_chapters.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "oj-listview-item"))
        )

        self.driver.implicitly_wait(10)
        logger.info("Chapters visible")

        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/ou/course/" in href:
                full_url = urljoin("https://mylearn.oracle.com/", href)
                if full_url not in self.course_links:
                    self.course_links.append(full_url)

        # Save course links to a CSV file
        self.save_course_links()

        for course_url in self.course_links:
            logger.info(f"parsing {course_url}")
            self.parse_course_page(course_url)

        return self.items

    def parse_video_url(self, video: WebElement):
        try:
            return video.get_attribute("href")
        except StaleElementReferenceException as e:
            return ""

    def parse_course_page(self, url: str):
        self.driver.get(url)
        playlist_dom = self.driver.find_element(by=By.ID, value="playlist-tab-panel")

        videos = playlist_dom.find_elements(by=By.TAG_NAME, value="a")
        for video in videos:
            href = self.parse_video_url(video)
            if href:
                self.parse_video(href)
            else:
                # kemungkinan icon dropdown bawah gitu kalo di web-nya
                logger.info(f"No href attribute found for this video. Text: {video}")

        time.sleep(5)

    def retry_if_element_not_interactable(exception):
        """
        Returns True if we should retry on ElementNotInteractableException, False otherwise.
        """
        logger.warning("retrying play button")
        return isinstance(
            exception,
            (
                ElementNotInteractableException,
                ElementClickInterceptedException,
                StaleElementReferenceException,
                NoSuchElementException,
            ),
        )

    @retrying.retry(
        stop_max_delay=5000,
        stop_max_attempt_number=5,
        retry_on_exception=retry_if_element_not_interactable,
    )
    def click_play_button(self):
        logger.warning("clicking play button")

        self.driver.implicitly_wait(20)
        try:
            try:
                playButton = self.driver.find_element(By.ID, "playerIdbtn")
            except NoSuchElementException:
                playButton = self.driver.find_element(
                    By.CLASS_NAME, "vjs-big-play-button"
                )

            playButton.click()
        except ElementClickInterceptedException:
            logger.warning("ElementClickInterceptedException: Removing modal")
            try:
                modal_close_button = self.driver.find_element(
                    By.ID, "tooltipClose_wp136g6s"
                )

                modal_close_button.click()
                playButton.click()
            except NoSuchElementException:
                logger.warning("Modal close button not found")
        except NoSuchElementException:
            logger.warning("Play button not found")
            time.sleep(100)

    def parse_video(self, href: str):
        logger.warning(f"parsing video: {href}")

        self.driver.get(href)
        self.driver.implicitly_wait(10)
        self.click_play_button()

        # for for networks
        print("trying to find master m3u8 request")
        request = None
        for req in self.driver.requests:
            if req.response and "master.m3u8" in req.url:
                request = req
        if not request:
            raise Exception("No master.m3u8 request found")

        print(f"found request: {request.url}")

        parse_m3u8(request.url)

    def save_course_links(self):
        with open(
            os.path.join(
                self.csv_base_path,
                f"{"_".join(self.base_url.split("/")[-2:])}.csv",
            ),
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["Course Links"])
            for link in self.course_links:
                writer.writerow([link])


if __name__ == "__main__":

    # Argument parser
    parser = argparse.ArgumentParser(description="Oracle Learn Scraper")
    parser.add_argument("base_url", type=str, help="Base URL to start scraping from")
    args = parser.parse_args()

    # Web Driver
    logger.info("Initializing Web Driver")
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")  # Add specific window size
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--disable-dev-shm-usage")  # Disable /dev/shm usage
    options.add_argument("--no-sandbox")  # Disable sandbox mode
    web_driver = webdriver.Chrome(options=options)

    try:
        # Initialize Scraping with base_url from arguments
        scraper = Scraping(web_driver=web_driver, base_url=args.base_url)

        items = scraper.parse()
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        web_driver.save_screenshot("error.png")
    finally:
        # Always close the driver
        web_driver.quit()
