from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, json
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
from flask_jsglue import JSGlue
from random import randint

from helpers import *
import html
import plotly


# configure application
app = Flask(__name__)
JSGlue(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///tea.db")
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    #forget id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")
        
         # ensure confirm password was submitted
        elif not request.form.get("confirm_password"):
            return apology("must confirm")
            
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE id = :id", id=request.form.get("username"))
   
        # ensure username does not already exist
        if len(rows) == 1:
            return apology("username already exists")
            
        # verify that passwords match
        elif request.form.get("password") != request.form.get("confirm_password"):
            return apology("passwords do not match")
        
        else:
            hash = pwd_context.encrypt(request.form.get("password"))
            user_id = db.execute('INSERT INTO users(id, password) VALUES(:id, :password)', id = request.form.get("username"), password = hash)
            
            # remember which user has logged in
            session["user_id"] = user_id
    
            # redirect user to home page
            return redirect(url_for("home"))
            
    else:
        return render_template("register.html")
        
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE id = :id", id=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["password"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("home"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


#HOME PAGE
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "GET":
        return render_template("form.html")
        
    # get values from drop down menus
    if request.method == "POST":
        strength = request.form.get("Strength")
        volume = request.form.get("Volume_Water")
        Tea_Type = request.form.get("Tea_Type")
        
        
        # ensure that there are no errors
         # ensure all fields were submitted
        if not request.form.get("Tea_Type"):
            return apology("must provide tea")

        # ensure password was submitted
        elif not request.form.get("Strength"):
            return apology("must provide preferred strength")
        
        elif not request.form.get("Volume_Water"):
            return apology("must provide volume")
        
        
        else:
            
            #insert new row into diary
            entry_id = db.execute('INSERT INTO diary(id, tea, date) VALUES (:id, :tea, CURRENT_TIMESTAMP) ', id = session["user_id"], tea = request.form.get("Tea_Type"))
           # update stats table
            db.execute('UPDATE stats SET Cups = Cups + 1 WHERE Tea_Type = :Tea_Type', Tea_Type = Tea_Type)
           
           #query database for time
            get_time = db.execute("SELECT * FROM SteepTimes WHERE Strength = :Strength AND Tea_Type = :Tea_Type AND Volume_Water = :Volume_Water",  Strength = strength, Tea_Type = Tea_Type, Volume_Water = volume)
            return render_template('timer.html', time = get_time[0]["Time"])
            return jsonify(time = get_time[0]["Time"])
            
            
    # else if user reached route via GET (as by clicking a link or via redirect), return form
    else:
        return render_template("form.html")



@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

#random number generator acquires random fact from database
@app.route("/facts", methods=["GET", "POST"])
def facts():
        max = len(db.execute("SELECT * FROM facts"))
        random_num = randint(1, max)
        factdb = db.execute("SELECT * FROM facts WHERE id= :id", id = random_num)
        return render_template('facts.html', facts=factdb[0]["fact"])
        return jsonify(factdb)  
  
    
@app.route("/history")
@login_required
def history():
        diary_entry = db.execute("SELECT * FROM diary WHERE id = :id", id = session["user_id"])
        
        #find length of diary table
        cups = len(diary_entry)
        
        #define levels of tea-drinking
        if cups <= 30:
            level = "Novice"
        elif cups > 30 and cups <= 60:
            level = "Q-Tea"
        elif cups > 60 and cups <= 90:
            level = "Tea-Rex"
        elif cups > 90:
            level = "celebriTea"
        
        return render_template("hist.html", tea = diary_entry[0]["tea"], date = diary_entry[0]["date"], cups = cups, level = level)
        




@app.route("/stats")
def stats():

    # generating the da
    def chart(White, Black, Oolong, Green, Darjeeling, Rooibos, Puerh, Herbal):
 
        figure = {
            "data": [
                {
                    "labels": ["White", "Black", "Oolong", "Green", "Darjeeling", "Rooibos", "Pu-erh", "Herbal"],
                    "hoverinfo": "none",
                    "marker": {
                        "colors": [
                            "rgb(255,254,238)",
                            "rgb(142, 139, 132)",
                            "rgb(235,144,47)",
                            "rgb(170, 196, 139)",
                            "rgb(244, 146, 100)",
                            "rgb(247, 120, 61)",
                            "rgb(135, 126, 106)",
                            "rgb(225, 232, 187)"
                        ]
                    },
                    "type": "pie",
                    "values": [White, Black, Oolong, Green, Darjeeling, Rooibos, Puerh, Herbal]
                }
            ],
            "layout": {
                "showlegend": True
                }
        }
        return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)
        
    # getting data from SQL table
     
    White = (db.execute("SELECT Cups FROM Stats WHERE Tea_Type = 'White'"))
    White_count = White[0]["Cups"]
    
    Black = db.execute("SELECT Cups FROM Stats WHERE Tea_Type = 'Black'")
    Black_count = Black[0]["Cups"]
    
    Oolong = db.execute("SELECT Cups FROM Stats WHERE Tea_Type = 'Oolong'")
    Oolong_count = Oolong[0]["Cups"]
    
    Green = db.execute("SELECT Cups FROM Stats WHERE Tea_Type = 'Green'")
    Green_count = Green[0]["Cups"]
    
    Darjeeling = db.execute("SELECT Cups FROM Stats WHERE Tea_Type = 'Darjeeling'")
    Darjeeling_count = Darjeeling[0]["Cups"]
    
    Rooibos = db.execute("SELECT Cups FROM Stats WHERE Tea_Type = 'Rooibos'")
    Rooibos_count = Rooibos[0]["Cups"]
    
    Puerh = db.execute("SELECT Cups FROM Stats WHERE Tea_Type = 'Pu-erh'")
    Puerh_count = Puerh[0]["Cups"]
    
    Herbal = db.execute("SELECT Cups FROM Stats WHERE Tea_Type = 'Herbal'")
    Herbal_count = Herbal[0]["Cups"]
     
    
    chart = chart(White_count, Black_count, Oolong_count, Green_count, Darjeeling_count, Rooibos_count, Puerh_count, Herbal_count)
    
    
    total = White_count + Black_count + Oolong_count + Green_count + Darjeeling_count + Rooibos_count + Puerh_count + Herbal_count
    # render results
    return render_template("stats.html", chart=chart, total = total, White_count = White_count
    , Black_count = Black_count, Oolong_count = Oolong_count, Green_count = Green_count, 
    Darjeeling_count = Darjeeling_count, Rooibos_count = Rooibos_count, Puerh_count = Puerh_count, Herbal_count = Herbal_count )

    
    
    
    
   


    
    