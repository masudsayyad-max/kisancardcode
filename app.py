from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import unicodedata
from fpdf import FPDF
import io
import os
import glob
import qrcode
from functools import wraps

# ---------------- Flask App Setup ----------------
app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------------- MySQL DB Connection ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root123@localhost/agristack'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- Email Config ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "masuds653070@gmail.com"
app.config['MAIL_PASSWORD'] = "einp fxqb cvxr biaa"  # Google App Password
app.config['MAIL_DEFAULT_SENDER'] = "masuds653070@gmail.com"
mail = Mail(app)

# ---------------- Models ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    wallet = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)

    payments = db.relationship("Payment", backref="user", lazy=True)
    cards = db.relationship("Card", backref="user", lazy=True)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(50), default="Today")
    amount = db.Column(db.Integer, nullable=False)
    utr = db.Column(db.String(100))
    status = db.Column(db.String(20), default="Pending")  # Pending / Success / Rejected
    note = db.Column(db.String(255))


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    farmer_id = db.Column(db.String(50))
    name_en = db.Column(db.String(100))
    name_mr = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    aadhaar = db.Column(db.String(20))
    address_en = db.Column(db.String(200))
    address_mr = db.Column(db.String(200))

# ---------------- Assets ----------------
IMAGES_DIR = os.path.join("static", "images")
PHOTOS_DIR = os.path.join("static", "photos")
FONTS_DIR  = os.path.join("static", "fonts")

FRONT_TEMPLATE = os.path.join(IMAGES_DIR, "1.jpg")
BACK_TEMPLATE  = os.path.join(IMAGES_DIR, "2.jpg")

# Preferred Marathi font (Mangal) - support common filename variants
MANGAL_REGULAR_CANDIDATES = [
    os.path.join(FONTS_DIR, "mangalregular.ttf"),
    os.path.join(FONTS_DIR, "Mangal Regular.ttf"),
    os.path.join(FONTS_DIR, "Mangal.ttf"),
]
MANGAL_BOLD_CANDIDATES = [
    os.path.join(FONTS_DIR, "mangalbold.ttf"),
    os.path.join(FONTS_DIR, "Mangal Bold.ttf"),
]

# Fallback Devanagari font (Noto) - common filename variants
DEVANAGARI_REGULAR_CANDIDATES = [
    os.path.join(FONTS_DIR, "NotoSansDevanagari-Regular.ttf"),
    os.path.join(FONTS_DIR, "Noto Sans Devanagari Regular.ttf"),
]
DEVANAGARI_BOLD_CANDIDATES = [
    os.path.join(FONTS_DIR, "NotoSansDevanagari-Bold.ttf"),
    os.path.join(FONTS_DIR, "Noto Sans Devanagari Bold.ttf"),
]

def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

MANGAL_REGULAR_TTF = _first_existing(MANGAL_REGULAR_CANDIDATES)
MANGAL_BOLD_TTF = _first_existing(MANGAL_BOLD_CANDIDATES)
DEVANAGARI_TTF = _first_existing(DEVANAGARI_REGULAR_CANDIDATES)
DEVANAGARI_BOLD_TTF = _first_existing(DEVANAGARI_BOLD_CANDIDATES)

HAS_MANGAL_BOLD = MANGAL_BOLD_TTF is not None

# Pillow complex text layout (RAQM) support detection
# When available, this fixes Devanagari shaping/ligatures for Marathi text
RAQM_AVAILABLE = hasattr(ImageFont, "LAYOUT_RAQM")

def _truetype_with_layout(path: str, size: int):
    """
    Load a TrueType font using RAQM layout engine when available
    so that Devanagari scripts (Marathi) render correctly.
    Returns None if loading fails.
    """
    try:
        if RAQM_AVAILABLE:
            try:
                return ImageFont.truetype(path, size, layout_engine=ImageFont.LAYOUT_RAQM)
            except Exception:
                # If RAQM is not actually usable, fall back to BASIC engine
                return ImageFont.truetype(path, size)
        return ImageFont.truetype(path, size)
    except Exception:
        return None

