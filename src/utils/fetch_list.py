from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import dotenv
import os
import time
from pathlib import Path, PurePath

config = dotenv.dotenv_values(Path(PurePath(__file__).parents[2], ".env"))
DOWNLOAD_DIR = config.get('LIST')
PERISCOPE_URL = config.get('PERISCOPE_URL')
PERISCOPE_PASS= config.get('PERISCOPE_PASS')

def fetch_list(download_dir = DOWNLOAD_DIR, periscope_url = PERISCOPE_URL, periscope_pass = PERISCOPE_PASS):

    if download_dir is None:
        return None

    #make sure the download dir exists
    os.makedirs(os.path.abspath(download_dir), exist_ok=True)

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
        "downloadPath": os.path.abspath(download_dir),
    })

    wait = WebDriverWait(driver, 15)

    # auth section, fills in periscope pw given url
    driver.get(periscope_url)
    password_input = driver.find_element(By.XPATH, """//*[@id="password"]""")
    password_input.send_keys(periscope_pass)
    button = driver.find_element(By.XPATH, """//*[@id="submit-button"]""")
    ActionChains(driver).move_to_element(button).move_by_offset(10, 0).click().perform()
    print("Authorized periscope.")

    # scrolls to the widget, hovers to reveal controls, then click "More Options"
    # because periscope can't just give you a link to a csv for some reason
    title = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".widget-18183666 div.title")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title)
    time.sleep(0.5)
    ActionChains(driver).move_to_element(title).perform()
    print("Found main member widget.")

    # move to the little hamburger button
    expand = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".widget-18183666 div.expand.button")))
    ActionChains(driver).move_to_element(expand).click().perform()
    print("Found hamburger icon.")

    # click "Download Data" from the menu
    download_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Download Data')]")))
    download_option.click()
    print("Clicked Download Data")

    # waits for periscope to finish materializing the csv:
    # first wait for the loader to appear, then for it to disappear
    loader_css = ".widget-18183666 .loader.materializing"
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, loader_css))
    )
    print("Materializing...")
    WebDriverWait(driver, 120).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, loader_css))
    )
    print("Materialization complete.")

    # wait for the .csv file to finish downloading
    timeout = 60
    start = time.time()
    while time.time() - start < timeout:
        files = os.listdir(download_dir)
        csv_files = [f for f in files if f.endswith(".csv")]
        tmp_files = [f for f in files if f.endswith(".crdownload") or f.startswith(".com.google.Chrome")]
        if csv_files and not tmp_files:
            print("Downloaded:", csv_files)
            break
        time.sleep(1)
    else:
        print("Timed out waiting for download")

    driver.quit()

if __name__ == "__main__":
    fetch_list()
