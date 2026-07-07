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
    """Identify the current shopper and initialize their ticket collection and cart."""
    if "shopper_id" not in session:
        session["shopper_id"] = str(uuid.uuid4())
        session["tickets"] = []  # member's collection of golden tickets
        session["cart"] = []     # member's shopping cart
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
                               tag_id=None,
                               note="This tag is not registered in the store. Ask a team member.")

    if product["golden"]:
        # Check if this member already obtained this exact ticket
        existing_tags = [t["tag_id"] for t in session.get("tickets", [])]
        if tag_id in existing_tags:
            return render_template("product.html", product=product, tag_id=None,
                                   note="You already obtained this ticket. Check your portal!")
        
        coupon = "GOLD-" + session["shopper_id"][:6].upper()
        
        # Save the golden ticket to the member's collection
        add_ticket_to_collection(tag_id, product, coupon)
        
        return render_template("reward.html", product=product, coupon=coupon)

    return render_template("product.html", product=product, tag_id=tag_id, note=None)


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


@app.route("/cart")
def view_cart():
    """View shopping cart and golden tickets."""
    get_shopper()
    cart = session.get("cart", [])
    tickets = session.get("tickets", [])
    
    # Calculate cart totals
    cart_total = sum(float(item["price"].replace("$", "")) for item in cart)
    
    return render_template("cart.html", cart_items=cart, tickets=tickets, 
                           cart_total=f"${cart_total:.2f}", cart_count=len(cart))


@app.route("/cart/add/<tag_id>")
def add_to_cart(tag_id):
    """Add a product to the shopping cart."""
    get_shopper()
    product = PRODUCTS.get(tag_id)
    
    if product is None or product["golden"]:
        # Can't add unknown items or golden tickets to cart via this route
        return redirect(url_for("tag", tag_id=tag_id))
    
    if "cart" not in session:
        session["cart"] = []
    
    # Add item with a unique ID for removal
    cart_item = {
        "tag_id": tag_id,
        "name": product["name"],
        "price": product["price"],
        "added_at": datetime.now().isoformat(),
    }
    session["cart"].append(cart_item)
    session.modified = True
    
    return render_template("product.html", product=product, 
                           note=f"{product['name']} added to cart!")


@app.route("/cart/remove/<int:item_index>")
def remove_from_cart(item_index):
    """Remove an item from the shopping cart."""
    get_shopper()
    cart = session.get("cart", [])
    
    if 0 <= item_index < len(cart):
        cart.pop(item_index)
        session.modified = True
    
    return redirect(url_for("view_cart"))


@app.route("/checkout")
def checkout():
    """Checkout page: show cart items and applicable golden ticket coupons."""
    get_shopper()
    cart = session.get("cart", [])
    tickets = session.get("tickets", [])
    
    # Calculate totals
    cart_total = sum(float(item["price"].replace("$", "")) for item in cart)
    
    return render_template("checkout.html", cart_items=cart, tickets=tickets,
                           cart_total=f"${cart_total:.2f}")


if __name__ == "__main__":
    app.run(debug=True)
