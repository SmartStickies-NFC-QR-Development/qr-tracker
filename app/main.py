"""
SmartStickies - Golden Ticket prototype (cookie-based)
Based on haicenhacks/qr-tracker: kept its scan-a-URL-and-branch-the-response
concept, replaced its database visitor tracking with a signed-cookie session
so the prototype needs no database and no login.
"""

from flask import Flask, render_template, session, redirect, url_for
from datetime import datetime
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
    """Identify the current shopper and initialize their ticket collection."""
    if "shopper_id" not in session:
        session["shopper_id"] = str(uuid.uuid4())
        session["tickets"] = []  # member's collection of golden tickets
    return session["shopper_id"]


def add_ticket_to_collection(tag_id, product, coupon):
    """Add a won golden ticket to the member's collection."""
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
                               note="This tag is not registered in the store. Ask a team member.")

    # Check if this shopper has already won a golden ticket today
    if session.get("won"):
        return render_template("product.html", product=product,
                               note="You have already claimed a golden ticket today. Come back tomorrow!")

    if product["golden"]:
        session["won"] = True
        coupon = "GOLD-" + session["shopper_id"][:6].upper()
        
        # Save the golden ticket to the member's collection
        add_ticket_to_collection(tag_id, product, coupon)
        
        return render_template("reward.html", product=product, coupon=coupon)

    return render_template("product.html", product=product, note=None)


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


@app.route("/portal")
def portal():
    """Member Portal: display all golden tickets claimed by this shopper."""
    get_shopper()
    tickets = session.get("tickets", [])
    shopper_id = session.get("shopper_id")
    return render_template("portal.html", tickets=tickets, shopper_id=shopper_id)


@app.route("/ticket/<ticket_index>")
def obtain_ticket(ticket_index):
    """Open a saved ticket to obtain/redeem it (show the reward experience)."""
    get_shopper()
    tickets = session.get("tickets", [])
    
    try:
        index = int(ticket_index)
        if 0 <= index < len(tickets):
            ticket = tickets[index]
            # Find the original product for context
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
                           note="This ticket could not be found.")


if __name__ == "__main__":
    app.run(debug=True)
