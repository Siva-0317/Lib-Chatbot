# === Library Bot Script with Whisper Speech Recognition, Hyperlink Support, Book Emojis, and Responsive Visuals ===
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import mysql.connector as mysql
import threading
import pyttsx3
from llama_cpp import Llama
from datetime import datetime
import os
import tempfile
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import re
import webbrowser

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
    threading.Thread(target=lambda: (engine.say(text), engine.runAndWait())).start()

# === Whisper Speech Recognition Setup ===
WHISPER_MODEL_SIZE = "small"
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")

def listen_for_speech(duration=8, samplerate=16000):
    print("Listening (Whisper)... Please speak.")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    audio = np.squeeze(audio)
    # Save to temp WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        import wave
        with wave.open(tmpfile.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(audio.tobytes())
        wav_path = tmpfile.name
    # Transcribe with Whisper
    segments, info = whisper_model.transcribe(wav_path, beam_size=1)
    text = ""
    for segment in segments:
        text += segment.text
    os.remove(wav_path)
    print("Heard:", text.strip())
    return text.strip().lower() if text.strip() else None

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

# === General Chat Static Context ===
general_info = """
You are JUNE (full form: Journey to understand, navigate and enlighten), a helpful library assistant for Easwari Engineering College Central Library.

General Library Info:
- Incharge: Dr. Joseph Anburaj
- Timings: 7.45 AM to 6 PM, Monday to Saturday
- Borrowing Limit: 2 books per student
- Loan Duration: 14 days
- Fine: ₹5 per day if not returned on time
- Location: First Floor, South Wing, Civil Block
- Contact: centralibrary@eec.srmrmp.edu.in

Collections:
     Books	                          Count
1	Total no. of Volumes	          80294
2	Total no. of Titles	              21671 
3	Total no of National Journals	  117	 
4   IEEE (ASPP)                       222
5   ELSEVIER (SCIENCE DIRECT)         275
6   BUSNESS SOURCE ELITE(Management)  1056
7   Delnet Online	                  10000+

Membership:
S.No	Institutional Membership Libraries :
1	    British Council Library, Chennai
2	    CSIR- SERC – Knowledge Resource Center, Chennai*
3	    DELNET (Developing Library Network), New Delhi

Other Resources:
1 Open Access No of NPTEL (Web &amp; Video) Course
2 NDL (National Digital Library) and NDLI Club

Faculties:
S.No	NAME	                DESIGNATION	    QUALIFICATION
1	    Dr. A.JOSEPH ANBURAJ	LIBRARIAN	    M.LIS,M.PHIL,PH.D
2	    Mr.K.KADHIRAVAN	        LIB.ASSISTANT	B.A.,M.LIS
3	    Mrs.S.LEELAVATHI	    LIB.ASSISTANT	B.COM,M.LIS

Digital Access:
- Delnet Portal: https://delnet.in/
- E-books Portal: https://ndl.iitkgp.ac.in/
- Research Archives: https://www.sciencedirect.com/
- IEEE Access: https://ieeexplore.ieee.org/Xplore/home.jsp
- NPTEL Portal: https://nptel.ac.in/

Remote Access:
- Use your college email to access digital resources from home.
Link: https://srmeaswari.knimbus.com/user#/home

Respond to user questions only using the above info as JUNE. Do not perform book searches. Even if the question is repeated, always respond.
"""

class LibraryBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 JUNE - Library Manager Bot 📚")
        self.root.configure(bg="#f6f3ee")
        self.authenticated = False
        self.recording = False

        # --- Book background canvas at bottom ---
        self.bg_canvas = tk.Canvas(root, highlightthickness=0, bg="#f6f3ee")
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.root.update_idletasks()
        self.draw_book_background()

        # --- Book emojis decoration ---
        self.left_book = tk.Label(root, bg="#f6f3ee", text="📚", font=("Segoe UI Emoji", 48))
        self.left_book.place(relx=0.01, rely=0.01, anchor="nw")
        self.right_book = tk.Label(root, bg="#f6f3ee", text="📖", font=("Segoe UI Emoji", 48))
        self.right_book.place(relx=0.99, rely=0.01, anchor="ne")

        # --- Overlay frame for all widgets ---
        self.overlay = tk.Frame(root, bg="", highlightthickness=0)
        self.overlay.place(relx=0.5, rely=0.05, anchor="n", relwidth=0.96)

        # --- Title with emoji ---
        self.title_label = tk.Label(
            self.overlay,
            text="Welcome to JUNE! 📚 Your Library Assistant",
            font=("Segoe UI", 18, "bold"),
            bg="#f6f3ee",
            fg="#7c4700"
        )
        self.title_label.pack(pady=(0, 8))

        self.mode_var = tk.StringVar(value="Search")
        self.mode_frame = tk.Frame(self.overlay, bg="#f6f3ee")
        self.mode_frame.pack(pady=5)
        tk.Label(self.mode_frame, text="Choose Mode:", font=("Segoe UI", 12, "bold"), bg="#f6f3ee", fg="#7c4700").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(self.mode_frame, text="🔎 Search", variable=self.mode_var, value="Search", command=self.update_mode, bg="#f6f3ee", fg="#7c4700", selectcolor="#fbeee0", font=("Segoe UI", 11)).pack(side=tk.LEFT)
        tk.Radiobutton(self.mode_frame, text="💬 General Chat", variable=self.mode_var, value="Chat", command=self.update_mode, bg="#f6f3ee", fg="#7c4700", selectcolor="#fbeee0", font=("Segoe UI", 11)).pack(side=tk.LEFT)

        self.label = tk.Label(self.overlay, text="Enter Register Number:", font=("Segoe UI", 13, "bold"), bg="#f6f3ee", fg="#7c4700")
        self.label.pack(pady=10)
        self.entry = tk.Entry(self.overlay, font=("Segoe UI", 13), width=30, bg="#fffbe9", fg="#7c4700", relief=tk.FLAT, highlightthickness=2, highlightbackground="#e0b97d")
        self.entry.pack(pady=5)

        self.auth_button = tk.Button(self.overlay, text="Login", command=self.handle_authentication, font=("Segoe UI", 12, "bold"), bg="#e0b97d", fg="#7c4700", activebackground="#fbeee0", relief=tk.FLAT)
        self.auth_button.pack(pady=3)
        self.logout_button = tk.Button(self.overlay, text="Logout", command=self.handle_logout, font=("Segoe UI", 12, "bold"), bg="#e0b97d", fg="#7c4700", activebackground="#fbeee0", relief=tk.FLAT)
        self.logout_button.pack(pady=3)

        # --- Text Search Box ---
        self.text_search_frame = tk.Frame(self.overlay, bg="#f6f3ee")
        self.text_search_label = tk.Label(self.text_search_frame, text="Book Search:", font=("Segoe UI", 11, "bold"), bg="#f6f3ee", fg="#7c4700")
        self.text_search_label.pack(side=tk.LEFT, padx=5)
        self.text_search_entry = tk.Entry(self.text_search_frame, font=("Segoe UI", 11), width=40, bg="#fffbe9", fg="#7c4700", relief=tk.FLAT, highlightthickness=1, highlightbackground="#e0b97d")
        self.text_search_entry.pack(side=tk.LEFT, padx=5)
        self.text_search_button = tk.Button(self.text_search_frame, text="Search", command=self.handle_text_search, font=("Segoe UI", 11, "bold"), bg="#e0b97d", fg="#7c4700", activebackground="#fbeee0", relief=tk.FLAT)
        self.text_search_button.pack(side=tk.LEFT, padx=5)
        self.text_search_entry.bind('<Return>', self.handle_text_search)

        # --- Text General Chat Box ---
        self.text_chat_frame = tk.Frame(self.overlay, bg="#f6f3ee")
        self.text_chat_label = tk.Label(self.text_chat_frame, text="General Chat:", font=("Segoe UI", 11, "bold"), bg="#f6f3ee", fg="#7c4700")
        self.text_chat_label.pack(side=tk.LEFT, padx=5)
        self.text_chat_entry = tk.Entry(self.text_chat_frame, font=("Segoe UI", 11), width=40, bg="#fffbe9", fg="#7c4700", relief=tk.FLAT, highlightthickness=1, highlightbackground="#e0b97d")
        self.text_chat_entry.pack(side=tk.LEFT, padx=5)
        self.text_chat_button = tk.Button(self.text_chat_frame, text="Send", command=self.handle_text_chat, font=("Segoe UI", 11, "bold"), bg="#e0b97d", fg="#7c4700", activebackground="#fbeee0", relief=tk.FLAT)
        self.text_chat_button.pack(side=tk.LEFT, padx=5)
        self.text_chat_entry.bind('<Return>', self.handle_text_chat)

        self.text_area = scrolledtext.ScrolledText(self.overlay, wrap=tk.WORD, width=100, height=10, font=("Segoe UI", 12), bg="#fffbe9", fg="#7c4700", relief=tk.FLAT, highlightthickness=2, highlightbackground="#e0b97d")
        self.text_area.pack(pady=10)
        self.text_area.insert(tk.END, "📚 June: Hello! How can I help you today?\n\n")
        self.text_area.configure(state='disabled')

        self.speak_button = tk.Button(self.overlay, text="🎤 Hold to Speak", font=("Segoe UI", 12, "bold"), bg="#e0b97d", fg="#7c4700", activebackground="#fbeee0", relief=tk.FLAT)
        self.speak_button.pack(pady=5)
        self.speak_button.bind('<ButtonPress>', self.start_listening)
        self.speak_button.bind('<ButtonRelease>', self.stop_listening)
        self.speak_button.config(state=tk.DISABLED)

        self.table_frame = tk.Frame(self.overlay, bg="#f6f3ee")
        self.table_frame.pack(pady=10)
        self.table = None

        # For hyperlink tags
        self.link_count = 0
        self.links = {}

        # Set initial mode
        self.update_mode()

    def draw_book_background(self):
        # Responsive book background
        self.bg_canvas.delete("all")
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        y_offset = int(h * 0.7)
        # Book base
        self.bg_canvas.create_oval(w*0.13, y_offset+80, w*0.87, h, fill="#f5e6c8", outline="#e0b97d", width=4)
        # Left page
        self.bg_canvas.create_polygon(
            w*0.16, y_offset+20, w*0.48, y_offset+20, w*0.48, h-30, w*0.16, h-30,
            fill="#fffbe9", outline="#e0b97d", width=3
        )
        # Right page
        self.bg_canvas.create_polygon(
            w*0.52, y_offset+20, w*0.84, y_offset+20, w*0.84, h-30, w*0.52, h-30,
            fill="#fffbe9", outline="#e0b97d", width=3
        )
        # Book spine
        self.bg_canvas.create_line(w*0.489, y_offset+20, w*0.511, h-30, fill="#e0b97d", width=6, smooth=True)
        self.bg_canvas.create_line(w*0.511, y_offset+20, w*0.489, h-30, fill="#e0b97d", width=6, smooth=True)
        # Book shadow
        self.bg_canvas.create_oval(w*0.22, h-30, w*0.78, h, fill="#e0b97d", outline="", width=0)
        # Some lines on the pages
        for y in range(y_offset+50, h-30, 20):
            self.bg_canvas.create_line(w*0.19, y, w*0.46, y, fill="#f3d9b1", width=2)
            self.bg_canvas.create_line(w*0.54, y, w*0.81, y, fill="#f3d9b1", width=2)

    def update_mode(self):
        mode = self.mode_var.get()
        if mode == "Chat":
            self.text_search_frame.pack_forget()
            self.text_chat_frame.pack(pady=5)
        else:
            self.text_chat_frame.pack_forget()
            self.text_search_frame.pack(pady=5)

    def handle_authentication(self):
        reg = self.entry.get().strip()
        success, message = authenticate(reg)
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"📚 June: {message}\n")
        self.text_area.configure(state='disabled')
        if success:
            self.authenticated = True
            self.speak_button.config(state=tk.NORMAL)

    def handle_logout(self):
        logout_user()
        self.authenticated = False
        self.speak_button.config(state=tk.DISABLED)
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, "📚 June: Logged out.\n")
        self.text_area.configure(state='disabled')

    def start_listening(self, event):
        if not self.authenticated:
            speak("Please login first to use voice input.")
            return
        self.recording = True
        threading.Thread(target=self.handle_speech).start()

    def stop_listening(self, event):
        self.recording = False

    def handle_speech(self):
        while self.recording:
            user_input = listen_for_speech()
            if user_input is None:
                continue
            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, f"🗣️ You: {user_input}\n")
            self.text_area.configure(state='disabled')
            mode = self.mode_var.get()

            if mode == "Search":
                headers, results, count = lib_response(user_input)
                if headers and results:
                    self.render_table(headers, results)
                    self.text_area.configure(state='normal')
                    self.text_area.insert(tk.END, f"📚 June: Found {count} result(s).\n")
                    self.text_area.configure(state='disabled')
            else:
                response = handle_general_chat(user_input)
                self.insert_with_links(f"📚 June: {response}\n")
                speak(response)

    def handle_text_search(self, event=None):
        if not self.authenticated:
            speak("Please login first to use book search.")
            return
        user_input = self.text_search_entry.get().strip()
        if not user_input:
            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, "📚 June: Please enter a search term.\n")
            self.text_area.configure(state='disabled')
            return
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"📝 You (typed): {user_input}\n")
        self.text_area.configure(state='disabled')
        headers, results, count = lib_response(user_input)
        if headers and results:
            self.render_table(headers, results)
            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, f"📚 June: Found {count} result(s).\n")
            self.text_area.configure(state='disabled')

    def handle_text_chat(self, event=None):
        if not self.authenticated:
            speak("Please login first to use general chat.")
            return
        user_input = self.text_chat_entry.get().strip()
        if not user_input:
            self.text_area.configure(state='normal')
            self.text_area.insert(tk.END, "📚 June: Please enter your question.\n")
            self.text_area.configure(state='disabled')
            return
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"💬 You (chat): {user_input}\n")
        self.text_area.configure(state='disabled')
        response = handle_general_chat(user_input)
        self.insert_with_links(f"📚 June: {response}\n")
        speak(response)

    def render_table(self, headers, data):
        if self.table:
            self.table.destroy()
        self.table = ttk.Treeview(self.table_frame, columns=headers, show="headings")
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=28, background="#fffbe9", fieldbackground="#fffbe9", foreground="#7c4700")
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#e0b97d", foreground="#7c4700")
        self.table.configure(style="Treeview")
        for h in headers:
            self.table.heading(h, text=h)
            self.table.column(h, width=250)
        for row in data:
            self.table.insert("", tk.END, values=row)
        self.table.pack()

    def insert_with_links(self, text):
        # Regex for URLs
        url_regex = r'(https?://[^\s]+)'
        pos = 0
        self.text_area.configure(state='normal')
        for match in re.finditer(url_regex, text):
            start, end = match.span()
            # Insert text before the link
            if start > pos:
                self.text_area.insert(tk.END, text[pos:start])
            url = text[start:end]
            tag = f"link{self.link_count}"
            self.text_area.insert(tk.END, url, tag)
            self.text_area.tag_config(tag, foreground="#1a73e8", underline=1)
            self.text_area.tag_bind(tag, "<Button-1>", lambda e, url=url: webbrowser.open(url))
            self.link_count += 1
            pos = end
        # Insert the rest of the text
        if pos < len(text):
            self.text_area.insert(tk.END, text[pos:])
        self.text_area.configure(state='disabled')

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
    prompt = f"""You are JUNE, a helpful library assistant for Easwari Engineering College Central Library. Use the following information to answer user queries and provide the available links to the user if asked for and do not respond using tables format. If the query is not related to library services, respond with a polite acknowledgment. 
General Library Info:
{general_info}

Previous History:
{history}

User: {user_query}
June:
"""
    response = llm(
        prompt=prompt,
        max_tokens=1024,
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

if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')  # Fullscreen on Windows
    app = LibraryBotGUI(root)
    def on_resize(event):
        app.draw_book_background()
    root.bind("<Configure>", on_resize)
    root.mainloop()
    mydb.close()   