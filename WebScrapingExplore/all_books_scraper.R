# Data Science 346 Project Stellenbosch University
# Date: 2024-10-22
# TEAM
# - David Nicolay 26296918
# - Kellen Mossner 26024284
# - Matthew Holm 26067404

# Load required libraries
library(rvest)
library(tidyverse)
library(stringr)

rm(list = ls())
# URL of the product page
main_vector <- c()

front_page_url <- "https://www.goodreads.com"


headers <- c(
  "User-Agent" = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
  "Accept-Language" = "en-US,en;q=0.5"
)

page <- read_html(front_page_url, headers = headers)

genre_links <- page %>%
  html_nodes("#browseBox .gr-hyperlink") %>%
  html_attr("href")

genre_names <- genre_links[grep("^/genres/", genre_links)]
genre_names <- sub("^/genres/", "", genre_names)

full_shelf_links <- paste0("https://www.goodreads.com/shelf/show/", genre_names)

full_shelf_links[4] <- "https://www.goodreads.com/shelf/show/childrens"

# view(full_shelf_links)

for (shelf_link in full_shelf_links) {
  
  shelf_page <- read_html(shelf_link, headers = headers)
  
  book_links <- shelf_page %>%
    html_nodes(".bookTitle") %>%
    html_attr("href")
  
  full_book_links <- paste0(front_page_url, book_links)
  main_vector <- c(main_vector, full_book_links)
  
}

view(main_vector)

book_links_df <- data.frame(BookLinks = main_vector)

view(book_links_df)
write.csv(book_links_df, "book_links_all.csv", row.names = FALSE)
