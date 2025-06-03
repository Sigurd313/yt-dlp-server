from flask import Flask, request, jsonify
import subprocess
import os
import yt_dlp

app = Flask(__name__)

# Путь к cookies.txt
COOKIES_PATH = os.path.join(os.getcwd(), "cookies.txt")


@app.route("/download", methods=["POST"])
def download():
    try:
        data = request.get_json()
        url = data["url"]
        video_id = data["video_id"]

        output_path = f"downloads/{video_id}.mp4"

        ydl_opts = {
            "outtmpl": output_path,
            "cookiefile": COOKIES_PATH,
            "quiet": True,
            "no_warnings": True,
            "format": "mp4",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return jsonify({"status": "success", "file": output_path})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/refresh-cookies", methods=["POST"])
def refresh_cookies():
    try:
        # Запускаем selenium-скрипт
        result = subprocess.run(
            ["python3", "update_cookies_selenium.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        return jsonify({
            "status": "ok",
            "message": "cookies.txt updated",
            "log": result.stdout
        })

    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "message": e.stderr or str(e)
        }), 500


@app.route("/", methods=["GET"])
def index():
    return "✅ yt-dlp-server is live"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