# ---------------- Font Helper ----------------
def get_pillow_font(size: int, bold: bool = False):
    """
    Always try to return a font that supports Marathi correctly.
    Preference order:
    - Mangal Bold (if bold) -> Mangal Regular
    - Noto Sans Devanagari Bold/Regular
    - Arial Bold/Regular
    - Default PIL font
    """
    # Prefer Mangal
    if bold and os.path.exists(MANGAL_BOLD_TTF):
        f = _truetype_with_layout(MANGAL_BOLD_TTF, size)
        if f:
            return f
    if os.path.exists(MANGAL_REGULAR_TTF):
        f = _truetype_with_layout(MANGAL_REGULAR_TTF, size)
        if f:
            return f

    # Fallback to Noto
    if bold and os.path.exists(DEVANAGARI_BOLD_TTF):
        f = _truetype_with_layout(DEVANAGARI_BOLD_TTF, size)
        if f:
            return f
    if os.path.exists(DEVANAGARI_TTF):
        f = _truetype_with_layout(DEVANAGARI_TTF, size)
        if f:
            return f

    # Fallback to Arial
    try:
        if bold:
            return _truetype_with_layout("arialbd.ttf", size) or ImageFont.truetype("arialbd.ttf", size)
        return _truetype_with_layout("arial.ttf", size) or ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def _contains_devanagari(text: str) -> bool:
    return any('\u0900' <= ch <= '\u097F' for ch in text)

def draw_text_bold(draw: ImageDraw.ImageDraw, xy, text, font, fill):
    """
    Ensures bold appearance even when bold font file isn't available.
    If a real bold font is not present (e.g., only mangalregular.ttf),
    emulate bold by drawing multiple overlapped passes.
    """
    # Normalize to NFC to avoid split matras/nukta ordering issues
    if text is None:
        text = ""
    else:
        text = unicodedata.normalize('NFC', text)

    # Extra shaping hints for Devanagari when RAQM is present
    text_kwargs = {}
    if _contains_devanagari(text):
        # Enable common OpenType features and specify Marathi language tag
        text_kwargs = {
            "language": "mr",
            # Include key Indic shaping features to help engines that support them
            "features": [
                "kern", "liga", "clig", "calt",
                "akhn", "rphf", "pref", "blwf", "half", "pstf", "vatu"
            ],
            "direction": "ltr",
        }

    if HAS_MANGAL_BOLD:
        # Real bold loaded by get_pillow_font if available; one pass is enough
        draw.text(xy, text, font=font, fill=fill, **text_kwargs)
        return

    # Emulate bold by drawing with small offsets
    x, y = xy
    offsets = [(0,0), (1,0), (0,1), (1,1)]
    for dx, dy in offsets:
        draw.text((x + dx, y + dy), text, font=font, fill=fill, **text_kwargs)

