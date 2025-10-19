from flask import Blueprint, request, render_template_string, redirect, url_for, session
from sqlmodel import Session, select
from models import User, engine

auth_bp = Blueprint('auth', __name__)

SIGNUP_FORM = '''
<h2>Sign Up</h2>
<form method="post">
  Username: <input type="text" name="username"><br>
  Password: <input type="password" name="password"><br>
  <input type="submit" value="Sign Up">
</form>
'''

SIGNIN_FORM = '''
<h2>Sign In</h2>
<form method="post">
  Username: <input type="text" name="username"><br>
  Password: <input type="password" name="password"><br>
  <input type="submit" value="Sign In">
</form>
'''

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with Session(engine) as db:
            existing = db.exec(select(User).where(User.username == username)).first()
            if existing:
                return "Username already exists."
            db.add(User(username=username, password=password))
            db.commit()
        return redirect(url_for('auth.signin'))
    return render_template_string(SIGNUP_FORM)

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with Session(engine) as db:
            user = db.exec(select(User).where(User.username == username)).first()
            if user and user.password == password:
                session['user_id'] = user.id
                session['username'] = user.username
                return redirect(url_for('upload.upload_file'))
            return "Invalid credentials."
    return render_template_string(SIGNIN_FORM)
