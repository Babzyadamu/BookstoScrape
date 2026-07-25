#!/usr/bin/env python
# coding: utf-8

# What This Updated Version Does
# ✔ Extracts ALL required fields
# Directly from the product page table + description + breadcrumb.
# 
# ✔ Handles missing descriptions safely
# Some books have no description — your code now avoids crashing.
# 
# ✔ Writes everything to CSV
# With the exact column names your assignment requires.
# 
# ✔ Keeps your original structure
# So you still understand every part.

# In[1]:


import os
import csv
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://books.toscrape.com"


def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_book_rating(book_tag):
    rating_tag = book_tag.find("p", class_="star-rating")
    if rating_tag is None:
        return None

    classes = rating_tag.get("class", [])
    for c in classes:
        if c != "star-rating":
            return c
    return None


def get_book_details(book_relative_url):
    # Ensure correct path
    if not book_relative_url.startswith("catalogue/"):
        book_relative_url = "catalogue/" + book_relative_url

    book_url = BASE_URL + "/" + book_relative_url
    soup = get_soup(book_url)

    # CATEGORY (breadcrumb)
    breadcrumb = soup.find("ul", class_="breadcrumb")
    category = None
    if breadcrumb:
        li_tags = breadcrumb.find_all("li")
        if len(li_tags) >= 3:
            category = li_tags[2].get_text(strip=True)

    # PRODUCT INFORMATION TABLE
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

    # PRODUCT DESCRIPTION
    description_tag = soup.find("div", id="product_description")
    if description_tag:
        product_description = description_tag.find_next("p").get_text(strip=True)
    else:
        product_description = None

    return {
        "category": category,
        "product_page_url": book_url,
        "upc": upc,
        "price_excluding_tax": price_excl_tax,
        "price_including_tax": price_incl_tax,
        "quantity_available": quantity_available,
        "product_description": product_description,
    }


def scrape_page(page_url):
    try:
        soup = get_soup(page_url)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return []
        else:
            raise

    books = []
    book_tags = soup.find_all("article", class_="product_pod")

    for book in book_tags:
        title_tag = book.find("h3").find("a")
        title = title_tag.get("title")

        price_tag = book.find("p", class_="price_color")
        price = price_tag.get_text(strip=True)

        availability_tag = book.find("p", class_="instock availability")
        availability = availability_tag.get_text(strip=True)

        rating = get_book_rating(book)

        relative_url = title_tag.get("href")

        image_tag = book.find("img")
        image_relative_url = image_tag.get("src").replace("../", "")
        image_url = BASE_URL + "/" + image_relative_url

        details = get_book_details(relative_url)

        book_data = {
            "product_page_url": details["product_page_url"],
            "universal_product_code": details["upc"],
            "book_title": title,
            "price_including_tax": details["price_including_tax"],
            "price_excluding_tax": details["price_excluding_tax"],
            "quantity_available": details["quantity_available"],
            "product_description": details["product_description"],
            "category": details["category"],
            "review_rating": rating,
            "image_url": image_url,
        }

        books.append(book_data)

    return books


def scrape_all_books():
    all_books = []
    page_number = 1

    while True:
        page_url = f"{BASE_URL}/catalogue/page-{page_number}.html"
        print(f"Scraping page {page_number}: {page_url}")
        books = scrape_page(page_url)

        if not books:
            break

        all_books.extend(books)
        page_number += 1

    print(f"Total books scraped: {len(all_books)}")
    return all_books


def save_to_csv(books, filename="books.csv"):
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


if __name__ == "__main__":
    books = scrape_all_books()
    save_to_csv(books)

