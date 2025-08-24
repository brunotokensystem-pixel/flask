from flask import Flask, request, jsonify
import os, json, io, datetime
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
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def _now_eest():
    tz = pytz.timezone("Europe/Sofia")
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")

@app.route("/", methods=["GET"])
def root():
    return "Bruno Token Automation API is running!"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/upload", methods=["POST"])
def upload():
    # simple header auth
    required = os.environ.get("ALLOWED_API_KEY", "")
    if required and request.headers.get("X-API-Key") != required:
        return jsonify({"error": "Forbidden"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    filename = f.filename or "upload.bin"
    mimetype = f.mimetype or "application/octet-stream"
    file_bytes = f.read()

    # 1) Upload to Drive
    drive = build("drive", "v3", credentials=_creds())
    folder_id = os.environ["DRIVE_FOLDER_ID"]
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mimetype, resumable=False)
    created = drive.files().create(
        body={"name": filename, "parents": [folder_id]},
        media_body=media,
        fields="id,webViewLink"
    ).execute()
    drive_link = created.get("webViewLink", "")

    # 2) Optional log to Google Sheet
    sheet_id = os.environ.get("SHEET_ID", "")
    if sheet_id:
        sheets = build("sheets", "v4", credentials=_creds())
        rng = os.environ.get("SHEET_RANGE", "Sheet1!A:G")
        row = [[
            request.form.get("task_id", "AUTO"),
            request.form.get("commanded_by", "Costa"),
            request.form.get("executed_by", "Pepi"),
            request.form.get("action_type", "Content"),
            request.form.get("content", drive_link) or drive_link,
            _now_eest(),
            request.form.get("status", "uploaded"),
        ]]
        sheets.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=rng,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": row}
        ).execute()

    return jsonify({"ok": True, "drive_link": drive_link})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
