from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import re
import tempfile

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DOWNLOADS = "Downloads"
os.makedirs(DOWNLOADS, exist_ok=True)

def clean_filename(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    try:
        data = request.get_json()
        video_url = data.get("url")

        if not video_url:
            return jsonify({"status": "error", "message": "No URL provided"}), 400

        cookies_content = os.environ.get("YOUTUBE_COOKIES")
        cookiefile_path = None

        if cookies_content:
            with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
                tmp.write(cookies_content)
                cookiefile_path = tmp.name

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(DOWNLOADS, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "noplaylist": True,
        }

        if cookiefile_path:
            ydl_opts["cookiefile"] = cookiefile_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get("title", "audio")
            filename = clean_filename(title) + ".mp3"

        if cookiefile_path:
            os.remove(cookiefile_path)

        return jsonify({"status": "success", "file": filename, "title": title})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get-file/<filename>")
def get_file(filename):
    file_path = os.path.join(DOWNLOADS, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename, mimetype="audio/mpeg")
    return jsonify({"status": "error", "message": "File not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
