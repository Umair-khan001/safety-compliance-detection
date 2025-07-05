import os
import cv2
import time
import asone
from asone import ASOne
from tracker import EuclideanDistTracker
from hubconfCustom import plot_one_boxCustom  # Assuming plot_one_boxCustom in hubconfCustom.py

# --- Configuration ---
WEIGHTS_PATH = 'best.pt'  # adjust if needed
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
USE_CUDA = False  # Set to True if you have a CUDA-enabled GPU
CAMERA_INDEX = 0  # Typically 0 for the default webcam

# Output directory for webcam recording and frames
OUTPUT_DIR = 'PPE/runs/detect'
VIDEO_OUTPUT = 'webcam_output.mp4'
FRAMES_DIR = 'frames'

# Class labels must match your custom model's training order
CLASS_NAMES = [
    'face_nomask', 'face_wmask',
    'hand_noglove', 'hand_wglove',
    'head_nohelmet', 'head_whelmet',
    'person', 'vest'
]

def main():
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, FRAMES_DIR), exist_ok=True)

    # Initialize the ASOne model (loads once)
    try:
        model = ASOne(
            tracker=asone.BYTETRACK,
            detector=asone.YOLOV8N_PYTORCH,
            weights=WEIGHTS_PATH,
            use_cuda=USE_CUDA
        )
    except Exception as e:
        print(f"Error initializing ASOne model: {e}")
        print("Ensure 'best.pt' exists and check CUDA availability if use_cuda is True.")
        return

    # Euclidean tracker for counting
    tracker = EuclideanDistTracker()

    # Open webcam
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Error: Cannot open camera index {CAMERA_INDEX}")
        return

    # Probe webcam properties for writer
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Initialize video writer for saving webcam feed
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(
        os.path.join(OUTPUT_DIR, VIDEO_OUTPUT),
        fourcc,
        fps,
        (width, height)
    )
    if not writer.isOpened():
        print(f"Error: Could not create video writer for '{OUTPUT_DIR}/{VIDEO_OUTPUT}'")
        return

    print(f"Starting PPE detection and recording to '{OUTPUT_DIR}/{VIDEO_OUTPUT}' (conf={CONF_THRESHOLD}, iou={IOU_THRESHOLD}). Press 'q' to exit.")

    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame from webcam.")
            break

        frame_count += 1
        elapsed = time.time() - start_time
        current_fps = frame_count / elapsed if elapsed > 0 else 0.0

        # Run detection
        results = model.detect(
            source=frame,
            conf_thres=CONF_THRESHOLD,
            iou_thres=IOU_THRESHOLD,
            filter_classes=None
        )

        output_detected = results[0] if results else []

        person_boxes = []
        equipment_boxes = []
        for det in output_detected:
            x1, y1, x2, y2, score, cls = det
            cls = int(cls)
            if 0 <= cls < len(CLASS_NAMES):
                label = f"{CLASS_NAMES[cls]} {score:.2f}"
                if CLASS_NAMES[cls] == 'person':
                    person_boxes.append([x1, y1, x2, y2, label])
                else:
                    equipment_boxes.append([x1, y1, x2, y2, label])
            else:
                print(f"Warning: Detected class ID {cls} out of range.")

        tracked = tracker.update([person_boxes, equipment_boxes])

        total_ids = safe_ids = 0
        for x1, y1, x2, y2, obj_id, label_list in tracked:
            total_ids += 1
            is_safe = False
            if label_list and label_list[0].strip() == 'person':
                safe_tags = {'head_whelmet', 'vest', 'face_wmask'}
                labels_no_conf = set(label_list[:-1]) if len(label_list) > 1 else set(label_list)
                is_safe = safe_tags.issubset(labels_no_conf)
            if is_safe:
                safe_ids += 1
            plot_one_boxCustom([x1, y1, x2, y2], frame, label_list=label_list, line_thickness=3, obj_id=obj_id)

        h, w, _ = frame.shape
        # FPS top-left
        cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (255, 255, 255), 2, cv2.LINE_AA)
        # Total/Safe bottom-right
        info = f"Total: {total_ids} Safe: {safe_ids}"
        ts, _ = cv2.getTextSize(info, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        cv2.putText(frame, info, (w - ts[0] - 10, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)

        # Save processed frame as JPEG
        frame_filename = os.path.join(OUTPUT_DIR, FRAMES_DIR, f"frame_{frame_count:06d}.jpg")
        cv2.imwrite(frame_filename, frame)

        cv2.imshow("PPE Compliance Detection", frame)
        writer.write(frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
