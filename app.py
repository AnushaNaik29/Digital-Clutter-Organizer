from flask import Flask, render_template, request, jsonify
import sqlite3
import requests
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
            url TEXT NOT NULL,
            title TEXT DEFAULT '',
            category TEXT DEFAULT 'Other',
            notes TEXT DEFAULT '',
            pinned INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    columns = connection.execute(
        "PRAGMA table_info(saved_links)"
    ).fetchall()

    existing_columns = [column["name"] for column in columns]

    if "title" not in existing_columns:
        connection.execute(
            "ALTER TABLE saved_links ADD COLUMN title TEXT DEFAULT ''"
        )

    if "category" not in existing_columns:
        connection.execute(
            "ALTER TABLE saved_links ADD COLUMN category TEXT DEFAULT 'Other'"
        )

    if "notes" not in existing_columns:
        connection.execute(
            "ALTER TABLE saved_links ADD COLUMN notes TEXT DEFAULT ''"
        )

    if "pinned" not in existing_columns:
        connection.execute(
            "ALTER TABLE saved_links ADD COLUMN pinned INTEGER DEFAULT 0"
        )

    if "created_at" not in existing_columns:
        connection.execute(
            "ALTER TABLE saved_links ADD COLUMN created_at TEXT"
        )

    if "updated_at" not in existing_columns:
        connection.execute(
            "ALTER TABLE saved_links ADD COLUMN updated_at TEXT"
        )

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/links", methods=["GET"])
def get_links():
    connection = get_db()

    links = connection.execute("""
        SELECT *
        FROM saved_links
        ORDER BY pinned DESC, id DESC
    """).fetchall()

    connection.close()

    return jsonify([dict(link) for link in links])


