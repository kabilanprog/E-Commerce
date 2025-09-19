import os, json, sqlite3, io, re, random, string, datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify
import qrcode
# --- Config ---
app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
app.config['DATABASE'] = os.path.join(app.instance_path, 'orders.db')

# Example UPI ID for QR text. Replace with your own.
PAYMENT_QR_UPI = "dineshrajendiran789@okhdfcbank"
SHOP_NAME = "DIRTY MENS"
SHOP_ADDRESS = "Coimbatore, Malumichampatti"
SHOP_PHONE = "865446254345"
SHOP_EMAIL = "dirtymens@gamil.com"  # kept as provided

os.makedirs(app.instance_path, exist_ok=True)

# --- DB helpers ---
def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE,
        name TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        items TEXT,
        total_price REAL,
        utr VARCHAR(100),
        status TEXT DEFAULT 'Pending',
        created_at TEXT
    );''')
    conn.commit()

init_db()

def new_order_id():
    return "DM" + datetime.datetime.now().strftime("%y%m%d") + ''.join(random.choices(string.digits, k=6))

# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/address', methods=['GET','POST'])
def address():
    if request.method == 'POST':
        cart_json = request.form.get('cart_json')
        print("DEBUG CART JSON:", cart_json)   # 👈 check in terminal
        try:
            cart = json.loads(cart_json) if cart_json else {}
        except Exception as e:
            print("JSON ERROR:", e)
            cart = {}

        if not isinstance(cart, dict):
            cart = {}

        session['cart'] = cart
        return render_template('address.html', cart=cart, total=cart.get('total', 0))

    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('index'))
    return render_template('address.html', cart=cart, total=cart.get('total', 0))
@app.route('/upi_qr')
def upi_qr():
    if not session.get('order_id') or not session.get('cart'):
        return redirect(url_for('index'))

    oid = session['order_id']
    total = session['cart'].get('total', 0)
    upi_id = PAYMENT_QR_UPI
    name = session['address_info']['name']

    # UPI QR format: "upi://pay?pa=<UPI_ID>&pn=<Name>&am=<Amount>&cu=INR"
    upi_text = f"upi://pay?pa={upi_id}&pn={name}&am={total}&cu=INR"

    img = qrcode.make(upi_text)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/payment', methods=['POST', 'GET'])
def payment():
    if request.method == 'POST':
        if not session.get('cart'):
            return redirect(url_for('index'))

        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        street = request.form.get('street', '').strip()
        town = request.form.get('town', '').strip()
        district = request.form.get('district', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', '').strip()
        full_addr = f"{street}, {town}, {district}, {state}, {country}"

        cart = session.get('cart')
        total = float(cart.get('total', 0))
        oid = new_order_id()

        conn = get_db()
        conn.execute(
            "INSERT INTO orders (order_id, name, phone, email, address, items, total_price, status, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (oid, name, phone, email, full_addr, json.dumps(cart.get("items", [])), total, 'Pending',
             datetime.datetime.now().isoformat())
        )
        conn.commit()

        session['order_id'] = oid
        session['address_info'] = dict(name=name, phone=phone, email=email, address=full_addr)

        # set expiry time (10 minutes from now)
        expiry_time = (datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp()

        return render_template(
            'payment.html',
            order_id=oid,
            address=session['address_info'],
            cart=cart,
            total=total,
            upi=PAYMENT_QR_UPI,
            expiry_time=expiry_time
        )

    if not session.get('order_id'):
        return redirect(url_for('index'))

    oid = session['order_id']
    cart = session.get('cart', {})

    # also set expiry time for GET (if refresh page)
    expiry_time = (datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp()

    return render_template(
        'payment.html',
        order_id=oid,
        address=session.get('address_info'),
        cart=cart,
        total=cart.get('total', 0),
        upi=PAYMENT_QR_UPI,
        expiry_time=expiry_time
    )


@app.route('/confirm', methods=['POST'])
def confirm():
    oid = session.get('order_id')
    if not oid:
        return redirect(url_for('index'))
    utr = request.form.get('utr','').strip()
    '''if not re.fullmatch(r'\d{12}', utr):
        flash("UTR must be exactly 12 digits.", "danger")
        return redirect(url_for('index'))'''
    

    conn = get_db()
    if not utr:
      conn.execute("UPDATE orders SET utr=?, status=? WHERE order_id=?", ("Cash on delivery", 'confirm', oid))
    else:
      utr="online \nUTR:"+utr
      conn.execute("UPDATE orders SET utr=?, status=? WHERE order_id=?", (utr, 'pending....', oid))
    conn.commit()
    return redirect(url_for('bill'))

@app.route('/bill')
def bill():
    oid = session.get('order_id')
    cart = session.get('cart')
    addr = session.get('address_info')
    if not all([oid, cart, addr]):
        return redirect(url_for('index'))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from reportlab.lib.utils import simpleSplit
    except ImportError:
        out = io.StringIO()
        out.write(f"{SHOP_NAME} - BILL\nOrder ID: {oid}\n\nTo:\n{addr['name']}\n{addr['address']}\nPhone: {addr['phone']}\nEmail: {addr['email']}\n\nItems:\n")
        for item in cart.get('items', []):
            out.write(f"- {item['name']} ({item.get('size','')}) x {item['qty']} @ ₹{item['price']} = ₹{item['subtotal']}\n")
        out.write(f"\nTotal: ₹{cart.get('total',0)}\n\nFrom:\n{SHOP_NAME}\n{SHOP_ADDRESS}\nPhone: {SHOP_PHONE}\nEmail: {SHOP_EMAIL}\n")
        mem = io.BytesIO(out.getvalue().encode('utf-8'))
        return send_file(mem, as_attachment=True, download_name=f"bill_{oid}.txt", mimetype="text/plain")

    mem = io.BytesIO()
    c = canvas.Canvas(mem, pagesize=A4)
    W, H = A4
    y = H - 30*mm

    def draw_text(text, x, y, max_width=W-40*mm, leading=14):
        lines = simpleSplit(text, 'Helvetica', 11, max_width)
        for ln in lines:
            c.drawString(x, y, ln)
            y -= leading
        return y

    c.setTitle(f"BILL_{oid}")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, y, SHOP_NAME); y -= 10*mm
    c.setFont("Helvetica", 11)
    y = draw_text(f"From: {SHOP_ADDRESS}\nPhone: {SHOP_PHONE}\nEmail: {SHOP_EMAIL}", 20*mm, y)
    y -= 5*mm
    c.drawString(20*mm, y, f"Order ID: {oid}"); y -= 7*mm
    c.drawString(20*mm, y, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"); y -= 12*mm

    y = draw_text(f"Bill To:\n{addr['name']}\n{addr['address']}\nPhone: {addr['phone']}\nEmail: {addr['email']}", 20*mm, y); y -= 5*mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, "Items"); y -= 7*mm
    c.setFont("Helvetica", 11)
    total = 0
    for item in cart.get('items', []):
        line = f"{item['name']}  Size:{item.get('size','-')}  Qty:{item['qty']}  @ ₹{item['price']}  = ₹{item['subtotal']}"
        c.drawString(22*mm, y, line); y -= 16
        total += float(item['subtotal'])
        if y < 30*mm:
            c.showPage()
            y = H - 20*mm
    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, f"TOTAL: ₹{total:.2f}"); y -= 12
    c.setFont("Helvetica", 10)
    y = draw_text("Thank you for shopping with us!", 20*mm, y)
    c.showPage()
    c.save()
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name=f"bill_{oid}.pdf", mimetype="application/pdf")
    
# --- Admin ---
@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u == 'cheran' and p == '123':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash("Invalid credentials", "danger")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()

    processed_orders = []
    for r in rows:
        order = dict(r)
        try:
            order['order_items'] = json.loads(order.get('items', '[]'))  # rename here
        except:
            order['order_items'] = []
        processed_orders.append(order)

    return render_template('admin_dashboard.html', orders=processed_orders)



@app.route('/admin/update/<order_id>', methods=['POST'])
def admin_update(order_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    status = request.form.get('status')
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE order_id=?", (status, order_id))
    conn.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<order_id>', methods=['POST'])
def admin_delete(order_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
    conn.commit()
    return redirect(url_for('admin_dashboard'))

# --- Order Status ---
@app.route('/order-status', methods=['GET','POST'])
def order_status():
    result = None
    if request.method == 'POST':
        oid = request.form.get('order_id','').strip()
        conn = get_db()
        row = conn.execute("SELECT order_id, status FROM orders WHERE order_id=?", (oid,)).fetchone()
        if row:
            result = dict(order_id=row['order_id'], status=row['status'])
        else:
            result = "NOT_FOUND"
    return render_template('order_status.html', result=result)

# --- Contact ---
@app.route('/contact')
def contact():
    return render_template('contact.html',
                           shop_name=SHOP_NAME,
                           shop_address=SHOP_ADDRESS,
                           shop_phone=SHOP_PHONE,
                           shop_email=SHOP_EMAIL)

# --- API ---
@app.route('/api/order/<order_id>')
def api_order(order_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE order_id=?", (order_id,)).fetchone()
    if not row: return jsonify(error="not_found"), 404
    data = dict(row)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
