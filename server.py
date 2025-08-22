import os, io, json, datetime
from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pytz

app = Flask(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

def get_creds():
    sa_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(sa_json)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def upload_to_drive(filename, filebytes, mimetype, folder_id):
    creds = get_creds()
    drive = build("drive", "v3", credentials=creds)
    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(filebytes), mimetype=mimetype, resumable=False)
    created = drive.files().create(
        body=file_metadata, media_body=media, fields="id,webViewLink"
    ).execute()
    return created

def append_to_sheet(row, sheet_id, range_name):
    creds = get_creds()
    sheets = build("sheets", "v4", credentials=creds)
    body = {"values": [row]}
    return sheets.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/upload")
def upload():
    api_key = request.headers.get("X-API-Key")
    if api_key != os.environ.get("ALLOWED_API_KEY"):
        return jsonify({"error": "Forbidden"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    file_bytes = f.read()
    filename = f.filename or "upload.bin"
    mimetype = f.mimetype or "application/octet-stream"

    task_id = request.form.get("task_id", "AUTO")
    commanded_by = request.form.get("commanded_by", "Costa")
    executed_by = request.form.get("executed_by", "Pepi")
    action_type = request.form.get("action_type", "Content")
    content = request.form.get("content", "")
    status = request.form.get("status", "executed")

    folder_id = os.environ["DRIVE_FOLDER_ID"]
    sheet_id = os.environ["SHEET_ID"]
    sheet_range = os.environ.get("SHEET_RANGE", "Sheet1!A:G")

    created = upload_to_drive(filename, file_bytes, mimetype, folder_id)
    drive_link = created.get("webViewLink", "")

    tz = pytz.timezone("Europe/Sofia")
    ts = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    row = [task_id, commanded_by, executed_by, action_type, content or drive_link, ts, status]
    append_to_sheet(row, sheet_id, sheet_range)

    return jsonify({"ok": True, "drive_link": drive_link})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