# ---------------- Utility ----------------
def find_latest_user_photo(user_id: int):
    pattern = os.path.join(PHOTOS_DIR, f"user_{user_id}_*")
    files = glob.glob(pattern)
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def compose_card_image(card: Card, side: str) -> Image.Image:
    template_path = FRONT_TEMPLATE if side == "front" else BACK_TEMPLATE
    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    w, h = img.size
    # main text size a bit larger; bold=True (we also emulate bold if needed)
    f_main  = get_pillow_font(max(18, int(h * 0.050)), bold=True)
    f_bottom = get_pillow_font(max(28, int(h * 0.07)), bold=True)

    # --- Mehendi Color (set here) ---
    # Hex #1c3d2b -> RGB (28, 61, 43)
    mehendi_color = (28, 61, 43)

    # --- QR CODE ---
    qr_size = int(min(w, h) * 0.37)

    if side == "front":
        qr_payload = f"{card.farmer_id}|{card.name_en}|{card.mobile}|{card.aadhaar}"
        qr_x = int(w * 0.68)
        qr_y = int(h * 0.43)

        # PHOTO (shifted right + down)
        photo_path = find_latest_user_photo(card.user_id)
        if photo_path and os.path.exists(photo_path):
            ph_w = int(w * 0.17)
            ph_h = int(h * 0.25)
            photo = Image.open(photo_path).convert("RGB")
            photo = ImageOps.fit(photo, (ph_w, ph_h), method=Image.BICUBIC)
            img.paste(photo, (int(w * 0.12), int(h * 0.34)))

        # DETAILS (front)
        x = int(w * 0.30)
        y = int(h * 0.32)
        gap = int(h * 0.055)

        draw_text_bold(draw, (x, y + 0*gap), f"Name  : {card.name_en or ''}", f_main, mehendi_color)
        draw_text_bold(draw, (x, y + 1*gap), f"नाव   : {card.name_mr or ''}", f_main, mehendi_color)
        draw_text_bold(draw, (x, y + 2*gap), f"DOB   : {card.dob or ''}", f_main, mehendi_color)
        draw_text_bold(
            draw,
            (x, y + 3*gap),
            "पुरुष / Male" if (card.gender or '').lower().startswith("m") else "स्त्री / Female",
            f_main,
            mehendi_color
        )
        draw_text_bold(draw, (x, y + 4*gap), f"Mob No. : {card.mobile or ''}", f_main, mehendi_color)
        draw_text_bold(draw, (x, y + 5*gap), f"UID  : {card.aadhaar or ''}", f_main, mehendi_color)

    else:  # BACK SIDE
        qr_payload = f"{card.farmer_id}|{card.address_en}|{card.address_mr}"
        qr_x = int(w * 0.68)
        qr_y = int(h * 0.40)

        # BACK DETAILS
        x = int(w * 0.10)
        y = int(h * 0.30)
        gap = int(h * 0.06)

        draw_text_bold(draw, (x, y),       f"Address (EN): {card.address_en or ''}", f_main, mehendi_color)
        draw_text_bold(draw, (x, y + gap), f"पत्ता (MR): {card.address_mr or ''}",  f_main, mehendi_color)

    # Paste QR
    qr = qrcode.make(qr_payload).resize((qr_size, qr_size))
    img.paste(qr, (qr_x, qr_y))

    # --- FARMER ID at bottom (numeric only) ---
    if card.farmer_id:
        text = str(card.farmer_id)
        bbox = draw.textbbox((0, 0), text, font=f_bottom)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        text_x = (w - text_w) // 2
        text_y = h - text_h - 500  # move up from bottom
        draw_text_bold(draw, (text_x, text_y), text, f_bottom, mehendi_color)

    return img

def fpdf_bytes(pdf: FPDF) -> bytes:
    data = pdf.output(dest="S")
    return data if isinstance(data, (bytes, bytearray)) else data.encode("latin-1")

# Helper: save images sized correctly for physical card and return temp paths
def save_card_images_for_pdf(front_img: Image.Image, back_img: Image.Image, card_id: int, dpi=300):
    # target physical size in mm
    target_w_mm, target_h_mm = 86, 54
    # convert mm -> inches -> pixels at dpi
    px_w = int(dpi * (target_w_mm / 25.4))
    px_h = int(dpi * (target_h_mm / 25.4))

    front = front_img.convert("RGB").resize((px_w, px_h), Image.LANCZOS)
    back  = back_img.convert("RGB").resize((px_w, px_h), Image.LANCZOS)

    tmp_front = os.path.join(IMAGES_DIR, f"_tmp_front_{card_id}.jpg")
    tmp_back  = os.path.join(IMAGES_DIR, f"_tmp_back_{card_id}.jpg")
    front.save(tmp_front, "JPEG", quality=95)
    back.save(tmp_back,  "JPEG", quality=95)
    return tmp_front, tmp_back

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user"] = user.email
            return redirect(url_for("dashboard"))
        flash("Invalid email or password!")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        contact = request.form.get("contact")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered!")
            return redirect(url_for("login"))

        hashed_pw = generate_password_hash(password)
        user = User(name=name, contact=contact, email=email, password=hashed_pw, wallet=0)
        db.session.add(user)
        db.session.commit()

        session["user"] = user.email
        return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    user = User.query.filter_by(email=session["user"]).first()
    return render_template("dashboard.html", user=user, balance=user.wallet)

