import matplotlib.pyplot as plt

# Class distribution (from your dataset analysis)
class_counts_train = [1987, 111, 2144, 547, 2231, 1050, 1797]  # Train set class distribution
class_counts_valid = [596, 25, 645, 149, 765, 314, 580]  # Validation set class distribution
class_counts_test = [269, 14, 309, 88, 300, 162, 258]  # Test set class distribution

# Class labels (optional, to make the plot more readable)
class_labels = ['Class 0', 'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5', 'Class 6']

# Create subplots
fig, ax = plt.subplots(1, 3, figsize=(18, 6))

# Plotting Train Set Distribution
ax[0].bar(range(7), class_counts_train, color='b', alpha=0.7)
ax[0].set_title('Train Set Class Distribution')
ax[0].set_xlabel('Classes')
ax[0].set_ylabel('Frequency')
ax[0].set_xticks(range(7))
ax[0].set_xticklabels(class_labels)

# Plotting Validation Set Distribution
ax[1].bar(range(7), class_counts_valid, color='g', alpha=0.7)
ax[1].set_title('Validation Set Class Distribution')
ax[1].set_xlabel('Classes')
ax[1].set_ylabel('Frequency')
ax[1].set_xticks(range(7))
ax[1].set_xticklabels(class_labels)

# Plotting Test Set Distribution
ax[2].bar(range(7), class_counts_test, color='r', alpha=0.7)
ax[2].set_title('Test Set Class Distribution')
ax[2].set_xlabel('Classes')
ax[2].set_ylabel('Frequency')
ax[2].set_xticks(range(7))
ax[2].set_xticklabels(class_labels)

# Display the plots
plt.tight_layout()
plt.show()
