#Created by Augmented Startups
#YOLOv7 Flask Application
#Enroll at www.augmentedstartups.com/store
from flask import Flask, render_template, Response, jsonify, request, session
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired
import os
from flask_bootstrap import Bootstrap
import cv2

from hubconfCustom import video_detection

import secrets
from dotenv import load_dotenv

# Explicitly load environment variables from 'config.env'
load_dotenv(dotenv_path='config.env') 

app = Flask(__name__)
Bootstrap(app)

# Set SECRET_KEY from env file or generate a secure random key
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secrets.token_hex(32)

# Uncomment the following line to print the loaded SECRET_KEY for debugging purposes
# print(f"Loaded SECRET_KEY: {app.config['SECRET_KEY']}")

# app.config['SECRET_KEY'] = 'daniyalkey'
app.config['UPLOAD_FOLDER'] = 'static/files'

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    conf_slide = IntegerRangeField('Confidence:  ', default=25, validators=[InputRequired()])
    submit = SubmitField("Run")

detect_count = 0
safe_count = 0

def generate_frames(path_x='', conf_=0.25):
    global detect_count, safe_count
    # If path_x is 0, then use webcam mode.
    if path_x == 0:
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # Process the current frame (pass is_webcam=True)
            yolo_output = video_detection(frame, conf_, is_webcam=True)
            for detection_, d_count, s_count in yolo_output:
                detect_count = str(d_count)
                safe_count = str(s_count)
                ret2, buffer = cv2.imencode('.jpg', detection_)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        cap.release()
    else:
        # Process the uploaded video (path_x is file path)
        yolo_output = video_detection(path_x, conf_)
        for detection_, d_count, s_count in yolo_output:
            detect_count = str(d_count)
            safe_count = str(s_count)
            ret, buffer = cv2.imencode('.jpg', detection_)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route("/", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
def home():
    session.clear()
    return render_template('root.html')

@app.route('/FrontPage', methods=['GET','POST'])
def front():
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        conf_ = form.conf_slide.data
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               app.config['UPLOAD_FOLDER'],
                               secure_filename(file.filename)))
        session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                             app.config['UPLOAD_FOLDER'],
                                             secure_filename(file.filename))
        session['conf_'] = conf_
    return render_template('video.html', form=form)

@app.route('/video')
def video():
    return Response(generate_frames(path_x=session.get('video_path', None),
                                      conf_=round(float(session.get('conf_', None))/100, 2)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam_feed')
def webcam_feed():
    # For webcam, pass 0 as path_x to signal webcam mode.
    return Response(generate_frames(path_x=0, conf_=0.25),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/graphData')
def graph_data():
    # Return both detection counts for the graph.
    return jsonify(total=detect_count, safe=safe_count)

@app.route('/detectionCount', methods=['GET'])
def fps_fun():
    global detect_count
    return jsonify(detectCount=detect_count)

@app.route('/safeCount', methods=['GET'])
def size_fun():
    global safe_count
    return jsonify(safecount=safe_count)

@app.route('/tracker_logs')
def tracker_logs():
    output_file_path = os.path.join('data', 'tracking_results.txt')
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as f:
            logs = f.read()
    else:
        logs = "No logs available yet."
    return logs

if __name__ == "__main__":
    app.run(debug=True)
