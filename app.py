import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Убедиться, что папка downloads существует
if not os.path.exists("downloads"):
    os.makedirs("downloads")

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    video_url = data.get("url")
    video_id = data.get("video_id")

    if not video_url or not video_id:
        return jsonify({"status": "error", "message": "Missing url or video_id"}), 400

    output_path = f"downloads/{video_id}.mp4"
    cmd = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "-o", output_path,
        video_url,
    ]

    try:
        subprocess.run(cmd, check=True)
        return jsonify({"status": "success", "file": output_path})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/refresh-cookies", methods=["POST"])
def refresh_cookies():
    try:
        subprocess.run(["python3", "update_cookies.py"], check=True)
        return jsonify({"status": "success", "message": "Cookies updated"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
