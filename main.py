@app.route("/upload", methods=["POST"])
def upload():
    try:
        if 'file' in request.files:
            file = request.files['file']
            filename = file.filename
            saved_as = f"uploaded/{filename}"
            file.save(saved_as)
        else:
            data = request.get_json()
            if not data or "drive_link" not in data:
                return jsonify({"error": "No file or drive_link provided"}), 400
            filename = data.get("filename", "no_name")
            saved_as = data["drive_link"]

        row = {
            "task_id": request.form.get("task_id") or data.get("task_id"),
            "commanded_by": request.form.get("commanded_by") or data.get("commanded_by"),
            "executed_by": request.form.get("executed_by") or data.get("executed_by"),
            "action_type": request.form.get("action_type") or data.get("action_type"),
            "content": request.form.get("content") or data.get("content"),
            "status": request.form.get("status") or data.get("status"),
            "filename": filename,
            "saved_as": saved_as
        }
        sheet.append_row(list(row.values()))
        return jsonify({"status": "success", "row": row})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
