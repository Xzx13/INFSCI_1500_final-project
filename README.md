# Movie Rental Database System

INFSCI 1500 Database Management - Final Project  
Fall 2025

**Team Members:** Zachary Renaud, Hangting Zhu, Zhexi Xu

---

## What is this?

This is a web-based movie rental management system we built for our database class. Think of it like a digital version of those old Blockbuster stores (if you're old enough to remember those lol). Store employees can use it to manage movies, track rentals, and handle returns.

---

## How to Run

### Prerequisites
- Python 3.x
- Flask (`pip install flask`)

### Steps

1. Clone/download this repo

2. Navigate to the project folder:
   ```bash
   cd movie_rental_project
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Open your browser and go to:
   ```
   http://127.0.0.1:5000
   ```

That's it! The database will be created automatically on first run with some sample data.

---

## Features

- **Browse Movies** - Search by title, view movie details and availability
- **Rent Movies** - Select a customer and movie, system handles the rest
- **Return Movies** - Process returns, automatically updates inventory
- **View Customers** - See all registered customers
- **Popular Movies Report** - Shows which movies are rented the most (uses GROUP BY)

---

## Database Structure

We have 9 tables total:

| Table | What it stores |
|-------|----------------|
| customer | Customer info (name, email, phone, etc.) |
| movie | Movie details (title, year, rating, etc.) |
| category | Movie genres (Action, Comedy, etc.) |
| actor | Actor names |
| movie_category | Links movies to categories (many-to-many) |
| movie_actor | Links movies to actors with role names |
| inventory_copy | Physical copies of each movie |
| rental | Rental transactions |
| payment | Payment records |

---

## Tech Stack

- **Backend:** Python + Flask
- **Database:** SQLite
- **Frontend:** HTML + Bootstrap 5 + Jinja2 templates

We chose SQLite because it's simple and doesn't require any setup - the database is just a single file. For a real production system you'd probably want MySQL or PostgreSQL, but SQLite works great for a class project.

---

## Project Structure

```
movie_rental_project/
├── app.py              # Main Flask application
├── movierental.db      # SQLite database (auto-generated)
├── schema.sql          # MySQL version of schema (for reference)
├── templates/          # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── browse_movies.html
│   ├── movie_detail.html
│   ├── customers.html
│   ├── rent.html
│   ├── return.html
│   └── popular_movies.html
└── README.md
```

---

## Sample Data

The system comes pre-loaded with:
- 19 movies (classics like The Shawshank Redemption, The Godfather, etc.)
- 6 categories
- 19 actors
- 8 customers (including us three as test accounts lol)
- Some sample rentals to play around with

---

## Known Limitations

- No login system - we assume only store employees use this
- Can only search movies by title (no category/actor search in UI)
- Payment processing is basic - no actual payment gateway
- No late fee calculation in the web interface

These could be added but we ran out of time 😅

---

## Division of Work

- **Zach:** ER diagram, relational schema, testing documentation
- **Zhexi:** DDL statements, SQL queries
- **Hangting:** Frontend code, system overview, implementation sections

---

## Notes for Demo

To reset the database and start fresh:
```bash
rm movierental.db
python app.py
```

The `init_db()` function will recreate everything with sample data.

---

## Questions?

Feel free to reach out to any of us or check the final report for more details.
