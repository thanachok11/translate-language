from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from pydub import AudioSegment
import os
import uuid
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# จัดรูปแบบข้อความให้เหมาะสมกับประโยค
def format_text(text):
    sentences = re.split(r'(?<=[.?!…])\s+|(?<=\u0E2F)', text)
    formatted = '\n'.join(s.strip().capitalize() for s in sentences if s.strip())
    return formatted

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'audiofile' not in request.files:
        return jsonify({'error': 'ไม่มีไฟล์แนบมา'}), 400

    file = request.files['audiofile']
    original_filename = file.filename
    file_ext = original_filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(input_path)

    # แปลงเป็น .wav หากไม่ใช่
    wav_path = input_path
    if not input_path.endswith('.wav'):
        wav_path = input_path.replace(f".{file_ext}", ".wav")
        sound = AudioSegment.from_file(input_path)
        sound.export(wav_path, format="wav")

    # แปลงเสียงเป็นข้อความ
    r = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="th-TH")
            formatted_text = format_text(text)
            return jsonify({'text': formatted_text})
    except sr.UnknownValueError:
        return jsonify({'text': 'ไม่สามารถแปลงเสียงได้'})
    except sr.RequestError as e:
        return jsonify({'text': f'เกิดข้อผิดพลาด: {e}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

