import os

from flask import Flask, render_template, request, session,g, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
app.secret_key = os.urandom(24)

book_id = ""

@app.route("/", methods=['GET', 'POST'])
def index():
	if g.user:
		return redirect(url_for('home'))
	if request.method == 'POST':
		signin()
	return render_template('index.html')

@app.route("/home")
def home():
	if g.user:
		books = db.execute("SELECT * FROM books").fetchall()
		reviews = db.execute("SELECT * FROM reviews").fetchall()
		return render_template("home.html", books=books, reviews=reviews)
	return redirect(url_for('index'))

@app.route("/signin", methods=["POST"])
def signin():
	username = request.form.get("username")
	password = request.form.get("password")
	
	session.pop('user', None)
	if db.execute("SELECT * FROM users WHERE username=:username", {"username":username}).rowcount == 1:
		user = db.execute("SELECT id FROM users WHERE username=:username",{"username":username}).fetchone()
		session['user'] = int(user[0])
		return redirect(url_for('home'))
	return render_template("error.html", message="user does not exists.")

@app.route("/signup", methods=["POST"])
def signup():
	username = request.form.get("username")
	password = request.form.get("password")

	if db.execute("SELECT * FROM users WHERE username=:username", {"username":username}).rowcount != 0:
		return render_template("error.html", message="user alredy exists.")
	db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
		{"username": username, "password": password})
	db.commit()
	return render_template("success.html", message="signed up")

@app.route("/search", methods=["POST"])
def search():
	if g.user:
		id = request.form.get("isbn")
		id = "%" + id + "%"
		title = request.form.get("title")
		title = "%" + title + "%"
		author = request.form.get("author")
		author = "%" + author + "%"
		books = db.execute("SELECT * FROM books WHERE id LIKE :id AND author LIKE :author AND title LIKE :title", {"id":id , "title":title, "author":author}).fetchall()
		reviews = db.execute("SELECT * FROM reviews").fetchall();
		return render_template("books.html", books=books, reviews=reviews)
	return redirect(url_for('index'))

@app.route("/review", methods=["POST"])
def review():
	if g.user:
		text = request.form.get("review")
		rating = int(request.form.get("rating"))
		user_id = 1
		db.execute("INSERT INTO reviews(user_id, book_id, rating, text) VALUES (:user_id, :book_id, :rating, :text)",
			{"user_id":user_id, "book_id":book_id, "rating": rating, "text":text})
		db.commit()
		return render_template("success.html", message="left a review")
	return redirect(url_for('index'))

@app.route("/details", methods=["POST"])
def details():
	if g.user:
		global book_id
		book_id = request.form.get("select")
		book = db.execute("SELECT * FROM books WHERE id=:book_id", {"book_id":book_id}).fetchone()
		reviews = db.execute("SELECT * FROM reviews WHERE book_id=:book_id", {"book_id":book_id}).fetchall()
		return render_template("review.html",book=book, reviews = reviews)
	return redirect(url_for('index'))

@app.route("/dropsession")
def dropsession():
	session.pop('user',None)
	return 'Succesfully logged out!'

@app.before_request
def before_request():
	g.user = None
	if 'user' in session:
		g.user = session['user']

if __name__ == '__main__':
	app.run(debug=True)