from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

# SQLite database file path (no password needed)
DB_PATH = os.path.join(os.path.dirname(__file__), "movierental.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # let us use row["column_name"]
    return conn

def init_db():
    """Create tables and sample data if database is empty."""
    conn = get_connection()
    cur = conn.cursor()

    # Create tables (similar to MySQL schema, but in SQLite syntax)
    cur.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name  TEXT NOT NULL,
        last_name   TEXT NOT NULL,
        email       TEXT NOT NULL UNIQUE,
        phone       TEXT,
        address     TEXT,
        signup_date TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS movie (
        movie_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        title          TEXT NOT NULL,
        release_year   INTEGER,
        mpaa_rating    TEXT,
        length_minutes INTEGER,
        movie_rating   REAL,
        description    TEXT
    );

    CREATE TABLE IF NOT EXISTS category (
        category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS movie_category (
        movie_id    INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (movie_id, category_id),
        FOREIGN KEY (movie_id) REFERENCES movie(movie_id) ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS inventory_copy (
        copy_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id       INTEGER NOT NULL,
        status         TEXT NOT NULL DEFAULT 'AVAILABLE',
        store_location TEXT,
        FOREIGN KEY (movie_id) REFERENCES movie(movie_id) ON DELETE CASCADE ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS rental (
        rental_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id   INTEGER NOT NULL,
        copy_id       INTEGER NOT NULL,
        rental_date   TEXT NOT NULL,
        due_date      TEXT NOT NULL,
        return_date   TEXT,
        rental_status TEXT NOT NULL DEFAULT 'OPEN',
        FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
        FOREIGN KEY (copy_id) REFERENCES inventory_copy(copy_id) ON DELETE RESTRICT ON UPDATE CASCADE
    );
    """)

    # If there is no movie data yet, insert sample data
    cur.execute("SELECT COUNT(*) FROM movie")
    (count,) = cur.fetchone()
    if count == 0:
        cur.executescript("""
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES
        ('Alice', 'Johnson', 'alice@example.com', '412-111-2222', '123 Main St', '2024-01-01'),
        ('Bob',   'Lee',     'bob@example.com',   '412-333-4444', '456 Oak Ave', '2024-02-10');

        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description) VALUES
        ('The Matrix', 1999, 'R',     136, 8.7, 'A hacker discovers reality is a simulation.'),
        ('Inception',  2010, 'PG-13', 148, 8.8, 'A thief enters dreams to steal secrets.'),
        ('Toy Story',  1995, 'G',      81, 8.3, 'Animated toys come to life.');

        INSERT INTO category (category_name) VALUES
        ('Action'),
        ('Sci-Fi'),
        ('Animation'),
        ('Family');

        INSERT INTO movie_category (movie_id, category_id) VALUES
        (1, 1),
        (1, 2),
        (2, 1),
        (2, 2),
        (3, 3),
        (3, 4);

        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES
        (1, 'AVAILABLE', 'Front Shelf'),
        (1, 'AVAILABLE', 'Back Shelf'),
        (2, 'AVAILABLE', 'Front Shelf'),
        (3, 'AVAILABLE', 'Kids Section');

        INSERT INTO rental (customer_id, copy_id, rental_date, due_date, rental_status)
        VALUES
        (1, 1, '2025-11-01T10:00:00', '2025-11-05T10:00:00', 'OPEN'),
        (2, 3, '2025-10-20T14:00:00', '2025-10-25T14:00:00', 'RETURNED');
        """)

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/movies")
def browse_movies():
    keyword = request.args.get("keyword", "")
    conn = get_connection()
    cur = conn.cursor()

    if keyword:
        cur.execute(
            """
            SELECT movie_id, title, release_year, mpaa_rating
            FROM movie
            WHERE title LIKE ?
            ORDER BY title;
            """,
            (f"%{keyword}%",),
        )
    else:
        cur.execute(
            """
            SELECT movie_id, title, release_year, mpaa_rating
            FROM movie
            ORDER BY title;
            """
        )

    movies = cur.fetchall()
    conn.close()
    return render_template("browse_movies.html", movies=movies, keyword=keyword)

@app.route("/movies/<int:movie_id>")
def movie_detail(movie_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM movie WHERE movie_id = ?", (movie_id,))
    movie = cur.fetchone()

    cur.execute(
        """
        SELECT COUNT(*) AS total_copies,
               SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available_copies
        FROM inventory_copy
        WHERE movie_id = ?
        """,
        (movie_id,),
    )
    availability = cur.fetchone()

    conn.close()
    return render_template("movie_detail.html", movie=movie, availability=availability)

@app.route("/customers")
def customers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customer ORDER BY last_name, first_name")
    customers = cur.fetchall()
    conn.close()
    return render_template("customers.html", customers=customers)

@app.route("/rent", methods=["GET", "POST"])
def rent_movie():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        movie_id = request.form.get("movie_id")

        # find an available copy
        cur.execute(
            """
            SELECT copy_id
            FROM inventory_copy
            WHERE movie_id = ? AND status = 'AVAILABLE'
            LIMIT 1
            """,
            (movie_id,),
        )
        copy = cur.fetchone()

        if not copy:
            flash("No available copies for this movie.", "error")
        else:
            copy_id = copy["copy_id"]
            rental_date = datetime.now()
            due_date = rental_date + timedelta(days=5)

            cur.execute(
                """
                INSERT INTO rental (customer_id, copy_id, rental_date, due_date, rental_status)
                VALUES (?, ?, ?, ?, 'OPEN')
                """,
                (
                    customer_id,
                    copy_id,
                    rental_date.isoformat(timespec="seconds"),
                    due_date.isoformat(timespec="seconds"),
                ),
            )

            cur.execute(
                """
                UPDATE inventory_copy
                SET status = 'RENTED'
                WHERE copy_id = ?
                """,
                (copy_id,),
            )

            conn.commit()
            flash("Rental created successfully.", "success")

        conn.close()
        return redirect(url_for("rent_movie"))

    # GET: show form
    cur.execute("SELECT movie_id, title FROM movie ORDER BY title")
    movies = cur.fetchall()

    cur.execute(
        """
        SELECT customer_id,
               first_name || ' ' || last_name AS name
        FROM customer
        ORDER BY last_name, first_name
        """
    )
    customers = cur.fetchall()

    conn.close()
    return render_template("rent.html", movies=movies, customers=customers)

@app.route("/return", methods=["GET", "POST"])
def return_movie():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        rental_id = request.form.get("rental_id")

        cur.execute(
            """
            SELECT rental_id, copy_id
            FROM rental
            WHERE rental_id = ? AND rental_status = 'OPEN'
            """,
            (rental_id,),
        )
        rental = cur.fetchone()

        if not rental:
            flash("Rental not found or already closed.", "error")
        else:
            now = datetime.now().isoformat(timespec="seconds")

            cur.execute(
                """
                UPDATE rental
                SET return_date = ?, rental_status = 'RETURNED'
                WHERE rental_id = ?
                """,
                (now, rental_id),
            )

            cur.execute(
                """
                UPDATE inventory_copy
                SET status = 'AVAILABLE'
                WHERE copy_id = ?
                """,
                (rental["copy_id"],),
            )

            conn.commit()
            flash("Movie returned successfully.", "success")

        conn.close()
        return redirect(url_for("return_movie"))

    cur.execute(
        """
        SELECT r.rental_id,
               r.rental_date,
               c.first_name,
               c.last_name,
               m.title
        FROM rental r
        JOIN customer c ON r.customer_id = c.customer_id
        JOIN inventory_copy ic ON r.copy_id = ic.copy_id
        JOIN movie m ON ic.movie_id = m.movie_id
        WHERE r.rental_status = 'OPEN'
        ORDER BY r.rental_date DESC
        """
    )
    rentals = cur.fetchall()

    conn.close()
    return render_template("return.html", rentals=rentals)

@app.route("/reports/popular")
def popular_movies():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT m.movie_id,
               m.title,
               COUNT(*) AS rental_count
        FROM rental r
        JOIN inventory_copy ic ON r.copy_id = ic.copy_id
        JOIN movie m ON ic.movie_id = m.movie_id
        GROUP BY m.movie_id, m.title
        ORDER BY rental_count DESC
        LIMIT 10
        """
    )

    movies = cur.fetchall()
    conn.close()
    return render_template("popular_movies.html", movies=movies)

if __name__ == "__main__":
    init_db()          # create DB + sample data if needed
    app.run(debug=True)
