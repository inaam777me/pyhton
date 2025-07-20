from flask import Flask, render_template, request, jsonify
from conn import get_db

app = Flask(__name__ , template_folder="../templates", static_folder="../static")

@app.route('/')
def index():
    hot_deals = []
    db = get_db()
    sql = "SELECT * FROM hot_deals"
    cursor = db.cursor()
    cursor.execute(sql)
    hot_deals = cursor.fetchall()
    return render_template('index.html', hot_deals=hot_deals)


@app.route('/scan')
def scan():
    return render_template("scan.html")

if __name__ == '__main__':
    app.run(debug=True)
