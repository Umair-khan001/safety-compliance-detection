
import os
import cv2
from hubconfCustom import video_detection

# --- Configuration ---
VIDEO_PATH = 'static/files/construction_2.mp4'        # Path to input video
OUTPUT_VIDEO_PATH = 'data/results/output_test3.mp4'  # Path to save annotated video
CONF_THRESHOLD = 0.4                              # Confidence threshold
USE_CUDA = False                                  # Toggle GPU usage

# --- Prepare output directory ---
os.makedirs(os.path.dirname(OUTPUT_VIDEO_PATH), exist_ok=True)

# --- Probe input video for properties ---
cap_probe = cv2.VideoCapture(VIDEO_PATH)
if not cap_probe.isOpened():
    print(f"Error: Could not open video file '{VIDEO_PATH}'")
    exit(1)
width = int(cap_probe.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap_probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap_probe.get(cv2.CAP_PROP_FPS) or 25.0  # Default to 25 if FPS = 0
cap_probe.release()

# --- Initialize video writer ---
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
writer = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (width, height))
if not writer.isOpened():
    print(f"Error: Could not create video writer for '{OUTPUT_VIDEO_PATH}'")
    exit(1)

# --- Create resizable OpenCV window that fits the video resolution ---
window_name = 'PPE Compliance Video'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, width, height)

print(f"Processing '{VIDEO_PATH}' @ {width}x{height}@{fps:.1f}FPS -> '{OUTPUT_VIDEO_PATH}'")
print("Press 'q' to stop early.")

# --- Process video via your custom generator (icons + Euclidean tracking) ---
for frame, total_count, safe_count in video_detection(
    path_x=VIDEO_PATH,
    conf_=CONF_THRESHOLD,
    use_cuda=USE_CUDA
):
    # Overlay counts
    info = f"Total: {total_count}  Safe: {safe_count}"
    cv2.putText(
        frame,
        info,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )

    # Show and write
    cv2.imshow(window_name, frame)
    writer.write(frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print('Stopping early by user.')
        break

# --- Cleanup ---
writer.release()
cv2.destroyAllWindows()
print('Finished processing. Output saved to:', OUTPUT_VIDEO_PATH)
