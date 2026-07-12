from flask import Flask, render_template, session, redirect, url_for, request
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-string-before-deploy"

PRODUCTS = {
    "A17": {"name": "Single-Origin Coffee Beans", "price": "$12.00", "golden": True},
    "B02": {"name": "Oat Milk, 1L", "price": "$4.50", "golden": False},
    "C04": {"name": "Dark Chocolate Bar", "price": "$6.00", "golden": True},
    "D09": {"name": "Sparkling Water, 6-pack", "price": "$5.25", "golden": False},
    "F22": {"name": "Aged Cheddar Wedge", "price": "$9.75", "golden": True},
}


def get_shopper():
    if "shopper_id" not in session:
        session["shopper_id"] = str(uuid.uuid4())
        session["tickets"] = []
        session["cart"] = []
    return session["shopper_id"]


def is_logged_in():
    return "member_name" in session


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.",
                                   name=name, email=email)
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.",
                                   name=name, email=email)
        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters.",
                                   name=name, email=email)

        session["member_email"] = email
        session["member_name"] = name
        return redirect(url_for("portal"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("login.html", error="Email and password are required.", email=email)

        session["member_email"] = email
        if "member_name" not in session:
            session["member_name"] = email.split("@")[0]
        return redirect(url_for("portal"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("member_email", None)
    session.pop("member_name", None)
    return redirect(url_for("index"))


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
    return render_template("index.html", products=PRODUCTS,
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

    if product["golden"]:
        existing_tags = [t["tag_id"] for t in session.get("tickets", [])]
        if tag_id in existing_tags:
            return render_template("product.html", product=product, tag_id=None,
                                   note="You already obtained this ticket. Check your portal!")

        coupon = "GOLD-" + session["shopper_id"][:6].upper()
        add_ticket_to_collection(tag_id, product, coupon)
        return render_template("reward.html", product=product, coupon=coupon)

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
    cart_total = sum(float(item["price"].replace("$", "")) for item in cart)
    return render_template("cart.html", cart_items=cart, tickets=tickets,
                           cart_total=f"${cart_total:.2f}", cart_count=len(cart))


@app.route("/cart/add/<tag_id>")
def add_to_cart(tag_id):
    get_shopper()
    product = PRODUCTS.get(tag_id)

    if product is None or product["golden"]:
        return redirect(url_for("tag", tag_id=tag_id))

    if "cart" not in session:
        session["cart"] = []

    cart_item = {
        "tag_id": tag_id,
        "name": product["name"],
        "price": product["price"],
        "added_at": datetime.now().isoformat(),
    }
    session["cart"].append(cart_item)
    session.modified = True

    return render_template("product.html", product=product, tag_id=None,
                           note=f"{product['name']} added to cart!")


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
    tickets = session.get("tickets", [])
    cart_total = sum(float(item["price"].replace("$", "")) for item in cart)
    return render_template("checkout.html", cart_items=cart, tickets=tickets,
                           cart_total=f"${cart_total:.2f}")


if __name__ == "__main__":
    app.run(debug=True)
