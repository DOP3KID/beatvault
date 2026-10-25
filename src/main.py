import os, pathlib, sqlite3
from flask import Flask, request, redirect, render_template_string, session, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dop3kid-v74-final-0680458336")
BASE_DIR = pathlib.Path(__file__).parent.parent
app.config['UPLOAD_FOLDER'] = str(BASE_DIR / "uploads" / "beats")
app.config['PROOF_FOLDER'] = str(BASE_DIR / "uploads" / "proofs")
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROOF_FOLDER'], exist_ok=True)
DB = str(BASE_DIR / "beatvault_v74.db")

PLATFORM_EWALLET = "0680458336"
PLATFORM_DISPLAY = "068 045 8336"
PLATFORM_WHATSAPP = "27680458336"
PLATFORM_NAME = "DOP3KID.LK"
PREMIUM_PRICE = 149

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, earnings REAL DEFAULT 0, beats_count INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0, ewallet TEXT, whatsapp TEXT, bank_name TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS beats (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, genre TEXT, bpm INTEGER, price REAL, filename TEXT, sales INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, beat_id INTEGER, buyer_id INTEGER, seller_id INTEGER, amount REAL, reference TEXT, proof_file TEXT, status TEXT, buyer_phone TEXT)")
    conn.execute("INSERT OR IGNORE INTO users (id, username, password, ewallet, whatsapp, is_premium) VALUES (1, 'DOP3KID.LK', '123', ?, ?, 1)", (PLATFORM_EWALLET, PLATFORM_WHATSAPP))
    conn.commit()
    conn.close()

init_db()

BASE_HTML = """
<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>BeatVault v7.4 FINAL</title>
<style>
body{font-family:'Segoe UI',Arial;max-width:1100px;margin:auto;padding:15px;background:#050505;color:#fff}
a{color:#1DB954;text-decoration:none;font-weight:bold}.card{border:1px solid #222;padding:18px;margin:12px 0;border-radius:14px;background:#111}
.btn{background:#1DB954;border:none;padding:12px 22px;border-radius:8px;color:#fff;cursor:pointer;font-weight:bold}
.btn-gold{background:linear-gradient(90deg,#FFD700,#FFA500);color:#000}.btn-pay{background:linear-gradient(90deg,#00C9FF,#00A8E8);color:#fff;font-size:16px}
.btn-whatsapp{background:#25D366;color:#fff}.input{padding:12px;width:100%;max-width:500px;border-radius:8px;border:1px solid #333;background:#000;color:#fff;margin:6px 0}
.nav{background:#111;padding:12px;border-radius:12px;display:flex;gap:10px;flex-wrap:wrap;justify-content:space-between;position:sticky;top:0;z-index:10}
audio{width:100%;margin-top:12px;height:45px}
.bankbox{background:#000;border:1px dashed gold;padding:15px;border-radius:10px}
.badge-pending{background:#FFA500;color:#000;padding:3px 10px;border-radius:20px;font-size:12px}
</style></head><body>
<div class="nav"><div style="display:flex;gap:12px;flex-wrap:wrap;"><a href="/">🏠 Home</a><a href="/add">➕ Upload</a><a href="/profile">⚙️ Profile</a><a href="/sales">📦 Sales</a><a href="/dashboard">💰 Dash</a><a href="/upgrade">⭐ Premium</a></div><div>__USERSECTION__</div></div>
__CONTENT__<p style="text-align:center;color:#555;margin-top:30px;font-size:12px;">BeatVault v7.4 FINAL • Multi-Vendor eWallet • Premium → 068 045 8336 • DOP3KID.LK • LIVE</p></body></html>
"""

def render(inner):
    conn = get_db()
    us=""
    if "user_id" in session:
        cur = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
        u = cur.fetchone()
        if u:
            prem="⭐" if u["is_premium"] else "FREE"
            us=f"<span>👤 {u['username']} {prem} R{int(u['earnings'])} | {u['ewallet'] or 'NO EWALLET'}</span><a href='/logout'>Logout</a>"
    if not us:
        us="<a href='/login'>🔑 Login</a> <a href='/register'>📝 Register</a>"
    conn.close()
    return render_template_string(BASE_HTML.replace("__USERSECTION__", us).replace("__CONTENT__", inner))

