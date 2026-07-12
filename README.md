# MrFoodie — QR-Based Restaurant Ordering System

A Flask web application for restaurant table ordering via QR code. Customers scan a QR code at their table, browse the menu, place an order, and track its preparation status in real time — while kitchen staff receive live order notifications.

## Features

- **QR Code Table Ordering** — customers scan a QR code (via `html5-qrcode`) to start an order at their table
- **Menu Browsing** — categorized menu with images, pricing, and a "Hot Deals" section
- **Cart Management** — session-based cart with add/update/remove, persisted per visitor session
- **Order Submission** — server-side validation of item prices and totals to prevent client-side tampering
- **Live Order Tracking** — customers see real-time order progress (Pending → In Progress → Ready → Delivered) with estimated preparation time
- **Kitchen Notifications** — new orders are automatically pushed to all users with the "Chef" role
- **Security** — CSRF protection (Flask-WTF), secure session cookies, environment-based secret management

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | MySQL (`mysql-connector-python`) |
| QR Scanning | html5-qrcode (client-side JS library) |
| Security | Flask-WTF (CSRF), python-dotenv (env config) |

## Project Structure

```
pyhton/
├── python/
│   ├── app.py          # Flask routes: menu, cart, order flow, order status API
│   └── conn.py          # MySQL connection (via environment variables)
├── templates/
│   ├── index.html       # Menu / home page
│   ├── orders.html       # Cart / order review
│   ├── scan.html         # QR code scanner page
│   └── order_confirmation.html  # Live order status/progress page
├── static/
│   ├── foods/            # Menu item images
│   ├── icon/              # UI icons, QR assets
│   └── scripts/            # Frontend JS (cart, order, confirmation flows)
├── requirements.txt
└── .env.example
```

## Database

The app expects a MySQL database (default name `MrFoodie`) with tables including `MenuItems`, `Customers`, `Orders`, `OrderItems`, `Notifications`, `Notification_Users`, and `Users` (with a `Role` column for `Chef`).

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/inaam777me/pyhton.git
   cd pyhton
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your own values:
   ```
   cp .env.example .env
   ```
4. Set up a MySQL database matching the schema described above.
5. Run the app:
   ```
   cd python
   python app.py
   ```
6. Open `http://localhost:5000` in your browser.

## Usage

- Customers scan the table QR code (or visit `/scan`) to begin.
- Browse the menu, add items to the cart, and submit the order.
- After submitting, customers are redirected to a live order status page that polls for kitchen progress.
- Kitchen/chef staff receive a notification for each new order via the `Notifications` system.

## Security Notes

Secrets (Flask `SECRET_KEY`, database credentials) are loaded from environment variables via `.env` — no credentials are committed to the repository. Order totals and item prices are re-validated server-side on submission to prevent tampering with client-supplied values.
