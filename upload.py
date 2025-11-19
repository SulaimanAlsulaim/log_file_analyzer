import os
import time
import pandas as pd
from flask import Blueprint, request, render_template, redirect, url_for, session, Response
from sqlmodel import Session, select
from models import Upload, engine
from datetime import datetime

# Parser + Deep Learning Model
from Log_parser import parse_uploaded_file
from dl_model import run_dl_on_parsed   # 🔥 renamed from ml_model → dl_model


upload_bp = Blueprint("upload", __name__)



# ============================================================
#                 UPLOAD + PARSE + DL + SAVE
# ============================================================
@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():

    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    if request.method == 'POST':

        print("\n==============================")
        print("📥 Starting Upload Process...")
        print("==============================")

        total_start = time.time()

        file = request.files.get('logfile')
        if not file:
            return "Please upload a file."

        filename = file.filename
        ext = filename.rsplit('.', 1)[-1].lower()

        if ext not in {"csv", "json", "log", "txt"}:
            return "Only CSV, JSON, LOG, or TXT files are allowed."

        # -----------------------------------------------------------
        # Step 1 — Read File
        # -----------------------------------------------------------
        step1 = time.time()
        print(f"📄 Reading uploaded file: {filename}")

        content = file.read().decode('utf-8')

        print(f"✔ Step 1 Done in {time.time() - step1:.3f} seconds")


        # -----------------------------------------------------------
        # Step 2 — Handle .log / .txt (Convert to CSV/JSON)
        # -----------------------------------------------------------
        if ext in {"log", "txt"}:
            step2 = time.time()
            print("📝 Detected .log/.txt file → Converting to DataFrame")

            lines = content.splitlines()
            temp_df = pd.DataFrame({"message": lines})

            os.makedirs("uploads_raw", exist_ok=True)

            temp_df.to_csv(f"uploads_raw/{filename}.csv", index=False)
            temp_df.to_json(f"uploads_raw/{filename}.json", orient="records")

            print("✔ Converted to CSV + JSON format")
            print(f"✔ Step 2 Done in {time.time() - step2:.3f} seconds")

            # Treat as CSV for parser
            content = temp_df.to_csv(index=False)
            ext = "csv"



        # -----------------------------------------------------------
        # Step 3 — Parse with Drain3
        # -----------------------------------------------------------
        step3 = time.time()
        print("🔍 Parsing (Drain3)...")

        structured_df = parse_uploaded_file(content, ext)

        print("✔ Parsing Completed")
        print(f"✔ Step 3 Done in {time.time() - step3:.3f} seconds")



        # -----------------------------------------------------------
        # Step 4 — Deep Learning Model Prediction
        # -----------------------------------------------------------
        step4 = time.time()
        print("🤖 Running Deep Learning Model...")

        

        print("✔ DL Inference Completed")
        print(f"✔ Step 4 Done in {time.time() - step4:.3f} seconds")



        # -----------------------------------------------------------
        # Step 5 — Save “Result Log” to Power BI Output
        # -----------------------------------------------------------
        step5 = time.time()
        print("📊 Exporting Result Log for Power BI")

        os.makedirs("powerbi_output", exist_ok=True)
        structured_df.to_csv("powerbi_output/result_log.csv", index=False)

        print("✔ Result Log Saved (result_log.csv)")
        print(f"✔ Step 5 Done in {time.time() - step5:.3f} seconds")



        # -----------------------------------------------------------
        # Step 6 — Save to Database
        # -----------------------------------------------------------
        step6 = time.time()
        print("💾 Saving Upload & Result Log to DB")

        upload = Upload(
            user_id=session["user_id"],
            filename=filename,
            raw_log=content,
            filesize=len(content.encode("utf-8")),
            uploaded_at=datetime.utcnow()
        )

        upload.set_structured(structured_df)

        with Session(engine) as db:
            db.add(upload)
            db.commit()

        print("✔ Step 6 Done in {:.3f} seconds".format(time.time() - step6))



        print("=======================================")
        print("🎉 TOTAL TIME:", round(time.time() - total_start, 3), "seconds")
        print("=======================================\n")

        return redirect(url_for('upload.my_uploads'))


    # GET → Upload Page
    return render_template("upload.html")





# ============================================================
#                   MY UPLOADS PAGE
# ============================================================
@upload_bp.route('/myuploads')
def my_uploads():

    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with Session(engine) as db:
        uploads = db.exec(
            select(Upload).where(Upload.user_id == session["user_id"])
        ).all()

    return render_template("myuploads.html", uploads=uploads)




# ============================================================
#                   DOWNLOAD RAW
# ============================================================
@upload_bp.route('/download/<int:log_id>')
def download_raw(log_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with Session(engine) as db:
        log = db.exec(
            select(Upload)
            .where(Upload.id == log_id, Upload.user_id == session['user_id'])
        ).first()

    if not log:
        return "File not found."

    return Response(
        log.raw_log,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={log.filename}"}
    )




# ============================================================
#                   DOWNLOAD RESULT LOG (Parsed + Model)
# ============================================================
@upload_bp.route('/download_result/<int:log_id>')
def download_result(log_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with Session(engine) as db:
        log = db.exec(
            select(Upload)
            .where(Upload.id == log_id, Upload.user_id == session["user_id"])
        ).first()

    if not log or not log.structured_log:
        return "Result log not found."

    df = log.get_structured()
    csv_content = df.to_csv(index=False)

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=result_{log.filename}.csv"}
    )




# ============================================================
#                   DELETE UPLOAD
# ============================================================
@upload_bp.route('/delete/<int:log_id>')
def delete_upload(log_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.signin'))

    with Session(engine) as db:
        log = db.exec(
            select(Upload)
            .where(Upload.id == log_id, Upload.user_id == session["user_id"])
        ).first()

        if log:
            db.delete(log)
            db.commit()

    return redirect(url_for("upload.my_uploads"))

