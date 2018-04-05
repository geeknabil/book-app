import os

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

@app.route("/login", methods=["GET", "POST"])
def login():
    # if submitting the form take username, email and password and insert them into db
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
        {"username": username, "email": email, "password": password})

        db.commit()
        return render_template("login.html", mess="You have successfully registered!")

    # in case user try to login with login button (get request)
    return render_template("login.html")

@app.route("/search", methods=["POST"])
def search():
    username = request.form.get("username")
    password = request.form.get("password")

    user = db.execute("SELECT id, username, password FROM users WHERE username = :username AND password = :password",
    {"username": username, "password": password}).fetchone()

    if user is None:
        return render_template("error.html", error="Error, No user found try to register instead!", back="register")
    # elif username != user.username or password != user.password:
    #     return render_template("error.html", error="Error, username or password not correct!", back="login")

    session["user_id"] = user.id
    print(session["user_id"])

    return render_template("search.html")


@app.route("/search", methods=["POST"])
def list_books():
    book_query = request.form.get("search")
    books = db.execute("SELECT * FROM books WHERE isbn = :book_query OR title = :book_query OR author = :book_query",
    {"book_query": book_query})

    return render_template("search.html", books=books)

