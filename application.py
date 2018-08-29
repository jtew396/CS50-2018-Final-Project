from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


# Configure application
app = Flask(__name__)


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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final_project.db")


@app.route("/", methods=["GET"])
def index():
    """Show Tournament Information"""


    return render_template("index.html")

@app.route("/teams", methods=["GET"])
def teams():

    if request.method == "GET":

        users = db.execute("SELECT team_name, team_city, team_state, conference, region FROM users")

        return render_template("teams.html", users=users)

    return render_template("teams.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/roster", methods=["GET", "POST"])
@login_required
def roster():
    """Adjust the team roster."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure that a player number was submitted
        if not request.form.get("roster_number"):
            return apology("Missing Player Number!", 400)

        # Ensure that the player name was submitted
        if not request.form.get("roster_name"):
            return apology("Missing Player Name!", 400)

        # Ensure that the player position was submitted
        if not request.form.get("roster_position"):
            return apology("Missing Player Position!", 400)

        # Ensure that the player height was submitted
        if not request.form.get("roster_height"):
            return apology("Missing Player Height!", 400)

        # Store the player in the roster database
        result = db.execute("INSERT INTO roster (roster_number, roster_name, roster_position, roster_height) VALUES(:roster_number, :roster_name, :roster_position, :roster_height)",
                            roster_number=request.form.get("roster_number"), roster_name=request.form.get("roster_name"),
                            roster_position=request.form.get("roster_position"), roster_height=request.form.get("roster_height"))

        # Query the roster database for the team's roster
        roster = db.execute("")

        return render_template("roster.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        team_name = db.execute("SELECT team_name FROM users WHERE id = :id", id=session["user_id"])

        return render_template("roster.html", team_name=team_name[0]["team_name"])


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Missing username!", 400)

        # Ensure a team name was submitted
        if not request.form.get("team_name"):
            return apology("Missing username!", 400)

        # Ensure a team city was submitted
        if not request.form.get("team_city"):
            return apology("Missing team city!", 400)

        # Ensure a team state was submitted
        if not request.form.get("team_state"):
            return apology("Missing team state!", 400)

        # Ensure a conference was submitted
        if not request.form.get("conference"):
            return apology("Missing team conference!", 400)

        # Ensure a region was submitted
        if not request.form.get("region"):
            return apology("Missing team region!", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Missing password!", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("Must input password twice!", 400)

        # Ensure confirmation matches password
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("Passwords must match!", 400)

        # Store the username in the database
        result = db.execute("INSERT INTO users (username, hash, team_name, team_city, team_state, conference, region) VALUES(:username, :hash, :team_name, :team_city, :team_state, :conference, :region)",
                            username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")),
                            team_name=request.form.get("team_name"), team_city=request.form.get("team_city"),
                            team_state=request.form.get("team_state"), conference=request.form.get("conference"),
                            region=request.form.get("region"))
        if not result:
            return apology("Username currently in use", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        states = db.execute("SELECT * FROM states")
        print(states)


        return render_template("register.html", states=states)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)