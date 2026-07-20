from flask import Flask, render_template, session, redirect, url_for, request, jsonify, send_file
from datetime import datetime
import json
import os
import urllib.request
import uuid

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-string-before-deploy"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The admin dashboard configures golden tickets in this Firestore collection;
# the store reads it back so the admin controls which items really win.
FIRESTORE_PRODUCTS_URL = ("https://firestore.googleapis.com/v1/projects/"
                          "smart-stickies-b3034/databases/(default)/documents/products")

# Pages a visitor can reach before logging in.
PUBLIC_ENDPOINTS = {"login", "register", "auth_complete", "logout",
                    "admin_dashboard", "static"}

PRODUCTS = {
    # Produce
    "P01": {"name": "Bananas, bunch", "price": "$1.80", "golden": False, "category": "Produce"},
    "P02": {"name": "Gala Apples, 3 lb", "price": "$4.20", "golden": False, "category": "Produce"},
    "P03": {"name": "Baby Spinach, 10 oz", "price": "$3.50", "golden": False, "category": "Produce"},
    "P04": {"name": "Avocado", "price": "$1.25", "golden": True, "category": "Produce"},
    # Bakery
    "K01": {"name": "Sourdough Loaf", "price": "$4.75", "golden": False, "category": "Bakery"},
    "K02": {"name": "Blueberry Muffins, 4-pack", "price": "$5.50", "golden": True, "category": "Bakery"},
    "K03": {"name": "Everything Bagels, 6-pack", "price": "$4.00", "golden": False, "category": "Bakery"},
    "K04": {"name": "Butter Croissant", "price": "$2.75", "golden": False, "category": "Bakery"},
    # Dairy & Eggs
    "D01": {"name": "Whole Milk, 1 gal", "price": "$3.90", "golden": False, "category": "Dairy & Eggs"},
    "D02": {"name": "Large Eggs, dozen", "price": "$4.60", "golden": False, "category": "Dairy & Eggs"},
    "D03": {"name": "Greek Yogurt, 32 oz", "price": "$5.25", "golden": False, "category": "Dairy & Eggs"},
    "D04": {"name": "Aged Cheddar Wedge", "price": "$9.75", "golden": True, "category": "Dairy & Eggs"},
    # Beverages
    "B01": {"name": "Sparkling Water, 6-pack", "price": "$5.25", "golden": False, "category": "Beverages"},
    "B02": {"name": "Cold Brew Coffee, 1L", "price": "$6.50", "golden": True, "category": "Beverages"},
    "B03": {"name": "Orange Juice, 52 oz", "price": "$4.30", "golden": False, "category": "Beverages"},
    "B04": {"name": "Green Tea, 20-pack", "price": "$3.75", "golden": False, "category": "Beverages"},
    # Snacks
    "S01": {"name": "Dark Chocolate Bar", "price": "$6.00", "golden": True, "category": "Snacks"},
    "S02": {"name": "Kettle Potato Chips", "price": "$3.20", "golden": False, "category": "Snacks"},
    "S03": {"name": "Trail Mix, 1 lb", "price": "$5.80", "golden": False, "category": "Snacks"},
    "S04": {"name": "Sea Salt Pretzels", "price": "$2.90", "golden": False, "category": "Snacks"},
    # Pantry
    "A01": {"name": "Single-Origin Coffee Beans", "price": "$12.00", "golden": True, "category": "Pantry"},
    "A02": {"name": "Extra-Virgin Olive Oil", "price": "$8.50", "golden": False, "category": "Pantry"},
    "A03": {"name": "Penne Pasta, 1 lb", "price": "$1.95", "golden": False, "category": "Pantry"},
    "A04": {"name": "Creamy Peanut Butter", "price": "$4.40", "golden": False, "category": "Pantry"},
}


def get_products():
    """The catalog with golden flags overlaid from Firestore (what the admin
    dashboard sets). Falls back to the built-in flags if Firestore is
    unreachable, so the store keeps working either way."""
    products = {tag: dict(p) for tag, p in PRODUCTS.items()}
    try:
        with urllib.request.urlopen(FIRESTORE_PRODUCTS_URL, timeout=3) as resp:
            data = json.load(resp)
        for doc in data.get("documents", []):
            tag = doc["name"].rsplit("/", 1)[-1]
            fields = doc.get("fields", {})
            if tag in products and "golden" in fields:
                products[tag]["golden"] = bool(fields["golden"].get("booleanValue", False))
    except Exception:
        pass
    return products


def products_by_aisle():
    """Group the catalog into aisles (categories) for the store page."""
    aisles = {}
    for tag_id, product in PRODUCTS.items():
        aisles.setdefault(product["category"], []).append((tag_id, product))
    return aisles


def cart_total_value(cart):
    """Sum a cart's line totals (unit price × quantity)."""
    total = 0.0
    for item in cart:
        total += float(item["price"].replace("$", "")) * item.get("qty", 1)
    return total


def cart_unit_count(cart):
    """Total number of individual units across the cart."""
    return sum(item.get("qty", 1) for item in cart)


def get_shopper():
    if "shopper_id" not in session:
        session["shopper_id"] = str(uuid.uuid4())
        session["tickets"] = []
        session["cart"] = []
    return session["shopper_id"]


def is_logged_in():
    return "member_name" in session


@app.before_request
def require_login():
    if request.endpoint in PUBLIC_ENDPOINTS:
        return
    if not is_logged_in():
        return redirect(url_for("login"))


# Login and register share one Firebase-backed page (member-portal.html),
# which switches between modes client-side.
@app.route("/login")
def login():
    return render_template("member-portal.html")


@app.route("/register")
def register():
    return render_template("member-portal.html")


