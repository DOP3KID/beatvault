import os, json
from flask import Flask, render_template, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "beatvault-final-2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
UPLOAD_BEATS = os.path.join(PROJECT_ROOT, "uploads", "beats")
DATA_FILE = os.path.join(PROJECT_ROOT, "uploads", "beats.json")

os.makedirs(UPLOAD_BEATS, exist_ok=True)
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

app.config['UPLOAD_BEATS'] = UPLOAD_BEATS
app.config['MAX_CONTENT_LENGTH'] = 150 * 1024 * 1024

def load_beats():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_beats(beats):
    with open(DATA_FILE, 'w') as f:
        json.dump(beats, f)

@app.route('/')
def index():
    beats = load_beats()
    return render_template('index.html', beats=beats)

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        try:
            file = request.files.get('beat')
            if not file or file.filename == '':
                return "No file selected - go back", 400
            
            title = request.form.get('title','Untitled')
            price = request.form.get('price','100')
            bpm = request.form.get('bpm','140')
            key = request.form.get('key','C Min')
            wallet = request.form.get('ewallet','068 045 8336')

            filename = datetime.now().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
            save_path = os.path.join(UPLOAD_BEATS, filename)
            print(f"Saving to {save_path}")
            file.save(save_path)

            beats = load_beats()
            beats.insert(0, {
                'title': title,
                'price': price,
                'bpm': bpm,
                'key': key,
                'filename': filename,
                'seller': wallet,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'cover': f"https://picsum.photos/seed/{len(beats)+5}/300/300"
            })
            save_beats(beats)
            print(f"Saved beat {title}")
            return redirect('/')
        except Exception as e:
            print(f"UPLOAD ERROR: {e}")
            return f"Upload failed: {e} - check logs", 500

    return render_template('upload.html')

@app.route('/beats/<filename>')
def serve_beat(filename):
    return send_from_directory(UPLOAD_BEATS, filename)

@app.route('/register')
def register(): return render_template('index.html', beats=load_beats())
@app.route('/login')
def login(): return render_template('index.html', beats=load_beats())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))