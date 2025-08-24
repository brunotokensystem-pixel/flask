from flask import Flask, request, jsonify
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Club Avalanche Command Center").sheet1


def append_to_sheets(row):
    sheet.append_row([
        row.get("task_id", ""),
        row.get("commanded_by", ""),
        row.get("executed_by", ""),
        row.get("action_type", ""),
        row.get("content", ""),
        row.get("status", ""),
        row.get("saved_as", "")
    ])


@app.route("/")
def home():
    return "Bruno Token Automation API is running!"


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.route("/upload", methods=["POST"])
def upload():
    data = request.form or request.json

    task_id = data.get("task_id")
    commanded_by = data.get("commanded_by")
    executed_by = data.get("executed_by")
    action_type = data.get("action_type")
    content = data.get("content")
    status = data.get("status")
    drive_link = data.get("drive_link")
    filename = data.get("filename")

    # Case 1: файл е качен директно
    if "file" in request.files:
        file = request.files["file"]
        filename = file.filename
        saved_as = filename

    # Case 2: даден е Google Drive линк
    elif drive_link:
        saved_as = drive_link

    else:
        return jsonify({"error": "No file or drive_link provided"}), 400

    # Логване в Google Sheets
    row = {
        "task_id": task_id,
        "commanded_by": commanded_by,
        "executed_by": executed_by,
        "action_type": action_type,
        "content": content,
        "status": status,
        "saved_as": saved_as
    }
    append_to_sheets(row)

    return jsonify({
        "status": "success",
        "task_id": task_id,
        "saved_as": saved_as
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
