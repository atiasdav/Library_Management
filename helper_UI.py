#helper functions

import os
from tkinter import Tk, Label, Button, filedialog, messagebox
from PIL import Image, ImageTk
import tkinter as tk
from utilities import *

#parameters
DF_RANGE="not all" #change to "all" to see all of the photos
class ImageRotator:
    def __init__(self, master):
        self.master = master
        master.title("Image Rotator")

        self.label = Label(master, text="Select a folder with JPG images")
        self.label.pack()

        self.select_folder_button = Button(master, text="Select Folder", command=self.select_folder)
        self.select_folder_button.pack()

        self.image_label = Label(master)
        self.image_label.pack()

        self.rotate_button = Button(master, text="Rotate Image [r]", command=self.rotate_image)
        self.rotate_button.pack()

        self.save_button = Button(master, text="Save & Next Image [s]", command=self.save_and_next)
        self.save_button.pack()

        # Bind 'r' key to rotate_image function
        master.bind('r', self.rotate_image)

        # Bind 's' key to save_and_next function
        master.bind('s', self.save_and_next)

        self.folder_path = ''
        self.images = []
        self.current_image = None
        self.current_image_index = -1

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.images = [f for f in os.listdir(self.folder_path) if f.lower().endswith('.jpg')]
            self.current_image_index = -1
            self.next_image()

    def next_image(self):
        self.current_image_index += 1
        if self.current_image_index < len(self.images):
            image_path = os.path.join(self.folder_path, self.images[self.current_image_index])
            self.current_image = Image.open(image_path)
            self.show_image(self.current_image)
        else:
            self.label.config(text="No more images.")
            self.image_label.config(image='')

    def show_image(self, image):
        # Get the size of the image
        original_width, original_height = image.size
        
        # Set the maximum size that you want for the images (change these values as needed)
        max_width = 800
        max_height = 600
        
        # Calculate the ratio to maintain aspect ratio
        ratio = min(max_width/original_width, max_height/original_height)
        new_size = (int(original_width * ratio), int(original_height * ratio))
        
        # Resize the image using the calculated ratio while maintaining aspect ratio
        resized_image = image.resize(new_size, Image.ANTIALIAS)
        
        # Convert the image to a Tkinter PhotoImage and display it
        tk_image = ImageTk.PhotoImage(resized_image)
        self.image_label.config(image=tk_image)
        self.image_label.image = tk_image

    def rotate_image(self, event=None): 
        if self.current_image:
            # Rotate the image 90 degrees to the right (clockwise)
            self.current_image = self.current_image.rotate(-90, expand=True)
            self.show_image(self.current_image)

    def save_and_next(self, event=None): 
        if self.current_image:
            save_path = os.path.join(self.folder_path, self.images[self.current_image_index])
            self.current_image.save(save_path)
            self.next_image()

class ISBNConfirmationApp:
    def __init__(self, master, dataframe):
        self.master = master
        self.master.title("ISBN Confirmation")
        
        # Filter the DataFrame and create a new DataFrame to work with
        self.dataframe = dataframe
        self.filtered_df = dataframe[dataframe['checksum_valid'] == False].reset_index(drop=True)
        
        # will show all of the photos or just the False checksum records 
        if DF_RANGE=="all":
            self.selectedDF=self.dataframe
            self.original_indices = list(range(len(self.dataframe)))  # Use a range for all indices
        else:
            self.selectedDF = self.filtered_df
            self.original_indices = self.filtered_df.index.tolist()  # Only use indices of filtered rows

        self.current_index = 0
        
        # Create a label to show the image
        self.image_label = tk.Label(master)
        self.image_label.pack()
        
        # ISBN entry
        self.isbn_entry = tk.Entry(master, width=20, font=('Arial', 14))
        self.isbn_entry.pack(pady=10)
        
        # Confirm button
        self.confirm_button = tk.Button(master, text="Next ISBN", command=self.confirm_isbn)
        self.confirm_button.pack(side=tk.LEFT, padx=10)
        
        # Change button
        self.change_button = tk.Button(master, text="Update ISBN", command=self.update_isbn)
        self.change_button.pack(side=tk.RIGHT, padx=10)
        
        # Load the first image
        self.load_image()

    def load_image(self):
        if self.current_index < len(self.selectedDF):
            img_path = self.selectedDF.iloc[self.current_index]['file_name']
            img = Image.open(img_path)
            img.thumbnail((400, 400))  # Resize for display
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
            # Update the ISBN entry
            isbn = self.selectedDF.iloc[self.current_index]['isbn']
            if isbn is None:
                isbn = ""  # Or some other placeholder text indicating a missing ISBN
            self.isbn_entry.delete(0, 'end')  # Clear any existing text in the entry
            self.isbn_entry.insert(0, isbn)
        else:
            messagebox.showinfo("End", "No more images.")
            self.master.quit()
            return self.dataframe


    def confirm_isbn(self):
        self.next_image()

    def update_isbn(self):
        if self.current_index < len(self.selectedDF):
            # Update the ISBN in the DataFrame
            new_isbn = self.isbn_entry.get()
            if DF_RANGE == "all":
                self.dataframe.at[self.current_index, 'isbn'] = new_isbn
                self.dataframe.at[self.current_index, 'checksum_valid'] = checksum_confirmation(new_isbn)
            else:
                self.filtered_df.at[self.current_index, 'isbn'] = new_isbn
                original_index = self.original_indices[self.current_index]
                self.dataframe.at[original_index, 'isbn'] = new_isbn
                self.dataframe.at[original_index, 'checksum_valid'] = checksum_confirmation(new_isbn)
            self.next_image()
        else:
            messagebox.showerror("Error", "No more records to update.")

    def next_image(self):
        self.current_index += 1
        self.load_image()

    def save_data(self):
        # Save the updated DataFrame after the GUI is closed
        books_DF['ISBN13'] = books_DF['isbn'].apply(isbn10_to_isbn13)

        self.dataframe.to_csv('books_with_isbn.csv', index=False)


def ISBN_APP():
    books_DF=main_isbn_extraction()
    books_DF['ISBN13'] = books_DF['isbn'].apply(isbn10_to_isbn13)
    root = tk.Tk()
    app = ISBNConfirmationApp(root, books_DF)
    root.mainloop()
    app.save_data()
    return books_DF

def rotateUI():
    root = Tk()
    my_gui = ImageRotator(root)
    root.mainloop()



if __name__ == "__main__": #uncomment in order to run
    # rotateUI()
    books_DF=ISBN_APP()
    print(books_DF)
    pass