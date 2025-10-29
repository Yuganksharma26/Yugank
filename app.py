from flask import Flask, render_template, request, jsonify
import requests
import base64

app = Flask(__name__)

# free demo model (AnimateDiff on HuggingFace)
HF_API_URL = "https://api-inference.huggingface.co/models/TencentARC/AnimateDiff-Lightning"
HF_API_KEY = "your_huggingface_token"  # (we’ll get this in step 2)

headers = {"Authorization": f"Bearer {HF_API_KEY}"}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_video():
    file = request.files["image"]
    if not file:
        return jsonify({"error": "No image uploaded"}), 400

    # encode uploaded image
    b64_image = base64.b64encode(file.read()).decode("utf-8")

    payload = {"inputs": b64_image}
    r = requests.post(HF_API_URL, headers=headers, json=payload)

    if r.status_code != 200:
        return jsonify({"error": f"Request failed: {r.text}"}), 500

    # save output video
    with open("static/output.mp4", "wb") as f:
        f.write(r.content)

    return jsonify({"video_url": "/static/output.mp4"})
