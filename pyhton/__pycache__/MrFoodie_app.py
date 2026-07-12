import os
from flask import Flask, json, redirect, render_template, request, jsonify, session, url_for, flash
from conn import get_db
from flask_debugtoolbar import DebugToolbarExtension
import uuid
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect, generate_csrf
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
orders = {}

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
        
        session['cart'] = {}
        
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


@app.route('/submit_order', methods=['POST'])
def submit_order():
    try:
        # Get order data from request
        order_data = request.get_json()
        
        if not order_data or 'items' not in order_data:
            return jsonify({'success': False, 'message': 'Invalid order data'}), 400
        
        # Validate items and quantities
        if not isinstance(order_data['items'], list) or len(order_data['items']) == 0:
            return jsonify({'success': False, 'message': 'No items in order'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Initialize totals
        total_amount = 0
        total_prep_time = 0
        order_items = []
        
        # Process each item in the order
        for item in order_data['items']:
            # Validate item structure
            if not all(k in item for k in ['id', 'quantity', 'price']):
                return jsonify({'success': False, 'message': 'Invalid item format'}), 400
            
            # Get menu item details including preparation time
            cursor.execute(
                "SELECT Price, PreparationTime FROM MenuItems WHERE MenuItemID = %s",
                (item['id'],)
            )
            menu_item = cursor.fetchone()
            
            if not menu_item:
                return jsonify({
                    'success': False, 
                    'message': f"Menu item {item['id']} not found"
                }), 400
                
            item_price, prep_time = menu_item
            
            # Validate price matches
            if abs(float(item_price) - float(item['price'])) > 0.01:
                return jsonify({
                    'success': False,
                    'message': f"Price mismatch for item {item['id']}"
                }), 400
                
            quantity = int(item['quantity'])
            if quantity <= 0:
                continue  # Skip items with zero or negative quantity
                
            # Calculate item totals
            item_total = float(item_price) * quantity
            item_prep_time = prep_time * quantity
            
            total_amount += item_total
            total_prep_time += item_prep_time
            
            order_items.append({
                'menu_item_id': item['id'],
                'quantity': quantity,
                'price': item_price,
                'prep_time': prep_time
            })
        
        # Validate total amount
        if abs(total_amount - float(order_data.get('total', 0))) > 0.01:
            return jsonify({
                'success': False,
                'message': 'Total amount mismatch'
            }), 400
        
        # Get table number from request or default to 'Takeaway'
        table_number = order_data.get('table_number', 'Takeaway')
        
        # Create customer record if not exists
        session_id = session.get('session_id', str(uuid.uuid4()))
        cursor.execute(
            "INSERT IGNORE INTO Customers (SessionID) VALUES (%s)",
            (session_id,)
        )
        
        # Get customer ID
        cursor.execute(
            "SELECT CustomerID FROM Customers WHERE SessionID = %s",
            (session_id,)
        )
        customer_id = cursor.fetchone()[0]
        
        # Create order record
        cursor.execute(
            "INSERT INTO Orders (CustomerID, OrderTime, TotalAmount, EstimatedPrepTime, TableNumber) "
            "VALUES (%s, NOW(), %s, %s, %s)",
            (customer_id, total_amount, total_prep_time, table_number)
        )
        order_id = cursor.lastrowid
        
        # Create order items
        for item in order_items:
            cursor.execute(
                "INSERT INTO OrderItems (OrderID, MenuItemID, Quantity, Price) "
                "VALUES (%s, %s, %s, %s)",
                (order_id, item['menu_item_id'], item['quantity'], item['price'])
            )
        
        # Create initial notification
        cursor.execute(
            "INSERT INTO Notifications (Message, CheffStatus, CompletionStatus, OrderID) "
            "VALUES (%s, %s, %s, %s)",
            (f"New order #{order_id} received", "Pending", "Not Started", order_id)
        )
        notification_id = cursor.lastrowid
        
        # Assign notification to all chefs
        cursor.execute("SELECT UserID FROM Users WHERE Role = 'Chef'")
        chefs = cursor.fetchall()
        for (chef_id,) in chefs:
            cursor.execute(
                "INSERT INTO Notification_Users (NotificationID, UserID) "
                "VALUES (%s, %s)",
                (notification_id, chef_id)
            )
        
        # Clear the session cart
        session['cart'] = {}
        session.modified = True
        
        db.commit()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'estimated_wait_time': total_prep_time,
            'redirect_url': url_for('order_confirmation', order_id=order_id),
            'message': 'Order received successfully'
        })
        
    except Exception as e:
        db.rollback()
        app.logger.error(f"Error processing order: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'Error processing order'
        }), 500
    finally:
        cursor.close()



