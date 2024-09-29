# Load required libraries
library(rvest)
library(tidyverse)
library(stringr)

# Base URL of the product reviews
base_url <- "https://www.walmart.com/reviews/product/10450114?aspect=48&lookup=3H34WSS08ANB"

# Set up the headers to mimic a request coming from Google
headers <- c(
  "User-Agent" = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
  "Accept-Language" = "en-US,en;q=0.5"
)

# Function to scrape reviews from a single page
scrape_page <- function(url) {
  page <- read_html(url, headers = headers)
  
  # Extract reviews
  reviews <- page %>%
    html_nodes(".db-m") %>%
    html_text() %>%
    str_trim()
  
  # Check for next page
  next_page <- page %>%
    html_node(".primary") %>%
    html_attr("href")
  
  list(reviews = reviews, next_page = next_page)
}

# Initialize variables
all_reviews <- vector("list")
current_url <- base_url
print(current_url)
page_number <- 1

# Scrape all pages
repeat {
  cat("Scraping page", page_number, "\n")
  
  print("Scraping Page: ")
  print(current_url)
  # Scrape current page
  result <- scrape_page(current_url)
  
  # Add reviews to the list
  all_reviews <- c(all_reviews, result$reviews)
  
  # Check if there's a next page
  if (is.na(result$next_page)) {
    break
  }
  
  # Prepare URL for next page
  current_url <- paste0("https://www.walmart.com", result$next_page)
  page_number <- page_number + 1
  
  # add a delay to be respectful to the server
  Sys.sleep(2)
}

# Convert list of reviews to a data frame
reviews_df <- data.frame(review_text = unlist(all_reviews))

# Save reviews to a CSV file
write.csv(reviews_df, "walmart_reviews.csv", row.names = FALSE)

cat("Scraping complete. Total reviews collected:", nrow(reviews_df), "\n")
cat("Reviews saved to 'walmart_reviews.csv'\n")