# --- Bruno Token Pepi Uploader (central main.py) ---
import os, io, json, datetime
from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pytz

app = Flask(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

def _creds():
    sa_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(sa_json)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def _drive_upload(file_bytes, filename, mimetype, folder_id):
    drive = build("drive", "v3", credentials=_creds())
    metadata = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mimetype, resumable=False)
    created = drive.files().create(
        body=metadata, media_body=media, fields="id,webViewLink"
    ).execute()
    return created  # {id, webViewLink}

def _sheet_append(row):
    sheets = build("sheets", "v4", credentials=_creds())
    sheet_id = os.environ["SHEET_ID"]
    rng = os.environ.get("SHEET_RANGE", "Sheet1!A:G")
    body = {"values": [row]}
    sheets.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=rng,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

def _now_eest():
    tz = pytz.timezone("Europe/Sofia")
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Pepi Uploader is running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/api/task", methods=["POST"])
def api_task():
    data = request.get_json(silent=True) or {}
    return jsonify({"status": "success", "received": data}), 200

@app.route("/upload", methods=["POST"])
def upload():
    # прост header ключ
    required = os.environ.get("ALLOWED_API_KEY", "")
    if required and request.headers.get("X-API-Key") != required:
        return jsonify({"error": "Forbidden"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    filename = f.filename or "upload.bin"
    mimetype = f.mimetype or "application/octet-stream"
    file_bytes = f.read()

    # 1) Drive upload
    folder_id = os.environ["DRIVE_FOLDER_ID"]
    created = _drive_upload(file_bytes, filename, mimetype, folder_id)
    drive_link = created.get("webViewLink", "")

    # 2) Sheets log
    task_id      = request.form.get("task_id", "AUTO")
    commanded_by = request.form.get("commanded_by", "Costa")
    executed_by  = request.form.get("executed_by", "Pepi")
    action_type  = request.form.get("action_type", "Content")
    content      = request.form.get("content", "") or drive_link
    status       = request.form.get("status", "uploaded")
    ts = _now_eest()
    _sheet_append([task_id, commanded_by, executed_by, action_type, content, ts, status])

    return jsonify({"ok": True, "drive_link": drive_link})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
