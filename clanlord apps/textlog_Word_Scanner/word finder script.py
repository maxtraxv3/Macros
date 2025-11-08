import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def search_word_in_file(file_path, word):
    """
    Opens the file and checks if the specified word exists.
    Returns True if found, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            contents = f.read()
            if word in contents:
                return True
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return False

def scan_directory(directory, word):
    """
    Recursively scans the directory for .txt files containing the search word.
    Returns a list of matching file paths.
    """
    found_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.txt'):
                full_path = os.path.join(root, filename)
                if search_word_in_file(full_path, word):
                    found_files.append(full_path)
    return found_files

def open_file_with_default_app(file_path):
    """
    Opens a file with the system's default application.
    """
    try:
        if sys.platform.startswith('win'):
            os.startfile(file_path)
        elif sys.platform.startswith('darwin'):
            # macOS
            from subprocess import Popen
            Popen(['open', file_path])
        else:
            # Linux and others
            from subprocess import Popen
            Popen(['xdg-open', file_path])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open file: {e}")

class LogScannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Text Log Scanner")
        self.geometry("700x500")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        # Folder selection
        folder_label = tk.Label(self, text="Folder:")
        folder_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.folder_var = tk.StringVar()
        folder_entry = tk.Entry(self, textvariable=self.folder_var, width=50)
        folder_entry.grid(row=0, column=1, padx=5, pady=5)

        folder_button = tk.Button(self, text="Browse", command=self.browse_folder)
        folder_button.grid(row=0, column=2, padx=5, pady=5)

        # Search word entry
        word_label = tk.Label(self, text="Word to search:")
        word_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.word_var = tk.StringVar()
        word_entry = tk.Entry(self, textvariable=self.word_var, width=50)
        word_entry.grid(row=1, column=1, padx=5, pady=5)

        search_button = tk.Button(self, text="Search", command=self.start_search)
        search_button.grid(row=1, column=2, padx=5, pady=5)

        # Results display area: using Listbox with a Scrollbar.
        results_label = tk.Label(self, text="Matching Files:")
        results_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.results_list = tk.Listbox(self, width=90, height=20)
        self.results_list.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=3, column=3, sticky="ns")
        self.results_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_list.yview)

        # Bind double-click event to open file
        self.results_list.bind('<Double-Button-1>', self.open_selected_file)

        # Open file button
        open_button = tk.Button(self, text="Open File", command=self.open_selected_file)
        open_button.grid(row=4, column=1, pady=10)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_var.set(folder_selected)

    def start_search(self):
        folder = self.folder_var.get()
        word = self.word_var.get()

        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        if not word:
            messagebox.showerror("Error", "Please enter a word to search for.")
            return

        # Clear previous results and show message
        self.results_list.delete(0, tk.END)
        self.results_list.insert(tk.END, "Scanning... Please wait.")
        
        # Run scan in a separate thread to keep GUI responsive
        threading.Thread(target=self.run_scan, args=(folder, word), daemon=True).start()

    def run_scan(self, folder, word):
        found_files = scan_directory(folder, word)
        # Update the results in the GUI thread
        self.results_list.after(0, self.update_results, found_files, word)

    def update_results(self, found_files, word):
        self.results_list.delete(0, tk.END)
        if found_files:
            self.results_list.insert(tk.END, f"Found the word '{word}' in:")
            self.results_list.insert(tk.END, "-------------------------------")
            for file in found_files:
                self.results_list.insert(tk.END, file)
        else:
            self.results_list.insert(tk.END, f"No files found containing the word '{word}'.")

    def open_selected_file(self, event=None):
        # Get currently selected file from the Listbox.
        selection = self.results_list.curselection()
        if selection:
            # If the first two entries are header lines, adjust based on index >1
            file_path = self.results_list.get(selection[0])
            # Only attempt to open if the selected line is a valid file path
            if os.path.isfile(file_path):
                open_file_with_default_app(file_path)
            else:
                messagebox.showinfo("Info", "Please select a valid file from the list.")
        else:
            messagebox.showinfo("Info", "No file is selected.")

if __name__ == "__main__":
    app = LogScannerApp()
    app.mainloop()
