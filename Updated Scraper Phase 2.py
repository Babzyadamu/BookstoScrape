#!/usr/bin/env python
# coding: utf-8

# In[1]:


import csv
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------
# BASE URL for the website
# ---------------------------------------------------------
BASE_URL = "http://books.toscrape.com"


# ---------------------------------------------------------
# Helper function: download HTML and convert to BeautifulSoup
# ---------------------------------------------------------
def get_soup(url):
    """
    Sends an HTTP GET request to the given URL.
    If the request succeeds, returns a BeautifulSoup object
    that allows us to search the HTML easily.
    """
    response = requests.get(url)
    response.raise_for_status()  # stops the program if the page is missing
    return BeautifulSoup(response.text, "html.parser")


# ---------------------------------------------------------
# Extract star rating from a book page
# ---------------------------------------------------------
def get_book_rating(soup):
    """
    Finds the star rating on the product page.
    The rating is stored in a <p> tag with classes like:
    <p class="star-rating Three"></p>
    """
    rating_tag = soup.find("p", class_="star-rating")
    if rating_tag is None:
        return None

    classes = rating_tag.get("class", [])
    for c in classes:
        if c != "star-rating":
            return c  # e.g. "Three"
    return None


# ---------------------------------------------------------
# Normalize URLs from category pages
# ---------------------------------------------------------
def normalize_book_url(relative_url):
    """
    Category pages use weird relative URLs like:
    ../../../its-only-the-himalayas_981/index.html

    This function cleans them and ensures they start with:
    catalogue/...
    """
    # Remove ../../../
    relative_url = relative_url.replace("../../..", "")

    # Ensure catalogue/ prefix
    if not relative_url.startswith("catalogue/"):
        relative_url = "catalogue/" + relative_url

    return relative_url


# ---------------------------------------------------------
# Extract full details from a single product page
# ---------------------------------------------------------
def get_book_details(relative_url):
    """
    Takes a relative URL (like catalogue/book_123/index.html),
    visits the product page, and extracts ALL required fields.
    """
    # Fix the URL if needed
    relative_url = normalize_book_url(relative_url)

    # Build full URL
    book_url = BASE_URL + "/" + relative_url

    # Download page
    soup = get_soup(book_url)

    # -------------------------
    # CATEGORY (breadcrumb)
    # -------------------------
    breadcrumb = soup.find("ul", class_="breadcrumb")
    category = breadcrumb.find_all("li")[2].get_text(strip=True)

    # -------------------------
    # PRODUCT INFO TABLE
    # -------------------------
    table = soup.find("table", class_="table table-striped")
    rows = table.find_all("tr")

    product_info = {}
    for row in rows:
        key = row.find("th").get_text(strip=True)
        value = row.find("td").get_text(strip=True)
        product_info[key] = value

    upc = product_info.get("UPC")
    price_excl_tax = product_info.get("Price (excl. tax)")
    price_incl_tax = product_info.get("Price (incl. tax)")
    quantity_available = product_info.get("Availability")

    # -------------------------
    # PRODUCT DESCRIPTION
    # -------------------------
    description_tag = soup.find("div", id="product_description")
    if description_tag:
        product_description = description_tag.find_next("p").get_text(strip=True)
    else:
        product_description = None

    # -------------------------
    # TITLE
    # -------------------------
    title = soup.find("h1").get_text(strip=True)

    # -------------------------
    # RATING
    # -------------------------
    rating = get_book_rating(soup)

    # -------------------------
    # IMAGE URL
    # -------------------------
    image_tag = soup.find("img")
    image_relative_url = image_tag.get("src").replace("../", "")
    image_url = BASE_URL + "/" + image_relative_url

    # Return everything as a dictionary
    return {
        "product_page_url": book_url,
        "universal_product_code": upc,
        "book_title": title,
        "price_including_tax": price_incl_tax,
        "price_excluding_tax": price_excl_tax,
        "quantity_available": quantity_available,
        "product_description": product_description,
        "category": category,
        "review_rating": rating,
        "image_url": image_url,
    }


# ---------------------------------------------------------
# PHASE 2: Extract all product URLs from a category
# ---------------------------------------------------------
def get_category_book_urls(category_url):
    """
    Visits a category page and extracts ALL product URLs.
    Handles pagination automatically.
    """
    book_urls = []
    page_number = 1

    while True:
        # First page uses index.html
        if page_number == 1:
            page_url = category_url
        else:
            # Later pages use page-x.html
            page_url = category_url.replace("index.html", f"page-{page_number}.html")

        print(f"Scraping category page: {page_url}")

        try:
            soup = get_soup(page_url)
        except requests.exceptions.HTTPError as e:
            # Stop when page does not exist
            if e.response.status_code == 404:
                break
            else:
                raise

        # Find all book entries
        book_tags = soup.find_all("article", class_="product_pod")
        if not book_tags:
            break

        # Extract URLs
        for book in book_tags:
            relative_url = book.find("h3").find("a").get("href")
            relative_url = normalize_book_url(relative_url)
            book_urls.append(relative_url)

        page_number += 1

    print(f"Total books found in category: {len(book_urls)}")
    return book_urls


# ---------------------------------------------------------
# Scrape all books in a category (Phase 2)
# ---------------------------------------------------------
def scrape_category(category_url):
    """
    Uses Phase 1 logic to extract full details for every book
    found in the selected category.
    """
    book_urls = get_category_book_urls(category_url)
    all_books = []

    for relative_url in book_urls:
        details = get_book_details(relative_url)
        all_books.append(details)

    return all_books


# ---------------------------------------------------------
# Save results to CSV
# ---------------------------------------------------------
def save_to_csv(books, filename="category_books.csv"):
    """
    Writes all book dictionaries into a CSV file.
    """
    fieldnames = [
        "product_page_url",
        "universal_product_code",
        "book_title",
        "price_including_tax",
        "price_excluding_tax",
        "quantity_available",
        "product_description",
        "category",
        "review_rating",
        "image_url",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(books)

    print(f"CSV saved: {filename}")


# ---------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------
if __name__ == "__main__":
    # Pick ANY category you want
    category_url = "http://books.toscrape.com/catalogue/category/books/travel_2/index.html"

    books = scrape_category(category_url)
    save_to_csv(books)


# What This Script Achieves
# ✔ Scrapes one category
# You can change the category URL to any category on the site.
# 
# ✔ Handles pagination automatically
# ✔ Extracts all product URLs in that category
# ✔ Uses your Phase 1 logic to extract full book details
# ✔ Writes everything to one CSV file
