from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta
import os
from functools import wraps
import hashlib

app = Flask(__name__)
app.secret_key = "change_this_secret_key_for_production"

# ============== Authentication Decorators ==============
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash("Admin access required.", "error")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# SQLite database file path (no password needed)
DB_PATH = os.path.join(os.path.dirname(__file__), "movierental.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
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
        description    TEXT,
        rental_rate    REAL NOT NULL DEFAULT 4.99,
        late_fee       REAL NOT NULL DEFAULT 1.00
    );

    CREATE TABLE IF NOT EXISTS category (
        category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS actor (
        actor_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS movie_category (
        movie_id    INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        PRIMARY KEY (movie_id, category_id),
        FOREIGN KEY (movie_id) REFERENCES movie(movie_id) ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS movie_actor (
        movie_id  INTEGER NOT NULL,
        actor_id  INTEGER NOT NULL,
        role_name TEXT,
        PRIMARY KEY (movie_id, actor_id),
        FOREIGN KEY (movie_id) REFERENCES movie(movie_id) ON DELETE CASCADE ON UPDATE CASCADE,
        FOREIGN KEY (actor_id) REFERENCES actor(actor_id) ON DELETE CASCADE ON UPDATE CASCADE
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

    CREATE TABLE IF NOT EXISTS payment (
        payment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        rental_id      INTEGER NOT NULL,
        amount         REAL NOT NULL,
        payment_date   TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        FOREIGN KEY (rental_id) REFERENCES rental(rental_id) ON DELETE CASCADE ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS user (
        user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        username  TEXT NOT NULL UNIQUE,
        password  TEXT NOT NULL,
        role      TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL
    );
    """)

    # If there is no movie data yet, insert sample data
    cur.execute("SELECT COUNT(*) FROM movie")
    (count,) = cur.fetchone()
    if count == 0:
        cur.executescript("""
        -- Categories
        INSERT INTO category (category_name) VALUES ('Comedy');
        INSERT INTO category (category_name) VALUES ('Crime');
        INSERT INTO category (category_name) VALUES ('Action');
        INSERT INTO category (category_name) VALUES ('Drama');
        INSERT INTO category (category_name) VALUES ('Western');
        INSERT INTO category (category_name) VALUES ('Biography');

        -- Actors
        INSERT INTO actor (actor_name) VALUES ('Martin Short');
        INSERT INTO actor (actor_name) VALUES ('Morgan Freeman');
        INSERT INTO actor (actor_name) VALUES ('Al Pacino');
        INSERT INTO actor (actor_name) VALUES ('Matthew Ziff');
        INSERT INTO actor (actor_name) VALUES ('Krystyna Janda');
        INSERT INTO actor (actor_name) VALUES ('Christian Bale');
        INSERT INTO actor (actor_name) VALUES ('Robert De Niro');
        INSERT INTO actor (actor_name) VALUES ('Kirsten Dunst');
        INSERT INTO actor (actor_name) VALUES ('Orlando Bloom');
        INSERT INTO actor (actor_name) VALUES ('Jack Warden');
        INSERT INTO actor (actor_name) VALUES ('Clint Eastwood');
        INSERT INTO actor (actor_name) VALUES ('Bruce Willis');
        INSERT INTO actor (actor_name) VALUES ('Liam Neeson');
        INSERT INTO actor (actor_name) VALUES ('Brad Pitt');
        INSERT INTO actor (actor_name) VALUES ('Tom Hanks');
        INSERT INTO actor (actor_name) VALUES ('Christopher Lee');
        INSERT INTO actor (actor_name) VALUES ('Harrison Ford');
        INSERT INTO actor (actor_name) VALUES ('Leonardo DiCaprio');
        INSERT INTO actor (actor_name) VALUES ('Rob McElhenney');

        -- Movies (19 movies)
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Towering Inferno', 2000, 'PG-13', 120, 9.5, 'A comedy about unexpected events.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('The Shawshank Redemption', 1994, 'R', 142, 9.3, 'Two imprisoned men bond over years, finding solace and eventual redemption.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('The Godfather', 1972, 'R', 175, 9.2, 'The aging patriarch of an organized crime dynasty transfers control to his son.', 5.99, 1.50);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Kickboxer: Vengeance', 2016, 'R', 90, 9.1, 'A fighter seeks revenge for his brother.', 3.99, 0.75);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Dekalog', 2000, 'PG', 572, 9.1, 'Ten films based on the Ten Commandments.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('The Dark Knight', 2008, 'PG-13', 152, 9.0, 'Batman raises the stakes in his war on crime.', 5.99, 1.50);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('The Godfather: Part II', 1974, 'R', 202, 9.0, 'The early life and career of Vito Corleone and his son Michael.', 5.99, 1.50);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Fargo', 2000, 'R', 98, 9.0, 'A car salesman hires two criminals to kidnap his wife.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('The Lord of the Rings: The Return of the King', 2003, 'PG-13', 201, 8.9, 'Gandalf and Aragorn lead the World of Men against Sauron.', 5.99, 1.50);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('12 Angry Men', 1957, 'PG', 96, 8.9, 'A jury holdout attempts to prevent a miscarriage of justice.', 3.99, 0.75);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('The Good, the Bad and the Ugly', 1966, 'R', 178, 8.9, 'A bounty hunting scam joins two men in an uneasy alliance.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Pulp Fiction', 1994, 'R', 154, 8.9, 'The lives of two mob hitmen, a boxer, and a pair of bandits intertwine.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Schindlers List', 1993, 'R', 195, 8.9, 'Oskar Schindler saves over a thousand Polish-Jewish refugees.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Fight Club', 1999, 'R', 139, 8.8, 'An insomniac office worker forms an underground fight club.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Forrest Gump', 1994, 'PG-13', 142, 8.8, 'The presidencies of Kennedy and Johnson unfold through the perspective of Forrest Gump.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('The Lord of the Rings: The Fellowship of the Ring', 2001, 'PG-13', 178, 8.8, 'A meek Hobbit sets out on a journey to destroy a powerful ring.', 5.99, 1.50);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Star Wars: Episode V - The Empire Strikes Back', 1980, 'PG', 124, 8.8, 'After the Rebels are overpowered by the Empire, Luke Skywalker trains with Yoda.', 4.99, 1.00);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Inception', 2010, 'PG-13', 148, 8.8, 'A thief enters dreams to steal secrets.', 5.99, 1.50);
        INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee) VALUES ('Its Always Sunny in Philadelphia', 2000, 'TV-MA', 22, 8.8, 'Five friends run a bar in Philadelphia.', 2.99, 0.50);

        -- Movie-Category relationships
        INSERT INTO movie_category (movie_id, category_id) VALUES (1, 1);
        INSERT INTO movie_category (movie_id, category_id) VALUES (2, 2);
        INSERT INTO movie_category (movie_id, category_id) VALUES (2, 4);
        INSERT INTO movie_category (movie_id, category_id) VALUES (3, 2);
        INSERT INTO movie_category (movie_id, category_id) VALUES (3, 4);
        INSERT INTO movie_category (movie_id, category_id) VALUES (4, 3);
        INSERT INTO movie_category (movie_id, category_id) VALUES (5, 4);
        INSERT INTO movie_category (movie_id, category_id) VALUES (6, 3);
        INSERT INTO movie_category (movie_id, category_id) VALUES (6, 2);
        INSERT INTO movie_category (movie_id, category_id) VALUES (7, 2);
        INSERT INTO movie_category (movie_id, category_id) VALUES (7, 4);
        INSERT INTO movie_category (movie_id, category_id) VALUES (8, 2);
        INSERT INTO movie_category (movie_id, category_id) VALUES (8, 1);
        INSERT INTO movie_category (movie_id, category_id) VALUES (9, 3);
        INSERT INTO movie_category (movie_id, category_id) VALUES (10, 2);
        INSERT INTO movie_category (movie_id, category_id) VALUES (10, 4);
        INSERT INTO movie_category (movie_id, category_id) VALUES (11, 5);
        INSERT INTO movie_category (movie_id, category_id) VALUES (12, 2);
        INSERT INTO movie_category (movie_id, category_id) VALUES (13, 6);
        INSERT INTO movie_category (movie_id, category_id) VALUES (13, 4);
        INSERT INTO movie_category (movie_id, category_id) VALUES (14, 4);
        INSERT INTO movie_category (movie_id, category_id) VALUES (15, 1);
        INSERT INTO movie_category (movie_id, category_id) VALUES (15, 4);
        INSERT INTO movie_category (movie_id, category_id) VALUES (16, 3);
        INSERT INTO movie_category (movie_id, category_id) VALUES (17, 3);
        INSERT INTO movie_category (movie_id, category_id) VALUES (18, 3);
        INSERT INTO movie_category (movie_id, category_id) VALUES (19, 1);

        -- Movie-Actor relationships
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (1, 1, 'Lead Role');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (2, 2, 'Red');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (3, 3, 'Michael Corleone');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (4, 4, 'Kurt Sloane');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (5, 5, 'Dorota');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (6, 6, 'Bruce Wayne / Batman');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (7, 7, 'Young Vito Corleone');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (8, 8, 'Supporting Role');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (9, 9, 'Legolas');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (10, 10, 'Juror #7');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (11, 11, 'Blondie');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (12, 12, 'Butch Coolidge');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (13, 13, 'Oskar Schindler');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (14, 14, 'Tyler Durden');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (15, 15, 'Forrest Gump');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (16, 16, 'Saruman');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (17, 17, 'Han Solo');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (18, 18, 'Cobb');
        INSERT INTO movie_actor (movie_id, actor_id, role_name) VALUES (19, 19, 'Mac');

        -- Inventory (3 copies per movie = 57 total)
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (1, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (1, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (1, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (2, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (2, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (2, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (3, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (3, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (3, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (4, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (4, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (4, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (5, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (5, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (5, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (6, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (6, 'RENTED', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (6, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (7, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (7, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (7, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (8, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (8, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (8, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (9, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (9, 'RENTED', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (9, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (10, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (10, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (10, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (11, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (11, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (11, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (12, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (12, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (12, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (13, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (13, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (13, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (14, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (14, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (14, 'RENTED', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (15, 'AVAILABLE', 'Kids Section');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (15, 'AVAILABLE', 'Kids Section');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (15, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (16, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (16, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (16, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (17, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (17, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (17, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (18, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (18, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (18, 'AVAILABLE', 'Back Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (19, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (19, 'AVAILABLE', 'Front Shelf');
        INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (19, 'AVAILABLE', 'Back Shelf');

        -- Customers
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES ('Alice', 'Smith', 'alice@example.com', '412-555-0101', '123 Main St, Pittsburgh, PA', '2024-01-15');
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES ('Bob', 'Jones', 'bob@example.com', '412-555-0102', '456 Oak Ave, Pittsburgh, PA', '2024-02-20');
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES ('Charlie', 'Brown', 'charlie@example.com', '412-555-0103', '789 Elm St, Pittsburgh, PA', '2024-03-10');
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES ('David', 'Wilson', 'david@example.com', '412-555-0104', '321 Pine Rd, Pittsburgh, PA', '2024-04-05');
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES ('Eve', 'Davis', 'eve@example.com', '412-555-0105', '654 Maple Dr, Pittsburgh, PA', '2024-05-01');
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES ('Hangting', 'Zhu', 'haz126@pitt.edu', '412-377-3813', '888 Somewhere, Pittsburgh, PA', '2021-08-08');
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES ('Zhexi', 'Xu', 'zhx77@pitt.edu', '412-973-6007', '345 Aplace, Pittsburgh, PA', '2021-01-02');
        INSERT INTO customer (first_name, last_name, email, phone, address, signup_date) VALUES ('Zachary', 'Renaud', 'zlr10@pitt.edu', '203-560-5246', '456 Hishome, Pittsburgh, PA', '2021-08-08');

        -- Active Rentals (copy 17=Dark Knight, 26=LOTR Return, 42=Fight Club)
        INSERT INTO rental (customer_id, copy_id, rental_date, due_date, rental_status) VALUES (1, 17, '2025-12-01 10:00:00', '2025-12-06 10:00:00', 'OPEN');
        INSERT INTO rental (customer_id, copy_id, rental_date, due_date, rental_status) VALUES (2, 26, '2025-12-02 14:00:00', '2025-12-07 14:00:00', 'OPEN');
        INSERT INTO rental (customer_id, copy_id, rental_date, due_date, rental_status) VALUES (3, 42, '2025-12-03 09:00:00', '2025-12-08 09:00:00', 'OPEN');

        -- Completed Rentals
        INSERT INTO rental (customer_id, copy_id, rental_date, due_date, return_date, rental_status) VALUES (1, 1, '2025-11-20 10:00:00', '2025-11-25 10:00:00', '2025-11-24 15:00:00', 'RETURNED');
        INSERT INTO rental (customer_id, copy_id, rental_date, due_date, return_date, rental_status) VALUES (2, 4, '2025-11-22 11:00:00', '2025-11-27 11:00:00', '2025-11-26 16:00:00', 'RETURNED');
        INSERT INTO rental (customer_id, copy_id, rental_date, due_date, return_date, rental_status) VALUES (4, 10, '2025-11-25 13:00:00', '2025-11-30 13:00:00', '2025-11-29 14:00:00', 'RETURNED');
        INSERT INTO rental (customer_id, copy_id, rental_date, due_date, return_date, rental_status) VALUES (5, 15, '2025-11-28 10:00:00', '2025-12-03 10:00:00', '2025-12-02 11:00:00', 'RETURNED');

        -- Payments
        INSERT INTO payment (rental_id, amount, payment_date, payment_method) VALUES (4, 4.99, '2025-11-24 15:00:00', 'CARD');
        INSERT INTO payment (rental_id, amount, payment_date, payment_method) VALUES (5, 4.99, '2025-11-26 16:00:00', 'CASH');
        INSERT INTO payment (rental_id, amount, payment_date, payment_method) VALUES (6, 3.99, '2025-11-29 14:00:00', 'CARD');
        INSERT INTO payment (rental_id, amount, payment_date, payment_method) VALUES (7, 5.99, '2025-12-02 11:00:00', 'CARD');
        """)
        
        # Add default users (password: admin123 for admin, user123 for user)
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        user_pw = hashlib.sha256("user123".encode()).hexdigest()
        cur.execute("INSERT INTO user (username, password, role, created_at) VALUES (?, ?, 'admin', datetime('now'))", ("admin", admin_pw))
        cur.execute("INSERT INTO user (username, password, role, created_at) VALUES (?, ?, 'user', datetime('now'))", ("user", user_pw))
    
    # Always check if default users exist (for existing databases)
    cur.execute("SELECT COUNT(*) FROM user WHERE username = 'admin'")
    (admin_count,) = cur.fetchone()
    if admin_count == 0:
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        user_pw = hashlib.sha256("user123".encode()).hexdigest()
        cur.execute("INSERT INTO user (username, password, role, created_at) VALUES (?, ?, 'admin', datetime('now'))", ("admin", admin_pw))
        cur.execute("INSERT INTO user (username, password, role, created_at) VALUES (?, ?, 'user', datetime('now'))", ("user", user_pw))

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")

# ============== Authentication Routes ==============
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Please enter username and password.", "error")
            return render_template("login.html")
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, password, role FROM user WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        
        if user and user["password"] == hash_password(password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.", "error")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not username or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")
        
        if len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Check if username exists
        cur.execute("SELECT user_id FROM user WHERE username = ?", (username,))
        if cur.fetchone():
            conn.close()
            flash("Username already exists.", "error")
            return render_template("register.html")
        
        # Create new user
        cur.execute(
            "INSERT INTO user (username, password, role, created_at) VALUES (?, ?, 'user', datetime('now'))",
            (username, hash_password(password))
        )
        conn.commit()
        conn.close()
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))

@app.route("/movies")
def browse_movies():
    keyword = request.args.get("keyword", "").strip()
    category_id = request.args.get("category_id", "").strip()
    year = request.args.get("year", "").strip()
    min_rating = request.args.get("min_rating", "").strip()
    sort_by = request.args.get("sort_by", "title")
    sort_dir = request.args.get("sort_dir", "asc")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT category_id, category_name FROM category ORDER BY category_name;")
    categories = cur.fetchall()

    cur.execute(
        """
        SELECT DISTINCT release_year
        FROM movie
        WHERE release_year IS NOT NULL
        ORDER BY release_year DESC;
        """
    )
    years = [row["release_year"] for row in cur.fetchall()]

    base_query = """
        SELECT
            m.movie_id,
            m.title,
            m.release_year,
            m.mpaa_rating,
            m.movie_rating,
            GROUP_CONCAT(DISTINCT c.category_name) AS categories
        FROM movie m
        LEFT JOIN movie_category mc ON m.movie_id = mc.movie_id
        LEFT JOIN category c ON mc.category_id = c.category_id
    """

    conditions = []
    params = []

    if keyword:
        conditions.append("m.title LIKE ?")
        params.append(f"%{keyword}%")

    if category_id:
        conditions.append("c.category_id = ?")
        params.append(category_id)

    if year:
        conditions.append("m.release_year = ?")
        params.append(year)

    if min_rating:
        conditions.append("m.movie_rating >= ?")
        params.append(min_rating)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += """
        GROUP BY
            m.movie_id,
            m.title,
            m.release_year,
            m.mpaa_rating,
            m.movie_rating
    """

    sort_map = {
        "title": "m.title",
        "year": "m.release_year",
        "rating": "m.movie_rating",
    }
    order_col = sort_map.get(sort_by, "m.title")
    order_dir = "DESC" if sort_dir == "desc" else "ASC"
    base_query += f" ORDER BY {order_col} {order_dir};"

    cur.execute(base_query, params)
    movies = cur.fetchall()
    conn.close()

    return render_template(
        "browse_movies.html",
        movies=movies,
        keyword=keyword,
        categories=categories,
        years=years,
        selected_category=category_id,
        selected_year=year,
        selected_min_rating=min_rating,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


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

# ============== Admin: Add Movie ==============
@app.route("/admin/movies/add", methods=["GET", "POST"])
@admin_required
def add_movie():
    conn = get_connection()
    cur = conn.cursor()
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        release_year = request.form.get("release_year", "").strip()
        mpaa_rating = request.form.get("mpaa_rating", "").strip()
        length_minutes = request.form.get("length_minutes", "").strip()
        movie_rating = request.form.get("movie_rating", "").strip()
        description = request.form.get("description", "").strip()
        rental_rate = request.form.get("rental_rate", "4.99").strip()
        late_fee = request.form.get("late_fee", "1.00").strip()
        category_ids = request.form.getlist("categories")
        actor_ids = request.form.getlist("actors")
        num_copies = request.form.get("num_copies", "1").strip()
        store_location = request.form.get("store_location", "Front Shelf").strip()
        
        if not title:
            flash("Movie title is required.", "error")
            cur.execute("SELECT * FROM category ORDER BY category_name")
            categories = cur.fetchall()
            cur.execute("SELECT * FROM actor ORDER BY actor_name")
            actors = cur.fetchall()
            conn.close()
            return render_template("add_movie.html", categories=categories, actors=actors)
        
        try:
            # Insert movie
            cur.execute("""
                INSERT INTO movie (title, release_year, mpaa_rating, length_minutes, movie_rating, description, rental_rate, late_fee)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title,
                int(release_year) if release_year else None,
                mpaa_rating or None,
                int(length_minutes) if length_minutes else None,
                float(movie_rating) if movie_rating else None,
                description or None,
                float(rental_rate),
                float(late_fee)
            ))
            movie_id = cur.lastrowid
            
            # Insert movie-category relationships
            for cat_id in category_ids:
                cur.execute("INSERT INTO movie_category (movie_id, category_id) VALUES (?, ?)", (movie_id, cat_id))
            
            # Insert movie-actor relationships
            for actor_id in actor_ids:
                cur.execute("INSERT INTO movie_actor (movie_id, actor_id) VALUES (?, ?)", (movie_id, actor_id))
            
            # Insert inventory copies
            for _ in range(int(num_copies)):
                cur.execute("INSERT INTO inventory_copy (movie_id, status, store_location) VALUES (?, 'AVAILABLE', ?)", (movie_id, store_location))
            
            conn.commit()
            flash(f"Movie '{title}' added successfully with {num_copies} copies!", "success")
            conn.close()
            return redirect(url_for("movie_detail", movie_id=movie_id))
            
        except Exception as e:
            conn.rollback()
            flash(f"Error adding movie: {str(e)}", "error")
    
    # GET: show form
    cur.execute("SELECT * FROM category ORDER BY category_name")
    categories = cur.fetchall()
    cur.execute("SELECT * FROM actor ORDER BY actor_name")
    actors = cur.fetchall()
    conn.close()
    return render_template("add_movie.html", categories=categories, actors=actors)

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
    
    # Get search parameters
    keyword = request.args.get("keyword", "").strip()
    category_id = request.args.get("category_id", "").strip()

    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        movie_id = request.form.get("movie_id")

    
        if customer_id == "new":
            first_name = (request.form.get("new_first_name") or "").strip()
            last_name = (request.form.get("new_last_name") or "").strip()
            email = (request.form.get("new_email") or "").strip()
            phone = (request.form.get("new_phone") or "").strip()
            address = (request.form.get("new_address") or "").strip()

            if not first_name or not last_name or not email:
                flash("Please fill in first name, last name, and email for the new customer.", "error")

            
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
                cur.execute("SELECT * FROM category ORDER BY category_name")
                categories = cur.fetchall()
                conn.close()
                return render_template("rent.html", movies=movies, customers=customers, categories=categories, keyword=keyword, selected_category=category_id)

        
            cur.execute(
                """
                INSERT INTO customer (first_name, last_name, email, phone, address, signup_date)
                VALUES (?, ?, ?, ?, ?, DATE('now'))
                """,
                (first_name, last_name, email, phone, address),
            )
            customer_id = cur.lastrowid 

    
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

    # GET: show form with search
    # Build movie query with filters
    movie_query = """
        SELECT DISTINCT m.movie_id, m.title,
               (SELECT COUNT(*) FROM inventory_copy ic WHERE ic.movie_id = m.movie_id AND ic.status = 'AVAILABLE') as available
        FROM movie m
        LEFT JOIN movie_category mc ON m.movie_id = mc.movie_id
        WHERE 1=1
    """
    params = []
    
    if keyword:
        movie_query += " AND m.title LIKE ?"
        params.append(f"%{keyword}%")
    
    if category_id:
        movie_query += " AND mc.category_id = ?"
        params.append(category_id)
    
    movie_query += " ORDER BY m.title"
    
    cur.execute(movie_query, params)
    movies = cur.fetchall()
    
    # Get categories for filter dropdown
    cur.execute("SELECT * FROM category ORDER BY category_name")
    categories = cur.fetchall()

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
    return render_template("rent.html", movies=movies, customers=customers, categories=categories, keyword=keyword, selected_category=category_id)


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

    # Top rented movies
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
    
    # ============== Average Statistics ==============
    
    # 1. Average rental duration (for returned rentals)
    cur.execute(
        """
        SELECT AVG(julianday(return_date) - julianday(rental_date)) AS avg_duration
        FROM rental
        WHERE return_date IS NOT NULL
        """
    )
    avg_duration_result = cur.fetchone()
    avg_rental_duration = round(avg_duration_result["avg_duration"], 2) if avg_duration_result["avg_duration"] else 0
    
    # 2. Average rental rate per movie
    cur.execute("SELECT AVG(rental_rate) AS avg_rate FROM movie")
    avg_rate_result = cur.fetchone()
    avg_rental_rate = round(avg_rate_result["avg_rate"], 2) if avg_rate_result["avg_rate"] else 0
    
    # 3. Average rentals per customer
    cur.execute(
        """
        SELECT AVG(rental_count) AS avg_rentals
        FROM (
            SELECT customer_id, COUNT(*) AS rental_count
            FROM rental
            GROUP BY customer_id
        )
        """
    )
    avg_rentals_result = cur.fetchone()
    avg_rentals_per_customer = round(avg_rentals_result["avg_rentals"], 2) if avg_rentals_result["avg_rentals"] else 0
    
    # 4. Average movie rating
    cur.execute("SELECT AVG(movie_rating) AS avg_rating FROM movie WHERE movie_rating IS NOT NULL")
    avg_rating_result = cur.fetchone()
    avg_movie_rating = round(avg_rating_result["avg_rating"], 2) if avg_rating_result["avg_rating"] else 0
    
    # 5. Average copies per movie
    cur.execute(
        """
        SELECT AVG(copy_count) AS avg_copies
        FROM (
            SELECT movie_id, COUNT(*) AS copy_count
            FROM inventory_copy
            GROUP BY movie_id
        )
        """
    )
    avg_copies_result = cur.fetchone()
    avg_copies_per_movie = round(avg_copies_result["avg_copies"], 2) if avg_copies_result["avg_copies"] else 0
    
    # 6. Average payment amount
    cur.execute("SELECT AVG(amount) AS avg_payment FROM payment")
    avg_payment_result = cur.fetchone()
    avg_payment_amount = round(avg_payment_result["avg_payment"], 2) if avg_payment_result["avg_payment"] else 0
    
    # 7. Total statistics
    cur.execute("SELECT COUNT(*) AS total FROM movie")
    total_movies = cur.fetchone()["total"]
    
    cur.execute("SELECT COUNT(*) AS total FROM customer")
    total_customers = cur.fetchone()["total"]
    
    cur.execute("SELECT COUNT(*) AS total FROM rental")
    total_rentals = cur.fetchone()["total"]
    
    cur.execute("SELECT COUNT(*) AS total FROM rental WHERE rental_status = 'OPEN'")
    active_rentals = cur.fetchone()["total"]

    conn.close()
    return render_template(
        "popular_movies.html",
        movies=movies,
        avg_rental_duration=avg_rental_duration,
        avg_rental_rate=avg_rental_rate,
        avg_rentals_per_customer=avg_rentals_per_customer,
        avg_movie_rating=avg_movie_rating,
        avg_copies_per_movie=avg_copies_per_movie,
        avg_payment_amount=avg_payment_amount,
        total_movies=total_movies,
        total_customers=total_customers,
        total_rentals=total_rentals,
        active_rentals=active_rentals
    )

if __name__ == "__main__":
    init_db()          # create DB + sample data if needed
    app.run(debug=True)
