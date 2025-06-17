#Library BOT == May
#Fully functional lib bot -1 May
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import mysql.connector as mysql
import threading
import speech_recognition as sr
import pyttsx3
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup SQL Database connection for library and student data
mydb = mysql.connect(
    host="localhost",
    user="root",
    passwd="Lynx_123@",
    database="library"
)
mycursor = mydb.cursor()

# Text-to-Speech setup
engine = pyttsx3.init()
engine.setProperty('voice', engine.getProperty('voices')[1].id)
engine.setProperty('rate', engine.getProperty('rate') - 25)

# Flask API setup
app = Flask(__name__)
CORS(app)

# Global variable to store student name after authentication
authenticated_user = None

# Flag to indicate if recording should stop
recording_flag = False

# Function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen for speech
def listen_for_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        while not recording_flag:  # Continuously listen until the flag is True
            audio = recognizer.listen(source, timeout=10)
            try:
                user_input = recognizer.recognize_google(audio)
                return user_input.lower()
            except sr.UnknownValueError:
                speak("Sorry, I didn't catch that, please try again.")
                return None
            except sr.WaitTimeoutError:
                return None

# Function to authenticate user
def authenticate(register_number):
    global authenticated_user
    mycursor.execute("SELECT name FROM students WHERE reg_no = %s", (register_number,))
    result = mycursor.fetchone()
    if result:
        authenticated_user = result[0]
        speak(f"Welcome, {authenticated_user}!")
        return True, f"Welcome, {authenticated_user}!"
    else:
        authenticated_user = None
        speak("Invalid register number. Please try again")
        return False, "Invalid register number. Please try again."

# Function to check for close matches in book names
def suggest_close_match(user_input):
    
    mycursor.execute("SELECT title, author FROM main_lib")
    all_books = mycursor.fetchall()

    # Check for close matches in both title and author name
    suggestions = [
        (book[0], book[1]) for book in all_books 
        if book[0].lower().startswith(user_input.lower()) or book[1].lower().startswith(user_input.lower())
    ]
    
    if suggestions:
        # Return the first close match found with both title and author
        return f"Did you mean the book '{suggestions[0][0]}' by {suggestions[0][1]}?"
    return None

# Function to handle library response
def lib_response(user_input):
    if user_input is None:
        reply="Sorry, I didn't catch that. Please try again."
        speak("Sorry, I didn't catch that, please try again")
        return reply
    
    mycursor.execute("select * from main_lib")
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
            flag=True

    if not flag:
        suggested_book = suggest_close_match(user_input)
        if suggested_book:
            speak(f"Did you mean the book '{suggested_book}'?")
            return None, f"Did you mean the book '{suggested_book}'?"

    if flag:
        speak(f"Here are {len(results)} search results. Feel free to search more books.")
        return headers, results, len(results)
    else:
        msg = "No books found. Please try searching for any other books."
        speak(msg)
        return None, msg, 0

# Tkinter GUI setup
class LibraryBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Manager Bot")
        self.authenticated = False
        
        # GUI Layout
        self.label = tk.Label(root, text="Enter Register Number:", font=("Helvetica", 14))
        self.label.pack(pady=10)
        self.entry = tk.Entry(root, font=("Helvetica", 14))
        self.entry.pack(pady=10)
        self.auth_button = tk.Button(root, text="Authenticate", command=self.handle_authentication, font=("Helvetica", 14))
        self.auth_button.pack(pady=10)
        
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=10, font=("Helvetica", 14))
        self.text_area.pack(pady=10)
        self.table_frame = tk.Frame(root)
        self.table_frame.pack(pady=10)
        self.table = ttk.Treeview(self.table_frame, columns=[], show='headings')
        self.table.pack(side='left')
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient='vertical', command=self.table.yview)
        self.table.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side='right', fill='y')
        
        # Bind events to speak button
        self.speak_button = tk.Button(root, text="Speak", bg='#4CAF50', fg='white', font=("Helvetica", 14, "bold"))
        self.speak_button.pack(pady=10)
        self.speak_button.bind("<ButtonPress>", self.start_listening)
        self.speak_button.bind("<ButtonRelease>", self.stop_listening)

    def handle_authentication(self):
        register_number = self.entry.get()
        valid, message = authenticate(register_number)
        messagebox.showinfo("Authentication", message)
        if valid:
            self.authenticated = True
            self.speak_button.config(state=tk.NORMAL)
        else:
            self.authenticated = False
            self.speak_button.config(state=tk.DISABLED)

    def start_listening(self, event):
        global recording_flag
        if self.authenticated:
            recording_flag = False
            threading.Thread(target=self.handle_speech).start()
        else:
            messagebox.showerror("Authentication Required", "Please authenticate before using the bot.")

    def stop_listening(self, event):
        global recording_flag
        recording_flag = True

    def handle_speech(self):
        if self.authenticated:
            user_input = listen_for_speech()
            if user_input:
                self.text_area.insert(tk.END, f"User: {user_input}\n")
                headers, results, total_results = lib_response(user_input)
                if headers:
                    self.display_table(headers, results)
                    self.text_area.insert(tk.END, f"Bot: Here are {total_results} search results.\n")
                else:
                    self.text_area.insert(tk.END, f"Bot: {results}\n")
            else:
                self.text_area.insert(tk.END, "Bot: Sorry, I didn't catch that. Please try again.\n")
            
            # Reset authentication for the next user
            self.authenticated = False
            self.speak_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Authentication Required", "Please authenticate before using the bot.")
    
    def display_table(self, headers, results):
        # Clear previous table entries
        for item in self.table.get_children():
            self.table.delete(item)
        
        # Set headers
        self.table["columns"] = headers
        for col in headers:
            self.table.heading(col, text=col)
            self.table.column(col, anchor='center', width=150)
        
        # Insert results
        for row in results:
            self.table.insert("", "end", values=row)

# Running the Tkinter GUI
def run_gui():
    root = tk.Tk()
    app = LibraryBotGUI(root)
    root.mainloop()

# Running the Flask API
def run_flask():
    app.run(debug=True, port=5000, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_gui()
