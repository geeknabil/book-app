import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")
    # # if user logging in
    # if session["user"]["user_id"] is None:
    # else:
    #     return render_template("user.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # if submitting the form
    if request.method == "POST":
        # get user input
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # make sure user not exist
        user = db.execute("SELECT email FROM users WHERE email = :email",
        {"email": email}).fetchone()

        # if not exist insert as a new user and redirect to login page
        if user is None:
            db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
            {"username": username, "email": email, "password": password})
            # save changes
            db.commit()
            return render_template("success.html", mess="You have successfully registered!", url='login')
        # if already exist return error mess
        else:
            return render_template("register.html", mess="Error, the user with this email already exist!")

    # in case user access the page normally via GET request
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # make sure user logged in correctly
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE email = :email AND password = :password",
        {"email": email, "password": password}).fetchone()
        if user is None:
            return render_template("login.html", mess="Error, either email or password not correct!", again="again")

        # store username and id for this user inside a session variable
        session["user"] = {"id": user.id, "username": user.username}

        return render_template("success.html", mess="Thanks for logging in!", url='search')

    return render_template("login.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    # render books that user asked
    if request.method == "POST":
        book_query = request.form.get("search")
        book_query_like = '%' + book_query + '%'

        books = db.execute("SELECT * FROM books WHERE isbn LIKE :book_query_like OR title LIKE :book_query_like OR author LIKE :book_query_like",
        {"book_query_like": book_query_like}).fetchall()

        return render_template("search.html", username=session["user"]["username"], no_books= (len(books) == 0), books=books)

    return render_template("search.html", username=session["user"]["username"])

@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book(book_id):
    # first select book and it's reviews and make them global so we can render them in POST requests
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()

    # call for Goodreads api
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
    params={"key": "NDxVHeRzgVMWpplzuO3BWQ", "isbns": book.isbn})

    if res.status_code != 200:
        raise Exception("Error: API request unsuccessful.")

    # extract api json data
    data = res.json()
    rating_num = data["books"][0]["work_ratings_count"]
    api_avg_rate = data["books"][0]["average_rating"]

    # if user submit a review
    if request.method == "POST":
        # take review inputs
        review_text = request.form.get("review_text")
        avg_rate = request.form.get("avg_rate")

        # check if user submit any reviews before
        user = db.execute("SELECT user_id FROM reviews WHERE user_id = :id AND book_id= :book_id",
        {"id": session['user']['id'], "book_id": book_id}).fetchone()

        # if not - Add this user and it's reviews for this book
        if user is None:
            db.execute("INSERT INTO reviews (review_text, avg_rate, api_avg_rate, rating_num, book_id, user_id, username) VALUES (:review_text, :avg_rate, :api_avg_rate, :rating_num, :book_id, :user_id, :username)",
            {"review_text": review_text, "avg_rate": avg_rate, "book_id": book_id,
            "user_id": session['user']['id'], "username": session['user']['username'],
            "api_avg_rate": api_avg_rate, "rating_num": rating_num})
            # save changes
            db.commit()
        else:
            return render_template("details.html", err_mess="Error: You submitted a review before!", book=book, reviews=reviews)

        # after making sure that the user doesn't exist and submitted a review: render all reviews
        reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
        return render_template("details.html", reviews=reviews, book=book)


    if book is None:
        return render_template("details.html", no_book=True)

    return render_template("details.html", book=book, reviews=reviews)