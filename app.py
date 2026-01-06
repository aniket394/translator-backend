from flask import Flask, request, jsonify
from flask_cors import CORS
from deep_translator import GoogleTranslator
import os
import docx
import PyPDF2
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import shutil

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# -------------------------
# TESSERACT CONFIGURATION
# -------------------------
if shutil.which("tesseract"):
    print("Tesseract found in system PATH.")
else:
    print("WARNING: Tesseract not found. OCR may fail.")

# -------------------------
# LANGUAGE CODES
# -------------------------
lang_codes = {
    "English": "en", "Hindi": "hi", "Marathi": "mr", "Tamil": "ta",
    "Telugu": "te", "Kannada": "kn", "Gujarati": "gu", "Punjabi": "pa",
    "Malayalam": "ml", "Bengali": "bn", "Odia": "or", "Assamese": "as",
    "Urdu": "ur", "Chinese": "zh", "Japanese": "ja", "Spanish": "es",
}

# -------------------------
# UPLOAD FOLDER
# -------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------
# FILE UPLOAD
# -------------------------
@app.route("/upload_file", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file found"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        return jsonify({
            "message": "File uploaded successfully",
            "file_name": file.filename
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# FILE TRANSLATE
# -------------------------
@app.route("/file_translate", methods=["POST"])
def file_translate():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file found"}), 400

        file = request.files["file"]
        target_lang = request.form.get("target_lang", "hi")
        text_content = ""

        if file.filename.endswith(".txt"):
            text_content = file.read().decode("utf-8")

        elif file.filename.endswith(".docx"):
            doc = docx.Document(file)
            for para in doc.paragraphs:
                text_content += para.text + "\n"

        elif file.filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                if page.extract_text():
                    text_content += page.extract_text() + "\n"

        elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(file)
            image = ImageOps.exif_transpose(image)
            image = ImageOps.grayscale(image)
            image = ImageEnhance.Contrast(image).enhance(2.0)
            text_content = pytesseract.image_to_string(image)

        else:
            return jsonify({"error": "Unsupported file type"}), 400

        if not text_content.strip():
            return jsonify({"error": "No text extracted"}), 400

        translated_text = GoogleTranslator(
            source="auto",
            target=target_lang
        ).translate(text_content)

        return jsonify({
            "original_text": text_content,
            "translated_text": translated_text
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# TEXT TRANSLATE (Flutter calls this)
# -------------------------
@app.route("/translate", methods=["POST"])
def translate_text():
    data = request.json
    text = data.get("text")
    target_lang = data.get("target_lang", "hi")

    if not text:
        return jsonify({"error": "Text is required"}), 400

    translated_text = GoogleTranslator(
        source="auto",
        target=target_lang
    ).translate(text)

    return jsonify({"translated_text": translated_text})

# -------------------------
if __name__ == "__main__":
    print("Server running on port 5000")
    app.run(host="0.0.0.0", port=5000)