@app.route("/auth/complete", methods=["POST"])
def auth_complete():
    """Bridge: Firebase authenticates the user in the browser, then posts the
    name/email here so the Flask session knows who is logged in."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    if not name:
        name = email.split("@")[0] if email else "Member"

    get_shopper()
    session["member_email"] = email
    session["member_name"] = name
    return jsonify({"ok": True})


@app.route("/logout")
def logout():
    session.pop("member_email", None)
    session.pop("member_name", None)
    return redirect(url_for("login"))


# The admin dashboard is a static page; on Vercel it's served as a static file,
# and this route serves the same file locally so it shares the Flask origin.
@app.route("/admin-dashboard.html")
def admin_dashboard():
    return send_file(os.path.join(BASE_DIR, "admin-dashboard.html"))


def add_ticket_to_collection(tag_id, product, coupon):
    ticket = {
        "tag_id": tag_id,
        "product_name": product["name"],
        "price": product["price"],
        "coupon": coupon,
        "claimed_at": datetime.now().isoformat(),
    }
    if "tickets" not in session:
        session["tickets"] = []
    session["tickets"].append(ticket)
    session.modified = True


@app.route("/")
def index():
    get_shopper()
    return render_template("index.html", aisles=products_by_aisle(),
                           won=session.get("won", False))


@app.route("/tag/<tag_id>")
def tag(tag_id):
    get_shopper()
    product = PRODUCTS.get(tag_id)

    if product is None:
        return render_template("product.html",
                               product={"name": "Unknown item", "price": "N/A"},
                               tag_id=None,
                               note="This tag is not registered in the store. Ask a team member.")

    # Golden status stays secret: every item looks like a normal product.
    # A golden ticket is only revealed after the item is purchased at checkout.
    return render_template("product.html", product=product, tag_id=tag_id, note=None)


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


@app.route("/portal")
def portal():
    if not is_logged_in():
        return redirect(url_for("register"))
    get_shopper()
    tickets = session.get("tickets", [])
    member_name = session.get("member_name", "Member")
    return render_template("portal.html", tickets=tickets, member_name=member_name)


@app.route("/ticket/<ticket_index>")
def obtain_ticket(ticket_index):
    get_shopper()
    tickets = session.get("tickets", [])

    try:
        index = int(ticket_index)
        if 0 <= index < len(tickets):
            ticket = tickets[index]
            product = PRODUCTS.get(ticket["tag_id"], {
                "name": ticket["product_name"],
                "price": ticket["price"],
                "golden": True
            })
            return render_template("reward.html", product=product, coupon=ticket["coupon"], ticket_index=index)
    except (ValueError, IndexError):
        pass

    return render_template("product.html",
                           product={"name": "Invalid ticket", "price": "N/A"},
                           tag_id=None,
                           note="This ticket could not be found.")


@app.route("/cart")
def view_cart():
    get_shopper()
    cart = session.get("cart", [])
    tickets = session.get("tickets", [])
    cart_total = cart_total_value(cart)
    return render_template("cart.html", cart_items=cart, tickets=tickets,
                           cart_total=f"${cart_total:.2f}", cart_count=cart_unit_count(cart))


@app.route("/cart/add/<tag_id>")
def add_to_cart(tag_id):
    get_shopper()
    product = PRODUCTS.get(tag_id)

    if product is None:
        return redirect(url_for("tag", tag_id=tag_id))

    # How many of this item to add (default 1, clamped to a sensible range).
    try:
        qty = int(request.args.get("qty", 1))
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, min(qty, 99))

    # Golden items are added to the cart like any other item — the shopper
    # cannot tell a golden item from a normal one until they pay.
    if "cart" not in session:
        session["cart"] = []

    # If the item is already in the cart, bump its quantity instead of
    # adding a duplicate line.
    for item in session["cart"]:
        if item["tag_id"] == tag_id:
            item["qty"] = item.get("qty", 1) + qty
            break
    else:
        session["cart"].append({
            "tag_id": tag_id,
            "name": product["name"],
            "price": product["price"],
            "qty": qty,
            "added_at": datetime.now().isoformat(),
        })
    session.modified = True

    note = (f"{qty} × {product['name']} added to cart!" if qty > 1
            else f"{product['name']} added to cart!")
    return render_template("product.html", product=product, tag_id=None, note=note)


@app.route("/cart/remove/<int:item_index>")
def remove_from_cart(item_index):
    get_shopper()
    cart = session.get("cart", [])

    if 0 <= item_index < len(cart):
        cart.pop(item_index)
        session.modified = True

    return redirect(url_for("view_cart"))


@app.route("/checkout")
def checkout():
    get_shopper()
    cart = session.get("cart", [])
    cart_total = cart_total_value(cart)
    return render_template("checkout.html", cart_items=cart,
                           cart_total=f"${cart_total:.2f}")


@app.route("/checkout/pay", methods=["POST"])
def pay():
    get_shopper()
    cart = session.get("cart", [])
    if not cart:
        return redirect(url_for("view_cart"))

    order_items = list(cart)
    order_total = cart_total_value(cart)

    # Reveal any secret golden tickets now that the shopper has paid.
    # Golden status comes from the admin-controlled Firestore config.
    live_products = get_products()
    won = []
    for item in cart:
        product = live_products.get(item["tag_id"])
        if product and product.get("golden"):
            coupon = f"GOLD-{item['tag_id']}-{session['shopper_id'][:4].upper()}"
            add_ticket_to_collection(item["tag_id"], product, coupon)
            won.append({"product_name": product["name"], "coupon": coupon})

    session["cart"] = []
    session.modified = True

    return render_template("purchase.html", order_items=order_items,
                           order_total=f"${order_total:.2f}", won=won)


if __name__ == "__main__":
    app.run(debug=True)
