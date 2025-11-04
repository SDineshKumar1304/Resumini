# WARNING: Automated scraping of LinkedIn may violate its Terms of Service.
# Use responsibly. Prefer authorized APIs where possible.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import time
import re

class LinkedInSearch:
    def __init__(self, llm=None, headless=True, driver_path=None):
        """
        llm: optional LLM client (kept for compatibility)
        headless: whether to run Chrome headless
        driver_path: optional path to chromedriver executable (None => auto)
        """
        self.llm = llm
        self.headless = headless
        self.driver = None
        self.driver_path = driver_path

    def _setup_driver(self):
        """Setup Chrome WebDriver with or without GUI."""
        options = Options()
        if self.headless:
            # Use new headless flag for modern Chrome
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        # minimal user-agent to avoid obvious bot detection
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        )

        if self.driver_path:
            self.driver = webdriver.Chrome(executable_path=self.driver_path, options=options)  # noqa: E402
        else:
            self.driver = webdriver.Chrome(options=options)

    def _extract_location_from_query(self, query: str):
        """Try to parse 'in <location>' or '..., location' patterns."""
        # "Data Scientist in Bangalore"
        m = re.search(r"\bin\s+([A-Za-z0-9\s\-]+)$", query, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # "Data Scientist, Bangalore" or "Data Scientist - Bangalore"
        parts = re.split(r"[,-]\s*", query)
        if len(parts) > 1:
            possible = parts[-1].strip()
            # if looks like a location (contains letters)
            if re.search(r"[A-Za-z]", possible):
                return possible
        return None

    def _scroll_to_load(self, pause=0.8, attempts=6):
        """Scroll container to load more job cards (helper)."""
        # try scrolling the main window; LinkedIn lazy-loads content.
        for _ in range(attempts):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)

    def search_jobs(self, query: str = "Data Scientist Bangalore", location: str = None, max_results: int = 10):
        """
        Search LinkedIn jobs and return structured data.

        Args:
            query: primary keywords (e.g., "Data Scientist in Bangalore" or "Data Scientist")
            location: optional explicit location string (overrides any auto-parsed location)
            max_results: limit of job results to return
        Returns:
            list of dicts: {"title","company","location","link"}
        """
        # Setup driver
        try:
            self._setup_driver()
        except WebDriverException as e:
            print(f"⚠️ WebDriver error: {e}")
            return []

        # Try to auto-detect location if not provided
        parsed_location = None
        if not location:
            parsed_location = self._extract_location_from_query(query)
        effective_location = (location or parsed_location or "").strip()
        # Build simple search keywords (remove ' in <loc>' or trailing ', loc' if parsed)
        if parsed_location:
            # remove the trailing " in <loc>" or ", <loc>"
            query = re.sub(r"\bin\s+%s$" % re.escape(parsed_location), "", query, flags=re.IGNORECASE).strip()
            query = re.sub(r"[,-]\s*%s$" % re.escape(parsed_location), "", query, flags=re.IGNORECASE).strip()

        encoded_query = query.replace(" ", "%20")
        # append location param to URL if we have an explicit location term
        if effective_location:
            encoded_location = effective_location.replace(" ", "%20")
            url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={encoded_location}"
        else:
            url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}"

        print(f"🔍 Searching LinkedIn for: {query}" + (f" (location={effective_location})" if effective_location else ""))
        print(f"🌐 URL: {url}")

        try:
            self.driver.get(url)
            # initial wait for content
            time.sleep(4)

            # scroll a bit to let LinkedIn load more cards
            self._scroll_to_load(pause=1.0, attempts=5)

            jobs_data = []
            # job cards are usually inside ul.jobs-search__results-list li
            cards = self.driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")
            if not cards:
                # fallback: newer markup might use '.jobs-search-results__list-item'
                cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")

            for job in cards:
                if len(jobs_data) >= max_results:
                    break
                try:
                    # defensive selectors — LinkedIn sometimes changes DOM.
                    title_elem = job.find_element(By.CSS_SELECTOR, "h3") if job.find_elements(By.CSS_SELECTOR, "h3") else job.find_element(By.CSS_SELECTOR, ".job-card-list__title")
                    company_elem = job.find_element(By.CSS_SELECTOR, "h4") if job.find_elements(By.CSS_SELECTOR, "h4") else job.find_element(By.CSS_SELECTOR, ".job-card-container__company-name")
                    location_elem = None
                    # try multiple location selectors
                    for sel in (".job-search-card__location", ".job-card-container__metadata-item", ".job-card-list__location"):
                        elems = job.find_elements(By.CSS_SELECTOR, sel)
                        if elems:
                            location_elem = elems[0]
                            break
                    # fallback to any span
                    if location_elem is None:
                        elems = job.find_elements(By.TAG_NAME, "span")
                        location_elem = elems[-1] if elems else None

                    link_elem = job.find_element(By.TAG_NAME, "a")

                    title = title_elem.text.strip() if title_elem is not None else ""
                    company = company_elem.text.strip() if company_elem is not None else ""
                    location_text = location_elem.text.strip() if location_elem is not None else ""
                    link = link_elem.get_attribute("href")

                    # filter by effective_location if provided (case-insensitive substring)
                    if effective_location:
                        if effective_location.lower() not in location_text.lower():
                            # skip jobs that don't match the requested location
                            continue

                    job_info = {
                        "title": title,
                        "company": company,
                        "location": location_text,
                        "link": link,
                    }
                    jobs_data.append(job_info)
                except Exception:
                    # ignore single-card parse errors
                    continue

            print(f"✅ Found {len(jobs_data)} jobs for '{query}'.")
            return jobs_data

        except Exception as e:
            print(f"⚠️ Error while fetching jobs: {e}")
            return []

        finally:
            try:
                if self.driver:
                    self.driver.quit()
            except Exception:
                pass
