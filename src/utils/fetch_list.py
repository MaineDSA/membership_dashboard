import logging
import time
from pathlib import Path, PurePath

import dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
DOWNLOAD_DIR = config.get("LIST")
PERISCOPE_URL = config.get("PERISCOPE_URL")
PERISCOPE_PASS= config.get("PERISCOPE_PASS")

def fetch_list(download_dir: str | None = DOWNLOAD_DIR, periscope_url: str | None = PERISCOPE_URL, periscope_pass: str | None = PERISCOPE_PASS) -> None:

    if download_dir is None or periscope_url is None or periscope_pass is None:
        msg = "Missing required environment variables."
        raise RuntimeError(msg)

    #make sure the download dir exists
    Path(download_dir).resolve().mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument("--window-size=1920,1080") #set standard window size
    options.add_argument(argument="--headless=new") #headless
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
    })

    driver = webdriver.Chrome(options=options)

    # set download directory
    driver.execute_cdp_cmd("Browser.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": str(Path(download_dir).resolve()),
    })

    wait = WebDriverWait(driver, 15)

    # auth section, fills in periscope pw given url
    driver.get(periscope_url)
    password_input = driver.find_element(By.XPATH, """//*[@id="password"]""")
    password_input.send_keys(periscope_pass)
    button = driver.find_element(By.XPATH, """//*[@id="submit-button"]""")
    ActionChains(driver).move_to_element(button).move_by_offset(10, 0).click().perform()
    logger.info("Authorized periscope.")

    # scrolls to the widget, hovers to reveal controls, then click "More Options"
    # because periscope can't just give you a link to a csv for some reason
    title = wait.until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, ".widget-18183666 div.title")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title)
    time.sleep(0.5)
    ActionChains(driver).move_to_element(title).perform()
    logger.info("Found main member widget.")

    # move to the little hamburger button
    expand = wait.until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, ".widget-18183666 div.expand.button")))
    ActionChains(driver).move_to_element(expand).click().perform()
    logger.info("Found hamburger icon.")

    # click "Download Data" from the menu
    download_option = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Download Data')]")))
    download_option.click()
    logger.info("Clicked Download Data.")

    # waits for periscope to finish materializing the csv:
    # first wait for the loader to appear, then for it to disappear
    loader_css = ".widget-18183666 .loader.materializing"
    WebDriverWait(driver, 30).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, loader_css))
    )
    logger.info("Materializing...")
    WebDriverWait(driver, 120).until(
        expected_conditions.invisibility_of_element_located((By.CSS_SELECTOR, loader_css))
    )
    logger.info("Materialization complete.")

    # wait for the .csv file to finish downloading
    timeout = 60
    start = time.time()
    while time.time() - start < timeout:
        files = [f.name for f in Path(download_dir).iterdir()]
        csv_files = [f for f in files if f.endswith(".csv")]
        tmp_files = [f for f in files if f.endswith(".crdownload") or f.startswith(".com.google.Chrome")]
        if csv_files and not tmp_files:
            logger.info("Downloaded: %s", csv_files)
            break
        time.sleep(1)
    else:
        logger.warning("Timed out waiting for download.")

    driver.quit()

if __name__ == "__main__":
    fetch_list()
