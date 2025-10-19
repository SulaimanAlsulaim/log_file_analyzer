from flask import Flask, request, render_template_string, redirect, url_for, session, Response
from sqlmodel import SQLModel, Field, Session as DBSession, select, create_engine
from typing import Optional
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Optional: Delete old database during development
if os.path.exists("users.db"):
    os.remove("users.db")

DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)

# Models
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str  # ⚠️ Plain text — use hashing in production

class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: Optional[str] = Field()
    raw_log: Optional[str] = Field()
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

# HTML Templates
HOME_PAGE = '''
<h1>Welcome to the Log Analyzer App</h1>
<p><a href="/signup">Sign Up</a></p>
<p><a href="/signin">Sign In</a></p>
'''

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

UPLOAD_FORM = '''
<h2>Upload CSV or JSON Log File</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=logfile>
  <input type=submit value=Upload>
</form>
<p><a href="/myuploads">View My Uploads</a></p>
'''

# Routes
@app.route('/')
def home():
    return render_template_string(HOME_PAGE)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with DBSession(engine) as db:
            existing = db.exec(select(User).where(User.username == username)).first()
            if existing:
                return "Username already exists."
            user = User(username=username, password=password)
            db.add(user)
            db.commit()
        return redirect(url_for('signin'))
    return render_template_string(SIGNUP_FORM)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with DBSession(engine) as db:
            user = db.exec(select(User).where(User.username == username)).first()
            if user and user.password == password:
                session['user_id'] = user.id
                session['username'] = user.username
                return redirect(url_for('upload_file'))
            return "Invalid credentials."
    return render_template_string(SIGNIN_FORM)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    if request.method == 'POST':
        file = request.files.get('logfile')
        if not file or '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in {'csv', 'json'}:
            return "File type not allowed. Please upload CSV or JSON."
        content = file.read().decode('utf-8')
        log = Log(user_id=session['user_id'], filename=file.filename, raw_log=content)
        with DBSession(engine) as db:
            db.add(log)
            db.commit()
        return redirect(url_for('my_uploads'))
    return render_template_string(UPLOAD_FORM)

@app.route('/myuploads')
def my_uploads():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    with DBSession(engine) as db:
        logs = db.exec(select(Log).where(Log.user_id == session['user_id'])).all()

    html = '<h2>My Uploads</h2><ul>'
    for log in logs:
        html += f'<li>{log.filename} - {log.uploaded_at.strftime("%Y-%m-%d %H:%M")} ' \
                f'<a href="/download/{log.id}">Download</a> | ' \
                f'<a href="/delete/{log.id}">Delete</a></li>'
    html += '</ul><p><a href="/upload">Back to Upload</a></p>'
    return render_template_string(html)

@app.route('/download/<int:log_id>')
def download_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    with DBSession(engine) as db:
        log = db.exec(select(Log).where(Log.id == log_id, Log.user_id == session['user_id'])).first()
        if not log:
            return "File not found or access denied."
        return Response(
            log.raw_log,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment;filename={log.filename}"}
        )

@app.route('/delete/<int:log_id>')
def delete_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    with DBSession(engine) as db:
        log = db.exec(select(Log).where(Log.id == log_id, Log.user_id == session['user_id'])).first()
        if log:
            db.delete(log)
            db.commit()
    return redirect(url_for('my_uploads'))

# Create tables
SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    app.run(debug=True)
