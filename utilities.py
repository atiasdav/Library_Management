import requests
import os
import re
import pandas as pd
from PIL import Image, ImageTk
import pytesseract
import glob
from os.path import exists



def main(): #uncomment in order to run
    # rename_photos('books')
    main_isbn_extraction()
    pass

def main_isbn_extraction():
    if exists('books_with_isbn.csv'):
        # Load the existing data
        books_DF = pd.read_csv('books_with_isbn.csv')
        existing_files = set(books_DF['file_name'])
    else:
        # Initialize an empty DataFrame and set of existing files
        books_DF = pd.DataFrame()
        existing_files = set()

        
        # List of image files to process (replace with actual file paths)
    image_files = glob.glob('books/*ISBN.jpg')
    # Process each image and collect data
    data = []
    i=1
    for file_name in image_files:
        print(f"{i}")
        i+=1
        isbn = process_image(file_name)
        data.append({'file_name': file_name, 'isbn': isbn})

    # Create a pandas DataFrame
    books_DF = pd.DataFrame(data)

    # Add a new column 'checksum_valid' to the DataFrame
    books_DF['checksum_valid'] = books_DF['isbn'].apply(checksum_confirmation)

    # Save the DataFrame as a CSV file
    books_DF.to_csv('books_with_isbn.csv', index=False)
    print(books_DF)# Print the DataFrame
    return books_DF
# Function to extract ISBN from text using regex

def extract_isbn(text):
    # ISBN-10: 10 digits (may start with 0 or 1), with optional dashes/spaces
    # ISBN-13: 13 digits, typically starting with 978 or 979, with optional dashes/spaces
    isbn_pattern = r'(?:(\d{3})[-\s]?)?((?:\d[-\s]?){9}[\dX])'
    match = re.search(isbn_pattern, text)
    return match.group(0).replace('-', '').replace(' ', '') if match else None

def checksum_confirmation(isbn):
    if isbn is None:
        # Handle the case where the ISBN is None
        return False  # or some other appropriate action
    if len(isbn) == 10:  # ISBN-10
        total = 0
        for i, digit in enumerate(isbn[:-1]):
            if not digit.isdigit():
                return False
            total += int(digit) * (10 - i)
        check_digit = isbn[-1]
        if check_digit == 'X':
            check_digit = 10
        elif check_digit.isdigit():
            check_digit = int(check_digit)
        else:
            return False
        return (total + check_digit) % 11 == 0
    elif len(isbn) == 13:  # ISBN-13
        total = 0
        for i, digit in enumerate(isbn[:-1]):
            if not digit.isdigit():
                return False
            if i % 2 == 0:
                total += int(digit) * 1
            else:
                total += int(digit) * 3
        check_digit = int(isbn[-1])
        return (total + check_digit) % 10 == 0
    else:
        return False  # Invalid ISBN length


# Function to process an image file, detect text, and extract ISBN
def process_image(file_path):
    # Open the image file
    with Image.open(file_path) as img:
        # Use pytesseract to do OCR on the image
        text = pytesseract.image_to_string(img)
    
    # Extract ISBN from the text
    isbn = extract_isbn(text)
    
    return isbn

def isbn10_to_isbn13(isbn10):
    # Check if isbn10 is None or empty string before proceeding
    if isbn10 is None or isbn10 == '':
        return None
    # Check if the input is a valid ISBN-13
    if len(isbn10) == 13 and isbn10[:3] == '978' and isbn10[:-1].isdigit():
        return isbn10
    # Check if the input ISBN-10 is valid
    if len(isbn10) != 10 or not isbn10[:-1].isdigit() or (isbn10[-1] not in '0123456789Xx'):
        return "Invalid ISBN-10 format"

    # Prepend the '978' prefix to the first 9 digits of ISBN-10
    isbn13 = '978' + isbn10[:-1]

    # Calculate the ISBN-13 checksum digit
    checksum = 0
    for i, digit in enumerate(isbn13):
        if i % 2 == 0:
            checksum += int(digit)
        else:
            checksum += int(digit) * 3
    checksum = 10 - (checksum % 10)
    if checksum == 10:
        checksum = 0

    # Append the checksum to the ISBN-13
    isbn13 += str(checksum)

    return isbn13




def pad_number(number, length):
    return str(number).zfill(length)

def rename_photos(directory, prefix_length=6):
    # List all the files in the directory and sort them
    files = sorted(os.listdir(directory))
    
    # Initialize the counter for the photo set
    photo_set_counter = 1
    
    # Loop through all the files
    for i in range(0, len(files), 2): # Step by 2 since we're processing pairs
        # Define the new file names with padded numbers
        cover_name = f"{pad_number(photo_set_counter, prefix_length)}_cover.jpg"
        isbn_name = f"{pad_number(photo_set_counter, prefix_length)}_ISBN.jpg"
        
        # Get the current file paths
        cover_path = os.path.join(directory, files[i])
        isbn_path = os.path.join(directory, files[i+1])

        # Rename the files
        os.rename(cover_path, os.path.join(directory, cover_name))
        os.rename(isbn_path, os.path.join(directory, isbn_name))
        
        # Increment the photo set counter
        photo_set_counter += 1
        
    print("Renaming complete.")

# Change 'photos' to the path where your photos are located.

def get_book_details(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    data = response.json()
    return data
    if "items" in data:
        book = data["items"][0]["volumeInfo"]
        title = book.get("title", "Title not found")
        authors = book.get("authors", [])
        description = book.get("description", "Description not found")
        return {
            "Title": title,
            "Authors": authors,
            "Description": description
        }
    else:
        return "Book not found"
# Example usage
# isbn = "9789655120219"  # Replace this with your ISBN number
# book_details = get_book_details(isbn)

def save_data(DF):
    # Save the updated DataFrame after the GUI is closed
    DF.to_csv('books_with_isbn.csv', index=False)

if __name__ == "__main__":
    main()