from email.mime import image
from flask import flash
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
import mimetypes
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import sqlite3
DB_PATH = os.path.join(os.path.dirname(__file__), "threadsparkle.db")
app = Flask(__name__)

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        phone TEXT,
        address TEXT,
        product_name TEXT,
        price TEXT,
        size TEXT,
        thread_color TEXT,
        instructions TEXT,
        payment TEXT,
        image TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()
print("Creating database...")
try:
    create_database()
    print("Database created successfully")
except Exception as e:
    print("Database Error:", e)

load_dotenv()
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

mail = Mail(app)
app.secret_key = os.getenv("SECRET_KEY")
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Products
products = [
    {
        "id": 1,
        "name": "Bottle Green Bridal Set",
        "price": 350,
        "category": "Bridal",
        "image": "images/products/bridal/bottle-green.png"
    },
    {
        "id": 2,
        "name": "Purple Festive Set",
        "price": 230,
        "category": "Festive",
        "image": "images/products/festive/purple.png"
    }
]


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- SHOP ----------------

@app.route("/shop")
def shop():

    search = request.args.get("search", "").lower()

    filtered_products = []

    for product in products:

        if search in product["name"].lower():

            filtered_products.append(product)

    if search == "":
        filtered_products = products

    wishlist = session.get("wishlist", [])

    wishlist_ids = []

    for item in wishlist:
        wishlist_ids.append(int(item["id"]))

    return render_template(
        "shop.html",
        products=filtered_products,
        wishlist_ids=wishlist_ids
    )


# ---------------- OTHER PAGES ----------------

@app.route("/customize")
def customize():
    return render_template("customize.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")
@app.route("/send_message", methods=["POST"])
def send_message():

    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    msg = Message(
        subject="New Contact Message",
        sender=app.config["MAIL_USERNAME"],
        recipients=["piyushachebrolu26@gmail.com"]   # Your email
    )

    msg.body = f"""
New Contact Message

Name: {name}

Email: {email}

Message:

{message}
"""

    mail.send(msg)
    

    return redirect(url_for("contact"))

# ---------------- PRODUCT ----------------

@app.route("/product/<int:id>")
def product(id):

    selected_product = None

    for p in products:
        if p["id"] == id:
            selected_product = p
            break

    return render_template(
        "product.html",
        product=selected_product
    )
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (
            username == os.getenv("ADMIN_USERNAME")
            and password == os.getenv("ADMIN_PASSWORD")
        ):

            session["admin"] = True

            return redirect(url_for("admin_orders"))

        return render_template(
            "admin_login.html",
            error="Invalid username or password."
        )

    return render_template(
        "admin_login.html",
        error=""
    )

# ---------------- CART ----------------

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    cart = session.get("cart", [])

    item = {
        "id": request.form["id"],
        "name": request.form["name"],
        "price": request.form["price"],
        "image": request.form["image"],
        "size": request.form["size"],
        "thread_color": request.form["thread_color"],
        "other_color": request.form["other_color"],
        "instructions": request.form["instructions"]
    }

    cart.append(item)

    session["cart"] = cart

    return redirect(url_for("cart"))


@app.route("/cart")
def cart():

    cart_items = session.get("cart", [])

    return render_template(
        "cart.html",
        cart_items=cart_items
    )


@app.route("/remove_from_cart/<int:index>")
def remove_from_cart(index):

    cart = session.get("cart", [])

    if 0 <= index < len(cart):
        cart.pop(index)

    session["cart"] = cart

    return redirect(url_for("cart"))


# ---------------- WISHLIST ----------------

@app.route("/wishlist")
def wishlist():

    wishlist_items = session.get("wishlist", [])

    return render_template(
        "wishlist.html",
        wishlist_items=wishlist_items
    )


@app.route("/add_to_wishlist", methods=["POST"])
def add_to_wishlist():

    wishlist = session.get("wishlist", [])

    item_id = request.form["id"]

    found = False

    for item in wishlist:
        if item["id"] == item_id:
            wishlist.remove(item)
            found = True
            break

    if not found:
        wishlist.append({
            "id": request.form["id"],
            "name": request.form["name"],
            "price": request.form["price"],
            "image": request.form["image"]
        })

    session["wishlist"] = wishlist

    return redirect(url_for("shop"))


@app.route("/remove_from_wishlist/<int:index>")
def remove_from_wishlist(index):

    wishlist = session.get("wishlist", [])

    if 0 <= index < len(wishlist):
        wishlist.pop(index)

    session["wishlist"] = wishlist

    return redirect(url_for("wishlist"))


# ---------------- CHECKOUT ----------------

@app.route("/checkout", methods=["POST"])
def checkout():

    order = {
        "id": request.form["id"],
        "name": request.form["name"],
        "price": request.form["price"],
        "image": request.form["image"],
        "size": request.form["size"],
        "thread_color": request.form["thread_color"],
        "instructions": request.form["instructions"]
    }

    session["current_order"] = order

    return render_template(
        "checkout.html",
        order=order
    )


# ---------------- PLACE ORDER ----------------
@app.route("/place_order", methods=["POST"])
def place_order():

    customer = {
        "name": request.form["customer_name"],
        "phone": request.form["phone"],
        "address": request.form["address"],
        "payment": request.form["payment"]
    }

    order = session.get("current_order")

    if not order:
        return redirect(url_for("shop"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        phone TEXT,
        address TEXT,
        product_name TEXT,
        price TEXT,
        size TEXT,
        thread_color TEXT,
        instructions TEXT,
        payment TEXT,
        image TEXT,
        status TEXT
    )
    """)

    cursor.execute("""
    INSERT INTO orders (
        customer_name,
        phone,
        address,
        product_name,
        price,
        size,
        thread_color,
        instructions,
        payment,
        image,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer["name"],
        customer["phone"],
        customer["address"],
        order["name"],
        order["price"],
        order["size"],
        order["thread_color"],
        order["instructions"],
        customer["payment"],
        order.get("image", ""),
        "Pending"
    ))

    conn.commit()
    conn.close()

    # Clear cart after successful order
    session.pop("cart", None)
    session.modified = True

    return render_template(
        "order_success.html",
        customer=customer,
        order=order
    )
    
@app.route("/update_status/<int:order_id>", methods=["POST"])

def update_status(order_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    status = request.form["status"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (status, order_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_orders")) 

@app.route("/admin_orders")
def admin_orders():

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders")

    orders = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_orders.html",
        orders=orders
    )
@app.route("/admin_logout")
def admin_logout():

    session.pop("admin", None)

    return redirect(url_for("home"))    
@app.route("/custom_checkout", methods=["POST"])
def custom_checkout():

    image = request.files["image"]

    filename = secure_filename(image.filename)

    image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    order = {
    "name": "Customized Bangle",
    "price": "To Be Confirmed",
    "image": "uploads/" + filename,
    "size": request.form["size"],
    "thread_color": request.form["thread_color"],
    "instructions": request.form["instructions"]
}

    session["current_order"] = order

    return render_template(
        "checkout.html",
        order=order
    )
# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)