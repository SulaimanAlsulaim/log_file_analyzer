from flask import Blueprint, request, render_template_string, redirect, url_for, session, Response
from sqlmodel import Session, select
from models import Log, engine
from datetime import datetime

upload_bp = Blueprint('upload', __name__)

UPLOAD_FORM = '''
<h2>Upload CSV or JSON Log File</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=logfile>
  <input type=submit value=Upload>
</form>
<p><a href="/myuploads">View My Uploads</a></p>
'''

@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    if request.method == 'POST':
        file = request.files.get('logfile')
        if not file or '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in {'csv', 'json'}:
            return "File type not allowed."
        content = file.read().decode('utf-8')
        log = Log(user_id=session['user_id'], filename=file.filename, raw_log=content, uploaded_at=datetime.utcnow())
        with Session(engine) as db:
            db.add(log)
            db.commit()
        return redirect(url_for('upload.my_uploads'))
    return render_template_string(UPLOAD_FORM)

@upload_bp.route('/myuploads')
def my_uploads():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with Session(engine) as db:
        logs = db.exec(select(Log).where(Log.user_id == session['user_id'])).all()

    html = '<h2>My Uploads</h2><ul>'
    for log in logs:
        html += f'<li>{log.filename} - {log.uploaded_at.strftime("%Y-%m-%d %H:%M")} ' \
                f'<a href="/download/{log.id}">Download</a> | ' \
                f'<a href="/delete/{log.id}">Delete</a></li>'
    html += '</ul><p><a href="/upload">Back to Upload</a></p>'
    return render_template_string(html)

@upload_bp.route('/download/<int:log_id>')
def download_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with Session(engine) as db:
        log = db.exec(select(Log).where(Log.id == log_id, Log.user_id == session['user_id'])).first()
        if not log:
            return "File not found."
        return Response(log.raw_log, mimetype="text/plain",
                        headers={"Content-Disposition": f"attachment;filename={log.filename}"})

@upload_bp.route('/delete/<int:log_id>')
def delete_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with Session(engine) as db:
        log = db.exec(select(Log).where(Log.id == log_id, Log.user_id == session['user_id'])).first()
        if log:
            db.delete(log)
            db.commit()
    return redirect(url_for('upload.my_uploads'))
