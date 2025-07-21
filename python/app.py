from flask import Flask, render_template, request, jsonify
from conn import get_db
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__ , template_folder="../templates", static_folder="../static")
app.debug = True
app.config['SECRET_KEY'] = 'your-secret-key'
toolbar = DebugToolbarExtension(app)

@app.route('/')
def index():
    hot_deals = []
    db = get_db()
    sql = "SELECT * FROM MenuItems"
    cursor = db.cursor()
    cursor.execute(sql)
    hot_deals = cursor.fetchall()
    print(hot_deals)
    return render_template('index.html', hot_deals=hot_deals)


@app.route('/scan')
def scan():
    return render_template("scan.html")

if __name__ == '__main__':
    app.run(debug=True)
