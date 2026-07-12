# Member Portal Implementation – Summary

## What Changed

### 1. **Ticket Collection Storage** (main.py)
- Replaced `session["won"]` (boolean flag) with `session["tickets"]` (list of ticket objects)
- Each ticket stores: `tag_id`, `product_name`, `price`, `coupon`, `claimed_at` (ISO timestamp)
- Storage lives in the signed Flask session cookie (same as shopper_id)

### 2. **Core Logic Updates** (main.py)
- `get_shopper()`: Now initializes `session["tickets"] = []` when a new shopper is created
- New function `add_ticket_to_collection()`: Appends a ticket object to the collection when a golden ticket is claimed
- `/tag/<tag_id>` route: When a golden ticket is won, it now calls `add_ticket_to_collection()` to save the ticket

### 3. **New Routes** (main.py)
- `GET /portal`: Displays the Member Portal with all tickets claimed by the current shopper

### 4. **New Template** (portal.html)
- Full portal page showing:
  - List of claimed tickets (product name, price, claimed date, coupon code)
  - Empty state if no tickets claimed yet
  - Quick links to "Tap More Items" (index) and "Clear & Start Over" (reset)
  - Styled consistently with the existing reward/product pages

### 5. **Navigation Updates**
- **index.html**: Added "View my tickets" link to portal
- **reward.html**: Added "View all your tickets →" link after winning a ticket

---

## How It Works

**Flow:**
1. Shopper taps/scans a tag → `/tag/A17`
2. App checks if it's a golden ticket
3. If golden:
   - Sets `session["won"] = True` (still blocks second win today)
   - Calls `add_ticket_to_collection()` to save the ticket details to `session["tickets"]`
   - Shows reward page
4. Shopper can click "View all your tickets" to go to `/portal`
5. Portal displays all saved tickets with coupons ready to use at checkout

**Persistence:**
- Tickets persist in the signed session cookie for the browser
- Same browser = same tickets (across sessions until cookie expires)
- Different browser/device = different tickets (different shopper_id)

---

## Integration Point with Login

When the other intern's login is ready:
- `current_member` becomes whoever is logged in (instead of the hardcoded placeholder)
- The ticket storage approach **does not change** — it's the same `session["tickets"]` list
- At that point, the seam is just: where does `session["shopper_id"]` come from?
  - Now: generated UUID in cookie
  - Later: read from authenticated user ID

**For a shared database later**, swap the storage:
```python
# Instead of session["tickets"], store in DB:
tickets = db.query(Ticket).filter_by(member_id=current_member).all()
# and add a ticket with:
db.add(Ticket(member_id=current_member, product_name=..., coupon=...))
```

The portal logic itself stays exactly the same.

---

## Testing Checklist

- [ ] Click a golden tag (A17, C04, F22) → reward page appears
- [ ] Click "View all your tickets" → portal shows the ticket you just won
- [ ] Click another golden tag → portal shows both tickets
- [ ] Try clicking a golden tag a second time → get "already claimed today" message
- [ ] Click /reset → session clears, portal is empty, can claim a golden ticket again
- [ ] Different browser tab (new session cookie) → different shopper_id, different tickets

---

## Files Changed
- `app/main.py` – Added ticket collection & portal route
- `app/templates/portal.html` – New Member Portal page
- `app/templates/index.html` – Added portal link
- `app/templates/reward.html` – Added portal link after winning

