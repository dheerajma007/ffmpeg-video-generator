from flask import Flask, request, jsonify, send_file
import os
import requests
import subprocess
import uuid
import tempfile

app = Flask(__name__)
WORKDIR = os.path.join(tempfile.gettempdir(), "ffmpeg_jobs")

os.makedirs(WORKDIR, exist_ok=True)

def download_file(url, file_path):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        with requests.get(url, headers=headers, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Download complete.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download: {e}")

@app.route("/generate-video", methods=["POST"])
def generate_video():
    data = request.get_json()
    audio_url = data["audio_url"]
    frames = data["frames"]  # list of {image_url, duration}

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(WORKDIR, job_id)
    os.makedirs(job_dir)

    # Download audio
    audio_path = os.path.join(job_dir, "audio.mp3")
#    with open(audio_path, "wb") as f:
#        f.write(requests.get(audio_url).content)
    download_file(audio_url, audio_path)

    

    # Download images and prepare input.txt
    input_txt_path = os.path.join(job_dir, "input.txt")
    image_paths = []

    with open(input_txt_path, "w") as input_file:
        for i, frame in enumerate(frames):
            #img_resp = requests.get(frame["image_url"])
            img_path = os.path.join(job_dir, f"img_{i}.jpg")
            #with open(img_path, "wb") as img_file:
            #    img_file.write(img_resp.content)
            download_file(frame["image_url"], img_path)

            image_paths.append(img_path)
            input_file.write(f"file '{img_path}'\n")
            input_file.write(f"duration {frame['duration']}\n")

        # Repeat last frame without duration
        input_file.write(f"file '{image_paths[-1]}'\n")

    with open(input_txt_path, 'r') as f:
        print(f.read())

    # Generate video
    video_path = os.path.join(job_dir, "output.mp4")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", input_txt_path, "-i", audio_path,
        "-c:v", "libx264", "-c:a", "aac", "-vsync", "vfr",
        "-pix_fmt", "yuv420p", video_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)

    print("Video generated")

    # TODO: Upload `video_path` to a file host like transfer.sh, return link
    return send_file(video_path, mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
