import os

# Define paths for train, valid, and test datasets
dataset_paths = {
    'train': 'Dataset/train/labels',
    'valid': 'Dataset/valid/labels',
    'test': 'Dataset/test/labels'
}

# Initialize a dictionary to hold class counts for each subset (train, valid, test)
class_counts = {'train': [0] * 7, 'valid': [0] * 7, 'test': [0] * 7}

# Loop through each dataset split
for split, path in dataset_paths.items():
    # Loop through label files in each split's labels folder
    for file_name in os.listdir(path):
        if file_name.endswith('.txt'):  # Only consider label files
            with open(os.path.join(path, file_name), 'r') as file:
                for line in file:
                    class_id = int(line.split()[0])  # Class ID is the first value in each line
                    if 0 <= class_id < 7:  # Ensure class_id is within range (for 7 classes)
                        class_counts[split][class_id] += 1

# Print out the class distribution for each subset (train, valid, test)
for split, counts in class_counts.items():
    print(f"\n{split.capitalize()} Set Class Distribution:")
    for i, count in enumerate(counts):
        print(f"Class {i}: {count} annotations")


