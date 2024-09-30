# Load required libraries
library(RSelenium)
library(rvest)
library(tidyverse)

# Start the Selenium server and browser
driver <- rsDriver(browser = "chrome", port = 4567L) # You can use "chrome" if you prefer
remote_driver <- driver[["client"]]

# Base URL of the product reviews
base_url <- "https://www.goodreads.com/book/show/63079845/reviews"

# Function to scrape reviews from the page
scrape_reviews <- function() {
  review_elements <- remote_driver$findElements("css", ".Formatted")
  sapply(review_elements, function(elem) elem$getElementText())
}

# Function to click "More reviews" button
click_more_reviews <- function() {
  tryCatch({
    more_button <- remote_driver$findElement("css", ".Button--secondary")
    more_button$clickElement()
    Sys.sleep(2)  # Wait for new reviews to load
    return(TRUE)
  }, error = function(e) {
    return(FALSE)
  })
}

# Main scraping process
all_reviews <- vector("list")
remote_driver$navigate(base_url)

repeat {
  new_reviews <- scrape_reviews()
  all_reviews <- c(all_reviews, new_reviews)
  cat("Total reviews collected:", length(all_reviews), "\n")
  
  if (!click_more_reviews()) {
    cat("No more reviews to load.\n")
    break
  }
}

# Close the browser and stop the server
remote_driver$close()
driver[["server"]]$stop()

# Convert list of reviews to a data frame
reviews_df <- data.frame(review_text = unlist(all_reviews))

# Save reviews to a CSV file
write.csv(reviews_df, "goodreads_reviews.csv", row.names = FALSE)

cat("Scraping complete. Total reviews collected:", nrow(reviews_df), "\n")
cat("Reviews saved to 'goodreads_reviews.csv'\n")