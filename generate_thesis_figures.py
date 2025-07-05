import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Set style for professional-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Dataset statistics from class_counts.py output
class_names = ['boots', 'face_shield', 'gloves', 'goggles', 'helmet', 'mask', 'vest']
train_counts = [1987, 111, 2144, 547, 2231, 1050, 1797]
valid_counts = [596, 25, 645, 149, 765, 314, 580]
test_counts = [269, 14, 309, 88, 300, 162, 258]

# Calculate totals
total_counts = [train_counts[i] + valid_counts[i] + test_counts[i] for i in range(7)]
total_annotations = sum(total_counts)

# Create Figure 4.1: Technology Stack Diagram (Text-based representation)
fig1, ax1 = plt.subplots(figsize=(14, 10))
ax1.axis('off')

# Technology stack layers
layers = [
    "Development Environment\nPython 3.10 | VS Code | Git",
    "Web Framework\nFlask 2.3.3 | Flask-Login | Werkzeug",
    "Database & Auth\nPostgreSQL | bcrypt | python-dotenv",
    "ML & Computer Vision\nYOLOv8 | PyTorch | OpenCV | NumPy",
    "Data Processing\nPandas | Matplotlib | Seaborn | Pillow",
    "Cloud Training\nGoogle Colab | Roboflow | GPU",
    "Deployment\nFlask Dev Server | Google App Engine | Gunicorn"
]

colors = ['#E8F4FD', '#D1E7DD', '#FFF3CD', '#F8D7DA', '#E2E3F3', '#D3D3D4', '#FCF8E3']

