import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from flask_session import Session
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from random import randint
from tempfile import mkdtemp
from datetime import date


from helpers import apology, login_required

UPLOAD_FOLDER = "C:/Users/Emmett/Desktop/pdfshare/StorageFolder"

ALLOWED_EXTENSIONS = ["pdf"]

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Max file size = 8mb
app.config['MAX_CONTENT_LENGTH'] = 8 * 1000 * 1000


#Mail config
mail = Mail(app)
app.config["MAIL_SERVER"]='smtp.gmail.com'  
app.config["MAIL_PORT"] = 465      
app.config["MAIL_USERNAME"] = 'hchsshare@gmail.com'  
app.config['MAIL_PASSWORD'] = "JQfPg3G8KkbbYK"  
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)    


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


tableDict = {
    "SECTION" : 0,
    "CLASS" : 1,
    "TEACHER" : 2,
    "MONDAY" : 3,
    "TUESDAY" : 4,
    "WEDNESDAY" : 5,
    "THURSDAY" : 6,
    "FRIDAY" : 7
}

weekdayList = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday"
]

@app.route("/", methods=["GET", "POST"])
def index():    
    if request.method == "POST":
        return render_template("index.html")
    return render_template("enter.html")

@app.route("/table", methods=["GET"])
def teachers():
    period = request.args.get("period")
    weekday = request.args.get("weekday")
    subject = request.args.get("subject")
    
    if not period or not weekday or not subject:
        return apology("Please input required information")

    if weekday not in weekdayList or not period.isdigit():
        return apology("Don't hack the website lol")

    weekday = weekday[0:3]

    #Configure database 
    connection = sqlite3.connect("classes.db"); db = connection.cursor()
    #Bad code solution, couldn't figure out how to insert column name with db.execute
    #Number to track the position of weekday in the table
    matchingWeekdayNumber = 0
    if weekday == "Mon":
        db.execute("SELECT * FROM classes WHERE Mon LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = tableDict["MONDAY"]
    elif weekday == "Tue":
        db.execute("SELECT * FROM classes WHERE Tue LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = tableDict["TUESDAY"]
    elif weekday == "Wed":
        db.execute("SELECT * FROM classes WHERE Wed LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = tableDict["WEDNESDAY"]
    elif weekday == "Thu":
        db.execute("SELECT * FROM classes WHERE Thu LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = tableDict["THURSDAY"]
    elif weekday == "Fri":
        db.execute("SELECT * FROM classes WHERE Fri LIKE ? AND Class = ?", ("%"+period+"%",subject))
        matchingWeekdayNumber = tableDict["FRIDAY"]
    ans = db.fetchall()
    return render_template("table.html",rows=ans, rowCount=len(ans), weekday=matchingWeekdayNumber)    

@app.route("/view",methods=["GET"])
def view():
    teacher = request.args.get("teacher")
    weekday = request.args.get("weekday")
    period = request.args.get("period")

    if not weekday or not period or not teacher:
        return apology("Not enough information")

    if not weekday.isdigit() or not period.isdigit():
        return apology("Weekday and period must be digits")

    #Get dictionary key by index
    weekday = list(tableDict.keys())[int(weekday)]

    #Capitalize first letter of weekday
    weekday = weekday.lower()
    weekday = weekday[0].upper() + weekday[1:]
    inputWeekday = weekday[0:3]

    connection = sqlite3.connect("classes.db"); db = connection.cursor()
    db.execute("SELECT * FROM notes WHERE teacher = ? AND weekday = ? AND period = ? ORDER BY date DESC, notes_id DESC", (teacher, inputWeekday, period))
    rows = db.fetchall()

    filenameList = []
    #Get names of uploaders 
    uploaderList = []
    FILENAME_INDEX = 2
    for row in rows: 
        i = 0
        filenameList.append(row[FILENAME_INDEX])
        db.execute("SELECT * FROM users WHERE users_id = ?", (rows[i][1],))
        uploaderRow = db.fetchall()
        uploaderList.append(uploaderRow[0][1])
        i += 1

    return render_template("view.html",teacher=teacher,weekday=weekday,period=period,filenameList=filenameList, fileCount=len(filenameList), rows=rows, uploaderList=uploaderList)   

@app.route("/me")
def me():
    return render_template("me.html")

@app.route('/storage/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
         'favicon.ico', mimetype='image/vnd.microsoft.icon')
    

@app.route("/login", methods=["GET","POST"])
def login():
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
        connection = sqlite3.connect("classes.db"); db = connection.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username").strip(),))
        rows = db.fetchall()

        # Ensure username exists and password is correct   
        # Hash index is 3
        HASH = 3 
        USERS_ID = 0
        VERIFIED = 4

        if len(rows) != 1 or not check_password_hash(rows[0][HASH], request.form.get("password").strip()):
            return apology("invalid username and/or password", 403)

        if rows[0][VERIFIED] == "NO":
            return apology("Unverified user")

        # Remember which user has logged in
        session["user_id"] = rows[0][USERS_ID]

        # Redirect user to home page
        return redirect("/upload")

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        username = request.form.get("username").strip()
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()
        confirmPassword = request.form.get("confirmation").strip()

        if not username or not password or not confirmPassword:
            return apology("Please put in all required information", 400)

        connection = sqlite3.connect("classes.db"); db = connection.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (username,))
        rows = db.fetchall()

        if rows:
            return apology("Username taken", 400)

        db.execute("SELECT * FROM users WHERE email = ?", (email,))
        rows = db.fetchall()

        if rows:
            return apology("email taken", 400)
        
        domain = email[email.index('@') + 1 : ]
        if domain not in ["hunterschools.org","hccs.hunter.cuny.edu"]:
            return apology("Hunter emails only!")

        if password == confirmPassword:
            # One time password for this account, used in email verification
            otp = randint(000000,999999) 
            db.execute("INSERT INTO users (username, email, hash, otp) VALUES (?, ?, ?, ?)", (username, email, generate_password_hash(password), otp))
            connection.commit()

            # Auto log in 
            db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username").strip(),))
            rows = db.fetchall()
            session["user_id"] = rows[0][0]

            return redirect("/verify")
        else:
            return apology("Passwords do not match", 400)


        #Generate password hash
    return render_template("register.html")

@app.route("/verify",methods=["GET"])
@login_required
def verify():
    connection = sqlite3.connect("classes.db"); db = connection.cursor()

    db.execute("SELECT * FROM users WHERE users_id = ?", (session["user_id"],))
    rows = db.fetchall()

    EMAIL_INDEX = 2
    OTP_INDEX = 5
    email = rows[0][EMAIL_INDEX]
    otp = rows[0][OTP_INDEX]

    msg = Message('OTP',sender = 'hchsshare@gmail.com', recipients = [email])  
    msg.body = str(otp)  
    mail.send(msg)  

    return render_template("verify.html")

@app.route("/validate", methods=["POST"])
def validate():
    connection = sqlite3.connect("classes.db"); db = connection.cursor()
    db.execute("SELECT * FROM users WHERE users_id = ?", (session["user_id"],))
    rows = db.fetchall()
    
    code = request.form.get("code")
    id = rows[0][0]
    otp = rows[0][5]

    if not code:
        code = 0
    
    if int(code) == int(otp):
        db.execute("UPDATE users SET verified = \"YES\" WHERE users_id = ?", (int(id),))
        connection.commit()
        return render_template("confirmedverified.html")
    else:
        return render_template("notverified.html")
    

    
@app.route("/upload", methods=["GET","POST"])
@login_required
def upload():
    connection = sqlite3.connect("classes.db"); db = connection.cursor()
    db.execute("SELECT * FROM users WHERE users_id = ?", (session["user_id"],))
    rows = db.fetchall()

    verify = rows[0][4]

    if verify == "NO":
        return apology("Unverified User")

    if request.method == "POST":
        period = request.form.get("period")
        weekday = request.form.get("weekday")
        subject = request.form.get("subject")
        
        if not period or not weekday or not subject:
            return apology("Please input required information")
        if weekday not in weekdayList or not period.isdigit():
            return apology("Don't hack the website lol")
        
        weekday = weekday[0:3]

        #Configure database 
        connection = sqlite3.connect("classes.db"); db = connection.cursor()
        #Bad code solution, couldn't figure out how to insert column name with db.execute
        #Number to track the position of weekday in the table
        matchingWeekdayNumber = 0
        if weekday == "Mon":
            db.execute("SELECT * FROM classes WHERE Mon LIKE ? AND Class = ?", ("%"+period+"%",subject))
            matchingWeekdayNumber = tableDict["MONDAY"]
        elif weekday == "Tue":
            db.execute("SELECT * FROM classes WHERE Tue LIKE ? AND Class = ?", ("%"+period+"%",subject))
            matchingWeekdayNumber = tableDict["TUESDAY"]
        elif weekday == "Wed":
            db.execute("SELECT * FROM classes WHERE Wed LIKE ? AND Class = ?", ("%"+period+"%",subject))
            matchingWeekdayNumber = tableDict["WEDNESDAY"]
        elif weekday == "Thu":
            db.execute("SELECT * FROM classes WHERE Thu LIKE ? AND Class = ?", ("%"+period+"%",subject))
            matchingWeekdayNumber = tableDict["THURSDAY"]
        elif weekday == "Fri":
            db.execute("SELECT * FROM classes WHERE Fri LIKE ? AND Class = ?", ("%"+period+"%",subject))
            matchingWeekdayNumber = tableDict["FRIDAY"]
        ans = db.fetchall()
        return render_template("uploadTable.html",rows=ans,rowCount=len(ans), period=period, weekday=weekday, subject=subject, weekdayCount=matchingWeekdayNumber)
    
    
    return render_template("upload.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/thankyou",methods=["POST"])
def thankyou():
    teacher = request.form.get("teacher")
    weekday = request.form.get("weekday")
    period = request.form.get("period")
    formdate = request.form.get("date")

    if not teacher or not weekday or not period or not formdate:
        return apology("Please input required information")

    if formdate > str(date.today()):
        return apology("Sorry! No time travel")
    
    if "filename" not in request.files:
        return apology("Error uploading file")
    file = request.files["filename"]
    if file.filename == '':
        return apology("No selected file")
    if file and allowed_file(file.filename):
        connection = sqlite3.connect("classes.db"); db = connection.cursor()
        db.execute("SELECT * FROM notes ORDER BY notes_id DESC")
        rows = db.fetchall()
        #Notes id is added, this is the most recent file so increment it by one and that'll be this file
        key = rows[0][0]
        
        filename = secure_filename(str(formdate) + "-" + str(teacher) + "-" + str(weekday)  + "-" + str(key+1) + "-" + str(period) + ".pdf")

        db.execute("INSERT INTO notes (uploader_id, filename, date, teacher, weekday, period) VALUES (?, ?,?,?,?,?)", (int(session["user_id"]),filename,formdate,teacher,weekday,period))
        connection.commit()
        
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if weekday == "Mon":
            weekday = 3
        if weekday == "Tue":
            weekday = 4
        if weekday == "Wed":
            weekday = 5
        if weekday == "Thu":
            weekday = 6
        if weekday == "Fri":
            weekday = 7
        return render_template("success", teacher=teacher, period=period, weekday=weekday)
    else:
        return apology("Not a pdf")

if __name__ == "__main__": 
    app.run(debug=True)