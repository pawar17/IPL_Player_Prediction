import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('selenium_test.log'),
        logging.StreamHandler()
    ]
)

def test_selenium():
    driver = None
    try:
        logging.info("Setting up Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        logging.info("Installing ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        logging.info("Creating Chrome WebDriver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test accessing IPL website
        logging.info("Testing connection to IPL website...")
        driver.get("https://www.iplt20.com")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        logging.info(f"Page title: {driver.title}")
        logging.info(f"Current URL: {driver.current_url}")
        
        # Get page source and log its length
        page_source = driver.page_source
        logging.info(f"Page source length: {len(page_source)} characters")
        
        # Test accessing a team page
        logging.info("Testing access to team page...")
        driver.get("https://www.iplt20.com/teams/chennai-super-kings")
        time.sleep(2)  # Wait for page to load
        
        logging.info(f"Team page title: {driver.title}")
        logging.info(f"Team page URL: {driver.current_url}")
        
        # Test accessing a player page
        logging.info("Testing access to player page...")
        driver.get("https://www.iplt20.com/teams/chennai-super-kings/squad")
        time.sleep(2)  # Wait for page to load
        
        logging.info(f"Squad page title: {driver.title}")
        logging.info(f"Squad page URL: {driver.current_url}")
        
        logging.info("Test completed successfully!")
        return True

    except Exception as e:
        logging.error(f"Error during test: {str(e)}")
        return False
        
    finally:
        if driver:
            logging.info("Closing Chrome WebDriver...")
            driver.quit()

if __name__ == "__main__":
    success = test_selenium()
    if success:
        logging.info("All tests passed!")
    else:
        logging.error("Test failed!") 