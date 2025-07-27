from flask import Flask, redirect, render_template, request, jsonify, session, url_for, flash
from conn import get_db
from flask_debugtoolbar import DebugToolbarExtension
import uuid
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect, generate_csrf

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.debug = True
app.config['SECRET_KEY'] = '135-991-309'
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# Initialize extensions
toolbar = DebugToolbarExtension(app)
csrf = CSRFProtect(app)
app.permanent_session_lifetime = timedelta(days=7)

# Security configurations
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

@app.after_request
def inject_csrf_token(response):
    response.set_cookie('csrf_token', generate_csrf(), secure=True, samesite='Lax', httponly=True)
    return response

@app.before_request
def before_request():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session.permanent = True
    if 'cart' not in session:
        session['cart'] = {}

@app.route('/')
def index():
    hot_deals = fetchData("SELECT * FROM MenuItems WHERE hotdeals = TRUE")
    regular_items = fetchData("SELECT * FROM MenuItems WHERE hotdeals = FALSE ORDER BY MenuItemID")
    
    return render_template('index.html', 
                         hot_deals=hot_deals,
                         regular_items=regular_items)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    item_id = request.json.get('item_id')
    change = request.json.get('change', 1)
    
    session['cart'][item_id] = session['cart'].get(item_id, 0) + change
    
    if session['cart'][item_id] <= 0:
        session['cart'].pop(item_id, None)
    
    session.modified = True
    return jsonify({
        'success': True,
        'quantity': session['cart'].get(item_id, 0)
    })

@app.route('/add_selected_items', methods=['POST'])
def add_selected_items():
    try:
        selected_ids = request.form.getlist('selected_items')
        if not selected_ids:
            flash('No items selected', 'warning')
            return redirect(url_for('index'))
        
        for item_id in selected_ids:
            session['cart'][item_id] = session['cart'].get(item_id, 0) + 1
        
        session.modified = True
        flash('Items added to cart!', 'success')
        return redirect(url_for('order'))
        
    except Exception as e:
        app.logger.error(f"Error in add_selected_items: {str(e)}")
        flash('Failed to add items to cart', 'danger')
        return redirect(url_for('index'))

@app.route('/order')
def order():
    cart = session.get('cart', {})
    items = []
    for item_id, quantity in cart.items():
        item = fetchData(f"SELECT * FROM MenuItems WHERE MenuItemID = {item_id}")[0]
        items.append({
            'id': item_id,
            'title': item['title'],
            'price': item['price'],
            'quantity': quantity,
            'total': item['price'] * quantity
        })
    
    return render_template('orders.html', cart_items=items)

@app.route('/scan')
def scan():
    return render_template("scan.html")

def fetchData(sql):
    try: 
        db = get_db()
        cursor = db.cursor()
        cursor.execute(sql)
        return format_menu_items(cursor.fetchall())
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        cursor.close()

def format_menu_items(items):
    return [{
        'id': item[0],
        'title': item[1],
        'price': item[2],
        'image': item[3],
        'description': f"Rs. {item[2]:.2f}",
        'is_hotdeal': item[4]
    } for item in items]

if __name__ == '__main__':
    app.run(debug=True)