@app.route("/")
def home():
    conn = get_db()
    beats = conn.execute("SELECT beats.*, users.username, users.ewallet FROM beats JOIN users ON beats.user_id=users.id ORDER BY beats.id DESC").fetchall()
    conn.close()
    html=f"<h2>🔥 Marketplace - Pay Each Seller Direct</h2><div class='card' style='border-color:#25D366;'><p>📱 Each beat → seller's own eWallet | Premium → <b>{PLATFORM_DISPLAY}</b> (DOP3KID.LK)</p></div>"
    if not beats:
        html+="<div class='card'><h3>No beats yet</h3><a href='/add'>Upload!</a> <a href='/profile'>Set eWallet!</a></div>"
    for b in beats:
        audio=f"<audio controls><source src='/uploads/{b['filename']}'></audio>" if b['filename'] else ""
        price_r=float(b['price'])*18
        ew = b['ewallet'] or PLATFORM_DISPLAY
        html+=f"<div class='card'><h3>{b['title']} - {b['genre']} • {b['bpm']} BPM • by {b['username']} <span style='font-size:11px;color:gold;'>eWallet: {ew}</span></h3>{audio}<p>Price: <b>R{price_r:.0f}</b> • Sales: {b['sales']}</p><a href='/pay/{b['id']}'><button class='btn btn-pay'>📱 Buy R{price_r:.0f} → Pay {b['username']}</button></a></div>"
    return render(html)

@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if request.method=="POST":
        ewallet = request.form.get("ewallet","").strip().replace(" ","")
        whatsapp = request.form.get("whatsapp","").strip().replace(" ","")
        if whatsapp.startswith("0"):
            whatsapp_27 = "27" + whatsapp[1:]
        else:
            whatsapp_27 = whatsapp
        bank = request.form.get("bank_name","eWallet")
        conn.execute("UPDATE users SET ewallet=?, whatsapp=?, bank_name=? WHERE id=?", (ewallet, whatsapp_27, bank, session["user_id"]))
        conn.commit()
        conn.close()
        return redirect("/profile")
    conn.close()
    return render(f"""
    <h2>⚙️ My Payment Profile</h2>
    <div class='card' style='border-color:gold;'>
        <p>User: <b>{user['username']}</b> | {'⭐ PREMIUM' if user['is_premium'] else 'FREE - 3 beats'} | Earnings: R{user['earnings']:.0f}</p>
        <form method="POST">
            <p>Your eWallet Number (BUYERS PAY YOU HERE)<br><input class="input" name="ewallet" value="{user['ewallet'] or ''}" placeholder="0680458336" required></p>
            <p>WhatsApp Number<br><input class="input" name="whatsapp" value="{user['whatsapp'] or ''}" placeholder="0680458336" required></p>
            <p>Bank Type<br><select class="input" name="bank_name"><option>eWallet</option><option>Capitec</option><option>FNB</option></select></p>
            <p><button class="btn btn-gold" type="submit">💾 Save My eWallet</button></p>
        </form>
    </div>
    """)

