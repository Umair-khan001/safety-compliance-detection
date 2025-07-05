import asone
from asone import ASOne
import cv2
import random
import time
import numpy as np
import os
from tracker import * # EuclideanDistTracker is in here

# Ensure the data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Ensure the output directory for processed videos/frames exists
PROCESSED_OUTPUT_DIR = 'PPE/runs/detect'
if not os.path.exists(PROCESSED_OUTPUT_DIR):
    os.makedirs(PROCESSED_OUTPUT_DIR)


sizeLogo = 100
vestGreen = cv2.imread("static/files/greenVest.png")
vestRed = cv2.imread("static/files/redVest.png")
helmetGreen = cv2.imread("static/files/greenHelmet.png")
helmetRed = cv2.imread("static/files/redHelmet.png")
maskGreen = cv2.imread("static/files/greenMask.png")
maskRed = cv2.imread("static/files/redMask.png")

# Warnings for image loading
if vestGreen is None: print("Warning: static/files/greenVest.png could not be loaded.")
if vestRed is None: print("Warning: static/files/redVest.png could not be loaded.")
if helmetGreen is None: print("Warning: static/files/greenHelmet.png could not be loaded.")
if helmetRed is None: print("Warning: static/files/redHelmet.png could not be loaded.")
if maskGreen is None: print("Warning: static/files/greenMask.png could not be loaded.")
if maskRed is None: print("Warning: static/files/redRed.png could not be loaded.") # Corrected typo
if maskRed is None: print("Warning: static/files/redMask.png could not be loaded.") # Corrected typo

# Resize images and create masks (ensure base images are loaded before this)
if helmetRed is not None and helmetGreen is not None:
    helmetGreen = cv2.resize(helmetGreen, (sizeLogo, sizeLogo))
    helmetRed = cv2.resize(helmetRed, (sizeLogo, sizeLogo))
    img2grayH = cv2.cvtColor(helmetRed, cv2.COLOR_BGR2GRAY)
    retH, maskH = cv2.threshold(img2grayH, 1, 255, cv2.THRESH_BINARY)
else:
    maskH = None
    print("Warning: Helmet images not loaded correctly, helmet icons will not work.")

if vestRed is not None and vestGreen is not None:
    vestGreen = cv2.resize(vestGreen, (sizeLogo, sizeLogo))
    vestRed = cv2.resize(vestRed, (sizeLogo, sizeLogo))
    img2grayV = cv2.cvtColor(vestRed, cv2.COLOR_BGR2GRAY)
    retV, maskV = cv2.threshold(img2grayV, 1, 255, cv2.THRESH_BINARY)
else:
    maskV = None
    print("Warning: Vest images not loaded correctly, vest icons will not work.")

if maskRed is not None and maskGreen is not None:
    maskGreen = cv2.resize(maskGreen, (sizeLogo, sizeLogo))
    maskRed = cv2.resize(maskRed, (sizeLogo, sizeLogo))
    img2grayM = cv2.cvtColor(maskRed, cv2.COLOR_BGR2GRAY)
    retM, maskM = cv2.threshold(img2grayM, 1, 255, cv2.THRESH_BINARY)
else:
    maskM = None
    print("Warning: Mask images not loaded correctly, mask icons will not work.")


