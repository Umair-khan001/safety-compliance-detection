import math
def overlap_Area(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    # compute the area of intersection rectangle
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    # compute the area of both the prediction and ground-truth
    # rectangles
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area

    iou = interArea / float(boxBArea) if boxBArea > 0 else 0.0 # Avoid division by zero
    # return the intersection over union value
    return float(iou)


class EuclideanDistTracker:
    def __init__(self):
        # Store the center positions of the objects
        self.center_points = {}
        # Keep the count of the IDs
        # each time a new object id detected, the count will increase by one
        self.id_count = 0

    def update(self, objects_rect):
        # objects_rect is expected to be a list: [detectionTracker_persons, equipmentList]
        # detectionTracker_persons: list of [x, y, w, h, label_str] for persons
        # equipmentList: list of [ex, ey, ew, eh, elabel_str] for equipment

        objects_bbs_ids = []

        # Get center point of new object (persons)
        for rect in objects_rect[0]: # Iterate through persons
            labelParent = []
            x, y, w, h, person_label_str = rect # x,y,w,h are x1,y1,x2,y2

            # Extract person class name (e.g., "person") and confidence
            person_label_parts = person_label_str.split(" ")
            person_class_name_with_space = person_label_parts[0] + " " if len(person_label_parts) > 0 else "unknown "
            person_confidence = person_label_parts[1] if len(person_label_parts) > 1 else "0.0"

            labelParent.append(person_class_name_with_space) # e.g., "person "

            # Check for associated equipment
            for equipment in objects_rect[1]: # Iterate through equipment
                ex, ey, ew, eh, equipment_label_str = equipment
                # Check overlap between person and equipment
                if(overlap_Area(boxA=[x, y, w, h],boxB=[ex, ey, ew, eh]) > 0.5): # 0.5 threshold for overlap
                    equipment_class_name = equipment_label_str.split(" ")[0]
                    labelParent.append(equipment_class_name) # e.g., "vest", "head_whelmet"

            labelParent.append(person_confidence) # Add person's confidence at the end

            # Calculate center of the person's bounding box
            cx = (x + w) // 2 # Center x: (x1 + x2) / 2
            cy = (y + h) // 2 # Center y: (y1 + y2) / 2

            # Find out if that object was detected already
            same_object_detected = False
            for id, pt_data in self.center_points.items():
                # pt_data could be just (cx,cy) or store more info if needed in future
                # For now, assume pt is (center_x, center_y)
                pt_center_x, pt_center_y = pt_data
                dist = math.hypot(cx - pt_center_x, cy - pt_center_y)

                if dist < 100: # Distance threshold for matching
                    self.center_points[id] = (cx, cy)
                    objects_bbs_ids.append([x, y, w, h, id, labelParent])
                    same_object_detected = True
                    break

            # New object is detected we assign the ID to that object
            if same_object_detected is False:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x, y, w, h, self.id_count, labelParent])
                self.id_count += 1

        # Clean the dictionary by center points to remove IDS not used anymore
        new_center_points = {}
        active_ids = {obj_bb_id[4] for obj_bb_id in objects_bbs_ids} # Get all active IDs in this frame

        for object_id in active_ids:
            if object_id in self.center_points: # Should always be true if logic is correct
                 new_center_points[object_id] = self.center_points[object_id]

        # Update dictionary with IDs not used removed
        self.center_points = new_center_points.copy()
        return objects_bbs_ids