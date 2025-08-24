from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "Bruno Token Automation API is running!"

@app.route("/health")
def health():
    return jsonify({"ok": True})

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400

        file = request.files["file"]
        filename = file.filename

        # Записваме временно файла
        save_path = os.path.join("/tmp", filename)
        file.save(save_path)

        # Тук вместо истинска интеграция с Drive връщаме mock линк
        return jsonify({
            "status": "success",
            "filename": filename,
            "drive_link": f"https://drive.google.com/mock/{filename}",
            "sheet_row": {
                "task_id": request.form.get("task_id"),
                "commanded_by": request.form.get("commanded_by"),
                "executed_by": request.form.get("executed_by"),
                "action_type": request.form.get("action_type"),
                "content": request.form.get("content"),
                "status": request.form.get("status")
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
