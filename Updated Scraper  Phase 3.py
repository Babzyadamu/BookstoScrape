#!/usr/bin/env python
# coding: utf-8

# This phase requires your scraper to:
# 
# ✔ Visit the homepage
# ✔ Extract all book categories
# ✔ Visit each category
# ✔ Scrape all books in that category (Phase 1 logic)
# ✔ Save one CSV per category

# In[6]:


import csv
import time
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, HTTPError

BASE_URL = "http://books.toscrape.com"


# ---------------------------------------------------------
# Helper: download HTML with retry logic
# ---------------------------------------------------------
def get_soup(url, retries=5, delay=2):
    """
    Downloads HTML from a URL.
    Retries automatically if the server refuses the connection.
    Prevents WinError 10061.
    """
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # raises HTTPError for 404, 500, etc.
            return BeautifulSoup(response.text, "html.parser")
        except ConnectionError:
            print(f"Connection failed. Retrying ({attempt+1}/{retries})...")
            time.sleep(delay)
        except HTTPError as e:
            # If page does not exist (404), return None
            if e.response.status_code == 404:
                return None
            else:
                raise

    raise ConnectionError(f"Failed to connect after {retries} retries: {url}")


# ---------------------------------------------------------
# Extract star rating from a book page
# ---------------------------------------------------------
def get_book_rating(soup):
    rating_tag = soup.find("p", class_="star-rating")
    if rating_tag is None:
        return None

    classes = rating_tag.get("class", [])
    for c in classes:
        if c != "star-rating":
            return c
    return None


# ---------------------------------------------------------
# Normalize URLs from category pages
# ---------------------------------------------------------
def normalize_book_url(relative_url):
    relative_url = relative_url.replace("../../..", "")
    relative_url = relative_url.replace("//", "/")

    if not relative_url.startswith("catalogue/"):
        relative_url = "catalogue/" + relative_url

    return relative_url


# ---------------------------------------------------------
# Extract full details from a single product page
# ---------------------------------------------------------
def get_book_details(relative_url):
    relative_url = normalize_book_url(relative_url)
    book_url = BASE_URL + "/" + relative_url

    soup = get_soup(book_url)
    if soup is None:
        return None  # page missing

    breadcrumb = soup.find("ul", class_="breadcrumb")
    category = breadcrumb.find_all("li")[2].get_text(strip=True)

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

    description_tag = soup.find("div", id="product_description")
    if description_tag:
        product_description = description_tag.find_next("p").get_text(strip=True)
    else:
        product_description = None

    title = soup.find("h1").get_text(strip=True)
    rating = get_book_rating(soup)

    image_tag = soup.find("img")
    image_relative_url = image_tag.get("src").replace("../", "")
    image_url = BASE_URL + "/" + image_relative_url

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
# Extract all product URLs from a category
# ---------------------------------------------------------
def get_category_book_urls(category_url):
    book_urls = []
    page_number = 1

    while True:
        if page_number == 1:
            page_url = category_url
        else:
            page_url = category_url.replace("index.html", f"page-{page_number}.html")

        print(f"Scraping category page: {page_url}")

        soup = get_soup(page_url)

        # If soup is None → page does not exist → stop pagination
        if soup is None:
            print("Reached last page.")
            break

        book_tags = soup.find_all("article", class_="product_pod")
        if not book_tags:
            break

        for book in book_tags:
            relative_url = book.find("h3").find("a").get("href")
            relative_url = normalize_book_url(relative_url)
            book_urls.append(relative_url)

        page_number += 1

    print(f"Total books found in category: {len(book_urls)}")
    return book_urls


# ---------------------------------------------------------
# Scrape all books in a category
# ---------------------------------------------------------
def scrape_category(category_url):
    book_urls = get_category_book_urls(category_url)
    all_books = []

    for relative_url in book_urls:
        time.sleep(1)
        details = get_book_details(relative_url)
        if details:
            all_books.append(details)

    return all_books


# ---------------------------------------------------------
# Save results to CSV
# ---------------------------------------------------------
def save_to_csv(books, filename):
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
# Extract ALL categories from homepage
# ---------------------------------------------------------
def get_all_categories():
    soup = get_soup(BASE_URL)

    category_section = soup.find("ul", class_="nav-list").find("ul")
    category_links = category_section.find_all("a")

    categories = {}

    for link in category_links:
        name = link.get_text(strip=True)
        relative_url = link.get("href")
        full_url = BASE_URL + "/" + relative_url
        categories[name] = full_url

    return categories


# ---------------------------------------------------------
# MAIN PROGRAM — PHASE 3
# ---------------------------------------------------------
if __name__ == "__main__":
    print("Extracting all categories...")
    categories = get_all_categories()

    print(f"Found {len(categories)} categories.\n")

    for category_name, category_url in categories.items():
        print(f"Scraping category: {category_name}")

        books = scrape_category(category_url)

        filename = f"{category_name.replace(' ', '_').lower()}.csv"
        save_to_csv(books, filename)

        print(f"Finished category: {category_name}\n")

    print("All categories scraped successfully!")


# Example Sample File
# travel.csv
# mystery.csv
# historical_fiction.csv
# science.csv
# poetry.csv
# ...
# 
