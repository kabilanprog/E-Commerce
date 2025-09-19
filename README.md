# DIRTY MENS — Flask E‑Commerce (Demo)

A small, single‑vendor ecommerce demo for clothing (Shirt, Pant, T‑Shirt, Shoe).

## Features
- Bootstrap responsive UI (2 products/row on mobile, 3 on desktop)
- Category filter buttons
- Size pickers per category (Shirt/Tshirt: S–XXL; Pant: 30–36; Shoe: 7–10)
- Quantity increment/decrement
- Cart → Address → Payment (shows QR placeholder + Order ID + UTR validation (12 digits))
- Auto PDF bill generation (uses `reportlab`)
- Order status lookup by Order ID
- Admin login (`admin` / `admin123`) to view, edit status, delete orders
- SQLite for orders. Product catalog is in `static/js/products.js`

## Quick Start
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=app.py  # Windows PowerShell: $env:FLASK_APP="app.py"
flask run --debug
```
Open http://127.0.0.1:5000

## Notes
- Replace the `upi_id` in `app.py` (PAYMENT_QR_UPI) with your own.
- PDF generation uses `reportlab`. If not installed, `pip install reportlab`.
- For production: set a strong `SECRET_KEY` in environment or in `app.py`.
