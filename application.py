import os
import requests
import urllib.parse

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from dataclasses import dataclass

###### CONFIGURATION ######
# Initialize Flask App Ojbect
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure Heroku Postgres database
db = SQL(os.getenv('DATABASE_URL'))

###### DATA STRUCTURES ######
# Set type variables
# Loteria
colors = ['black', 'red', 'turquoise', 'yellow', 'green', 'purple']
sizes = ['s', 'm', 'l']
loterias = {
    'La Dama': ['Frida', 'Frida Flowers'],
    'La Sirena': ['Mermaid Body', 'Mermaid Hair', 'Mermaid Tail'],
    'La Mano': ['Hand', 'Hand Swirls'],
    'La Bota': ['Boot', 'Boot Swirls', 'Boot Flames'],
    'El Corazon': ['Heart', 'Heart Swirls'],
    'El Musico': ['Guitar', 'Guitar Hands'],
    'La Estrella': ['Star', 'Star Swirls'],
    'El Pulpo': ['Octopus', 'Octopus Swirls', 'Octopus Tentacles'],
    'La Rosa': ['Rose', 'Rose Swirls', 'Rose Leaves'],
    'La Calavera': ['Skull', 'Skull Flames', 'Skull Swirls'],
    'El Poder': ['Fist', 'Fist Swirls', 'Fist Wrist']
}

@dataclass
class loteria:
    size: str
    a: str
    b: str
    c: str

@app.route('/')
def dashboard():
    # print(loteria)
    for key in loterias:
        # i = 0
        print(f"{key}:")
        tmp = loterias[key]
        print(tmp)

    return render_template('index.html', colors=colors, sizes=sizes, loterias=loterias)

@app.route('/items')
def items():
    return render_template('items.html')

@app.route('/parts')
def parts():
    return render_template('parts.html')

@app.route('/projections')
def projections():
    return render_template('projections.html')

@app.route('/shipping')
def shipping():
    return render_template('shipping.html')



###### ADMINSTRATIVE ######

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Serve registration page
    if request.method == 'GET':
        return render_template("register.html")

    # Process submitted form responses on POST
    else:

        # Error Checking
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", errcode=403, errmsg="Username required.")

        # Ensure password was submitted
        if not request.form.get("password"):
            return render_template("error.html", errcode=403, errmsg="Password required.")

        # Ensure password and password confirmation match
        if request.form.get("password") != request.form.get("passwordconfirm"):
            return render_template("error.html", errcode=403, errmsg="Passwords must match.")

        # Ensure minimum password length
        if len(request.form.get("password")) < 8:
            return render_template("error.html", errcode=403, errmsg="Password must be at least 8 characters.")

        # Store the hashed username and password
        username = request.form.get("username")
        hashedpass = generate_password_hash(request.form.get("password"))

        # Check if username is already taken
        if not db.execute("SELECT username FROM users WHERE username LIKE (?)", username):

            # Add the username
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashedpass)",
                        username=username, hashedpass=hashedpass)
            return redirect("/")

        else:
            return render_template("error.html", errcode=403, errmsg="Username invalid or already taken.")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", errcode=400, errmsg="Username required.")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", errcode=400, errmsg="Password required.")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists
        if len(rows) != 1:
            return render_template("register.html", errmsg="Username not found.")

        # Ensure username exists and password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html", errcode=403, errmsg="Incorrect password.")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Store login timestamp
        db.execute("INSERT INTO activity (user_id, action) VALUES (:user_id, :action)", user_id=session["user_id"], action="login")


        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
