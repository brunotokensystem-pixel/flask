from flask import Flask, request, jsonify

app = Flask(__name__)

# Home route
@app.route("/", methods=["GET"])
def home():
    return "Bruno Token Automation API is running!"

# Task API
@app.route("/api/task", methods=["POST"])
def handle_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    # Log the received task
    print("Received Task:", data)

    # Example response
    return jsonify({
        "status": "success",
        "received": data
    }), 200

# Upload API (for test file uploads)
@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save file temporarily
    filepath = f"/tmp/{file.filename}"
    file.save(filepath)

    return jsonify({
        "status": "uploaded",
        "filename": file.filename,
        "path": filepath
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