@app.route("/add", methods=["POST"])
def add_link():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        url = data.get("url", "").strip()
        title = data.get("title", "").strip()
        category = data.get("category", "Other").strip()
        notes = data.get("notes", "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        connection = get_db()

        duplicate = connection.execute("""
            SELECT id
            FROM saved_links
            WHERE url = ?
        """, (url,)).fetchone()

        if duplicate:
            connection.close()
            return jsonify({
                "error": "This link already exists"
            }), 409

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute("""
            INSERT INTO saved_links
            (
                url,
                title,
                category,
                notes,
                pinned,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, 0, ?, ?)
        """, (
            url,
            title,
            category,
            notes,
            now,
            now
        ))

        connection.commit()
        connection.close()

        return jsonify({
            "message": "Link saved successfully"
        }), 201

    except Exception as error:
        print("ADD LINK ERROR:", error)

        return jsonify({
            "error": "Could not save the link."
        }), 500


@app.route("/edit/<int:link_id>", methods=["PUT"])
def edit_link(link_id):
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        url = data.get("url", "").strip()
        title = data.get("title", "").strip()
        category = data.get("category", "Other").strip()
        notes = data.get("notes", "").strip()

        if not url:
            return jsonify({"error": "URL is required"}), 400

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        connection = get_db()

        duplicate = connection.execute("""
            SELECT id
            FROM saved_links
            WHERE url = ? AND id != ?
        """, (url, link_id)).fetchone()

        if duplicate:
            connection.close()
            return jsonify({
                "error": "Another saved link already uses this URL"
            }), 409

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = connection.execute("""
            UPDATE saved_links
            SET url = ?,
                title = ?,
                category = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            url,
            title,
            category,
            notes,
            now,
            link_id
        ))

        connection.commit()
        connection.close()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Link not found"
            }), 404

        return jsonify({
            "message": "Link updated successfully"
        })

    except Exception as error:
        print("EDIT LINK ERROR:", error)

        return jsonify({
            "error": "Could not update the link."
        }), 500


@app.route("/delete/<int:link_id>", methods=["DELETE"])
def delete_link(link_id):
    try:
        connection = get_db()

        cursor = connection.execute("""
            DELETE FROM saved_links
            WHERE id = ?
        """, (link_id,))

        connection.commit()
        connection.close()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Link not found"
            }), 404

        return jsonify({
            "message": "Link deleted successfully"
        })

    except Exception as error:
        print("DELETE LINK ERROR:", error)

        return jsonify({
            "error": "Could not delete the link."
        }), 500


@app.route("/pin/<int:link_id>", methods=["PUT"])
def toggle_pin(link_id):
    try:
        connection = get_db()

        link = connection.execute("""
            SELECT pinned
            FROM saved_links
            WHERE id = ?
        """, (link_id,)).fetchone()

        if not link:
            connection.close()

            return jsonify({
                "error": "Link not found"
            }), 404

        new_status = 0 if link["pinned"] else 1

        connection.execute("""
            UPDATE saved_links
            SET pinned = ?
            WHERE id = ?
        """, (
            new_status,
            link_id
        ))

        connection.commit()
        connection.close()

        return jsonify({
            "message": "Link pinned" if new_status else "Link unpinned",
            "pinned": new_status
        })

    except Exception as error:
        print("PIN ERROR:", error)

        return jsonify({
            "error": "Could not change pin status."
        }), 500


@app.route("/search", methods=["GET"])
def search_links():
    query = request.args.get("q", "").strip()

    connection = get_db()

    if not query:
        links = connection.execute("""
            SELECT *
            FROM saved_links
            ORDER BY pinned DESC, id DESC
        """).fetchall()

    else:
        search = f"%{query}%"

        links = connection.execute("""
            SELECT *
            FROM saved_links
            WHERE url LIKE ?
               OR title LIKE ?
               OR category LIKE ?
               OR notes LIKE ?
            ORDER BY pinned DESC, id DESC
        """, (
            search,
            search,
            search,
            search
        )).fetchall()

    connection.close()

    return jsonify([dict(link) for link in links])


@app.route("/category/<category>", methods=["GET"])
def filter_category(category):
    connection = get_db()

    links = connection.execute("""
        SELECT *
        FROM saved_links
        WHERE category = ?
        ORDER BY pinned DESC, id DESC
    """, (category,)).fetchall()

    connection.close()

    return jsonify([dict(link) for link in links])


@app.route("/check-link/<int:link_id>", methods=["GET"])
def check_link(link_id):
    connection = get_db()

    link = connection.execute("""
        SELECT url
        FROM saved_links
        WHERE id = ?
    """, (link_id,)).fetchone()

    connection.close()

    if not link:
        return jsonify({
            "error": "Link not found"
        }), 404

    url = link["url"]

    try:
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=8,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        status = response.status_code

        if status < 400:
            return jsonify({
                "status": "working",
                "code": status
            })

        return jsonify({
            "status": "broken",
            "code": status
        })

    except requests.RequestException:

        try:
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=8,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            status = response.status_code

            if status < 400:
                return jsonify({
                    "status": "working",
                    "code": status
                })

            return jsonify({
                "status": "broken",
                "code": status
            })

        except requests.RequestException:

            return jsonify({
                "status": "broken",
                "code": 0
            })


@app.route("/check-all-links", methods=["GET"])
def check_all_links():
    connection = get_db()

    links = connection.execute("""
        SELECT id, url
        FROM saved_links
    """).fetchall()

    connection.close()

    results = []

    for link in links:
        url = link["url"]

        try:
            response = requests.head(
                url,
                allow_redirects=True,
                timeout=5,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            results.append({
                "id": link["id"],
                "url": url,
                "status": (
                    "working"
                    if response.status_code < 400
                    else "broken"
                ),
                "code": response.status_code
            })

        except requests.RequestException:

            try:
                response = requests.get(
                    url,
                    allow_redirects=True,
                    timeout=5,
                    headers={
                        "User-Agent": "Mozilla/5.0"
                    }
                )

                results.append({
                    "id": link["id"],
                    "url": url,
                    "status": (
                        "working"
                        if response.status_code < 400
                        else "broken"
                    ),
                    "code": response.status_code
                })

            except requests.RequestException:

                results.append({
                    "id": link["id"],
                    "url": url,
                    "status": "broken",
                    "code": 0
                })

    return jsonify(results)


@app.route("/stats", methods=["GET"])
def get_stats():
    connection = get_db()

    total = connection.execute("""
        SELECT COUNT(*) AS count
        FROM saved_links
    """).fetchone()["count"]

    pinned = connection.execute("""
        SELECT COUNT(*) AS count
        FROM saved_links
        WHERE pinned = 1
    """).fetchone()["count"]

    categories = connection.execute("""
        SELECT category, COUNT(*) AS count
        FROM saved_links
        GROUP BY category
        ORDER BY count DESC
    """).fetchall()

    connection.close()

    return jsonify({
        "total": total,
        "pinned": pinned,
        "categories": [dict(category) for category in categories]
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
