# Lib-Chatbot

A desktop chatbot for Easwari Engineering College Central Library, featuring voice recognition (Whisper), text-to-speech, LLM-powered general chat, and book search via MySQL.

---

## Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)
- **MySQL Server** (with a database named `library`)
- **LM Studio** (for downloading GGUF LLM models)
- **Git** (optional, for cloning)
- **CUDA** (optional, for GPU acceleration)

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Lib-Chatbot.git
cd Lib-Chatbot
```

### 2. Create and Activate a Virtual Environment (Recommended)

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up the MySQL Database

- Ensure MySQL is running and you have a database named `library`.
- Create the necessary tables (`students`, `lib`, `history`) as per your schema.
- Import book data:
    - Edit the CSV path in `data import from csv to sql for lib bot.py` if needed.
    - Run the script to import books:
      ```bash
      python "data import from csv to sql for lib bot.py"
      ```

### 5. Download and Prepare the LLM Model

- **Install [LM Studio](https://lmstudio.ai/) on your machine.**
- Use LM Studio to download a GGUF-format Llama model (e.g., Llama-3.2-3B-Instruct).
- Note the downloaded model’s path (e.g., `D:/AI/lmstudio-community/Llama-3.2-3B-Instruct-GGUF/Llama-3.2-3B-Instruct-Q4_K_M.gguf`).
- Update the `model_path` in `main.py` and `lib_whisper.py` if your path differs.

### 6. (Optional) GPU Acceleration

- If you have a CUDA-capable GPU, ensure CUDA is installed and configure `llama_cpp` and `faster-whisper` to use GPU (see their docs).

---

## Running the Chatbot

```bash
python main.py
```

- A GUI window will open.
- Login with your register number (must exist in the `students` table).
- Use text or hold the "Hold to Speak" button for voice input.
- Switch between "Search" (book search) and "General Chat" (LLM-powered Q&A).

---

## Notes

- **Model Download:** Only GGUF models downloaded via LM Studio are supported.
- **Database:** Ensure your MySQL credentials in the scripts match your setup.
- **Voice:** Text-to-speech and Whisper require a working microphone and speakers.
- **Dependencies:** All required Python packages are listed in `requirements.txt`.

---

## Troubleshooting

- If you get errors about missing DLLs or drivers, ensure your Python, pip, and all dependencies are 64-bit and up to date.
- For MySQL errors, check your database connection and user permissions.
- For LLM errors, verify the GGUF model path and that the model is compatible with `llama-cpp-python`.

---
