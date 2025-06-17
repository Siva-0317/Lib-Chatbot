import tkinter as tk
from tkinter import ttk, scrolledtext
import speech_recognition as sr
import pyttsx3
import mysql.connector as mysql
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup for SQL Database connection
mydb = mysql.connect(
    host="localhost",
    user="root",
    passwd="Lynx_123@",
    database="library"
)
mycursor = mydb.cursor()

# Setup for text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('volume', 9.0)
engine.setProperty('rate', engine.getProperty('rate') - 25)

# Setup for speech recognition
recognizer = sr.Recognizer()

# Function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen for speech
def listen_for_speech():
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=10)
            user_input = recognizer.recognize_google(audio)
            return user_input.lower()
        except sr.UnknownValueError:
            return None
        except sr.WaitTimeoutError:
            return None

# Function to handle library response
def lib_response(user_input):
    if user_input is None:
        return "Sorry, I didn't catch that. Please try again."
    
    mycursor.execute("SELECT * FROM main_lib")
    headers = [i[0] for i in mycursor.description]
    rec = mycursor.fetchall()
    flag = False
    results = []

    for i in rec:
        if user_input in i[3].lower():
            results.append(i)
            flag = True
        elif user_input in i[2].lower():
            results.append(i)
            flag = True
        

    if flag:
        speak("Here are my search results. Feel free to search more books.")
        return headers, results
    else:
        msg = "No books found. Please try searching for any other books."
        speak(msg)
        return None, msg

# Function to handle book checkout
def check_out_book(barcode):
    mycursor.execute("SELECT status FROM main_lib WHERE barcode=%s", (barcode,))
    result = mycursor.fetchone()
    if result:
        status = result[0]
        if status == "Available":
            mycursor.execute("UPDATE main_lib SET status='Borrowed' WHERE barcode=%s", (barcode,))
            mydb.commit()
            return "Book checked out successfully."
        elif status == "Not for loan":
            return "Error: This is a reference book, not available for loan."
        else:
            return "Error: This book is already borrowed."
    else:
        return "Error: No book found with the provided barcode."

# Function to handle book check-in
def check_in_book(barcode):
    mycursor.execute("SELECT status FROM main_lib WHERE barcode=%s", (barcode,))
    result = mycursor.fetchone()
    if result:
        status = result[0]
        if status == "Borrowed":
            mycursor.execute("UPDATE main_lib SET status='Available' WHERE barcode=%s", (barcode,))
            mydb.commit()
            return "Book checked in successfully."
        else:
            return "Error: This book is currently not borrowed."
    else:
        return "Error: No book found with the provided barcode."

# Flask API setup
app = Flask(__name__)
CORS(app)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    user_input = data.get('query')
    headers, result = lib_response(user_input)
    if headers:
        result_text = "\t".join(headers) + "\n" + "\n".join(["\t".join(map(str, row)) for row in result])
        return jsonify({"response": result_text})
    else:
        return jsonify({"response": result})

