from flask import Flask, request, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return "Bruno Token Automation API is running!"

@app.route("/health")
def health():
    return jsonify(ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        # Четем полетата от формата
        task_id = request.form.get("task_id")
        commanded_by = request.form.get("commanded_by")
        executed_by = request.form.get("executed_by")
        action_type = request.form.get("action_type")
        content = request.form.get("content")
        status = request.form.get("status")

        # Четем файла
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Записваме файла
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        return jsonify({
            "status": "success",
            "task_id": task_id,
            "commanded_by": commanded_by,
            "executed_by": executed_by,
            "action_type": action_type,
            "content": content,
            "status_msg": status,
            "saved_as": filepath
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