@app.route("/pay/<int:beat_id>", methods=["GET","POST"])
def pay_beat(beat_id):
    conn = get_db()
    beat = conn.execute("SELECT beats.*, users.username as seller_name, users.ewallet as seller_ewallet, users.whatsapp as seller_whatsapp FROM beats JOIN users ON beats.user_id=users.id WHERE beats.id=?", (beat_id,)).fetchone()
    if not beat:
        conn.close()
        return render("<div class='card'><p>Beat not found</p></div>")
    price_r=float(beat['price'])*18
    seller_ewallet = beat["seller_ewallet"] or PLATFORM_EWALLET
    seller_display = seller_ewallet[:3]+" "+seller_ewallet[3:6]+" "+seller_ewallet[6:] if len(seller_ewallet)>=10 else seller_ewallet
    seller_whatsapp = beat["seller_whatsapp"] or PLATFORM_WHATSAPP
    
    if request.method=="POST":
        ref=request.form.get("reference","").strip()
        phone=request.form.get("phone","").strip()
        proof=request.files.get("proof")
        proof_filename=""
        if proof and proof.filename:
            proof_filename=secure_filename(f"{beat_id}_{phone}_{proof.filename}")
            proof.save(os.path.join(app.config['PROOF_FOLDER'], proof_filename))
        buyer_id=session.get("user_id", 1)
        conn.execute("INSERT INTO sales (beat_id, buyer_id, seller_id, amount, reference, proof_file, status, buyer_phone) VALUES (?,?,?,?,?,?,?,?)",
                     (beat_id, buyer_id, beat["user_id"], price_r, ref, proof_filename, "pending", phone))
        conn.commit()
        conn.close()
        wa_msg=f"Hi%20{beat['seller_name']}%20I%20sent%20R{price_r:.0f}%20for%20{beat['title']}%20to%20{seller_ewallet}%20Ref%20{ref}"
        return render(f"<h2>⏳ Sent to {beat['seller_name']} - {seller_display}</h2><div class='card' style='border-color:#FFA500;'><p>Beat: {beat['title']} - R{price_r:.0f} to {seller_display}</p><p>Ref: {ref} | From: {phone}</p><p><span class='badge-pending'>PENDING - DIRECT TO SELLER</span></p><a href='https://wa.me/{seller_whatsapp}?text={wa_msg}' target='_blank'><button class='btn btn-whatsapp'>📱 WhatsApp Seller</button></a></div>")
    
    conn.close()
    return render(f"""
    <h2>📱 Buy - Pay {beat['seller_name']} Direct</h2>
    <div class='card' style='border-color:gold;'>
        <div style="background:#111;border:1px solid #25D366;padding:10px;border-radius:8px;"><p>💰 DIRECT: Money goes to {beat['seller_name']}'s eWallet {seller_display}</p></div>
        <div class='bankbox'><p>Seller: <b>{beat['seller_name']}</b></p><p>Send eWallet To: <span style='font-size:32px;color:gold;'>{seller_display}</span></p><p>Amount: <span style='font-size:26px;color:#1DB954;'>R{price_r:.0f}</span></p><p>Beat: {beat['title']}</p><p style='color:#aaa;font-size:12px;'>*120*321# → eWallet → {seller_display}</p></div>
        <form method="POST" enctype="multipart/form-data"><p>Your Cell<br><input class="input" name="phone" required></p><p>eWallet Ref<br><input class="input" name="reference" required></p><p>Screenshot<br><input type="file" name="proof" accept="image/*" class="input"></p><p><button class="btn btn-pay" type="submit">✅ Sent eWallet to {seller_display}</button></p></form>
    </div>
    """)

