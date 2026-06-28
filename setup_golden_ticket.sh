#!/usr/bin/env bash
#
# setup_golden_ticket.sh
# Run this INSIDE your cloned qr-tracker folder (the one with app/, README.md,
# requirements.txt, etc). It converts the forked repo into the cookie-based
# Golden Ticket prototype, while preserving the originals for your writeup.
#
# Usage:
#   cd qr-tracker
#   bash setup_golden_ticket.sh
#
set -e

# --- 0. Safety check: make sure we're in the right place -------------------
if [ ! -d "app" ] || [ ! -f "requirements.txt" ]; then
  echo "ERROR: Run this from inside the cloned qr-tracker folder."
  echo "It should contain an 'app' folder and a requirements.txt."
  exit 1
fi

echo "==> Backing up the original tracking files into _unused/ ..."
mkdir -p _unused/templates

# Move the tracker/login templates we don't need (keep base.html + index.html)
for f in all_visits campaign create_qr login qr_list visit; do
  [ -f "app/templates/$f.html" ] && mv "app/templates/$f.html" "_unused/templates/" \
    && echo "    moved app/templates/$f.html"
done

# Move Docker/database run files we don't need for the cookie version
for f in entrypoint.sh Dockerfile docker-compose.yml; do
  [ -f "$f" ] && mv "$f" "_unused/" && echo "    moved $f"
done

# Keep their main.py as a reference instead of deleting it
[ -f "app/main.py" ] && cp "app/main.py" "_unused/main_original.py" \
  && echo "    copied app/main.py -> _unused/main_original.py (reference)"

echo "==> Writing the Golden Ticket files ..."

# --- 1. app.py -------------------------------------------------------------
cat > app/main.py << 'PYEOF'
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
PYEOF
echo "    wrote app/main.py"

# --- 2. templates ----------------------------------------------------------
cat > app/templates/index.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SmartStickies test</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='main.css') }}">
</head>
<body>
  <div class="card">
    <div class="eyebrow">SmartStickies / Test bench</div>
    <div class="product-name">Tap a tag</div>
    <div class="subtle">
      {% if won %}You have already claimed your golden ticket. Use /reset to test again.
      {% else %}Each link is one NFC tag or QR code. Gold ones win.{% endif %}
    </div>
    <ul class="tag-list">
      {% for tag_id, p in products.items() %}
        <li>
          <a href="{{ url_for('tag', tag_id=tag_id) }}">
            <span>{{ tag_id }} &middot; {{ p.name }}</span>
            {% if p.golden %}<span class="gold-dot">GOLDEN</span>{% endif %}
          </a>
        </li>
      {% endfor %}
    </ul>
    <a class="reset-link" href="{{ url_for('reset') }}">Reset my cookie</a>
  </div>
</body>
</html>
HTMLEOF
echo "    wrote app/templates/index.html"

cat > app/templates/reward.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>You found a Golden Ticket!</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='main.css') }}">
</head>
<body>
  <div class="card reward">
    <div class="eyebrow">SmartStickies</div>
    <div class="ticket">
      <div class="ticket-label">Golden Ticket</div>
      <div class="ticket-title">You won!</div>
      <div>Show this code at checkout</div>
      <div class="coupon">{{ coupon }}</div>
    </div>
    <div class="product-name">{{ product.name }}</div>
    <div class="subtle">Unlocked on the tag for this item.</div>
  </div>
</body>
</html>
HTMLEOF
echo "    wrote app/templates/reward.html"

cat > app/templates/product.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ product.name }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='main.css') }}">
</head>
<body>
  <div class="card">
    <div class="eyebrow">SmartStickies</div>
    <div class="product-name">{{ product.name }}</div>
    <div class="price">{{ product.price }}</div>
    {% if note %}
      <div class="note">{{ note }}</div>
    {% else %}
      <div class="note">Tap more items around the store. Some hide a golden ticket.</div>
    {% endif %}
  </div>
</body>
</html>
HTMLEOF
echo "    wrote app/templates/product.html"

# --- 3. CSS (overwrite their main.css) -------------------------------------
cat > app/static/main.css << 'CSSEOF'
:root {
  --ink: #1a1a1a;
  --paper: #faf8f4;
  --line: #e4ded2;
  --muted: #7a7468;
  --gold: #c79a2e;
  --gold-deep: #9a7411;
  --gold-glow: #f3d985;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--paper); color: var(--ink);
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 24px; line-height: 1.5;
}
.card {
  width: 100%; max-width: 380px; background: #fff;
  border: 1px solid var(--line); border-radius: 18px; padding: 32px 28px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.06);
}
.eyebrow { font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); margin-bottom: 14px; }
.product-name { font-size: 24px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 6px; }
.price { font-size: 18px; color: var(--muted); margin-bottom: 20px; }
.note { font-size: 14px; color: var(--muted); background: var(--paper); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; margin-top: 8px; }
.reward { text-align: center; }
.ticket {
  position: relative;
  background: linear-gradient(135deg, var(--gold-glow), var(--gold) 55%, var(--gold-deep));
  border-radius: 14px; padding: 26px 22px; color: #2a1f00; margin: 6px 0 22px;
  overflow: hidden; animation: pop 0.5s cubic-bezier(0.2,0.9,0.3,1.3);
}
.ticket::after {
  content: ""; position: absolute; top: -60%; left: -30%; width: 60%; height: 220%;
  background: rgba(255,255,255,0.35); transform: rotate(20deg);
  animation: shine 2.2s ease-in-out infinite;
}
.ticket-label { font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; font-weight: 700; opacity: 0.8; }
.ticket-title { font-size: 26px; font-weight: 800; margin: 8px 0 4px; }
.coupon {
  font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 20px; font-weight: 700;
  letter-spacing: 0.08em; background: rgba(255,255,255,0.55); border-radius: 8px;
  padding: 8px 12px; display: inline-block; margin-top: 12px;
}
.subtle { font-size: 13px; color: var(--muted); margin-top: 4px; }
.tag-list { list-style: none; margin-top: 16px; }
.tag-list li { border-top: 1px solid var(--line); }
.tag-list a { display: flex; justify-content: space-between; align-items: center; padding: 14px 4px; text-decoration: none; color: var(--ink); }
.tag-list .gold-dot { color: var(--gold-deep); font-size: 12px; font-weight: 700; }
.reset-link { display: inline-block; margin-top: 18px; font-size: 13px; color: var(--muted); }
@keyframes pop { from { transform: scale(0.85); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes shine { 0% { left: -30%; } 60% { left: 130%; } 100% { left: 130%; } }
@media (prefers-reduced-motion: reduce) { .ticket, .ticket::after { animation: none; } }
CSSEOF
echo "    wrote app/static/main.css"

# --- 4. requirements.txt + vercel.json -------------------------------------
echo "Flask==3.0.3" > requirements.txt
echo "    wrote requirements.txt"

cat > vercel.json << 'JSONEOF'
{
  "version": 2,
  "builds": [
    { "src": "app/main.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/static/(.*)", "dest": "/app/static/$1" },
    { "src": "/(.*)", "dest": "app/main.py" }
  ]
}
JSONEOF
echo "    wrote vercel.json"

echo ""
echo "==> Done. Next steps:"
echo "    pip install -r requirements.txt"
echo "    python app/main.py"
echo "    open http://localhost:5000"
echo ""
echo "    Test: click a GOLDEN tag (A17/C04/F22) = win,"
echo "          a normal tag (B02/D09) = product page,"
echo "          a second golden tag = blocked (cookie works)."
echo ""
echo "    Originals saved in _unused/ for your writeup."
