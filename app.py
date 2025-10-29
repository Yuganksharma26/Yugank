import os
import json
import uuid
import threading
from time import sleep
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Config
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
JOBS_FILE = os.path.join(os.getcwd(), 'jobs.json')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp'}
MOCK_VIDEO = "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# ensure jobs file
if not os.path.exists(JOBS_FILE):
    with open(JOBS_FILE, 'w') as f:
        json.dump({}, f)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def load_jobs():
    with open(JOBS_FILE, 'r') as f:
        return json.load(f)

def save_jobs(j):
    with open(JOBS_FILE, 'w') as f:
        json.dump(j, f, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def simulate_generation(job_id, filename):
    """Simulate a long-running generation task; replace this with real AI provider calls."""
    jobs = load_jobs()
    jobs[job_id]['status'] = 'processing'
    save_jobs(jobs)

    # simulate processing time (progress updates)
    steps = [1, 2, 3, 4]  # progress steps
    for i, s in enumerate(steps):
        sleep(1.5)  # wait a bit
        jobs = load_jobs()
        jobs[job_id]['progress'] = int(((i + 1) / len(steps)) * 100)
        save_jobs(jobs)

    # mark done and attach mock result
    jobs = load_jobs()
    jobs[job_id]['status'] = 'done'
    jobs[job_id]['result_url'] = MOCK_VIDEO
    jobs[job_id]['progress'] = 100
    save_jobs(jobs)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/result/<job_id>')
def result_page(job_id):
    jobs = load_jobs()
    job = jobs.get(job_id)
    if not job:
        return "Job not found", 404
    return render_template('result.html', job=job, job_id=job_id)

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'image' not in request.files:
        return jsonify({'ok': False, 'error': 'no file part'}), 400
    f = request.files['image']
    if f.filename == '':
        return jsonify({'ok': False, 'error': 'no file selected'}), 400
    if not allowed_file(f.filename):
        return jsonify({'ok': False, 'error': 'invalid file type'}), 400

    fn = secure_filename(f.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4().hex}_{fn}")
    f.save(save_path)

    # create job
    job_id = uuid.uuid4().hex
    jobs = load_jobs()
    jobs[job_id] = {
        'id': job_id,
        'filename': os.path.basename(save_path),
        'original_name': fn,
        'status': 'queued',
        'progress': 0,
        'result_url': None,
        'created_at': None
    }
    save_jobs(jobs)

    # start background thread to simulate generation
    t = threading.Thread(target=simulate_generation, args=(job_id, save_path), daemon=True)
    t.start()

    return jsonify({'ok': True, 'job_id': job_id, 'result_url': url_for('result_page', job_id=job_id, _external=True)}), 200

@app.route('/api/status/<job_id>')
def api_status(job_id):
    jobs = load_jobs()
    job = jobs.get(job_id)
    if not job:
        return jsonify({'ok': False, 'error': 'not found'}), 404
    return jsonify({'ok': True, 'job': job})

# optional: allow downloading uploaded images
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Render binds on port 10000 by default as detected earlier — but running with gunicorn on Render will be used.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)
