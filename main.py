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
)
from selenium.webdriver.remote.webelement import WebElement

import retrying

from utils import make_output_dir
from dotenv import load_dotenv

# Logger
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Scraping:
    def __init__(self, web_driver: webdriver.Chrome, labels: list):
        # Prepare output dir in case not exist
        make_output_dir()

        self.driver = web_driver
        self.base_url = "https://mylearn.oracle.com/ou/learning-path/become-a-certified-order-management-order-to-cash-implementer/97141"
        self.labels = labels
        self.items = []
        self.course_links = []
        self.csv_base_path = os.path.join(os.path.curdir, "output/csv")

        self.authentication()

    # Authenticator
    def authentication(self):
        logger.warning("authenticating")

        self.driver.get(
            "https://mylearn.oracle.com/arrivals-gate?access_t=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE1NTE4YmQ1LTE3ZDktNDAzZS04OWYxLWZkNjFmYjAwYzk3NCIsImZpcnN0TmFtZSI6IkJlbmhhcmRpIiwibGFzdE5hbWUiOiJDaGFuZHJhIiwiZW1haWwiOiJiZW5oYXJkaS5jaGFuZHJhQG1ldHJvZGF0YS5jby5pZCIsImxlZ2FjeUd1aWQiOiIwRTgwNjI2QjBBRUQ1MDNDRTA1MEU2MEFEMTdGMTlERCIsInBlcm1pc3Npb25zIjpbInN0dWRlbnRfcHJvZmlsZSIsIm5vdGlmaWNhdGlvbiIsImludGVncmF0aW9uIl0sImxlYXJuZXJSb2xlUHJvZmlsZUlkIjoiMWMwZmNjNDMtNTFiNy00NDRmLWI2OTAtOTFmZTU4NGM0MjkzIiwiaW5kZXhlcyI6WyJtbHByb2RfY29udGVudF9vdV9pbmRleCIsIm1scHJvZF9jb250ZW50X2Zvb2RuYmV2X2luZGV4IiwibWxwcm9kX2NvbnRlbnRfcHJvZHVjdF9zdXBwb3J0X2luZGV4Il0sImNvbnRlbnRPd25lcnMiOlt7ImlkIjoiMTlmZDIwN2YtYjdlNC00MzdlLWIyOTYtM2M4Njc1ZGUwOWZkIiwibmFtZSI6Ik9VIiwibGVnYWN5TGVhcm5Pd25lcklkIjoxLCJsYWJlbCI6Ik9VIn0seyJpZCI6Ijg3ZGVjM2JmLTAxNmMtNGM5Ni05ZDVjLTE2MmM0ODhkOTJhNCIsIm5hbWUiOiJGT09ETkJFViIsImxlZ2FjeUxlYXJuT3duZXJJZCI6OCwibGFiZWwiOiJGT09ETkJFViJ9LHsiaWQiOiJmMGViMWNkMS1iMGIzLTRmODgtODVmZi05ZDFmOTk3ZmRmMmQiLCJuYW1lIjoiUFJPRFVDVF9TVVBQT1JUIiwibGVnYWN5TGVhcm5Pd25lcklkIjo2LCJsYWJlbCI6IlBST0RVQ1RfU1VQUE9SVCJ9LHsiaWQiOiJkMWM5M2IwYi1jY2M3LTRmNWYtYjVkMy05OThmZDBjZDM0Y2QiLCJuYW1lIjoiSE9TUElUQUxJVFkiLCJsZWdhY3lMZWFybk93bmVySWQiOjcsImxhYmVsIjoiSE9TUElUQUxJVFkifV0sImlhdCI6MTc0MDI5Mzg3NiwiZXhwIjoxNzQwMjk1MDc2fQ.bFUGpvFFuT0ZTHCb8iKS-sYIG0NUf6GjTRVCGrYIuA4&goTo=https%3A%2F%2Fmylearn.oracle.com%2Fou%2Fhome"
        )

        self.driver.implicitly_wait(10)
        username_field = self.driver.find_element(
            By.ID, "idcs-signin-basic-signin-form-username"
        )

        load_dotenv()
        username = os.getenv("EMAIL")
        username_field.send_keys(username)

        # click continue button
        button = self.driver.find_element(
            by=By.ID, value="idcs-signin-basic-signin-form-submit"
        )
        logger.warning(button)
        button.click()

        # password
        password_field = self.driver.find_element(
            by=By.ID, value="idcs-auth-pwd-input|input"
        )

        password = os.getenv("PASSWORD")
        password_field.send_keys(password)

        logger.warning(f"password: {password_field.text}")

        login_button = self.driver.find_element(
            by=By.ID, value="idcs-mfa-mfa-auth-user-password-submit-button"
        )

        login_button.click()
        logger.warning("login button clicked")

        time.sleep(20)

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
        except NoSuchElementException:
            logger.warning("Play button not found")
            time.sleep(100)

    def parse_video(self, href: str):
        logger.warning(f"parsing video: {href}")

        self.driver.get(href)
        self.driver.implicitly_wait(10)
        self.click_play_button()

        # for for networks
        request = self.driver.wait_for_request(
            r"https://manifest\.prod\.boltdns\.net/.*/master\.m3u8"
        )

        print(f"found request: {request.url}")

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

    # Web Driver
    logger.info("Initializing Web Driver")
    options = webdriver.ChromeOptions()
    web_driver = webdriver.Chrome()

    labels = [
        "Name",
        "Code",
        "Dimensional Url",
        "Height",
        "Length",
        "Width",
        "Extension",
        "Backplate",
        "Socket",
        "Wattage",
        "Weight",
    ]

    parser = Scraping(web_driver=web_driver, labels=labels)

    items = parser.parse()

    # debug || offs
    web_driver.quit()
