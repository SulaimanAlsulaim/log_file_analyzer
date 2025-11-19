from flask import Flask, request, render_template, redirect, url_for, session, Response
from sqlmodel import SQLModel, Session as DBSession, select, create_engine
from models import User, Upload
from auth import auth_bp
from upload import upload_bp          # Import upload blueprint
from datetime import datetime
import os
import pandas as pd
import io
import json

# ------------------------------------------
# Flask Setup
# ------------------------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)

# Database
DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)

if not os.path.exists("users.db"):
    SQLModel.metadata.create_all(engine)

# ------------------------------------------
# Drain3 (Used for analysis pages only)
# ------------------------------------------
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.file_persistence import FilePersistence

STATE_FILE = "drain3_state.bin"

def build_template_miner(state_path=STATE_FILE):
    cfg = TemplateMinerConfig()
    cfg.profiling_enabled = False
    cfg.drain_sim_th = 0.4
    cfg.drain_depth = 4
    cfg.drain_max_children = 100
    cfg.drain_max_clusters = 20000
    cfg.drain_extra_delimiters = ";,()"
    cfg.drain_param_str = "<*>"

    folder = os.path.dirname(state_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    persistence = FilePersistence(state_path)
    return TemplateMiner(persistence, cfg)

def parse_log_lines(lines, tm):
    rows = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        result = tm.add_log_message(line)
        rows.append({
            "LineId": i,
            "Content": line,
            "EventId": result["cluster_id"],
            "EventTemplate": result["template_mined"]
        })
    return pd.DataFrame(rows)

# ------------------------------------------
# Home Page
# ------------------------------------------
@app.route('/')
def home():
    return render_template("home.html")

# ------------------------------------------
# My Uploads Page
# ------------------------------------------
@app.route('/myuploads')
def my_uploads():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        uploads = db.exec(
            select(Upload).where(Upload.user_id == session['user_id'])
        ).all()

    return render_template("myuploads.html", uploads=uploads)

# ------------------------------------------
# Download Raw Log
# ------------------------------------------
@app.route('/download/<int:upload_id>')
def download_upload(upload_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        upload = db.exec(
            select(Upload)
            .where(Upload.id == upload_id, Upload.user_id == session['user_id'])
        ).first()

    if not upload:
        return "File not found."

    return Response(
        upload.raw_log,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={upload.filename}"}
    )

# ------------------------------------------
# Download Structured CSV
# ------------------------------------------
@app.route('/download_structured/<int:upload_id>')
def download_structured(upload_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        upload = db.exec(
            select(Upload)
            .where(Upload.id == upload_id, Upload.user_id == session['user_id'])
        ).first()

    if not upload or not upload.structured_log:
        return "No structured log found."

    df = upload.get_structured()
    csv_content = df.to_csv(index=False)

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=structured_{upload.filename}.csv"}
    )

# ------------------------------------------
# Delete Uploaded File
# ------------------------------------------
@app.route('/delete/<int:upload_id>')
def delete_upload(upload_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        upload = db.exec(
            select(Upload)
            .where(Upload.id == upload_id, Upload.user_id == session['user_id'])
        ).first()

        if upload:
            db.delete(upload)
            db.commit()

    return redirect(url_for('my_uploads'))

# ------------------------------------------
# Sign-in Page
# ------------------------------------------
@app.route('/sign')
def sign():
    return render_template('sign.html')

# ------------------------------------------
# Dashboard Page
# ------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))
    return render_template('dashboard.html')

# ------------------------------------------
# Analysis Result (List View)
# ------------------------------------------
@app.route('/analysis_result')
def analysis_result():
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        uploads = db.exec(
            select(Upload).where(Upload.user_id == session['user_id'])
        ).all()

    return render_template('analysis_result.html', uploads=uploads)

# ------------------------------------------
# Individual Log Analysis View
# ------------------------------------------
@app.route('/analysis_result/<int:upload_id>')
def show_analysis(upload_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with DBSession(engine) as db:
        upload = db.exec(
            select(Upload)
            .where(Upload.id == upload_id, Upload.user_id == session['user_id'])
        ).first()

    if not upload:
        return "Analysis not found."

    power_bi_embed_url = f"https://app.powerbi.com/view?r=EXAMPLE_EMBED_ID_FOR_{upload.id}"

    return render_template(
        'analysis_view.html',
        upload=upload,
        power_bi_embed_url=power_bi_embed_url
    )

# ------------------------------------------

# ------------------------------------------
# Run App
# ------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
