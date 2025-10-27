from flask import Flask, request, render_template, redirect, url_for, session, Response
from sqlmodel import SQLModel, Session as DBSession, select, create_engine
from models import User, Log
from auth import auth_bp
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.register_blueprint(auth_bp)

DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)

if not os.path.exists("users.db"):
    SQLModel.metadata.create_all(engine)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

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
    return render_template("upload.html")

@app.route('/myuploads')
def my_uploads():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        logs = db.exec(select(Log).where(Log.user_id == session['user_id'])).all()
    return render_template("myuploads.html", logs=logs)

@app.route('/download/<int:log_id>')
def download_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        log = db.exec(select(Log).where(Log.id == log_id, Log.user_id == session['user_id'])).first()
        if not log:
            return "File not found or access denied."
        return Response(log.raw_log, mimetype="text/plain", headers={"Content-Disposition": f"attachment;filename={log.filename}"})

@app.route('/delete/<int:log_id>')
def delete_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        log = db.exec(select(Log).where(Log.id == log_id, Log.user_id == session['user_id'])).first()
        if log:
            db.delete(log)
            db.commit()
    return redirect(url_for('my_uploads'))

@app.route('/sign')
def sign():
    return render_template('sign.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    return render_template('dashboard.html')

@app.route('/analysis_result')
def analysis_result():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    return render_template('analysis_result.html')






   
if __name__ == "__main__":
    app.run(debug=True)