def plot_one_boxCustom(x_coords, img, color=None, label_list=None, line_thickness=3, obj_id=None):
    # Plots one bounding box on image img
    # x_coords are [x1, y1, x2, y2]
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x_coords[0]), int(x_coords[1])), (int(x_coords[2]), int(x_coords[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)

    img_h, img_w = img.shape[:2]

    # Display Euclidean Tracker ID
    if obj_id is not None:
        id_text = f"E_ID:{obj_id}"
        # Position for ID text: Top-left of the bounding box, slightly above
        text_y_pos = c1[1] - (tl + 5) if c1[1] - (tl + 15) > 0 else c1[1] + 15
        cv2.putText(img, id_text, (c1[0], text_y_pos), 0, tl / 2.5, [225, 255, 255], thickness=max(1,tl//2), lineType=cv2.LINE_AA)

    if label_list and isinstance(label_list, list): # label_list is like ['person ', 'head_whelmet', '0.87']
        current_icon_y_offset = 5 # Initial y-offset from c1[1] for the first icon

        # Helmet icon
        if helmetGreen is not None and helmetRed is not None and maskH is not None:
            try:
                y_start = c1[1] + current_icon_y_offset
                y_end = y_start + sizeLogo
                x_start = c1[0] + 5 # Fixed x-offset from c1[0]
                x_end = x_start + sizeLogo

                if y_start >=0 and x_start >=0 and y_end <= img_h and x_end <= img_w :
                    roi_helmet = img[y_start:y_end, x_start:x_end]
                    if roi_helmet.shape[0] == sizeLogo and roi_helmet.shape[1] == sizeLogo:
                        chosen_helmet = helmetGreen if "head_whelmet" in label_list else helmetRed
                        # Apply mask and add icon
                        roi_helmet_masked = cv2.bitwise_and(roi_helmet, roi_helmet, mask=cv2.bitwise_not(maskH))
                        icon_masked = cv2.bitwise_and(chosen_helmet, chosen_helmet, mask=maskH)
                        cv2.add(roi_helmet_masked, icon_masked, dst=roi_helmet)
                        current_icon_y_offset += sizeLogo + 5
            except Exception as e:
                # print(f"Error plotting helmet icon: {e}") # Optional: for debugging
                pass

        # Mask icon
        if maskGreen is not None and maskRed is not None and maskM is not None:
            try:
                y_start = c1[1] + current_icon_y_offset
                y_end = y_start + sizeLogo
                x_start = c1[0] + 5 # Fixed x-offset from c1[0]
                x_end = x_start + sizeLogo

                if y_start >=0 and x_start >=0 and y_end <= img_h and x_end <= img_w:
                    roi_mask = img[y_start:y_end, x_start:x_end]
                    if roi_mask.shape[0] == sizeLogo and roi_mask.shape[1] == sizeLogo:
                        chosen_mask = maskGreen if "face_wmask" in label_list else maskRed
                        roi_mask_masked = cv2.bitwise_and(roi_mask, roi_mask, mask=cv2.bitwise_not(maskM))
                        icon_masked = cv2.bitwise_and(chosen_mask, chosen_mask, mask=maskM)
                        cv2.add(roi_mask_masked, icon_masked, dst=roi_mask)
                        current_icon_y_offset += sizeLogo + 5
            except Exception as e:
                # print(f"Error plotting mask icon: {e}")
                pass

        # Vest icon
        if vestGreen is not None and vestRed is not None and maskV is not None:
            try:
                y_start = c1[1] + current_icon_y_offset
                y_end = y_start + sizeLogo
                x_start = c1[0] + 5 # Fixed x-offset from c1[0]
                x_end = x_start + sizeLogo

                if y_start >=0 and x_start >=0 and y_end <= img_h and x_end <= img_w:
                    roi_vest = img[y_start:y_end, x_start:x_end]
                    if roi_vest.shape[0] == sizeLogo and roi_vest.shape[1] == sizeLogo:
                        chosen_vest = vestGreen if "vest" in label_list else vestRed
                        roi_vest_masked = cv2.bitwise_and(roi_vest, roi_vest, mask=cv2.bitwise_not(maskV))
                        # Corrected typo here: changed 'chosen_masked' to 'chosen_vest'
                        icon_masked = cv2.bitwise_and(chosen_vest, chosen_vest, mask=maskV)
                        cv2.add(roi_vest_masked, icon_masked, dst=roi_vest)
            except Exception as e:
                # print(f"Error plotting vest icon: {e}")
                pass


def video_detection(source_input, conf_=0.25, is_webcam=False, use_cuda=False, current_frame_num=0):
    names = ['face_nomask', 'face_wmask', 'hand_noglove',
             'hand_wglove', 'head_nohelmet', 'head_whelmet', 'person', 'vest']
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]
    filter_classes = None # Not currently used with this model's setup in ASOne

    dt_obj = ASOne(
        tracker=asone.BYTETRACK,
        detector=asone.YOLOV8N_PYTORCH, # Assuming this uses your 'best.pt'
        weights="best.pt", # Make sure this path is correct
        use_cuda=use_cuda
    )
    euclidean_tracker = EuclideanDistTracker() # Renamed for clarity
    output_file_path = os.path.join('data', 'tracking_results.txt')

    # Write header to the log file (clear content if starting a new run)
    # Clear log file only for new video processing or the very first webcam frame (frame 0)
    if not is_webcam or current_frame_num == 0:
         if os.path.exists(output_file_path):
             # Open in write mode ('w') to overwrite existing content
             with open(output_file_path, 'w') as output_file:
                 output_file.write("frame_number,obj_id,x,y,width,height,confidence,class_name,helmet_worn,mask_worn,vest_worn,compliance_status\n")
         else:
              # If file doesn't exist, create it and write header
             with open(output_file_path, 'w') as output_file:
                 output_file.write("frame_number,obj_id,x,y,width,height,confidence,class_name,helmet_worn,mask_worn,vest_worn,compliance_status\n")


    prev_time = time.time()

    if is_webcam:
        # Process a single webcam frame. source_input is the frame itself.
        img0 = source_input.copy()

        # FPS calculation is removed for webcam as requested
        # Display FPS on the frame is removed for webcam as requested


        # Perform detection
        detected_objects = dt_obj.detect(source=img0, conf_thres=conf_, iou_thres=0.45, filter_classes=filter_classes)

        # dt_obj.detect returns a list, typically with one element for single image processing
        output_detected_this_frame = detected_objects[0] if detected_objects else []

        detectionTracker_persons = []
        equipmentList = []

        for result in output_detected_this_frame:
            # result: [x1, y1, x2, y2, conf, class_id]
            box = [result[0], result[1], result[2], result[3]]
            class_id = int(result[5])
            # Ensure class_id is within bounds for 'names' list
            if 0 <= class_id < len(names):
                label_str = f'{names[class_id]} {result[4]:.2f}' # Confidence score
                if names[class_id].strip() == 'person':
                    detectionTracker_persons.append([box[0], box[1], box[2], box[3], label_str])
                else:
                    equipmentList.append([box[0], box[1], box[2], box[3], label_str])
            else:
                print(f"Warning: Detected class_id {class_id} is out of bounds for 'names' list.")


        tracked_persons_info = euclidean_tracker.update([detectionTracker_persons, equipmentList])

        safePersons_this_frame = []
        detectionsCount_this_frame = []

        with open(output_file_path, 'a') as output_file: # Keep append mode for subsequent frames in webcam
            for tracked_item in tracked_persons_info:
                x1, y1, x2, y2, obj_id, label_list = tracked_item # label_list from tracker

                if obj_id not in detectionsCount_this_frame:
                    detectionsCount_this_frame.append(obj_id)

                main_class_name = "unknown"
                confidence_str = "0.0"
                helmet_worn = "no"
                mask_worn = "no"
                vest_worn = "no"

                if label_list and isinstance(label_list, list):
                    main_class_name = label_list[0].strip() if label_list[0] else "unknown"
                    # Find confidence from the label list, assuming it's the last element
                    try:
                        confidence_str = str(float(label_list[-1])) if label_list[-1] else "0.0"
                    except ValueError:
                        confidence_str = "0.0" # Handle cases where last element isn't a float string


                    # Check for specific equipment in the label_list
                    if "head_whelmet" in label_list:
                        helmet_worn = "yes"
                    if "face_wmask" in label_list:
                        mask_worn = "yes"
                    if "vest" in label_list:
                        vest_worn = "yes"


                # Determine compliance status (primarily for 'person')
                is_safe = False
                compliance_status = "N/A" # Default to N/A

                if main_class_name == 'person':
                    is_safe = (helmet_worn == "yes") and \
                              (mask_worn == "yes") and \
                              (vest_worn == "yes") # Assuming all 3 are required
                    compliance_status = "safe" if is_safe else "unsafe"
                    if is_safe:
                        safePersons_this_frame.append(obj_id)


                # Log entry
                log_x = int(x1)
                log_y = int(y1)
                log_width = int(x2 - x1)
                log_height = int(y2 - y1)
                log_line = f"{current_frame_num},{obj_id},{log_x},{log_y},{log_width},{log_height},{confidence_str},{main_class_name},{helmet_worn},{mask_worn},{vest_worn},{compliance_status}\n"
                output_file.write(log_line)

                # Plotting
                plot_color = colors[names.index(main_class_name)] if main_class_name in names else colors[0]
                plot_one_boxCustom([x1, y1, x2, y2], img0, label_list=label_list, color=plot_color, line_thickness=2, obj_id=obj_id)


        yield img0, len(list(set(detectionsCount_this_frame))), len(list(set(safePersons_this_frame)))

    else:
        # Process video file. source_input is the video path.
        video = cv2.VideoCapture(source_input)
        if not video.isOpened():
            print(f"Error: Could not open video file {source_input}")
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
        original_filename = os.path.splitext(os.path.basename(source_input))[0]
        output_video_path = os.path.join(PROCESSED_OUTPUT_DIR, f'{original_filename}_processed_{video_timestamp}.mp4')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))


        for frame_idx in range(nframes):
            ret, img0 = video.read()
            if not ret:
                break

            current_frame_num_for_video = frame_idx # Use frame_idx for logging

            # Calculate FPS (only for video files as requested)
            curr_time = time.time()
            fps_display = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0.0
            prev_time = curr_time

            # Display FPS on the frame (only for video files as requested)
            fps_text = f"FPS: {fps_display:.2f}"
            # Position FPS text at top-left, slightly offset
            cv2.putText(img0, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)


            # Perform detection
            detected_objects = dt_obj.detect(source=img0, conf_thres=conf_, iou_thres=0.45, filter_classes=filter_classes)
            output_detected_this_frame = detected_objects[0] if detected_objects else []

            detectionTracker_persons = []
            equipmentList = []

            for result in output_detected_this_frame:
                box = [result[0], result[1], result[2], result[3]]
                class_id = int(result[5])
                if 0 <= class_id < len(names):
                    label_str = f'{names[class_id]} {result[4]:.2f}'
                    if names[class_id].strip() == 'person':
                        detectionTracker_persons.append([box[0], box[1], box[2], box[3], label_str])
                    else:
                        equipmentList.append([box[0], box[1], box[2], box[3], label_str])
                else:
                    print(f"Warning: Detected class_id {class_id} is out of bounds for 'names' list.")


            tracked_persons_info = euclidean_tracker.update([detectionTracker_persons, equipmentList])

            safePersons_this_frame = []
            detectionsCount_this_frame = []

            with open(output_file_path, 'a') as output_file: # Keep append mode for subsequent frames in video
                for tracked_item in tracked_persons_info:
                    x1, y1, x2, y2, obj_id, label_list = tracked_item

                    if obj_id not in detectionsCount_this_frame:
                        detectionsCount_this_frame.append(obj_id)

                    main_class_name = "unknown"
                    confidence_str = "0.0"
                    helmet_worn = "no"
                    mask_worn = "no"
                    vest_worn = "no"

                    if label_list and isinstance(label_list, list):
                        main_class_name = label_list[0].strip() if label_list[0] else "unknown"
                        # Find confidence from the label list, assuming it's the last element
                        try:
                           confidence_str = str(float(label_list[-1])) if label_list[-1] else "0.0"
                        except ValueError:
                           confidence_str = "0.0" # Handle cases where last element isn't a float string

                        if "head_whelmet" in label_list:
                            helmet_worn = "yes"
                        if "face_wmask" in label_list:
                            mask_worn = "yes"
                        if "vest" in label_list:
                            vest_worn = "yes"

                    is_safe = False
                    compliance_status = "N/A"

                    if main_class_name == 'person':
                        is_safe = (helmet_worn == "yes") and \
                                  (mask_worn == "yes") and \
                                  (vest_worn == "yes")
                        compliance_status = "safe" if is_safe else "unsafe"
                        if is_safe:
                            safePersons_this_frame.append(obj_id)


                    log_x = int(x1)
                    log_y = int(y1)
                    log_width = int(x2 - x1)
                    log_height = int(y2 - y1)
                    log_line = f"{current_frame_num_for_video},{obj_id},{log_x},{log_y},{log_width},{log_height},{confidence_str},{main_class_name},{helmet_worn},{mask_worn},{vest_worn},{compliance_status}\n"
                    output_file.write(log_line)

                    plot_color = colors[names.index(main_class_name)] if main_class_name in names else colors[0]
                    plot_one_boxCustom([x1, y1, x2, y2], img0, label_list=label_list, color=plot_color, line_thickness=2, obj_id=obj_id)

            # Write the processed frame to the output video file
            out.write(img0)

            yield img0, len(list(set(detectionsCount_this_frame))), len(list(set(safePersons_this_frame)))

        video.release()
        out.release() # Release the VideoWriter after processing the video
