# SmartStickies — Virtual Golden Ticket: Setup Guide

A grocery store web app where shoppers browse aisles, add items to a cart, and
check out. Some items secretly carry a **golden ticket**, revealed only *after*
payment. An **admin dashboard** decides which products are golden.

- **Store** — a Flask app (`app/main.py` + `app/templates/`).
- **Admin dashboard** — a static page (`admin-dashboard.html`) that reads/writes
  a **Firebase Firestore** database.
- **Login** — a single page (`app/templates/member-portal.html`) using **Firebase
  Authentication**, with a separate secure admin login.

The store reads golden flags from Firestore at checkout, so **whatever the admin
sets is what shoppers actually win.**

---

## 1. Prerequisites

- **Python 3.11 or 3.12** (⚠️ *not* 3.14 — its `pip`/`expat` is currently broken
  on this machine; use `python3.12`).
- A **Google account** for Firebase.
- **Node.js** is only needed if you want to run the automated tests.

Check your Python:

```bash
python3.12 --version   # should print Python 3.12.x
```

---

## 2. Install dependencies

```bash
cd qr-tracker
python3.12 -m pip install -r requirements.txt
```

---

## 3. Firebase setup (one time)

The app talks to a Firebase project. The code currently points at
`smart-stickies-b3034`. To use **your own** project instead, create one and swap
the config (Step 3f). Otherwise skip to Step 4.

### 3a. Create the project
1. Go to <https://console.firebase.google.com> and sign in.
2. **Add project** → name it → you can turn **Google Analytics OFF** → **Create**.

### 3b. Turn on Authentication (logins)
1. **Build → Authentication → Get started**.
2. Enable **Email/Password** → **Save**.

### 3c. Turn on Firestore (the database)
1. **Build → Firestore Database → Create database**.
2. Choose **Standard edition** → **Start in test mode** → pick a location → **Enable**.

> **Test mode** allows open read/write and **auto-expires in ~30 days**. Lock it
> down with the real rules (Step 6) before then.

### 3d. Load the product catalog
Open the store as admin and click **Load starter products** (see Step 5), *or*
add products by hand. Each document lives in the `products` collection, keyed by
its tag id, e.g. document `A01`:

| Field    | Type    | Example                       |
|----------|---------|-------------------------------|
| name     | string  | `Single-Origin Coffee Beans`  |
| price    | string  | `$12.00`                      |
| golden   | boolean | `true`                        |
| category | string  | `Pantry`                      |

### 3e. Create your admin account
1. Run the app (Step 4) and open <http://localhost:5001/login>.
2. **Sign up** with an email + password. Remember them.
3. In the console: **Authentication → Users** → copy your account's **User UID**.
4. **Firestore → Data → Start collection** → collection id `admins` → document id
   = your **UID** → add field `role` (string) = `admin` → **Save**.

That `admins/<uid>` document is what grants admin access. There is no self-serve
admin — you add admins by hand here.

### 3f. (Only if using your own project) Swap the Firebase config
Replace the `firebaseConfig` block in **both** files with your project's config
(from **Project settings → Your apps → `</>`**):

- `app/templates/member-portal.html`
- `admin-dashboard.html`

And update the project id in `app/main.py` → `FIRESTORE_PRODUCTS_URL`.

---

## 4. Run the app locally

```bash
cd qr-tracker
python3.12 -c "from app.main import app; app.run(port=5001)"
```

Open **<http://localhost:5001>**. Everything is on this one server:

| URL                              | What it is                     |
|----------------------------------|--------------------------------|
| `/login`                         | Member **and** admin login     |
| `/`                              | The store (aisles)             |
| `/cart`, `/checkout`             | Cart and checkout              |
| `/admin-dashboard.html`          | Admin dashboard                |

> If you see **"Address already in use"**, an old server is still running.
> Either use a different port (`app.run(port=5002)`) or stop the old one:
> `lsof -ti tcp:5001 | xargs kill`.

---

## 5. The full flow

**Shopper**
1. Go to `/login` → sign up / log in.
2. Browse aisles (click a category chip to jump), open an item, choose a **quantity**, **Add to Cart**.
3. **View cart → Checkout → Complete Purchase**.
4. If a purchased item is golden, a **Golden Ticket** is revealed on the receipt.
   Otherwise it's a normal receipt. Golden status is never shown before payment.

**Admin**
1. Go to `/login` → **Admin login** → sign in with your admin account.
2. On the dashboard, flip the **golden** switches → **Save changes**.
3. Those choices are stored in Firestore, and the store reads them at checkout —
   so what you toggle is what shoppers win.

---

## 6. Lock down the database (before real use)

While in test mode the database is wide open. Publish the included rules:

1. Firebase console → **Firestore Database → Rules**.
2. Replace the contents with the file **`firestore.rules`** (in this repo).
3. **Publish**.

These rules let anyone read products (shoppers aren't logged in), but only
accounts listed in `admins` can change them.

---

## 7. Deploy to Vercel

The repo already has a `vercel.json` that serves the Flask app plus the static
`admin-dashboard.html`.

1. Push the branch to GitHub and connect the repo to Vercel (or `vercel deploy`).
2. In Firebase console → **Authentication → Settings → Authorized domains**, add
   your Vercel URL (e.g. `your-project.vercel.app`) — otherwise logins are blocked
   on the live site.

---

## 8. Running the automated tests (optional)

The flow was verified with Playwright + curl. To re-run:

```bash
mkdir -p /tmp/qr-e2e && cd /tmp/qr-e2e
npm init -y && npm i playwright firebase && npx playwright install chromium
# then run the store locally (Step 4) and use the scripts from the dev session
```

---

## Project layout

```
qr-tracker/
├─ app/
│  ├─ main.py                 # Flask store: routes, cart, checkout, golden overlay
│  └─ templates/
│     ├─ member-portal.html   # Login (member + secure admin login)
│     ├─ index.html           # Store home (aisles)
│     ├─ product.html         # Item page (quantity + add to cart)
│     ├─ cart.html, checkout.html, purchase.html
│     ├─ portal.html, reward.html
├─ admin-dashboard.html       # Admin: configure golden tickets (Firestore)
├─ firestore.rules            # Security rules (publish in Firebase console)
├─ vercel.json                # Vercel build/routes
├─ requirements.txt
└─ SETUP.md                   # This file
```

## How golden tickets flow (in one picture)

```
Admin dashboard  ──writes──►  Firestore `products` (golden: true/false)
                                     │
                                     ▼  read at checkout (get_products)
Shopper buys item  ──►  Flask pay()  ──►  reveals Golden Ticket if golden
```
