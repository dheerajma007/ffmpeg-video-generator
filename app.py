from flask import Flask, request, send_file
import os, base64, subprocess, uuid
import requests

app = Flask(__name__)

@app.route("/generate-video", methods=["POST"])
def generate_video():
    data = request.get_json()
    audio_b64 = data.get("audio")
    image_urls = data.get("images")

    uid = str(uuid.uuid4())
    workdir = f"/tmp/{uid}"
    os.makedirs(workdir, exist_ok=True)

    audio_path = f"{workdir}/audio.mp3"
    with open(audio_path, "wb") as f:
        f.write(base64.b64decode(audio_b64))

    image_paths = []
    for i, url in enumerate(image_urls):
        img_path = f"{workdir}/img{i}.jpg"
        with open(img_path, "wb") as f:
            f.write(requests.get(url).content)
        image_paths.append(img_path)

    # Create FFmpeg input list
    with open(f"{workdir}/input.txt", "w") as f:
        for path in image_paths:
            f.write(f"file '{path}'\nduration 2\n")
        f.write(f"file '{image_paths[-1]}'\n")

    output_path = f"{workdir}/output.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", f"{workdir}/input.txt",
        "-i", audio_path,
        "-c:v", "libx264", "-c:a", "aac",
        "-shortest", output_path
    ], check=True)

    return send_file(output_path, mimetype="video/mp4")