@app.route("/sales")
def sales_page():
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    my_orders = conn.execute("SELECT sales.*, beats.title, beats.filename, users.username as seller_name FROM sales JOIN beats ON sales.beat_id=beats.id JOIN users ON sales.seller_id=users.id WHERE sales.buyer_id=? AND sales.beat_id!=0 ORDER BY sales.id DESC", (session["user_id"],)).fetchall()
    my_sales = conn.execute("SELECT sales.*, beats.title FROM sales JOIN beats ON sales.beat_id=beats.id WHERE sales.seller_id=? AND sales.beat_id!=0 ORDER BY sales.id DESC", (session["user_id"],)).fetchall()
    premium_pending = []
    if session["user_id"] == 1:
        premium_pending = conn.execute("SELECT sales.*, users.username as buyer_name FROM sales JOIN users ON sales.buyer_id=users.id WHERE sales.status='premium_pending' ORDER BY sales.id DESC").fetchall()
    conn.close()
    
    orders_html="".join([f"<div class='card'><p>{s['title']} by {s['seller_name']} - R{s['amount']:.0f} - {s['status'].upper()} {'<a href=/uploads/'+s['filename']+' download><button class=btn>⬇️ Download</button></a>' if s['status']=='approved' else ''}</p></div>" for s in my_orders]) or "<p>No orders</p>"
    sales_html=""
    for s in my_sales:
        if s["status"]=="pending":
            proof_link = f"<a href='/proofs/{s['proof_file']}' target='_blank'>View Proof</a>" if s["proof_file"] else "No proof"
            sales_html+=f"<div class='card' style='border-color:orange;'><p>🔔 SALE: {s['title']} - R{s['amount']:.0f} - Buyer: {s['buyer_phone']} - Ref: {s['reference']} - {proof_link}<br><a href='/approve/{s['id']}'><button class='btn'>✅ Approve</button></a></div>"
        else:
            sales_html+=f"<div class='card'><p>{s['title']} - R{s['amount']:.0f} - {s['status']}</p></div>"
    sales_html = sales_html or "<p>No sales yet</p>"
    
    premium_html="".join([f"<div class='card' style='border-color:gold;'><p>🌟 PREMIUM: {p['buyer_name']} paid R{p['amount']} - Ref: {p['reference']} - From: {p['buyer_phone']} <a href='/proofs/{p['proof_file']}' target='_blank'>View</a><br><a href='/approve_premium/{p['id']}'><button class='btn btn-gold'>✅ Approve Premium</button></a></div>" for p in premium_pending])
    premium_section = f"<h3>🌟 Premium Payments to YOU {PLATFORM_DISPLAY}</h3>{premium_html or '<p>No premium pending</p>'}" if session["user_id"]==1 else ""
    
    return render(f"<h2>📦 Sales</h2><h3>🛒 My Orders</h3>{orders_html}<h3>💰 My Beat Sales (Direct to MY eWallet)</h3>{sales_html}{premium_section}")

@app.route("/approve/<int:sale_id>")
def approve_sale(sale_id):
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    sale = conn.execute("SELECT * FROM sales WHERE id=? AND seller_id=?", (sale_id, session["user_id"])).fetchone()
    if sale:
        conn.execute("UPDATE sales SET status='approved' WHERE id=?", (sale_id,))
        conn.execute("UPDATE beats SET sales=sales+1 WHERE id=?", (sale["beat_id"],))
        conn.execute("UPDATE users SET earnings=earnings+? WHERE id=?", (sale["amount"], sale["seller_id"]))
        conn.commit()
    conn.close()
    return redirect("/sales")

@app.route("/approve_premium/<int:sale_id>")
def approve_premium(sale_id):
    if "user_id" not in session or session["user_id"] != 1:
        return redirect("/login")
    conn = get_db()
    sale = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
    if sale and sale["status"]=="premium_pending":
        conn.execute("UPDATE users SET is_premium=1 WHERE id=?", (sale["buyer_id"],))
        conn.execute("UPDATE sales SET status='premium_approved' WHERE id=?", (sale_id,))
        conn.execute("UPDATE users SET earnings=earnings+? WHERE id=1", (sale["amount"],))
        conn.commit()
    conn.close()
    return redirect("/sales")

@app.route("/reject/<int:sale_id>")
def reject_sale(sale_id):
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    conn.execute("UPDATE sales SET status='rejected' WHERE id=? AND (seller_id=? OR buyer_id=?)", (sale_id, session["user_id"], session["user_id"]))
    conn.commit()
    conn.close()
    return redirect("/sales")

