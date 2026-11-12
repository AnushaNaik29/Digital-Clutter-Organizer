from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "links.db"



def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS saved_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            description TEXT,
            link_status TEXT DEFAULT 'Not checked',
            created_at TEXT
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/links", methods=["GET"])
def get_links():

    connection = get_db()

    links = connection.execute("""
        SELECT * FROM saved_links
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return jsonify([dict(link) for link in links])


@app.route("/api/links", methods=["POST"])
def save_link():

    data = request.get_json()

    title = data.get("title", "").strip()
    url = data.get("url", "").strip()
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()

    if not title or not url or not category:
        return jsonify({
            "success": False,
            "message": "Title, URL and category are required."
        }), 400

    connection = get_db()

    try:

        connection.execute("""
            INSERT INTO saved_links
            (title, url, category, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            url,
            category,
            description,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Link saved successfully!"
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "This URL is already saved."
        }), 400

    finally:
        connection.close()


@app.route("/api/links/<int:link_id>", methods=["DELETE"])
def delete_link(link_id):

    connection = get_db()

    connection.execute(
        "DELETE FROM saved_links WHERE id = ?",
        (link_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Link deleted successfully."
    })


@app.route("/api/search", methods=["GET"])
def search_links():

    keyword = request.args.get("q", "").strip()

    connection = get_db()

    links = connection.execute("""
        SELECT * FROM saved_links
        WHERE title LIKE ?
        OR url LIKE ?
        OR category LIKE ?
        OR description LIKE ?
        ORDER BY id DESC
    """, (
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    )).fetchall()

    connection.close()

    return jsonify([dict(link) for link in links])


if __name__ == "__main__":
    init_db()
    app.run(debug=True)