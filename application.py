from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final_project.db")


@app.route("/", methods=["GET"])
# @login_required
def index():
    """Show Tournament Information"""


    return render_template("index.html")

@app.route("/teams", methods=["GET"])
def teams():

    return render_template("teams.html")


@app.route("/buy", methods=["GET", "POST"])
# @login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)

        # Ensure number of shares were submitted
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 400)

        elif not request.form.get("shares").isdigit():
            return apology("number of shares cannot contain text or symbols", 400)

        # Call lookup() to return a quote for the stock
        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("Stock symbol must be valid.", 400)

        # Store the price of the stock in a variable
        price = quote['price']

        # Convert shares into an int and store in variable shares
        shares = int(request.form.get("shares"))

        # Gather cash from database
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])

        # Store actual cash into a variable
        user_cash = cash[0]["cash"]

        # Gather username from session id
        query_username = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])

        # Store the username in a variable
        username = query_username[0]["username"]

        # Determine if the user has enough cash
        if user_cash > (shares * price):

            # The user's cash is then adjusted
            user_cash = round(user_cash - (shares * price), 2)

            # Process the transaction and store the information in the database
            result = db.execute("INSERT INTO portfolio (username, stock, shares) VALUES(:username, :stock, :shares)",
                                username=username, stock=request.form.get("symbol"), shares=shares)

            # Store the transaction history in the transaction database
            history = db.execute("INSERT INTO transactions (username, stock, shares, price) VALUES(:username, :stock, :shares, :price)",
                                 username=username, stock=request.form.get("symbol"), shares=shares, price=price)

            # Update the user database to reflect the change in cash
            update = db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=user_cash, id=session["user_id"])

        else:
            return apology("insufficent funds", 400)

        # Redirect user to homepage? Probably could send them anywhere.
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Show history of transactions"""

    if request.method == "GET":

        # Gather username from session id
        query_username = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])

        # Store the username in a variable
        username = query_username[0]["username"]

        user_history = []

        transactions = db.execute("SELECT * FROM transactions WHERE username = :username", username=username)

        for transaction in transactions:
            stock_symbol = transaction['stock']
            stock_shares = transaction['shares']
            stock_price = transaction['price']
            stock_timestamp = transaction['timestamp']
            stock_value = round(stock_shares * stock_price, 2)
            stock_quote = lookup(stock_symbol)
            stock_name = stock_quote['name']

            stock_dict = {
                "timestamp": stock_timestamp,
                "name": stock_name,
                "price": stock_price,
                "symbol": stock_symbol,
                "shares": stock_shares,
                "value": usd(stock_value)
            }

            user_history.append(stock_dict)

        return render_template("history.html", transactions=user_history)


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)

        quote = lookup(request.form.get("symbol"))
        if not quote:
            return apology("Stock symbol must be valid.", 400)

        name = quote['name']
        symbol = quote['symbol']
        price = quote['price']

        return render_template("quoted.html", name=name, symbol=symbol, price=usd(price))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


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
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                            username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))
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
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide stock symbol", 400)

        # Ensure number of shares were submitted
        elif not request.form.get("shares"):
            return apology("must provide number of shares", 400)

        elif not request.form.get("shares").isdigit():
            return apology("number of shares cannot contain text or symbols", 400)

        stock = request.form.get("symbol")
        # print(stock)

        # Call lookup() to return a quote for the stock
        quote = lookup(stock)
        if not quote:
            return apology("Stock symbol must be valid.", 400)

        # Query username from session id
        query_username = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])

        # Store username
        username = query_username[0]["username"]

        # Store the price of the stock in a variable
        price = quote["price"]

        # Convert shares into an int and store in variable shares
        shares = int(request.form.get("shares"))

        user_shares = db.execute("SELECT shares FROM portfolio WHERE username = :username AND stock = :stock",
                                 username=username, stock=stock)

        if shares > user_shares[0]["shares"]:
            return apology("shares exceed total shares currently held", 400)

        # Gather cash from database
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])

        # Store cash as a variable
        user_cash = cash[0]["cash"]

        # The user's cash is then adjusted
        user_cash = round(user_cash + (shares * price), 2)

        updated_shares = user_shares[0]["shares"] - shares

        # Process the transaction and store the information in the database
        delete_stock = db.execute("DELETE FROM portfolio WHERE stock = :stock AND username = :username",
                                  stock=stock, username=username)

        # Update the transaction and store the information in the database
        if updated_shares > 0:
            update_stock = db.execute("INSERT INTO portfolio (username, stock, shares) VALUES(:username, :stock, :updated_shares)",
                                      username=username, stock=request.form.get("symbol"), updated_shares=updated_shares)

        # Store the transaction history in the transaction database
        history = db.execute("INSERT INTO transactions (username, stock, shares, price) VALUES(:username, :stock, :shares, :price)",
                             username=username, stock=request.form.get("symbol"), shares=-shares, price=price)

        # Update the user database to reflect the change in cash
        update = db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=user_cash, id=session["user_id"])

        # Redirect user to homepage? Probably could send them anywhere.
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Query the database for the username of the current sesion
        check_username = db.execute("SELECT username FROM users WHERE id = :id", id=session["user_id"])

        # Store the username string into a variable
        username = check_username[0]["username"]

        # Query the database for all stocks of the user
        stocks = db.execute("SELECT stock FROM portfolio WHERE username = :username", username=username)

        # Declare user_stocks as an array
        user_stocks = []

        # Iterate through the stocks and append to the user_stocks array
        for stock in stocks:
            stock_symbol = stock["stock"]

            stock_dict = {
                "symbol": stock_symbol,
            }

            user_stocks.append(stock_dict)

        return render_template("sell.html", stocks=user_stocks)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)