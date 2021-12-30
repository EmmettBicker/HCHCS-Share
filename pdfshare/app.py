from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

SECTION = 0
CLASS = 1
TEACHER = 2
MONDAY = 3
TUESDAY = 4
WEDNESDAY = 5
THURSDAY = 6
FRIDAY = 7

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return render_template("index.html")

    return render_template("enter.html")

@app.route("/teachers", methods=["GET","POST"])
def view():
    period = request.args.get("period")
    weekday = request.args.get("weekday")
    subject = request.args.get("subject")
    
    weekday = weekday[0:3]
    #Configure database 
    connection = sqlite3.connect("classes.db"); db = connection.cursor()
    #Bad code solution, couldn't figure out how to insert column name with db.execute
    #Number to track the position of weekday in the table
    matchingWeekdayNumber = 0
    if weekday == "Mon":
        db.execute("SELECT * FROM classes WHERE Mon LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = MONDAY
    if weekday == "Tue":
        db.execute("SELECT * FROM classes WHERE Tue LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = TUESDAY
    if weekday == "Wed":
        db.execute("SELECT * FROM classes WHERE Wed LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = WEDNESDAY
    if weekday == "Thu":
        db.execute("SELECT * FROM classes WHERE Thu LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = THURSDAY
    if weekday == "Fri":
        db.execute("SELECT * FROM classes WHERE Fri LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = FRIDAY
    ans = db.fetchall()
    return render_template("table.html",rows=ans, rowCount=len(ans), weekday=matchingWeekdayNumber)    

