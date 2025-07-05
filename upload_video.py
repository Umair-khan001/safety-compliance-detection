import os
import cv2
# Import the video_detection function from your custom hubconf file
from hubconfCustom import video_detection, PROCESSED_OUTPUT_DIR

# --- Configuration ---
# Path to the input video file you want to process
VIDEO_PATH = 'static/files/invideo-ai-1080_Inside_a_Busy_Construction_Site__Safety_2025-04-01.mp4'
# Base name for the output video file (will be saved in PROCESSED_OUTPUT_DIR)
OUTPUT_VIDEO_BASENAME = 'invideo-ai-1080_Inside_a_Busy_Construction_Site__Safety_2025-04-01_processed.mp4'
# Confidence threshold for object detection
CONF_THRESHOLD = 0.4
# Toggle GPU usage (Set to True if you have a CUDA-enabled GPU)
USE_CUDA = False

# --- Prepare output directory ---
# Ensure the output directory exists. PROCESSED_OUTPUT_DIR is imported from hubconfCustom.
os.makedirs(PROCESSED_OUTPUT_DIR, exist_ok=True)
# Define the full path for the output video file
OUTPUT_VIDEO_PATH = os.path.join(PROCESSED_OUTPUT_DIR, OUTPUT_VIDEO_BASENAME)


# --- Probe input video for properties ---
# Open the input video file to get its properties (width, height, fps)
cap_probe = cv2.VideoCapture(VIDEO_PATH)
if not cap_probe.isOpened():
    print(f"Error: Could not open video file '{VIDEO_PATH}'")
    # Exit the script if the video cannot be opened
    exit(1)

# Get video properties
width = int(cap_probe.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap_probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
# Get FPS, default to 25 if it's 0
fps = cap_probe.get(cv2.CAP_PROP_FPS) or 25.0
# Release the probe capture object
cap_probe.release()

# --- Initialize video writer ---
# Define the codec for the output video (MP4)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# Create a VideoWriter object to save the processed video
writer = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (width, height))

# Check if the VideoWriter was initialized successfully
if not writer.isOpened():
    print(f"Error: Could not create video writer for '{OUTPUT_VIDEO_PATH}'")
    # Exit the script if the writer cannot be created
    exit(1)

print(f"Processing '{VIDEO_PATH}' @ {width}x{height}@{fps:.1f}FPS")
print(f"Saving output to '{OUTPUT_VIDEO_PATH}'")
print("Press 'q' to stop early.")

# --- Process video via your custom generator (detection, tracking, drawing) ---
# Call the video_detection function, which yields processed frames and counts.
# The video_detection function handles drawing bounding boxes, icons, and the Euclidean ID.
for frame, total_count, safe_count in video_detection(
    source_input=VIDEO_PATH, # Pass the video file path as source_input
    conf_=CONF_THRESHOLD,
    is_webcam=False, # Specify that this is not a webcam feed
    use_cuda=USE_CUDA
):
    # The 'frame' yielded by video_detection already has the detections,
    # tracking IDs, and icons drawn on it by plot_one_boxCustom.

    # Get frame dimensions for positioning text
    frame_height, frame_width, _ = frame.shape

    # Overlay total and safe counts on the frame
    info = f"Total: {total_count} Safe: {safe_count}"

    # Get the size of the text
    text_size, _ = cv2.getTextSize(info, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
    text_width, text_height = text_size

    # Calculate the position for the bottom-right corner
    # Subtract text width and height from frame dimensions, add some padding
    text_x = frame_width - text_width - 10 # 10 pixels padding from the right edge
    text_y = frame_height - 10 # 10 pixels padding from the bottom edge (adjust as needed)


    cv2.putText(
        frame,
        info,
        (text_x, text_y), # Position the text at the calculated bottom-right coordinates
        cv2.FONT_HERSHEY_SIMPLEX,
        1, # Font scale
        (0, 255, 0), # Green color
        2, # Thickness
        cv2.LINE_AA # Line type for anti-aliasing
    )

    # Show the processed frame in a window
    cv2.imshow('PPE Compliance Video', frame)
    # Write the processed frame to the output video file
    writer.write(frame)

    # Check for user input to stop early
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print('Stopping early by user.')
        break

# --- Cleanup ---
# Release the video writer object
writer.release()
# Close all OpenCV windows
cv2.destroyAllWindows()
print('Finished processing.')