for i, (layer, color) in enumerate(zip(layers, colors)):
    rect = plt.Rectangle((0.1, 0.8 - i*0.12), 0.8, 0.1, 
                        facecolor=color, edgecolor='black', linewidth=1)
    ax1.add_patch(rect)
    ax1.text(0.5, 0.85 - i*0.12, layer, ha='center', va='center', 
            fontsize=10, fontweight='bold')

ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.set_title('Figure 4.1: Development Environment and Technology Stack', 
              fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('Figure_4_1_Technology_Stack.png', dpi=300, bbox_inches='tight')
plt.show()

# Create Figure 4.2: Dataset Statistics and Class Distribution
fig2, ((ax2, ax3), (ax4, ax5)) = plt.subplots(2, 2, figsize=(16, 12))

# Subplot 1: Overall class distribution (pie chart)
colors_pie = plt.cm.Set3(np.linspace(0, 1, 7))
wedges, texts, autotexts = ax2.pie(total_counts, labels=class_names, autopct='%1.1f%%', 
                                  colors=colors_pie, startangle=90)
ax2.set_title('Overall Class Distribution\n(Total: 14,341 annotations)', 
              fontsize=12, fontweight='bold')

# Subplot 2: Train/Valid/Test split
split_labels = ['Training', 'Validation', 'Test']
split_counts = [sum(train_counts), sum(valid_counts), sum(test_counts)]
split_percentages = [count/total_annotations*100 for count in split_counts]

bars2 = ax3.bar(split_labels, split_counts, color=['#3498db', '#f39c12', '#e74c3c'])
ax3.set_title('Dataset Split Distribution', fontsize=12, fontweight='bold')
ax3.set_ylabel('Number of Annotations')

# Add percentage labels on bars
for i, (count, pct) in enumerate(zip(split_counts, split_percentages)):
    ax3.text(i, count + 100, f'{count:,}\n({pct:.1f}%)', 
            ha='center', va='bottom', fontweight='bold')

# Subplot 3: Class distribution comparison across splits
x = np.arange(len(class_names))
width = 0.25

bars1 = ax4.bar(x - width, train_counts, width, label='Training', color='#3498db', alpha=0.8)
bars2 = ax4.bar(x, valid_counts, width, label='Validation', color='#f39c12', alpha=0.8)
bars3 = ax4.bar(x + width, test_counts, width, label='Test', color='#e74c3c', alpha=0.8)

ax4.set_xlabel('PPE Classes')
ax4.set_ylabel('Number of Annotations')
ax4.set_title('Class Distribution Across Dataset Splits', fontsize=12, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(class_names, rotation=45, ha='right')
ax4.legend()
ax4.grid(True, alpha=0.3)

# Subplot 4: Class imbalance visualization
class_percentages = [count/total_annotations*100 for count in total_counts]
bars4 = ax5.barh(class_names, class_percentages, color=colors_pie)
ax5.set_xlabel('Percentage of Total Annotations (%)')
ax5.set_title('Class Imbalance Analysis', fontsize=12, fontweight='bold')
ax5.grid(True, alpha=0.3)

# Add percentage labels
for i, (name, pct) in enumerate(zip(class_names, class_percentages)):
    ax5.text(pct + 0.3, i, f'{pct:.1f}%', va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('Figure_4_2_Dataset_Statistics.png', dpi=300, bbox_inches='tight')
plt.show()

# Print summary statistics
print("=== DATASET SUMMARY STATISTICS ===")
print(f"Total Annotations: {total_annotations:,}")
print(f"Total Classes: {len(class_names)}")
print(f"Training Set: {sum(train_counts):,} ({sum(train_counts)/total_annotations*100:.1f}%)")
print(f"Validation Set: {sum(valid_counts):,} ({sum(valid_counts)/total_annotations*100:.1f}%)")
print(f"Test Set: {sum(test_counts):,} ({sum(test_counts)/total_annotations*100:.1f}%)")
print("\nClass Distribution:")
for i, name in enumerate(class_names):
    print(f"{name}: {total_counts[i]:,} ({total_counts[i]/total_annotations*100:.1f}%)")
print(f"\nClass Imbalance Ratio: {max(total_counts)/min(total_counts):.1f}:1")
print(f"Most Common Class: {class_names[total_counts.index(max(total_counts))]} ({max(total_counts):,})")
print(f"Least Common Class: {class_names[total_counts.index(min(total_counts))]} ({min(total_counts):,})")

# Create Figure 4.4: Flask Application Architecture
fig4, ax4 = plt.subplots(figsize=(16, 12))
ax4.axis('off')

# Define architecture layers
layers = [
    ("Client Layer", ["Web Browser", "Video Upload", "Admin Dashboard"], '#E8F4FD'),
    ("Flask Routes", ["Authentication", "Core App", "Admin Panel"], '#D1E7DD'),
    ("Authentication", ["Flask-Login", "bcrypt", "Sessions"], '#FFF3CD'),
    ("Detection Layer", ["hubconfCustom.py", "tracker.py", "YOLOv8"], '#F8D7DA'),
    ("Database Layer", ["PostgreSQL", "users", "sessions", "results"], '#E2E3F3'),
    ("Storage", ["static/files/", "templates/"], '#FCF8E3')
]

y_positions = [0.85, 0.7, 0.55, 0.4, 0.25, 0.1]
for i, (layer_name, components, color) in enumerate(layers):
    y_pos = y_positions[i]
    
    # Draw layer background
    rect = plt.Rectangle((0.05, y_pos - 0.05), 0.9, 0.12, 
                        facecolor=color, edgecolor='black', linewidth=1, alpha=0.7)
    ax4.add_patch(rect)
    
    # Add layer title
    ax4.text(0.02, y_pos + 0.02, layer_name, fontsize=12, fontweight='bold')
    
    # Add components
    comp_width = 0.8 / len(components)
    for j, comp in enumerate(components):
        x_pos = 0.1 + j * comp_width
        comp_rect = plt.Rectangle((x_pos, y_pos - 0.03), comp_width - 0.02, 0.06, 
                                 facecolor='white', edgecolor='black', linewidth=0.5)
        ax4.add_patch(comp_rect)
        ax4.text(x_pos + comp_width/2 - 0.01, y_pos, comp, ha='center', va='center', 
                fontsize=9, fontweight='normal')

# Add connection arrows
arrow_props = dict(arrowstyle='->', lw=1.5, color='blue')
ax4.annotate('', xy=(0.5, 0.65), xytext=(0.5, 0.8), arrowprops=arrow_props)
ax4.annotate('', xy=(0.5, 0.5), xytext=(0.5, 0.65), arrowprops=arrow_props)
ax4.annotate('', xy=(0.5, 0.35), xytext=(0.5, 0.5), arrowprops=arrow_props)
ax4.annotate('', xy=(0.5, 0.2), xytext=(0.5, 0.35), arrowprops=arrow_props)

ax4.set_xlim(0, 1)
ax4.set_ylim(0, 1)
ax4.set_title('Figure 4.4: Flask Application Architecture with Database Integration', 
              fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('Figure_4_4_Flask_Architecture.png', dpi=300, bbox_inches='tight')
plt.show()

# Create Figure 4.5: Detection Pipeline Flow
fig5, ax5 = plt.subplots(figsize=(18, 10))
ax5.axis('off')

# Define pipeline stages
pipeline_stages = [
    ("Input", ["Video/Webcam", "Frame Extraction"], '#E8F4FD'),
    ("Preprocessing", ["Resize", "Format Convert"], '#D1E7DD'),
    ("YOLO Detection", ["Model Inference", "Confidence Filter"], '#FFF3CD'),
    ("Object Tracking", ["ID Assignment", "Motion Tracking"], '#F8D7DA'),
    ("Compliance Check", ["Rule Evaluation", "Violation Detection"], '#E2E3F3'),
    ("Visualization", ["Bbox Overlay", "Output Generation"], '#FCF8E3'),
    ("Results", ["Statistics", "Database Storage"], '#E6F3FF')
]

# Horizontal layout for pipeline
x_positions = [0.05, 0.18, 0.31, 0.44, 0.57, 0.7, 0.83]
for i, (stage_name, components, color) in enumerate(pipeline_stages):
    x_pos = x_positions[i]
    
    # Draw stage background
    rect = plt.Rectangle((x_pos, 0.3), 0.12, 0.4, 
                        facecolor=color, edgecolor='black', linewidth=1, alpha=0.7)
    ax5.add_patch(rect)
    
    # Add stage title
    ax5.text(x_pos + 0.06, 0.75, stage_name, ha='center', fontsize=10, fontweight='bold', rotation=0)
    
    # Add components
    for j, comp in enumerate(components):
        y_pos = 0.55 - j * 0.15
        comp_rect = plt.Rectangle((x_pos + 0.01, y_pos), 0.1, 0.1, 
                                 facecolor='white', edgecolor='black', linewidth=0.5)
        ax5.add_patch(comp_rect)
        ax5.text(x_pos + 0.06, y_pos + 0.05, comp, ha='center', va='center', 
                fontsize=8, fontweight='normal')

# Add pipeline flow arrows
for i in range(len(pipeline_stages) - 1):
    start_x = x_positions[i] + 0.12
    end_x = x_positions[i + 1]
    ax5.annotate('', xy=(end_x, 0.5), xytext=(start_x, 0.5), 
                arrowprops=dict(arrowstyle='->', lw=2, color='blue'))

# Add process flow labels
flow_labels = ["Extract", "Process", "Detect", "Track", "Evaluate", "Visualize", "Store"]
for i, label in enumerate(flow_labels[:-1]):
    x_pos = x_positions[i] + 0.06
    ax5.text(x_pos, 0.25, label, ha='center', fontsize=9, style='italic', color='blue')

ax5.set_xlim(0, 1)
ax5.set_ylim(0, 1)
ax5.set_title('Figure 4.5: Detection Pipeline Flow from Input to Visualization', 
              fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('Figure_4_5_Detection_Pipeline.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n=== ARCHITECTURE SUMMARY ===")
print("Figure 4.4: Flask Application Architecture")
print("- Client Layer: Web interfaces and user interactions")
print("- Flask Routes: Authentication, core app, and admin functionality")
print("- Authentication: Secure login system with session management")
print("- Detection Layer: PPE detection and tracking modules")
print("- Database Layer: PostgreSQL with user and results storage")
print("- Storage: File system for videos and templates")

print("\nFigure 4.5: Detection Pipeline Flow")
print("- Input: Video/webcam capture and frame extraction")
print("- Preprocessing: Image resizing and format conversion")
print("- YOLO Detection: Object detection with confidence filtering")
print("- Object Tracking: ID assignment and motion tracking")
print("- Compliance Check: Safety rule evaluation and violation detection")
print("- Visualization: Bounding box overlay and result generation")
print("- Results: Statistics generation and database storage")
