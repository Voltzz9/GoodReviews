from selenium import webdriver 
from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import csv
import re
import os

def scrape_with_selenium(url, max_reviews=100):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        print(f"Page title: {driver.title}")  # Debug print
        
        # Extract book title
        wait = WebDriverWait(driver, 10)
        title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.Text.H1Title[itemprop="name"] a')))
        book_title = title_element.text
        print(f"Book title: {book_title}")  # Debug print
        
        reviews = []
        # Find all review elements
        review_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'section.ReviewText'))
        )
        while len(review_elements) < max_reviews:
            print(f"Number of reviews found: {len(review_elements)}, continuing scraping")  # Debug print
            # Keep loading more reviews until the number of review elements exceeds max_reviews
            try:
                # Wait for the "Load More" button to be present
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.Divider--largeMargin .Button--medium'))
                )
                # Scroll to the button
                driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                # Wait a bit for any animations to finish
                time.sleep(1)
                # Try to click the button
                try:
                    load_more_button.click()
                except ElementClickInterceptedException:
                    # If direct click fails, try using JavaScript
                    driver.execute_script("arguments[0].click();", load_more_button)
                # Wait for new content to load
                time.sleep(2)
            except TimeoutException:
                print("No more 'Show more reviews' button found or it's not clickable. All reviews loaded.")
                break
            # Find all review elements
            review_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'section.ReviewText'))
            )
            

        for review_element in review_elements:
            if len(reviews) >= max_reviews:
                break
            try:
                review_text = review_element.find_element(By.CSS_SELECTOR, 'span.Formatted').text
                reviews.append(review_text)
            except NoSuchElementException:
                print("Couldn't find review text for an element. Skipping.")
        print(f"Number of reviews found: {len(reviews)}")  # Debug print
        
        # Check if the file exists
        file_exists = os.path.isfile('goodreads_reviews.csv')
        # Open CSV file for writing (append mode if it exists, write mode if it doesn't)
        with open('goodreads_reviews.csv', mode='a' if file_exists else 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the header only if the file is being created
            if not file_exists:
                writer.writerow(['Book Title', 'Review Text'])
            # Write the reviews to the CSV file
            for review in reviews:
                cleaned_review = re.sub(r'\s+', ' ', review).strip()
                writer.writerow([book_title, cleaned_review])
        print(f"Reviews saved to goodreads_reviews.csv. Total reviews: {min(len(reviews), max_reviews)}")
        
    except TimeoutException:
        print("Timed out waiting for page elements to load")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()
        
def main():
    url = "https://www.goodreads.com/book/show/11588/reviews?reviewFilters={%22languageCode%22:%22en%22}"
    scrape_with_selenium(url, max_reviews=100)  # Change max_reviews as needed

if __name__ == "__main__":
    main()