@app.route("/upgrade", methods=["GET","POST"])
def upgrade():
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if user["is_premium"]:
        conn.close()
        return render("<h2>🌟 You are Premium!</h2><div class='card'><p>Unlimited uploads!</p><a href='/add'><button class='btn btn-gold'>Upload</button></a></div>")
    if request.method=="POST":
        ref=request.form.get("reference","").strip()
        phone=request.form.get("phone","").strip()
        proof=request.files.get("proof")
        proof_filename=""
        if proof and proof.filename:
            proof_filename=secure_filename(f"PREMIUM_{session['user_id']}_{proof.filename}")
            proof.save(os.path.join(app.config['PROOF_FOLDER'], proof_filename))
        conn.execute("INSERT INTO sales (beat_id, buyer_id, seller_id, amount, reference, proof_file, status, buyer_phone) VALUES (0, ?, 1, ?, ?, ?, ?, ?)",
                     (session["user_id"], PREMIUM_PRICE, ref, proof_filename, "premium_pending", phone))
        conn.commit()
        conn.close()
        wa_msg=f"Hi%20DOP3KID%20I%20sent%20R{PREMIUM_PRICE}%20for%20PREMIUM%20from%20{user['username']}%20Ref%20{ref}"
        return render(f"<h2>⏳ Premium R{PREMIUM_PRICE} Sent to {PLATFORM_DISPLAY}</h2><div class='card' style='border-color:gold;'><p>Ref: {ref} - From: {phone}</p><a href='https://wa.me/{PLATFORM_WHATSAPP}?text={wa_msg}' target='_blank'><button class='btn btn-whatsapp'>📱 WhatsApp {PLATFORM_DISPLAY}</button></a></div>")
    conn.close()
    return render(f"""
    <h2>⭐ Upgrade to Premium - R{PREMIUM_PRICE} to {PLATFORM_DISPLAY}</h2>
    <div class='card' style='border-color:gold;'>
        <p>✅ Unlimited uploads (Free=3)<br>✅ Beats paid DIRECT to your eWallet<br>✅ Featured</p>
        <div class='bankbox'><p>Send eWallet To: <span style='font-size:30px;color:gold;'>{PLATFORM_DISPLAY}</span></p><p>Name: {PLATFORM_NAME}</p><p>Amount: <b>R{PREMIUM_PRICE}</b></p><p>*120*321# → eWallet → {PLATFORM_EWALLET}</p></div>
        <form method="POST" enctype="multipart/form-data"><p>Your Cell<br><input class="input" name="phone" required></p><p>eWallet Ref<br><input class="input" name="reference" required></p><p>Screenshot<br><input type="file" name="proof" accept="image/*" class="input"></p><p><button class="btn btn-gold" type="submit">✅ Sent R{PREMIUM_PRICE} to {PLATFORM_DISPLAY}</button></p></form>
    </div>
    """)

@app.route("/proofs/<path:filename>")
def proof_file(filename):
    return send_from_directory(app.config['PROOF_FOLDER'], filename)
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form.get("username","").strip(); p=request.form.get("password","123"); ew=request.form.get("ewallet","").strip()
        conn=get_db()
        try:
            conn.execute("INSERT INTO users (username,password,ewallet) VALUES (?,?,?)",(u,p,ew)); conn.commit()
            cur=conn.execute("SELECT id FROM users WHERE username=?",(u,)); uid=cur.fetchone()["id"]; session["user_id"]=uid; conn.close(); return redirect("/profile")
        except Exception as e:
            conn.close(); return render(f"<div class='card'><p>Taken: {e}</p></div>")
    return render("<h2>📝 Register - Get Paid Direct to YOUR eWallet</h2><form method='POST' class='card' style='border-color:gold;'><p>Producer Name<br><input class='input' name='username' required></p><p>Your eWallet<br><input class='input' name='ewallet' placeholder='0680458336' required></p><p>Password<br><input class='input' name='password' type='password' required></p><p><button class='btn btn-gold'>Create</button></p></form>")
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form.get("username"); p=request.form.get("password")
        conn=get_db(); cur=conn.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)); user=cur.fetchone(); conn.close()
        if user:
            session["user_id"]=user["id"]; return redirect("/")
        return render("<div class='card'><p>Wrong</p></div>")
    return render("<h2>🔑 Login</h2><form method='POST' class='card'><p>Producer<br><input class='input' name='username' value='DOP3KID.LK' required></p><p>Password<br><input class='input' name='password' type='password' value='123' required></p><p><button class='btn'>Login</button></p></form>")
