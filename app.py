from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get("url")
    video_id = data.get("video_id")

    if not url or not video_id:
        return jsonify({"error": "Missing url or video_id"}), 400

    output_path = f"downloads/{video_id}.mp4"
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'mp4',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return jsonify({"status": "success", "file": output_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    return "yt-dlp server is running"

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