@app.route('/order_confirmation')
def order_confirmation():
    order_id = request.args.get('order_id')
    if not order_id:
        return "Order ID missing", 400
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Get order details
        cursor.execute("""
            SELECT o.OrderID, o.OrderTime, o.TotalAmount, o.TableNumber, o.EstimatedPrepTime
            FROM Orders o
            WHERE o.OrderID = %s
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return "Order not found", 404
        
        # Get order items
        cursor.execute("""
            SELECT mi.Name, oi.Quantity, oi.Price
            FROM OrderItems oi
            JOIN MenuItems mi ON oi.MenuItemID = mi.MenuItemID
            WHERE oi.OrderID = %s
        """, (order_id,))
        order['Items'] = cursor.fetchall()
        
        # Get current status
        cursor.execute("""
            SELECT CheffStatus, CompletionStatus
            FROM Notifications
            WHERE OrderID = %s
            ORDER BY NotificationID DESC
            LIMIT 1
        """, (order_id,))
        order_status = cursor.fetchone() or {'CheffStatus': 'Pending', 'CompletionStatus': 'Not Started'}
        
        # Calculate progress
        progress = 0
        if order_status['CheffStatus'] == 'Pending':
            progress = 0
        elif order_status['CheffStatus'] == 'In Progress':
            progress = 50
        elif order_status['CheffStatus'] == 'Completed' and order_status['CompletionStatus'] == 'Ready':
            progress = 75
        elif order_status['CompletionStatus'] == 'Delivered':
            progress = 100
        
        # Calculate remaining time (simplified - in production you'd track actual time spent)
        remaining_time = max(0, order['EstimatedPrepTime'] - (10 if progress >= 50 else 0))
        
        return render_template('order_confirmation.html',
                            order=order,
                            order_status=order_status,
                            progress_percentage=progress,
                            remaining_time=remaining_time)
        
    except Exception as e:
        app.logger.error(f"Error fetching order confirmation: {str(e)}")
        return "Error loading order confirmation", 500
    finally:
        cursor.close()

@app.route('/order_status/<order_id>')
def order_status(order_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Get current status
        cursor.execute("""
            SELECT CheffStatus, CompletionStatus
            FROM Notifications
            WHERE OrderID = %s
            ORDER BY NotificationID DESC
            LIMIT 1
        """, (order_id,))
        order_status = cursor.fetchone() or {'CheffStatus': 'Pending', 'CompletionStatus': 'Not Started'}
        
        # Calculate progress
        progress = 0
        step = 0
        if order_status['CheffStatus'] == 'Pending':
            progress = 0
            step = 0
        elif order_status['CheffStatus'] == 'In Progress':
            progress = 50
            step = 1
        elif order_status['CheffStatus'] == 'Completed' and order_status['CompletionStatus'] == 'Ready':
            progress = 75
            step = 2
        elif order_status['CompletionStatus'] == 'Delivered':
            progress = 100
            step = 3
        
        # Get estimated prep time
        cursor.execute("SELECT EstimatedPrepTime FROM Orders WHERE OrderID = %s", (order_id,))
        prep_time = cursor.fetchone()['EstimatedPrepTime']
        
        # Calculate remaining time
        remaining_time = max(0, prep_time - (10 if progress >= 50 else 0))
        
        return jsonify({
            'success': True,
            'order_status': order_status,
            'progress_percentage': progress,
            'remaining_time': remaining_time,
            'step': step
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching order status: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching status'}), 500
    finally:
        cursor.close()







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