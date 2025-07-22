from flask import Flask, render_template, request, jsonify, session
from conn import get_db
from flask_debugtoolbar import DebugToolbarExtension
import uuid
from datetime import timedelta

app = Flask(__name__ , template_folder="../templates", static_folder="../static")
app.debug = True
app.config['SECRET_KEY'] = '135-991-309'
toolbar = DebugToolbarExtension(app)
app.permanent_session_lifetime = timedelta(days=7) 

@app.before_request
def before_request():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session.permanent = True

@app.route('/')
def index():
    hot_deals = fetchData("SELECT * FROM MenuItems WHERE hotdeals = TRUE")

    page = request.args.get('page', 1, type=int)
    items_per_page = 10
    offset = (page - 1) * items_per_page
    sql = f"SELECT * FROM MenuItems WHERE hotdeals = FALSE ORDER BY MenuItemID LIMIT {items_per_page} OFFSET {offset};"
    try:
        regular_items = fetchData(sql)
    except Exception as e:
        print({e})
    finally:
        print(regular_items)

    # Get total count for pagination
    total_items = fetchData("SELECT COUNT(*) FROM MenuItems WHERE hotdeals = FALSE")
    total_items = total_items[0] if total_items else 0
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    return render_template('index.html', hot_deals=hot_deals,  regular_items=regular_items, current_page=page, total_pages=total_pages)

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

@app.route('/scan')
def scan():
    return render_template("scan.html")

if __name__ == '__main__':
    app.run(debug=True)