# Tkinter GUI setup
class LibraryBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Manager Bot")
        
        # Styles
        self.root.configure(bg='#f0f0f0')
        
        # Label
        self.label = tk.Label(root, text="Enter Register Number to Authenticate", bg='#f0f0f0', fg='#333333', font=("Helvetica", 14))
        self.label.pack(pady=10)
        
        # Register Number Entry
        self.register_label = tk.Label(root, text="Register Number:", bg='#f0f0f0', fg='#333333', font=("Helvetica", 14))
        self.register_label.pack(pady=10)
        self.register_entry = tk.Entry(root, font=("Helvetica", 14), width=40)
        self.register_entry.pack(pady=10)
        
        # Authenticate Button
        self.auth_button = tk.Button(root, text="Authenticate", command=self.authenticate_user, bg='#4CAF50', fg='white', font=("Helvetica", 14, "bold"))
        self.auth_button.pack(pady=10)
        
        # Text Area
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=10, font=("Helvetica", 14, "bold"), bg='#e6e6e6', fg='#333333')
        self.text_area.pack(pady=10)

        # Results Count Label
        self.results_label = tk.Label(root, text="", bg='#f0f0f0', fg='#333333', font=("Helvetica", 14))
        self.results_label.pack(pady=10)

        # Table
        self.table_frame = tk.Frame(root, bg='#f0f0f0')
        self.table_frame.pack(pady=10)
        self.table = ttk.Treeview(self.table_frame, columns=[], show='headings')
        self.table.pack(side='left')
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient='vertical', command=self.table.yview)
        self.table.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side='right', fill='y')
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"))
        style.configure("Treeview", font=("Helvetica", 12), rowheight=25)

        # Speak Button
        self.button = tk.Button(root, text="Speak", command=self.handle_speech, bg='#4CAF50', fg='white', font=("Helvetica", 14, "bold"), state=tk.DISABLED)
        self.button.pack(pady=10)

        # Barcode Entry for Check-in/Check-out
        self.barcode_entry_label = tk.Label(root, text="Enter Barcode:", bg='#f0f0f0', fg='#333333', font=('Helvetica', 14))
        self.barcode_entry_label.pack(pady=10)
        self.barcode_entry = tk.Entry(root, font=('Helvetica', 14), width=40)
        self.barcode_entry.pack(pady=10)

        # Check-in and Check-out Buttons
        self.buttons_frame = tk.Frame(root, bg='#f0f0f0')
        self.buttons_frame.pack(pady=10)
        self.check_out_button = tk.Button(self.buttons_frame, text="Check Out", command=self.check_out, bg='#FF5733', fg='white', font=("Helvetica", 14, "bold"))
        self.check_out_button.pack(side='left', padx=5)
        self.check_in_button = tk.Button(self.buttons_frame, text="Check In", command=self.check_in, bg='#337AFF', fg='white', font=("Helvetica", 14, "bold"))
        self.check_in_button.pack(side='left', padx=5)

    def authenticate_user(self):
        reg_no = self.register_entry.get()
        if reg_no:
            # Assume you have a table 'students' with columns 'register_number' and 'name'
            mycursor.execute("SELECT name FROM students WHERE reg_no = %s", (reg_no,))
            result = mycursor.fetchone()
            if result:
                self.authenticated = True
                self.user_name = result[0]
                self.button.config(state=tk.NORMAL)  # Enable the Speak button
                self.text_area.insert(tk.END, f"Authentication successful. Welcome {self.user_name}!\n")
            else:
                self.authenticated = False
                self.text_area.insert(tk.END, "Authentication failed. Please try again.\n")
        else:
            self.authenticated = False
            self.text_area.insert(tk.END, "Please enter your register number.\n")

    def check_out(self):
        barcode = self.barcode_entry.get()
        status = check_out_book(barcode)
        self.text_area.insert(tk.END, f"Checked out: {status}\n")

    def check_in(self):
        barcode = self.barcode_entry.get()
        status = check_in_book(barcode)
        self.text_area.insert(tk.END, f"Checked in: {status}\n")
        
    def handle_speech(self):
        if self.authenticated:
            user_input = listen_for_speech()
            if user_input:
                self.text_area.insert(tk.END, f"User: {user_input}\n")
                headers, results = lib_response(user_input)
                if headers:
                    self.display_table(headers, results)
                    self.results_label.config(text=f"Total results found: {len(results)}")
                    self.text_area.insert(tk.END, "Search results displayed below.\n")
                else:
                    self.text_area.insert(tk.END, f"{results}\n")
                self.button.config(state=tk.DISABLED)  # Disable the Speak button after use
            else:
                self.text_area.insert(tk.END, "Sorry, I couldn't hear you. Please try again.\n")
        else:
            self.text_area.insert(tk.END, "Please authenticate yourself before speaking.\n")

    def display_table(self, headers, results):
        self.table.delete(*self.table.get_children())
        self.table['columns'] = headers
        for header in headers:
            self.table.heading(header, text=header)
            self.table.column(header, width=100, anchor='center')
        for result in results:
            self.table.insert('', 'end', values=result)

root = tk.Tk()
library_gui = LibraryBotGUI(root)
root.mainloop()
