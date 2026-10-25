import os, json
from flask import Flask, render_template, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "beatvault-2026-final"

# USE /tmp - Render only allows writing here
UPLOAD_BEATS = "/tmp/uploads/beats"
DATA_FILE = "/tmp/uploads/beats.json"

os.makedirs(UPLOAD_BEATS, exist_ok=True)
os.makedirs("/tmp/uploads", exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

app.config['UPLOAD_BEATS'] = UPLOAD_BEATS
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB - WAV too big, use MP3

def load_beats():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_beats(b):
    with open(DATA_FILE, 'w') as f:
        json.dump(b, f)

@app.route('/')
def index():
    return render_template('index.html', beats=load_beats())

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        print("=== UPLOAD STARTED ===")
        file = request.files.get('beat')
        print(f"File: {file.filename if file else 'None'}")
        if not file or file.filename == '':
            return "No file! Go back and select file", 400
        
        try:
            title = request.form.get('title','Untitled')
            price = request.form.get('price','100')
            bpm = request.form.get('bpm','114')
            key = request.form.get('key','C Min')
            wallet = request.form.get('ewallet','068 045 8336')
            
            filename = datetime.now().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
            path = os.path.join(UPLOAD_BEATS, filename)
            file.save(path)
            print(f"Saved to {path} - size {os.path.getsize(path)}")

            beats = load_beats()
            beats.insert(0, {
                'title': title, 'price': price, 'bpm': bpm, 'key': key,
                'filename': filename, 'seller': wallet,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'cover': f"https://picsum.photos/seed/{len(beats)}/300/300"
            })
            save_beats(beats)
            return redirect('/')
        except Exception as e:
            print(f"ERROR: {e}")
            return f"Error: {e}", 500

    return render_template('upload.html')

@app.route('/beats/<filename>')
def serve_beat(filename):
    return send_from_directory(UPLOAD_BEATS, filename)

@app.route('/register')
def register(): return redirect('/')
@app.route('/login')
def login(): return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))