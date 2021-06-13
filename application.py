import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from tempfile import mkdtemp
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy


from models import apology, login_required

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config["SECRET_KEY"] = 'TPmi4aLWRbyVq8zu9v82dWYW1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Question(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    
    question = db.Column(db.Text)
    
    answer = db.Column(db.Text)


dbs = SQL("sqlite:///gym.db")

db.init_app(app)

MUSCLES = [
    "Biceps",
    "Triceps",
    "Back",
    "Chest",
    "Legs",
    "Shoulders"
    ]
    

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method=="POST":

        if not request.form.get("username"):
            return ("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return ("must provide password")

        # Query database for username
        rows = dbs.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return ("invalid username and/or password")

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



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method=="POST":

        if not request.form.get("username"):
            return ("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return ("must provide password")

        elif not request.form.get("check"):
            return ("must provide the confirm password")

        elif request.form.get("password") != request.form.get("check"):
            return ("The password and confirm password must match")

        # Query database for username
        rows = dbs.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 0:
            return ("This user already exists")

        password = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        dbs.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), password)

        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/routines", methods =["GET", "POST"])
@login_required
def routines():

    if request.method=="POST":

        if request.form.get("muscle") not in MUSCLES:
            return ("must choice a muscle")

        exercises= dbs.execute("SELECT exercises, description FROM exercises WHERE muscle = ?", request.form.get("muscle"))

        return render_template("routine.html", exercises=exercises)

    else:
        routines = dbs.execute ("SELECT * FROM routine WHERE user_id = ? ", session["user_id"])

        print(routines)

        return render_template("routines.html", routines=routines, muscles=MUSCLES)

@app.route("/makingroutine")
@login_required
def makingroutines():

    if not request.args.getlist("exercises"):
            return ("must select the exercises for the routine")

    print(request.args.getlist("exercises"))

    exercises = request.args.getlist("exercises")

    muscle = dbs.execute("SELECT muscle FROM exercises WHERE exercises = ?", request.args.get("exercises"))

    musc = muscle[0]['muscle']

    for exercise in exercises:
        dbs.execute("INSERT INTO routine (exercises, muscle, user_id) VALUES (?, ?, ?)",
        exercise, musc, session["user_id"])

    return redirect("/routines")


@app.route("/ask", methods=["GET", "POST"])
@login_required
def ask():

    if request.method=="POST":

        if not request.form.get("question"):
            return redirect("/ask")

        question = request.form.get("question")

        question = Question(
            question = question

        )

        db.session.add(question)
        db.session.commit()

        return redirect("/questions")


    else:
        return render_template("ask.html")


@app.route("/unanswered")
@login_required
def unanswered():
    unanswered_questions = Question.query.filter(Question.answer == None).all()


    context = {
        'unanswered_questions' : unanswered_questions
    }

    return render_template('unanswered.html', **context)

@app.route("/answer/<int:question_id>", methods=['GET', 'POST'])
def answer(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        question.answer = request.form['answer']
        db.session.commit()


        return redirect("/answered")



    context = {
        'question' : question
    }

    return render_template('answer.html', **context)


@app.route("/answered")
def answered():
    questions = Question.query.filter(Question.answer != None).all()

    context = {
        'questions' : questions
    }

    return render_template('answered.html', **context)


@app.route("/question/<int:question_id>")
def question(question_id):
    question = Question.query.get_or_404(question_id)

    context = {
        'question' : question
    }

    return render_template('question.html', **context)