@app.route("/cards")
def cards():
    if "user" not in session:
        return redirect(url_for("login"))
    user = User.query.filter_by(email=session["user"]).first()
    return render_template("cards.html", cards=user.cards)

# ----------- CARD CREATION WITH WALLET DEDUCTION ----------
@app.route("/submit_card", methods=["POST"])
def submit_card():
    if "user" not in session:
        return redirect(url_for("login"))
    user = User.query.filter_by(email=session["user"]).first()

    if user.wallet < 30:
        flash("You don’t have sufficient amount (₹30 required). Please recharge!", "danger")
        return redirect(url_for("dashboard"))

    user.wallet -= 30

    # Handle photo upload (optional)
    photo = request.files.get("photo")
    if photo and photo.filename != "":
        os.makedirs(PHOTOS_DIR, exist_ok=True)
        safe_name = f"user_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
        photo.save(os.path.join(PHOTOS_DIR, safe_name))

    # Create new card
    card = Card(
        user_id=user.id,
        farmer_id=request.form.get("farmer_id"),
        name_en=request.form.get("name_en"),
        name_mr=request.form.get("name_mr"),
        dob=request.form.get("dob"),
        gender=request.form.get("gender"),
        mobile=request.form.get("mobile"),
        aadhaar=request.form.get("aadhaar"),
        address_en=request.form.get("address_en"),
        address_mr=request.form.get("address_mr")
    )
    db.session.add(card)
    db.session.commit()

    flash("Card submitted successfully! ₹30 deducted from your wallet.", "success")
    return redirect(url_for("cards"))

@app.route("/preview/<int:card_id>")
def preview_card(card_id):
    card = Card.query.get_or_404(card_id)
    front_img = compose_card_image(card, "front")
    back_img = compose_card_image(card, "back")

    import base64
    import io

    front_buffer = io.BytesIO()
    back_buffer = io.BytesIO()
    front_img.save(front_buffer, format="JPEG")
    back_img.save(back_buffer, format="JPEG")
    front_base64 = base64.b64encode(front_buffer.getvalue()).decode()
    back_base64 = base64.b64encode(back_buffer.getvalue()).decode()

    # Pass card object to template
    return render_template(
        "preview.html",
        card=card,
        front_img=front_base64,
        back_img=back_base64
    )

@app.route("/download_qrcode/<int:card_id>")
def download_qrcode(card_id):
    card = Card.query.get_or_404(card_id)
    qr_data = f"{card.farmer_id}|{card.name_en}|{card.mobile}|{card.aadhaar}|{card.address_en}|{card.address_mr}"
    qr_img = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")

# ---------------- DOWNLOAD CARD AS JPG (uses your templates) ----------------
@app.route("/download_jpg/<int:card_id>/<side>")
def download_jpg(card_id, side):
    side = side.lower()
    if side not in ("front", "back"):
        flash("Invalid side requested.", "danger")
        return redirect(url_for("cards"))

    card = Card.query.get_or_404(card_id)
    img = compose_card_image(card, side)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=92)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"card_{card.id}_{side}.jpg", mimetype="image/jpeg")

