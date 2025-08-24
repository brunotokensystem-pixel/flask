from flask import Flask, request, jsonify
import os, io, json, datetime, re
import pytz

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

app = Flask(__name__)

# ---- ENV ----
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
SA_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")
SHEET_ID = os.environ.get("SHEET_ID", "")
SHEET_RANGE = os.environ.get("SHEET_RANGE", "Sheet1!A:G")
API_KEY_REQUIRED = os.environ.get("ALLOWED_API_KEY", "")

def creds():
    return service_account.Credentials.from_service_account_info(SA_INFO, scopes=SCOPES)

def now_eest():
    tz = pytz.timezone("Europe/Sofia")
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")

def append_row(row):
    if not SHEET_ID:
        return
    svc = build("sheets", "v4", credentials=creds())
    body = {"values": [row]}
    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=SHEET_RANGE,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

def upload_to_drive(filename:str, data:bytes, mimetype:str) -> str:
    if not DRIVE_FOLDER_ID:
        raise RuntimeError("DRIVE_FOLDER_ID is not set")
    drv = build("drive", "v3", credentials=creds())
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mimetype or "application/octet-stream", resumable=False)
    created = drv.files().create(
        body={"name": filename, "parents": [DRIVE_FOLDER_ID]},
        media_body=media,
        fields="id,webViewLink"
    ).execute()
    return created.get("webViewLink", "")

def extract_drive_id(link:str) -> str:
    """
    Поддържа формати:
    https://drive.google.com/file/d/<ID>/view
    https://drive.google.com/open?id=<ID>
    """
    m = re.search(r'/file/d/([A-Za-z0-9_\-]+)/', link) or re.search(r'[?&]id=([A-Za-z0-9_\-]+)', link)
    return m.group(1) if m else ""

def normalize_drive_link(file_id:str) -> str:
    return f"https://drive.google.com/file/d/{file_id}/view"

@app.get("/")
def root():
    return "Bruno Token Automation API is running!"

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/upload")
def upload():
    # Header auth
    if API_KEY_REQUIRED and request.headers.get("X-API-Key") != API_KEY_REQUIRED:
        return jsonify({"status": "error", "code": 403, "message": "Forbidden"}), 403

    # Данни от form или json
    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}
    # Подсигуряваме, че form полетата (ако са multipart) се четат също
    def g(key, default=None):
        return request.form.get(key) if key in request.form else data.get(key, default)

    task_id      = g("task_id", "AUTO")
    commanded_by = g("commanded_by", "Costa")
    executed_by  = g("executed_by", "Pepi")
    action_type  = g("action_type", "Content")
    content      = g("content", "")
    status       = g("status", "uploaded")

    drive_link_payload = g("drive_link", "").strip()

    try:
        drive_link = ""
        filename   = ""

        # Режим 1: multipart файл
        if "file" in request.files and request.files["file"].filename:
            f = request.files["file"]
            filename = f.filename
            mimetype = f.mimetype or "application/octet-stream"
            data_bytes = f.read()
            drive_link = upload_to_drive(filename, data_bytes, mimetype)

        # Режим 2: JSON с drive_link (не качваме, само валидираме/логваме)
        elif drive_link_payload:
            file_id = extract_drive_id(drive_link_payload)
            if not file_id:
                return jsonify({"status": "error", "code": 400, "message": "Invalid drive_link"}), 400
            # проверка за достъпност (опционална)
            try:
                drv = build("drive", "v3", credentials=creds())
                meta = drv.files().get(fileId=file_id, fields="id, name, webViewLink").execute()
                filename = meta.get("name", "file")
                drive_link = meta.get("webViewLink") or normalize_drive_link(file_id)
            except HttpError as e:
                return jsonify({"status": "error", "code": 403, "message": f"Drive access error: {e}"}), 403

        else:
            return jsonify({"status": "error", "code": 400, "message": "No file or drive_link provided"}), 400

        # Лог в Sheets
        append_row([
            task_id,
            commanded_by,
            executed_by,
            action_type,
            content or drive_link,
            now_eest(),
            status
        ])

        return jsonify({
            "status": "success",
            "task_id": task_id,
            "filename": filename,
            "drive_link": drive_link
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "code": 500, "message": str(e)}), 500
