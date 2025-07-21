from flask import Flask, render_template, request, jsonify
from conn import get_db
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__ , template_folder="../templates", static_folder="../static")
app.debug = True
app.config['SECRET_KEY'] = 'your-secret-key'
toolbar = DebugToolbarExtension(app)

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    # Get only hot deals items
    cursor.execute("SELECT * FROM MenuItems WHERE hotdeals = TRUE")
    hot_deals_data = cursor.fetchall()
    
    # Convert tuples to list of dictionaries with proper keys
    hot_deals = []
    for item in hot_deals_data:
        hot_deals.append({
            'id': item[0],
            'title': item[1],
            'price': item[2],
            'image': item[3],
            'description': f"Rs. {item[2]:.2f}",  # Format price as currency
            'is_hotdeal': item[4]
        })
    
    print(hot_deals)  # For debugging
    return render_template('index.html', hot_deals=hot_deals)

@app.route('/scan')
def scan():
    return render_template("scan.html")

if __name__ == '__main__':
    app.run(debug=True)