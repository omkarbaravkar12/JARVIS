"""
browser_controller.py — Selenium-powered browser automation for Jarvis
Handles smart navigation, YouTube search+play, and site opening.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from utils import setup_logger

logger = setup_logger(__name__)

# Single browser instance reused across commands
_driver = None


def _get_driver():
    """
    Launch Chrome browser once and reuse it.
    Opens in a normal visible window.
    """
    global _driver
    if _driver is None:
        logger.info("Launching Chrome browser...")
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=service, options=options)
        logger.info("Chrome launched successfully.")
    return _driver


def close_browser():
    """Close the browser and reset the driver."""
    global _driver
    if _driver:
        _driver.quit()
        _driver = None
        logger.info("Browser closed.")


def open_website(url: str) -> str:
    """Navigate to any URL in Chrome."""
    try:
        driver = _get_driver()
        driver.get(url)
        logger.info("Opened: %s", url)
        return f"Opened {url}"
    except Exception as exc:
        logger.error("Failed to open %s: %s", url, exc)
        return f"Sorry, I couldn't open {url}."


def youtube_search_and_play(query: str) -> str:
    """
    Search YouTube for a query and click the first video result.
    Example: youtube_search_and_play("cocomelon")
    """
    try:
        driver = _get_driver()
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        driver.get(search_url)

        # Wait for video thumbnails to load
        wait = WebDriverWait(driver, 10)
        first_video = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-video-renderer #video-title"))
        )
        video_title = first_video.text
        first_video.click()
        logger.info("Playing YouTube video: %s", video_title)
        return f"Playing: {video_title}"

    except Exception as exc:
        logger.error("YouTube play failed: %s", exc)
        return "Sorry, I couldn't play that video."


def google_search(query: str) -> str:
    """Search Google for a query."""
    try:
        driver = _get_driver()
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        driver.get(url)
        return f"Searched Google for: {query}"
    except Exception as exc:
        logger.error("Google search failed: %s", exc)
        return "Sorry, couldn't search Google."


def navigate_to_site(site_name: str) -> str:
    """
    Open a named website in the controlled browser.
    Works for canva, pinterest, github, etc.
    """
    sites = {
        "canva":         "https://www.canva.com",
        "pinterest":     "https://www.pinterest.com",
        "github":        "https://www.github.com",
        "gmail":         "https://mail.google.com",
        "youtube":       "https://www.youtube.com",
        "google":        "https://www.google.com",
        "linkedin":      "https://www.linkedin.com",
        "netflix":       "https://www.netflix.com",
        "reddit":        "https://www.reddit.com",
        "twitter":       "https://www.twitter.com",
        "instagram":     "https://www.instagram.com",
        "stackoverflow": "https://www.stackoverflow.com",
        "chatgpt":       "https://chat.openai.com",
        "wikipedia":     "https://www.wikipedia.org",
        "amazon":        "https://www.amazon.in",
        "flipkart":      "https://www.flipkart.com",
        "whatsapp":      "https://web.whatsapp.com",
        "spotify":       "https://open.spotify.com",
    }

    site_name = site_name.lower().strip()
    if site_name in sites:
        return open_website(sites[site_name])
    else:
        # Try anyway with www
        url = f"https://www.{site_name}.com"
        return open_website(url)