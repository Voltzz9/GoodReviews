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
import pandas as pd

def scrape_with_selenium(url, max_reviews=100, max_retries=5):
    
    retry_count = 0
    while retry_count < max_retries:
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
            
            # Extract total number of reviews
            reviews_count_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="reviewsCount"]')))
            reviews_count_text = reviews_count_element.text.split()[0].replace(',', '')
            total_reviews = int(reviews_count_text)
            print(f"Total reviews for this book: {total_reviews}")

            # Determine the number of reviews to scrape
            reviews_to_scrape = min(total_reviews, max_reviews)
            print(f"Scraping {reviews_to_scrape} reviews")
            
            reviews = []
            # Find all review elements
            review_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'section.ReviewText'))
            )

            previous_len = 0
            while len(review_elements) < reviews_to_scrape:
                # Check if the number of reviews has increased
                if len(review_elements) == previous_len:
                    print("Review count remained unchanged. Retrying...")
                    raise Exception("Failed to load new reviews")
                
                previous_len = len(review_elements)
                print(f"Number of reviews found: {len(review_elements)}, continuing scraping")  # Debug print

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
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.ReviewCard__content'))
                )
                                
            for review_element in review_elements:
                if len(reviews) >= reviews_to_scrape:
                    break
                try:
                    review_text = review_element.find_element(By.CSS_SELECTOR, 'span.Formatted').text
                    
                    # Extract review stars
                    review_stars = 0
                    stars_elements = review_element.find_elements(By.CLASS_NAME, 'RatingStar__backgroundFill')
                    review_stars = 5 - len(stars_elements)
                    
                    # Extract review date
                    review_date_element = review_element.find_element(By.CSS_SELECTOR, '.Text__body3 a')
                    review_date = review_date_element.text
                    
                    # Extract Number of likes
                    try:
                        review_likes_element = review_element.find_element(By.CSS_SELECTOR, '.Button__container:nth-child(1) .Button--subdued .Button__labelItem')
                        review_likes = review_likes_element.text
                        # Extract only the number from the string
                        review_likes = int(review_likes.split(' ')[0])
                    except NoSuchElementException:
                        review_likes = 0
                    
                    reviews.append([review_text, review_date, review_stars, review_likes])
                    
                    
                except NoSuchElementException:
                    print("Couldn't find review text for an element. Skipping.")
            print(f"Number of reviews scraped: {len(reviews)}")  # Debug print
            
            # Check if we have scraped any reviews
            if len(reviews) == 0:
                raise Exception("No reviews were scraped")

            # Check if the file exists
            file_exists = os.path.isfile('data/goodreads_reviews_all.csv')
            # Open CSV file for writing (append mode if it exists, write mode if it doesn't)
            with open('data/goodreads_reviews_all.csv', mode='a' if file_exists else 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Write the header only if the file is being created
                if not file_exists:
                    writer.writerow(['Book Title', 'Link', 'Review Text', 'Review Date', 'Review Stars', 'Review Likes'])
                # Write the reviews to the CSV file
                for review in reviews:
                    cleaned_review = re.sub(r'\s+', ' ', review[0]).strip()
                    writer.writerow([book_title, url, cleaned_review, review[1], review[2], review[3]])
            print(f"Reviews saved to data/goodreads_reviews_all.csv. Total reviews scraped: {len(reviews)}")
            
            # If we've reached this point without exceptions, we can break the retry loop
            break
            
        except TimeoutException:
            print(f"Timed out waiting for page elements to load. Retry {retry_count + 1} of {max_retries}")
            retry_count += 1
        except Exception as e:
            print(f"An error occurred: {str(e)}. Retry {retry_count + 1} of {max_retries}")
            retry_count += 1
    
    if retry_count == max_retries:
        print(f"Max retries reached for {url}. Skipping to next URL.")

    driver.quit()
    
        
def main():
    file_path = 'data/goodreads_reviews_all.csv'
    urls = pd.read_csv('data/book_links_all.csv')
    i = 0
    urls['BookLinks'] = urls['BookLinks'] + '/reviews?reviewFilters={%22languageCode%22:%22en%22}'
    
    # Check if the file exists
    if os.path.isfile(file_path):
        book_reviews = pd.read_csv(file_path)
        existing_links = set(book_reviews['Link'].values)
    else:
        existing_links = set()

    # Filter out URLs that are already in book_reviews
    filtered_urls = [url for url in urls['BookLinks'] if url not in existing_links]
    num_books = len(filtered_urls)
    
    # Proceed with the remaining URLs
    for url in filtered_urls:
         
        # Scrape the book
        i += 1
        scrape_with_selenium(url, max_reviews=120)  # Change max_reviews as needed
        print(f"Book {i}/{num_books} scraped\n")

if __name__ == "__main__":
    main()