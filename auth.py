from flask import Blueprint, request, render_template, redirect, url_for, session
from sqlmodel import Session, select
from sqlalchemy import or_
from models import User, engine

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        with Session(engine) as db:
            if db.exec(select(User).where(User.username == username)).first():
                return "Username already exists."
            if db.exec(select(User).where(User.email == email)).first():
                return "Email already registered."
            db.add(User(username=username, email=email, password=password))
            db.commit()
        return redirect(url_for('auth.signin'))
    return render_template("signup.html")

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        login_input = request.form['username']  # could be username or email
        password = request.form['password']

        with Session(engine) as db:
            user = db.exec(
                select(User).where(
                    or_(User.username == login_input, User.email == login_input)
                )
            ).first()

            if user and user.password == password:
                session['user_id'] = user.id
                session['username'] = user.username
                return redirect(url_for('upload_file'))

            return "Invalid credentials."
    return render_template("signin.html")
