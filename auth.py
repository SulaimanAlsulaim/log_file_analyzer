from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from sqlmodel import Session, select
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, engine
import re


auth_bp = Blueprint('auth', __name__)

# ✅ Password strength validator
def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""


# ✅ Signup route
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        if not password:
            flash("Password is required.", "error")
            return render_template("signup.html")

        valid, message = is_strong_password(password)
        if not valid:
            flash(message, "error")
            return render_template("signup.html")

        with Session(engine) as db:
            if db.exec(select(User).where(User.username == username)).first():
                flash("Username already exists.", "error")
                return render_template("signup.html")

            if db.exec(select(User).where(User.email == email)).first():
                flash("Email already registered.", "error")
                return render_template("signup.html")

            hashed = generate_password_hash(password)
            db.add(User(username=username, email=email, password=hashed))
            db.commit()

        # ❌ No success message shown
        return redirect(url_for('auth.signin'))

    return render_template("signup.html")


# ✅ Signin route
@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        login_input = request.form['username'].strip()
        password = request.form['password']

        with Session(engine) as db:
            user = db.exec(
                select(User).where(
                    or_(User.username == login_input, User.email == login_input)
                )
            ).first()

            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                return redirect(url_for('dashboard'))

            flash("Invalid username/email or password.", "error")

    return render_template("signin.html")


# ✅ Signout route
@auth_bp.route('/signout')
def signout():
    session.clear()
    flash("Signed out successfully.", "success")
    return redirect(url_for('home'))


# ✅ Edit Profile route
@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with Session(engine) as db:
        user = db.get(User, session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.signin'))

        if request.method == 'POST':
            current_password = request.form.get('current_password', '')
            new_username = request.form.get('username', '').strip()
            new_email = request.form.get('email', '').strip().lower()
            new_password = request.form.get('new_password', '').strip()

            # Verify current password
            if not check_password_hash(user.password, current_password):
                flash("Current password is incorrect.", "error")
                return render_template('edit_profile.html', user=user)

            # Update username
            if new_username:
                existing = db.exec(select(User).where(User.username == new_username, User.id != user.id)).first()
                if existing:
                    flash("Username already taken.", "error")
                    return render_template('edit_profile.html', user=user)
                user.username = new_username

            # Update email
            if new_email:
                existing = db.exec(select(User).where(User.email == new_email, User.id != user.id)).first()
                if existing:
                    flash("Email already in use.", "error")
                    return render_template('edit_profile.html', user=user)
                user.email = new_email

            # Update password (if provided)
            if new_password:
                valid, message = is_strong_password(new_password)
                if not valid:
                    flash(message, "error")
                    return render_template('edit_profile.html', user=user)

                user.password = generate_password_hash(new_password)

            db.add(user)
            db.commit()
            session['username'] = user.username

            # ✅ Stay on the same page and show success message above form
            flash("Profile updated successfully.", "success")
            return render_template('edit_profile.html', user=user)

    return render_template('edit_profile.html', user=user)
