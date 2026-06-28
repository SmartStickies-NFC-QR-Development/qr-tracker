"""
SmartStickies - Golden Ticket prototype (cookie-based)
Based on haicenhacks/qr-tracker: kept its scan-a-URL-and-branch-the-response
concept, replaced its database visitor tracking with a signed-cookie session
so the prototype needs no database and no login.
"""

from flask import Flask, render_template, session, redirect, url_for
import uuid

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-string-before-deploy"

PRODUCTS = {
    "A17": {"name": "Single-Origin Coffee Beans", "price": "$12.00", "golden": True},
    "B02": {"name": "Oat Milk, 1L",                "price": "$4.50",  "golden": False},
    "C04": {"name": "Dark Chocolate Bar",          "price": "$6.00",  "golden": True},
    "D09": {"name": "Sparkling Water, 6-pack",     "price": "$5.25",  "golden": False},
    "F22": {"name": "Aged Cheddar Wedge",          "price": "$9.75",  "golden": True},
}


def get_shopper():
    if "shopper_id" not in session:
        session["shopper_id"] = str(uuid.uuid4())
        session["won"] = False
    return session["shopper_id"]


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
                               note="This tag is not registered in the store. Ask a team member.")

    if session.get("won"):
        return render_template("product.html", product=product,
                               note="You have already claimed a golden ticket today. Come back tomorrow!")

    if product["golden"]:
        session["won"] = True
        coupon = "GOLD-" + session["shopper_id"][:6].upper()
        return render_template("reward.html", product=product, coupon=coupon)

    return render_template("product.html", product=product, note=None)


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
