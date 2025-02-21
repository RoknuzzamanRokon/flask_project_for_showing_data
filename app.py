from flask import Flask, render_template
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager, login_user
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
load_dotenv()

# Database connection details
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)


DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
engine = create_engine(DATABASE_URL)

app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Create a scoped session
Session = scoped_session(sessionmaker(bind=engine))
db_session = Session()


# Flask login setup
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        query = text("SELECT id, username, password FROM users WHERE id = :id")
        result = db_session.execute(query, {"id": user_id}).fetchone()
        if result:
            return User(*result)
        return None
    
    @staticmethod
    def find_by_username(username):
        query = text("SELECT id, username, password FROM users WHERE username = :username")
        result = db_session.execute(query, {"username": username}).fetchone()
        if result:
            return User(*result)
        return None
    
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

from flask import request, flash, redirect, url_for

@app.route('/register', methods=['GET', 'POST'])
def register():
    print("hii")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        query = text("INSERT INTO users (username, password) VALUES (:username, :password)")
        try:
            db_session.execute(query, {"username": username, "password": hashed_password})
            db_session.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash("Registration failed! Please try again.", "danger")
            return redirect(url_for('register'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.find_by_username(username)

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "danger")
    
    return render_template("login.html")



if __name__ == '__main__':
    app.run(debug=True, port=2424)
