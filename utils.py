#!/usr/bin/env python
# coding: utf-8

# After Scrapping, this is next
# 
# saving data, downloading images, zipping

# In[5]:


# src/utils.py

import os
import csv
import requests
import shutil


def ensure_folder(path):
    """
    Creates a folder if it does not already exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def save_books_to_csv(books, csv_path):
    """
    Saves a list of book dictionaries to a CSV file.
    """
    ensure_folder(os.path.dirname(csv_path))

    # Get the field names from the keys of the first book
    fieldnames = list(books[0].keys())

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(books)

    print(f"Saved data to {csv_path}")


def download_image(image_url, save_path):
    """
    Downloads a single image from image_url and saves it to save_path.
    """
    response = requests.get(image_url, stream=True)
    response.raise_for_status()

    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def download_all_images(books, images_folder):
    """
    Downloads all book cover images into the images_folder.
    Uses the book title to create a simple filename.
    """
    ensure_folder(images_folder)

    for i, book in enumerate(books, start=1):
        image_url = book["image_url"]
        # Simple filename: index + cleaned title
        title_clean = "".join(c for c in book["title"] if c.isalnum() or c in (" ", "_"))
        filename = f"{i:03d}_{title_clean}.jpg"
        save_path = os.path.join(images_folder, filename)

        print(f"Downloading image {i}: {image_url}")
        try:
            download_image(image_url, save_path)
        except Exception as e:
            print(f"Failed to download {image_url}: {e}")


def create_zip(source_folder, zip_path):
    """
    Creates a ZIP file from the source_folder.
    """
    # shutil.make_archive wants the base name without .zip and the format
    base_name = os.path.splitext(zip_path)[0]
    root_dir = source_folder

    shutil.make_archive(base_name, "zip", root_dir)
    print(f"Created ZIP file at {zip_path}")

