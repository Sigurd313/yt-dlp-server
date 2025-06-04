from flask import Flask, jsonify, request
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
    return "Selenium cookie updater is alive"

@app.route("/refresh-cookies", methods=["POST"])
def refresh_cookies():
    try:
        result = subprocess.run(
            ["python3", "update_cookies_selenium.py"],
            capture_output=True,
            text=True,
            check=True
        )
        return jsonify({"status": "ok", "output": result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": e.stderr, "return_code": e.returncode})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
