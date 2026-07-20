# SmartStickies — Virtual Golden Ticket

A grocery-store web app with a gamified rewards twist. Shoppers browse aisles,
add items to a cart, and check out. Some products secretly carry a **golden
ticket** that is revealed only *after* payment. An **admin dashboard** decides
which products are golden — and the store honors those choices in real time.

> This started as a fork of a QR-tracker project and has since been rebuilt into
> the SmartStickies golden-ticket store.

## Features

- 🛒 **Store flow** — aisles by category, product pages with quantity, cart, and checkout.
- 🎟️ **Golden tickets stay secret** until the shopper pays; the receipt reveals any wins.
- 🛠️ **Admin dashboard** — toggle which products are golden; changes are saved to Firebase.
- 🔗 **Admin controls the real store** — the store reads golden flags from Firebase at
  checkout, so what the admin sets is what shoppers actually win.
- 🔐 **Firebase Authentication** for members, with a separate secure admin login
  (admins are listed in a Firestore `admins` collection — no hardcoded passwords).

## Tech

- **Backend:** Flask (`app/main.py`), deployed on **Vercel** (`@vercel/python`).
- **Data:** **Firebase Firestore** (`products` + `admins` collections).
- **Auth:** **Firebase Authentication** (email/password).
- **Frontend:** server-rendered Jinja templates + a static admin dashboard.

## Quick start

```bash
git clone https://github.com/SmartStickies-NFC-QR-Development/VirtualGoldenTicket_TeamPrototype.git
cd VirtualGoldenTicket_TeamPrototype
python3.12 -m pip install -r requirements.txt
python3.12 -c "from app.main import app; app.run(port=5001)"
```

Then open <http://localhost:5001>. Full instructions — including Firebase project
setup and creating your admin account — are in **[SETUP.md](SETUP.md)**.

> **Note:** use Python 3.11 or 3.12. Some Python 3.14 builds ship a broken `pip`
> (an `expat`/XML error on import), so stick with 3.11/3.12.

## How golden tickets flow

```
Admin dashboard  ──writes──►  Firestore `products` (golden: true/false)
                                     │
                                     ▼  read at checkout (get_products)
Shopper buys item  ──►  Flask pay()  ──►  reveals Golden Ticket if golden
```

## Project layout

```
VirtualGoldenTicket_TeamPrototype/
├─ app/
│  ├─ main.py                 # Flask store: routes, cart, checkout, golden overlay
│  └─ templates/
│     ├─ member-portal.html   # Login (member + secure admin login)
│     ├─ index.html           # Store home (aisles)
│     ├─ product.html         # Item page (quantity + add to cart)
│     ├─ cart.html, checkout.html, purchase.html
│     └─ portal.html, reward.html
├─ admin-dashboard.html       # Admin: configure golden tickets (Firestore)
├─ firestore.rules            # Firestore security rules (publish in Firebase console)
├─ vercel.json                # Vercel build/routes
├─ requirements.txt
├─ SETUP.md                   # Full setup guide
└─ README.md
```

## Security notes

- Firestore should not be left in test mode — publish `firestore.rules`
  (Firebase console → Firestore → Rules) so only admins can change products.
- When deploying, add your Vercel domain to Firebase → Authentication →
  **Authorized domains**, or logins will be blocked on the live site.

## License

MIT — see [LICENSE.txt](LICENSE.txt). Originally forked from a QR-tracker project
by [haicen](https://ko-fi.com/haicen).
