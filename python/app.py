from flask import Flask, json, redirect, render_template, request, jsonify, session, url_for, flash
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
        quantities = request.form.getlist('quantities')
        
        if not selected_ids or len(selected_ids) != len(quantities):
            flash('No valid items selected', 'warning')
            return redirect(url_for('index'))
        
        # Clear the current cart
        session['cart'] = {}
        
        # Add the new items
        for item_id, quantity in zip(selected_ids, quantities):
            try:
                quantity = int(quantity)
                if quantity > 0:
                    session['cart'][item_id] = quantity
            except ValueError:
                continue
        
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
            'total': item['price'] * quantity,
            'image': item['image']
        })

    # Prepare cart data for JavaScript
    cart_js = {
        str(item['id']): {
            'quantity': item['quantity'],
            'price': float(item['price']),
            'title': item['title'],
            'image': item['image']
        }
        for item in items
    }

    return render_template('orders.html', 
                         cart_items=items,
                         cart_js=json.dumps(cart_js))

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



# order route to handle the order page
@app.route('/update_cart_item', methods=['POST'])
def update_cart_item():
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        change = data.get('change', 1)
        
        if not item_id:
            return jsonify({'success': False, 'message': 'Invalid item ID'}), 400
        
        # Get current quantity
        current_quantity = session['cart'].get(item_id, 0)
        new_quantity = current_quantity + change
        
        if new_quantity <= 0:
            # Remove item if quantity reaches 0
            session['cart'].pop(item_id, None)
        else:
            # Update quantity
            session['cart'][item_id] = new_quantity
        
        session.modified = True
        
        # Calculate new total for this item
        item = fetchData(f"SELECT * FROM MenuItems WHERE MenuItemID = {item_id}")[0]
        item_total = item['price'] * new_quantity
        
        # Calculate cart summary
        cart_summary = calculate_cart_summary()
        
        return jsonify({
            'success': True,
            'quantity': new_quantity if new_quantity > 0 else 0,
            'total': item_total,
            'cart_summary': cart_summary
        })
        
    except Exception as e:
        app.logger.error(f"Error updating cart item: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/remove_cart_item', methods=['POST'])
def remove_cart_item():
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        if not item_id:
            return jsonify({'success': False, 'message': 'Invalid item ID'}), 400
        
        session['cart'].pop(item_id, None)
        session.modified = True
        
        # Calculate cart summary
        cart_summary = calculate_cart_summary()
        
        return jsonify({
            'success': True,
            'cart_summary': cart_summary
        })
        
    except Exception as e:
        app.logger.error(f"Error removing cart item: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    try:
        session['cart'] = {}
        session.modified = True
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error clearing cart: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

def calculate_cart_summary():
    cart_items = []
    total_items = 0
    subtotal = 0.0
    
    for item_id, quantity in session.get('cart', {}).items():
        item = fetchData(f"SELECT * FROM MenuItems WHERE MenuItemID = {item_id}")[0]
        item_total = item['price'] * quantity
        cart_items.append({
            'id': item_id,
            'title': item['title'],
            'price': item['price'],
            'quantity': quantity,
            'total': item_total
        })
        total_items += quantity
        subtotal += item_total
    
    # Calculate taxes and fees (example values)
    service_charge = 0.0
    tax = subtotal * 0.1  # 10% tax example
    grand_total = subtotal + service_charge + tax
    
    return {
        'subtotal': subtotal,
        'service_charge': service_charge,
        'tax': tax,
        'grand_total': grand_total,
        'total_items': total_items
    }




if __name__ == '__main__':
    app.run(debug=True)