@app.route("/download_pdf/<int:card_id>")
def download_pdf(card_id):
    card = Card.query.get_or_404(card_id)
    front_img = compose_card_image(card, "front")
    back_img  = compose_card_image(card, "back")

    # Save images sized correctly for PDF embedding (86x54 mm @ 300 DPI)
    tmp_front, tmp_back = save_card_images_for_pdf(front_img, back_img, card.id, dpi=300)

    pdf = FPDF(unit="mm", format=(86, 54))
    pdf.set_auto_page_break(False)

    pdf.add_page()
    pdf.image(tmp_front, x=0, y=0, w=pdf.w, h=pdf.h)
    pdf.add_page()
    pdf.image(tmp_back,  x=0, y=0, w=pdf.w, h=pdf.h)

    # cleanup temp images
    try:
        os.remove(tmp_front)
        os.remove(tmp_back)
    except Exception:
        pass

    buffer = io.BytesIO(fpdf_bytes(pdf))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"card_{card.id}.pdf", mimetype="application/pdf")

# ---------------- PAYMENTS ----------------
@app.route("/mypayments")
def mypayments():
    if "user" not in session:
        return redirect(url_for("login"))
    user = User.query.filter_by(email=session["user"]).first()
    return render_template("mypayments.html", payments=user.payments, username=user.name)

@app.route("/recharge", methods=["GET", "POST"])
def recharge():
    if "user" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(email=session["user"]).first()

    if request.method == "POST":
        try:
            amount = int(request.form.get("amount", 0))
        except ValueError:
            flash("Invalid amount", "danger")
            return redirect(url_for("recharge"))

        utr = request.form.get("utr", "").strip()

        if amount < 50:
            flash("Minimum recharge amount is ₹50", "warning")
            return redirect(url_for("recharge"))

        txn = Payment(
            user_id=user.id,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            amount=amount,
            utr=utr,
            status="Pending",
            note="Waiting for admin approval"
        )
        db.session.add(txn)
        db.session.commit()

        try:
            msg = Message("📢 New Recharge Request", recipients=["masuds653070@gmail.com"])
            msg.body = f"""
New recharge request received:

👤 User: {user.name}
📧 Email: {user.email}
💰 Amount: ₹{amount}
🔑 UTR: {utr}
📅 Date: {txn.date}
📌 Status: Pending
"""
            mail.send(msg)
        except Exception as e:
            print("Email error while sending recharge request:", e)

        flash("Recharge request submitted! Waiting for admin approval.", "info")
        return redirect(url_for("mypayments"))

    return render_template("recharge.html", balance=user.wallet, username=user.name)

# ---------------- ADMIN ----------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("You must log in as admin first!", "danger")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            flash("Welcome Admin!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials!", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
@admin_required
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Logged out successfully!", "info")
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    payments = Payment.query.order_by(Payment.id.desc()).all()
    return render_template("admin.html", payments=payments)

@app.route("/update_payment/<int:txn_id>/<string:action>")
@admin_required
def update_payment(txn_id, action):
    txn = Payment.query.get_or_404(txn_id)
    user = txn.user

    if txn.status != "Pending":
        flash("This transaction is already processed.")
        return redirect(url_for("admin_dashboard"))

    if action == "approve":
        txn.status = "Success"
        txn.note = "Your payment has been approved successfully."
        user.wallet += txn.amount
        try:
            msg = Message("✅ Recharge Approved", recipients=[user.email])
            msg.body = f"Hello {user.name},\n\nYour recharge of ₹{txn.amount} has been approved.\nWallet balance: ₹{user.wallet}.\n\n- AgriStack Admin"
            mail.send(msg)
        except Exception as e:
            print("Email error (approval):", e)

    elif action == "reject":
        txn.status = "Rejected"
        txn.note = "Your payment request has been rejected due to the wrong UTR ID."
        try:
            msg = Message("❌ Recharge Rejected", recipients=[user.email])
            msg.body = f"Hello {user.name},\n\nYour recharge of ₹{txn.amount} has been rejected due to the wrong UTR ID.\n\n- AgriStack Admin"
            mail.send(msg)
        except Exception as e:
            print("Email error (rejection):", e)

    db.session.commit()
    flash(f"Transaction {action}d successfully!")
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---------------- MAIN ----------------
if __name__ == "__main__":
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    os.makedirs(FONTS_DIR,  exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
