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

@app.route("/register", methods=["GET", "POST"])
def register():
    # if submitting the form
    if request.method == "POST":
        # get user input
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        print(username)
        print(email)
        print(password)
        # make sure user not exist and if so insert it to db
        user = db.execute("SELECT email FROM users WHERE email = :email",
        {"email": email}).fetchone()
        if user is None:
            db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)",
            {"username": username, "email": email, "password": password})
            db.commit()
        # if exist return error mess
        else:
            return render_template("register.html", mess="Error, the user with this email already exist!")

        # if not exist render login page
        return render_template("success.html", mess="You have successfully registered!")

    # in case clicking register button
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # make sure user logged in correctly
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.execute("SELECT id, email, password FROM users WHERE email = :email AND password = :password",
        {"email": email, "password": password}).fetchone()

        if user is None:
            return render_template("login.html", mess="Error, either username or password not correct if you didn't registered try to register instead", again="again")

        # store user id inside a session variable
        session["user_id"] = user.id
        return render_template("thank.html", mess="Thanks for logging in!")

    return render_template("login.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    # render books that user asked
    if request.method == "POST":
        book_query = request.form.get("search")
        books = db.execute("SELECT * FROM books WHERE isbn = :book_query OR title = :book_query OR author = :book_query",
        {"book_query": book_query})

        return render_template("search.html", books=books)

    return render_template("search.html")


