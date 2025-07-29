import json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from google import genai
import fitz  # PyMuPDF
import docx  # python-docx
import re

# Set your API key here
API_KEY = "AIzaSyDyPWl1aBBXg9QocI6ZQ3X-3sN6j_DVXbs"  # 🔁 Replace with your actual key

# Initialize Gemini Client
client = genai.Client(api_key=API_KEY)

# Load regulation KB
def load_regulations(path="regulation.json"):
    with open(path, "r") as f:
        return json.load(f)

# Extract text from supported file formats
def extract_text_from_file(filepath):
    ext = Path(filepath).suffix.lower()

    if ext == ".pdf":
        text = ""
        doc = fitz.open(filepath)
        for page in doc:
            text += page.get_text()
        return text

    elif ext == ".docx":
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])

    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError("Unsupported file format. Use PDF, DOCX, or TXT.")

# Let user select file from system
def pick_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Car Specification File",
        filetypes=[
            ("All Supported", "*.pdf *.docx *.txt"),
            ("PDF Files", "*.pdf"),
            ("Word Docs", "*.docx"),
            ("Text Files", "*.txt")
        ]
    )
    return file_path

# Evaluate using Gemini
def evaluate_with_gemini(user_input, regulations):
    prompt = f"""
You are a car regulation checker AI agent.

1. Below is the official regulation standard in JSON format:
{json.dumps(regulations, indent=2)}

2. The manufacturer has provided this car specification:
\"\"\"
{user_input}
\"\"\"

3. Extract structured carData from the above spec.

4. Evaluate it against the regulation data and return this JSON format:
{{
  "status": "accepted" or "rejected",
  "regData": <regulationData>,
  "carData": <extractedCarData>,
  "issues": [{{"field": ..., "expected": ..., "actual": ..., "reason": ...}}],
  "reason": "summary of match/mismatch"
}}

Return only valid JSON output.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()

# Main runner
def main():
    print("📁 Please select a file (.pdf, .docx, .txt):")
    file_path = pick_file()
    if not file_path:
        print("❌ No file selected.")
        return

    print(f"✅ Selected: {file_path}")

    try:
        user_input = extract_text_from_file(file_path)
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return

    regulations = load_regulations("regulation.json")

    print("\n🔎 Evaluating with Gemini...\n")
    output = evaluate_with_gemini(user_input, regulations)

    try:
        output_clean = re.sub(r"^```(?:json)?\n?|```$", "", output.strip(), flags=re.MULTILINE)
        result = json.loads(output_clean)
        print(json.dumps(result, indent=2))
    except json.JSONDecodeError:
        print("❌ Gemini did not return valid JSON. Raw output:")
        print(output)

if __name__ == "__main__":
    main()