@app.route("/logout")
def logout():
    session.clear(); return redirect("/")
@app.route("/add", methods=["GET","POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")
    conn=get_db(); cur=conn.execute("SELECT * FROM users WHERE id=?",(session["user_id"],)); user=cur.fetchone()
    if not user["ewallet"]:
        conn.close()
        return render("<h2>⚠️ Set eWallet First!</h2><div class='card'><a href='/profile'><button class='btn btn-gold'>Set My eWallet</button></a></div>")
    if request.method=="POST":
        cnt=conn.execute("SELECT COUNT(*) as c FROM beats WHERE user_id=?",(user["id"],)).fetchone()["c"]
        if cnt>=3 and not user["is_premium"]:
            conn.close(); return render(f"<h2>⚠️ Free Limit 3</h2><div class='card'><p>Upgrade R{PREMIUM_PRICE} to {PLATFORM_DISPLAY}</p><a href='/upgrade'><button class='btn btn-gold'>Upgrade</button></a></div>")
        title=request.form.get("title","Untitled"); genre=request.form.get("genre","Trap"); bpm=request.form.get("bpm","150"); price=request.form.get("price","19.99")
        file=request.files.get("beatfile"); filename=""
        if file and file.filename:
            filename=secure_filename(file.filename); save_path=os.path.join(app.config['UPLOAD_FOLDER'], filename)
            base,ext=os.path.splitext(filename); c=1
            while os.path.exists(save_path):
                filename=f"{base}_{c}{ext}"; save_path=os.path.join(app.config['UPLOAD_FOLDER'], filename); c+=1
            file.save(save_path)
        try: bpm_i=int(float(bpm))
        except: bpm_i=150
        try: price_f=float(price)
        except: price_f=19.99
        conn.execute("INSERT INTO beats (user_id,title,genre,bpm,price,filename) VALUES (?,?,?,?,?,?)",(user["id"],title,genre,bpm_i,price_f,filename))
        conn.execute("UPDATE users SET beats_count=beats_count+1 WHERE id=?",(user["id"],)); conn.commit(); conn.close(); return redirect("/")
    conn.close()
    return render(f"<h2>➕ Upload - Paid to {user['ewallet']}</h2><form method='POST' enctype='multipart/form-data' class='card'><p>Title<br><input class='input' name='title' required></p><p>Genre<br><select class='input' name='genre'><option>Trap</option><option>Drill</option><option>Amapiano</option></select></p><p>BPM<br><input class='input' name='bpm' value='150'></p><p>Price USD<br><input class='input' name='price' value='19.99'></p><p>MP3<br><input type='file' name='beatfile' accept='.mp3,audio/*' class='input' required></p><p><button class='btn btn-gold'>Upload</button></p></form>")
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    conn=get_db()
    user=conn.execute("SELECT * FROM users WHERE id=?",(session["user_id"],)).fetchone()
    beats=conn.execute("SELECT COUNT(*) as total, SUM(sales) as sales FROM beats WHERE user_id=?",(session["user_id"],)).fetchone()
    conn.close()
    return render(f"<h2>💰 Dashboard - {user['username']} {'⭐ PREMIUM' if user['is_premium'] else 'FREE'}</h2><div class='card' style='border-color:gold;'><p>Your eWallet: <b>{user['ewallet'] or 'NOT SET'}</b></p><p>Earnings: <b>R{user['earnings']:.0f}</b></p><p>Beats: {beats['total'] or 0}</p><p><a href='/profile'><button class='btn'>⚙️ Edit</button></a> <a href='/sales'><button class='btn btn-gold'>Sales</button></a></p></div>")

# --- DEPLOY FIX ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 BeatVault v7.4 FINAL LIVE - Premium → {PLATFORM_DISPLAY} R{PREMIUM_PRICE}")
    app.run(host="0.0.0.0", port=port)