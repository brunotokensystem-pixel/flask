from flask import Flask, request, jsonify

app = Flask(__name__)

# GET /  -> тестов отговор (виждаш, че приложението работи)
@app.route("/", methods=["GET"])
def root():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})

# GET /health  -> за бърз здравен чек
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

# POST /task  -> приемаме JSON и връщаме обратно какво сме получили
@app.route("/task", methods=["POST"])
def task():
    data = request.get_json(silent=True) or {}
    return jsonify({"ok": True, "received": data}), 200

if __name__ == "__main__":
    # локално стартиране; в Railway върви през gunicorn
    app.run(host="0.0.0.0", port=8000)
