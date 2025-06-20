# === Updated Library Bot Script ===
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import mysql.connector as mysql
import threading
import speech_recognition as sr
import pyttsx3
from llama_cpp import Llama
from datetime import datetime

# === SQL Setup ===
mydb = mysql.connect(
    host="localhost",
    user="root",
    passwd="Lynx_123@",
    database="library"
)
mycursor = mydb.cursor()

# === Text-to-Speech ===
engine = pyttsx3.init()
engine.setProperty('voice', engine.getProperty('voices')[2].id)
engine.setProperty('rate', engine.getProperty('rate') - 25)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# === GGUF LLM Load ===
llm = Llama(
    model_path="D:/AI/lmstudio-community/Llama-3.2-3B-Instruct-GGUF/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=4,
    n_gpu_layers=20
)

# === Global Vars ===
authenticated_user = None
reg_number = None
recording_flag = False

# === General Chat Static Context ===
general_info = """
You are a helpful library assistant for Easwari Engineering College Central Library.

General Library Info:
- Incharge: Dr. Joseph Anburaj
- Timings: 7.45 AM to 6 PM, Monday to Saturday
- Borrowing Limit: 2 books per student
- Loan Duration: 14 days
- Fine: ₹5 per day if not returned on time
- Location: First Floor, South Wing
- Contact: library@college.edu

Respond to user questions only using the above info. Do not perform book searches.
"""

def listen_for_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=10)
            return recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
            return None
        except sr.WaitTimeoutError:
            return None

def authenticate(register_number):
    global authenticated_user, reg_number
    mycursor.execute("SELECT name FROM students WHERE reg_no = %s", (register_number,))
    result = mycursor.fetchone()
    if result:
        authenticated_user = result[0]
        reg_number = register_number
        speak(f"Welcome, {authenticated_user}!")
        return True, f"Welcome, {authenticated_user}!"
    else:
        authenticated_user = None
        reg_number = None
        speak("Invalid register number.")
        return False, "Invalid register number."

def logout_user():
    global authenticated_user, reg_number
    authenticated_user = None
    reg_number = None
    speak("You have been logged out.")

def lib_response(user_input):
    if user_input is None:
        speak("Sorry, I didn't catch that.")
        return None, "Sorry, I didn't catch that.", 0

    mycursor.execute("SELECT * FROM lib")
    headers = [i[0] for i in mycursor.description]
    rec = mycursor.fetchall()
    results = [i for i in rec if user_input in i[2].lower() or user_input in i[3].lower()]

    if not results:
        speak("No books found. Try again.")
        return None, "No books found. Try again.", 0

    speak(f"Found {len(results)} books.")
    if reg_number:
        save_history(reg_number, f"User: {user_input}\nBot: Found {len(results)} books.")
    return headers, results, len(results)

def fetch_history(reg_no):
    mycursor.execute("SELECT message FROM history WHERE reg_no = %s ORDER BY timestamp DESC LIMIT 10", (reg_no,))
    records = mycursor.fetchall()
    return "\n".join([r[0] for r in records])

def save_history(reg_no, message):
    mycursor.execute("INSERT INTO history (reg_no, message, timestamp) VALUES (%s, %s, %s)", (reg_no, message, datetime.now()))
    mydb.commit()

def handle_general_chat(user_query):
    history = fetch_history(reg_number) if reg_number else ""
    prompt = f"""
{general_info}

Previous History:
{history}

User: {user_query}
Assistant:
"""
    response = llm(
        prompt=prompt,
        max_tokens=512,
        temperature=0.4,
        top_p=0.9,
        stop=["User:", "Assistant:"]
    )
    answer = response["choices"][0]["text"].strip()
    if not answer:
        answer = "I'm here to help! Could you please repeat that?"
    if reg_number:
        save_history(reg_number, f"User: {user_query}\nAssistant: {answer}")
    return answer

class LibraryBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Manager Bot")
        self.authenticated = False
        self.recording = False

        self.mode_var = tk.StringVar(value="Search")
        self.mode_frame = tk.Frame(root)
        self.mode_frame.pack(pady=5)
        tk.Label(self.mode_frame, text="Choose Mode:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(self.mode_frame, text="Search", variable=self.mode_var, value="Search").pack(side=tk.LEFT)
        tk.Radiobutton(self.mode_frame, text="General Chat", variable=self.mode_var, value="Chat").pack(side=tk.LEFT)

        self.label = tk.Label(root, text="Enter Register Number:", font=("Helvetica", 14))
        self.label.pack(pady=10)
        self.entry = tk.Entry(root, font=("Helvetica", 14))
        self.entry.pack(pady=10)

        self.auth_button = tk.Button(root, text="Login", command=self.handle_authentication, font=("Helvetica", 14))
        self.auth_button.pack(pady=5)
        self.logout_button = tk.Button(root, text="Logout", command=self.handle_logout, font=("Helvetica", 14))
        self.logout_button.pack(pady=5)

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=10, font=("Helvetica", 14))
        self.text_area.pack(pady=10)

        self.speak_button = tk.Button(root, text="Hold to Speak", font=("Helvetica", 14))
        self.speak_button.pack(pady=5)
        self.speak_button.bind('<ButtonPress>', self.start_listening)
        self.speak_button.bind('<ButtonRelease>', self.stop_listening)
        self.speak_button.config(state=tk.DISABLED)

        self.table_frame = tk.Frame(root)
        self.table_frame.pack(pady=10)
        self.table = None

    def handle_authentication(self):
        reg = self.entry.get().strip()
        success, message = authenticate(reg)
        self.text_area.insert(tk.END, message + "\n")
        if success:
            self.authenticated = True
            self.speak_button.config(state=tk.NORMAL)

    def handle_logout(self):
        logout_user()
        self.authenticated = False
        self.speak_button.config(state=tk.DISABLED)
        self.text_area.insert(tk.END, "Logged out.\n")

    def start_listening(self, event):
        self.recording = True
        threading.Thread(target=self.handle_speech).start()

    def stop_listening(self, event):
        self.recording = False

    def handle_speech(self):
        while self.recording:
            user_input = listen_for_speech()
            if user_input is None:
                continue
            self.text_area.insert(tk.END, f"You: {user_input}\n")
            mode = self.mode_var.get()

            if mode == "Search":
                headers, results, count = lib_response(user_input)
                if headers and results:
                    self.render_table(headers, results)
                    self.text_area.insert(tk.END, f"Found {count} result(s).\n")
            else:
                response = handle_general_chat(user_input)
                self.text_area.insert(tk.END, f"Bot: {response}\n")
                speak(response)

    def render_table(self, headers, data):
        if self.table:
            self.table.destroy()
        self.table = ttk.Treeview(self.table_frame, columns=headers, show="headings")
        for h in headers:
            self.table.heading(h, text=h)
            self.table.column(h, width=150)
        for row in data:
            self.table.insert("", tk.END, values=row)
        self.table.pack()

if __name__ == '__main__':
    root = tk.Tk()
    app = LibraryBotGUI(root)
    root.mainloop()
