from flask import Flask, request, render_template, redirect, url_for, session, Response
from sqlmodel import SQLModel, Session as DBSession, select, create_engine
from models import User, Upload
from auth import auth_bp
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.register_blueprint(auth_bp)

DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)

if not os.path.exists("users.db"):
    SQLModel.metadata.create_all(engine)


# ------------------------------
# Home Page
# ------------------------------
@app.route('/')
def home():
    return render_template("home.html")


# ------------------------------
# Upload Page
# ------------------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    if request.method == 'POST':
        file = request.files.get('logfile')
        if not file or '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in {'csv', 'json'}:
            return "File type not allowed. Please upload CSV or JSON."

        content = file.read().decode('utf-8')
        filesize = len(content.encode('utf-8'))

        upload = Upload(
            user_id=session['user_id'],
            filename=file.filename,
            raw_log=content,
            filesize=filesize
        )
        with DBSession(engine) as db:
            db.add(upload)
            db.commit()

        return redirect(url_for('my_uploads'))

    return render_template("upload.html")


# ------------------------------
# My Uploads
# ------------------------------
@app.route('/myuploads')
def my_uploads():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        uploads = db.exec(select(Upload).where(Upload.user_id == session['user_id'])).all()

    return render_template("myuploads.html", uploads=uploads)


# ------------------------------
# Download Uploaded File
# ------------------------------
@app.route('/download/<int:upload_id>')
def download_upload(upload_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        upload = db.exec(select(Upload).where(Upload.id == upload_id, Upload.user_id == session['user_id'])).first()
        if not upload:
            return "File not found or access denied."

        return Response(
            upload.raw_log,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment;filename={upload.filename}"}
        )


# ------------------------------
# Delete Uploaded File
# ------------------------------
@app.route('/delete/<int:upload_id>')
def delete_upload(upload_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        upload = db.exec(select(Upload).where(Upload.id == upload_id, Upload.user_id == session['user_id'])).first()
        if upload:
            db.delete(upload)
            db.commit()

    return redirect(url_for('my_uploads'))


# ------------------------------
# Sign Page
# ------------------------------
@app.route('/sign')
def sign():
    return render_template('sign.html')


# ------------------------------
# Dashboard Page
# ------------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    return render_template('dashboard.html')


# ------------------------------
# Analysis Result Page
# ------------------------------
@app.route('/analysis_result')
def analysis_result():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        uploads = db.exec(select(Upload).where(Upload.user_id == session['user_id'])).all()

    return render_template('analysis_result.html', uploads=uploads)


# ------------------------------
# Single Analysis View
# ------------------------------
@app.route('/analysis_result/<int:upload_id>')
def show_analysis(upload_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        upload = db.exec(select(Upload).where(Upload.id == upload_id, Upload.user_id == session['user_id'])).first()
        if not upload:
            return "Analysis not found or access denied."

    power_bi_embed_url = f"https://app.powerbi.com/view?r=EXAMPLE_EMBED_ID_FOR_{upload.id}"

    return render_template('analysis_view.html', upload=upload, power_bi_embed_url=power_bi_embed_url)


# ------------------------------
# Run App
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)
