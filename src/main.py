import os
from flask import Flask, render_template, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "beatvault-dop3kid-2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_BEATS = os.path.join(BASE_DIR, "..", "uploads", "beats")
UPLOAD_PROOFS = os.path.join(BASE_DIR, "..", "uploads", "proofs")
os.makedirs(UPLOAD_BEATS, exist_ok=True)
os.makedirs(UPLOAD_PROOFS, exist_ok=True)

app.config['UPLOAD_BEATS'] = UPLOAD_BEATS
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

beats_db = []

@app.route('/')
def index():
    return render_template('index.html', beats=beats_db)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('beat')
        title = request.form.get('title', 'Untitled Beat')
        price = request.form.get('price', '149')
        bpm = request.form.get('bpm', '140')
        key = request.form.get('key', 'C Min')
        wallet = request.form.get('ewallet', '068 045 8336')
        
        if file and file.filename != '':
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext in ['mp3','wav','m4a','flac']:
                filename = datetime.now().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_BEATS, filename))
                beats_db.append({
                    'title': title,
                    'price': price,
                    'bpm': bpm,
                    'key': key,
                    'filename': filename,
                    'seller': wallet,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'cover': f"https://picsum.photos/seed/{len(beats_db)+10}/300/300"
                })
                return redirect('/')
    return render_template('upload.html')

@app.route('/beats/<filename>')
def serve_beat(filename):
    return send_from_directory(app.config['UPLOAD_BEATS'], filename)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))