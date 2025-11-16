# app.py
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

from helpers import apology

# Configure Flask application
app = Flask(__name__)

# Ensure responses aren't cached (useful during development)
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 SQL to use readtrack.db
db = SQL("sqlite:///readtrack.db")


# Simple login_required decorator (keeps app self-contained)
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# -------------------
# AUTH ROUTES
# -------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Register a new user.
    - GET: render registration form
    - POST: validate input, insert user, log them in
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Basic validation
        if not username or not password:
            return apology("missing username or password")

        if password != confirmation:
            return apology("passwords do not match")

        # Hash password and attempt to insert. If username exists, catch.
        hash_pw = generate_password_hash(password)
        try:
            user_id = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                username, hash_pw
            )
        except Exception as e:
            # likely UNIQUE constraint failed
            return apology("username already exists")

        # Log user in by storing user id in session
        session["user_id"] = user_id
        return redirect("/")

    # GET request
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Log a user in. On POST, validate credentials and set session['user_id'].
    """
    # Forget any user
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate input
        if not username or not password:
            return apology("must provide username and password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Check that username exists and password hash matches
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username or password")

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out and go to login page."""
    session.clear()
    return redirect("/")


# -------------------
# MAIN APP ROUTES
# -------------------

@app.route("/")
@login_required
def index():
    """
    Dashboard: show recent books, total books, total pages read.
    This aggregates the entries table to compute progress per book.
    """
    user_id = session["user_id"]

    # Get up to 5 recent books plus page progress
    books = db.execute("""
        SELECT b.id, b.title, b.author, b.pages,
               IFNULL(SUM(e.pages_read), 0) AS progress
        FROM books b
        LEFT JOIN entries e ON b.id = e.book_id
        WHERE b.user_id = ?
        GROUP BY b.id
        ORDER BY b.added DESC
        LIMIT 5
    """, user_id)

    # Overall stats
    total_books = db.execute("SELECT COUNT(*) AS c FROM books WHERE user_id = ?", user_id)[0]["c"]
    total_pages = db.execute("SELECT IFNULL(SUM(pages_read), 0) AS p FROM entries WHERE user_id = ?", user_id)[0]["p"]

    return render_template("index.html", books=books, total_books=total_books, total_pages=total_pages)


@app.route("/library")
@login_required
def library():
    """Full library: list all books with progress."""
    user_id = session["user_id"]
    books = db.execute("""
        SELECT b.id, b.title, b.author, b.pages,
               IFNULL(SUM(e.pages_read), 0) AS progress
        FROM books b
        LEFT JOIN entries e ON b.id = e.book_id
        WHERE b.user_id = ?
        GROUP BY b.id
        ORDER BY b.title
    """, user_id)

    return render_template("library.html", books=books)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add a new book to the user's library."""
    user_id = session["user_id"]

    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        pages = request.form.get("pages")

        if not title or not author:
            return apology("missing title or author")

        # pages is optional; convert if provided
        try:
            pages_val = int(pages) if pages else None
        except ValueError:
            return apology("pages must be an integer")

        db.execute("INSERT INTO books (user_id, title, author, pages) VALUES (?, ?, ?, ?)",
                   user_id, title, author, pages_val)

        flash("Book added")
        return redirect("/library")

    return render_template("add.html")


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
@login_required
def book(book_id):
    """
    View a single book:
    - GET: show book details, progress, reviews
    - POST: log pages read (append an entry)
    """
    user_id = session["user_id"]

    # POST: log progress
    if request.method == "POST":
        pages_read = request.form.get("pages_read")
        if not pages_read or not pages_read.isdigit():
            return apology("pages must be a positive integer")

        db.execute("INSERT INTO entries (user_id, book_id, pages_read) VALUES (?, ?, ?)",
                   user_id, book_id, int(pages_read))
        flash("Progress logged")
        return redirect(f"/book/{book_id}")

    # GET: fetch book
    rows = db.execute("SELECT * FROM books WHERE id = ? AND user_id = ?", book_id, user_id)
    if len(rows) != 1:
        return apology("book not found")

    book = rows[0]

    # Compute progress & fetch reviews
    progress = db.execute("SELECT IFNULL(SUM(pages_read), 0) AS total FROM entries WHERE book_id = ? AND user_id = ?",
                          book_id, user_id)[0]["total"]

    reviews = db.execute("SELECT rating, review, date FROM reviews WHERE book_id = ? AND user_id = ? ORDER BY date DESC",
                         book_id, user_id)

    return render_template("book.html", book=book, progress=progress, reviews=reviews)


@app.route("/review/<int:book_id>", methods=["POST"])
@login_required
def review(book_id):
    """Add a rating and review for a book (optional fields)."""
    user_id = session["user_id"]
    rating = request.form.get("rating")
    review_text = request.form.get("review")

    try:
        rating_val = int(rating)
        if rating_val < 1 or rating_val > 5:
            return apology("rating must be 1-5")
    except Exception:
        return apology("invalid rating")

    db.execute("INSERT INTO reviews (user_id, book_id, rating, review) VALUES (?, ?, ?, ?)",
               user_id, book_id, rating_val, review_text)

    flash("Review added")
    return redirect(f"/book/{book_id}")


@app.route("/stats")
@login_required
def stats():
    """Show user stats: books count, pages read, reviews count."""
    user_id = session["user_id"]
    totals = db.execute("""
        SELECT
            (SELECT COUNT(*) FROM books WHERE user_id = ?) AS books_count,
            (SELECT IFNULL(SUM(pages_read), 0) FROM entries WHERE user_id = ?) AS pages_count,
            (SELECT COUNT(*) FROM reviews WHERE user_id = ?) AS reviews_count
    """, user_id, user_id, user_id)[0]

    return render_template("stats.html", totals=totals)
