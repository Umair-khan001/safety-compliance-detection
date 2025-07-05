#YOLOv8 Flask Application
from flask import Flask, render_template, Response, jsonify, request, session
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired
import os
from flask_bootstrap import Bootstrap
import cv2
import time # Import time for timestamping saved frames

from hubconfCustom import video_detection, PROCESSED_OUTPUT_DIR # Import PROCESSED_OUTPUT_DIR

import secrets
from dotenv import load_dotenv

# Explicitly load environment variables from 'config.env'
load_dotenv(dotenv_path='config.env')

app = Flask(__name__)
Bootstrap(app)

# Set SECRET_KEY from env file or generate a secure random key
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'static/files'

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
# Ensure the output directory for processed videos/frames exists
if not os.path.exists(PROCESSED_OUTPUT_DIR):
    os.makedirs(PROCESSED_OUTPUT_DIR)


class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    conf_slide = IntegerRangeField('Confidence:  ', default=25, validators=[InputRequired()])
    submit = SubmitField("Run")

detect_count = "0" # Store as string, consistent with existing
safe_count = "0"  # Store as string

def generate_frames(path_x='', conf_=0.25, use_cuda=False):
    global detect_count, safe_count

    webcam_frame_idx = 0 # Initialize webcam frame counter
    out = None # Initialize VideoWriter to None

    try:
        # If path_x is 0, then use webcam mode.
        if path_x == 0:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Error: Could not open webcam.")
                return # Exit if webcam cannot be opened

            # Get webcam frame properties for VideoWriter
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = 20 # Default FPS for webcam output video

            # Generate a timestamp for webcam session to name saved frames and video
            webcam_session_timestamp = int(time.time())
            output_video_path = os.path.join(PROCESSED_OUTPUT_DIR, f'webcam_processed_{webcam_session_timestamp}.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec for MP4
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

            webcam_frame_counter = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame from webcam.")
                    break

                # Process the current frame (pass is_webcam=True and current_frame_num)
                # video_detection now takes the frame directly for webcam
                yolo_output_gen = video_detection(source_input=frame, # Pass the frame
                                                  conf_=conf_,
                                                  is_webcam=True,
                                                  use_cuda=use_cuda,
                                                  current_frame_num=webcam_frame_idx)

                try:
                    # Generator now yields frame, total_detections, safe_detections
                    detection_frame, d_count, s_count = next(yolo_output_gen)
                    detect_count = str(d_count)
                    safe_count = str(s_count)

                    # Save the processed frame as JPG
                    frame_filename = os.path.join(PROCESSED_OUTPUT_DIR, f'webcam_{webcam_session_timestamp}_frame_{webcam_frame_counter:06d}.jpg')
                    cv2.imwrite(frame_filename, detection_frame)

                    # Write the processed frame to the output video file
                    if out is not None:
                         out.write(detection_frame)

                    webcam_frame_counter += 1


                    ret2, buffer = cv2.imencode('.jpg', detection_frame)
                    if not ret2:
                        print("Error: Could not encode frame to JPG.")
                        continue # Skip this frame if encoding fails

                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except StopIteration:
                    # This might happen if video_detection finishes unexpectedly for a frame
                    print("StopIteration from yolo_output_gen in webcam.")
                    break
                except Exception as e:
                    print(f"Error during webcam frame processing: {e}")
                    # Optionally, yield an error frame or message
                    break # Or continue, depending on desired error handling

                webcam_frame_idx += 1 # Increment after processing the frame
            cap.release()
        else:
            # Process the uploaded video (path_x is file path)
            video = cv2.VideoCapture(path_x)
            if not video.isOpened():
                print(f"Error: Could not open video file {path_x}")
                return

            nframes = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = video.get(cv2.CAP_PROP_FPS)

            # Define the codec and create VideoWriter object
            # Using XVID as it's generally compatible. 'mp4v' or 'avc1' might also work depending on system.
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            # Generate a timestamp and base filename for the video
            video_timestamp = int(time.time())
            original_filename = os.path.splitext(os.path.basename(path_x))[0]
            output_video_path = os.path.join(PROCESSED_OUTPUT_DIR, f'{original_filename}_processed_{video_timestamp}.mp4')
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

            frame_counter = 0

            for detection_frame, d_count, s_count in video_detection(source_input=path_x, # Pass the video path
                                                                      conf_=conf_,
                                                                      is_webcam=False,
                                                                      use_cuda=use_cuda): # current_frame_num is handled internally for videos
                detect_count = str(d_count)
                safe_count = str(s_count)

                # Save the processed frame as JPG
                frame_filename = os.path.join(PROCESSED_OUTPUT_DIR, f'{original_filename}_{video_timestamp}_frame_{frame_counter:06d}.jpg')
                cv2.imwrite(frame_filename, detection_frame)
                frame_counter += 1

                # Write the processed frame to the output video file
                if out is not None:
                    out.write(detection_frame)


                ret, buffer = cv2.imencode('.jpg', detection_frame)
                if not ret:
                    print("Error: Could not encode video frame to JPG.")
                    continue

                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            video.release()

    finally:
        # Ensure the VideoWriter is released even if an error occurs
        if out is not None:
            out.release()
            print(f"Processed video saved to: {output_video_path}")


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

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        session['video_path'] = file_path
        session['conf_'] = conf_
        # Clear logs for the new video process - handled in video_detection now
        # output_file_path = os.path.join('data', 'tracking_results.txt')
        # if os.path.exists(output_file_path):
        #     with open(output_file_path, 'w') as f:
        #         f.write("") # Clear the file

        return render_template('video.html', form=form) # Redirect or render as appropriate
    return render_template('video.html', form=form) # Show form again if not POST or validation fails

@app.route('/video')
def video():
    video_path = session.get('video_path', None)
    conf_val = session.get('conf_', 25) # Default confidence if not set
    use_cuda_val = session.get('use_cuda', False)

    if not video_path: # Or some other condition if you want to allow direct access
        # Handle case where video_path is not set, e.g., redirect to upload page
        return "Error: No video path set in session. Please upload a video first."

    return Response(generate_frames(path_x=video_path,
                                   conf_=round(float(conf_val)/100, 2),
                                   use_cuda=use_cuda_val),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam_feed')
def webcam_feed():
    conf_val = session.get('conf_', 25) # Use session confidence for webcam too, or a fixed one
    use_cuda_val = session.get('use_cuda', False)
    # For webcam, pass 0 as path_x to signal webcam mode.
    return Response(generate_frames(path_x=0,
                                   conf_=round(float(conf_val)/100, 2),
                                   use_cuda=use_cuda_val),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/graphData')
def graph_data():
    # Return both detection counts for the graph.
    return jsonify(total=detect_count, safe=safe_count)

@app.route('/detectionCount', methods=['GET'])
def total_detection_count():
    global detect_count
    return jsonify(detectCount=detect_count)

@app.route('/safeCount', methods=['GET'])
def safe_person_count():
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
    # Return as plain text, which the browser will display.
    return Response(logs, mimetype='text/plain')


@app.route('/toggle_cuda')
def toggle_cuda():
    import torch # Keep import here to avoid dependency if CUDA check is not used often
    use_cuda = session.get('use_cuda', False)

    if use_cuda: # If already enabled, disable it
        session['use_cuda'] = False
        print("CUDA disabled by toggle.")
        return jsonify(message="CUDA disabled", use_cuda=False)
    else: # If disabled, try to enable it
        if torch.cuda.is_available():
            session['use_cuda'] = True
            print("CUDA enabled by toggle.")
            return jsonify(message="CUDA enabled", use_cuda=True)
        else:
            session['use_cuda'] = False # Ensure it's set to False if not available
            print("CUDA not supported on this device (toggle attempt).")
            return jsonify(error="CUDA not supported on this device.", use_cuda=False)

@app.route('/reset_counts')
def reset_counts():
    global detect_count, safe_count
    detect_count = "0"
    safe_count = "0"

    output_file_path = os.path.join('data', 'tracking_results.txt')
    if os.path.exists(output_file_path):
        try:
            with open(output_file_path, 'w') as f: # Open in write mode to clear
                # Write header again after clearing
                f.write("frame_number,obj_id,x,y,width,height,confidence,class_name,helmet_worn,mask_worn,vest_worn,compliance_status\n")
            print("Counts and logs (tracking_results.txt) reset.")
        except IOError as e:
            print(f"Error resetting logs: {e}")
            return jsonify(success=False, message=f"Error resetting logs: {e}")

    return jsonify(success=True, message="Counts and logs reset.")


if __name__ == "__main__":
    app.run(debug=True)
