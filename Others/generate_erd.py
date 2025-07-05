#!/usr/bin/env python3
"""
ERD Generator for PPE Detection System Database
Creates visual Entity Relationship Diagram using matplotlib and graphviz
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_erd_diagram():
    """Generate visual ERD diagram for PPE Detection System"""
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    primary_color = '#3B82F6'      # Blue
    secondary_color = '#10B981'    # Green
    accent_color = '#F59E0B'       # Amber
    text_color = '#1F2937'         # Dark gray
    bg_color = '#F9FAFB'           # Light gray
    
    # Set background
    fig.patch.set_facecolor('white')
    
    # Title
    ax.text(5, 9.5, 'PPE Detection System - Entity Relationship Diagram', 
            fontsize=20, fontweight='bold', ha='center', color=text_color)
    
    # USERS table
    users_box = FancyBboxPatch((0.5, 6), 3, 2.5, 
                               boxstyle="round,pad=0.1", 
                               facecolor=primary_color, 
                               edgecolor='black', 
                               alpha=0.8)
    ax.add_patch(users_box)
    
    # Users table content
    users_text = """USERS
    ──────────────────────
    🔑 id (PK)              SERIAL
    📧 email (UK)           VARCHAR
    👤 username (UK)        VARCHAR
    🔒 password_hash        VARCHAR
    👨 first_name           VARCHAR
    👩 last_name            VARCHAR
    🎭 role                 VARCHAR
    📊 status               VARCHAR
    📅 registration_date    TIMESTAMP
    ✅ approved_date        TIMESTAMP
    👨‍💼 approved_by (FK)     INTEGER
    🕐 last_login           TIMESTAMP
    📞 phone                VARCHAR
    🏢 company              VARCHAR"""
    
    ax.text(2, 7.2, users_text, fontsize=8, ha='center', va='center', 
            color='white', fontweight='bold')
    
    # USER_ACTIVITY_LOGS table
    activity_box = FancyBboxPatch((0.5, 3), 3, 2.2, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor=secondary_color, 
                                  edgecolor='black', 
                                  alpha=0.8)
    ax.add_patch(activity_box)
    
    activity_text = """USER_ACTIVITY_LOGS
    ──────────────────────
    🔑 id (PK)              SERIAL
    👤 user_id (FK)         INTEGER
    🎯 activity_type        VARCHAR
    📝 description          TEXT
    🎥 video_filename       VARCHAR
    🔍 detection_results    JSON
    🌐 ip_address           INET
    🖥️ user_agent           TEXT
    📅 created_at           TIMESTAMP"""
    
    ax.text(2, 4.1, activity_text, fontsize=8, ha='center', va='center', 
            color='white', fontweight='bold')
    
    # DETECTION_SESSIONS table
    sessions_box = FancyBboxPatch((6, 3), 3, 2.5, 
                                  boxstyle="round,pad=0.1", 
                                  facecolor=accent_color, 
                                  edgecolor='black', 
                                  alpha=0.8)
    ax.add_patch(sessions_box)
    
    sessions_text = """DETECTION_SESSIONS
    ──────────────────────
    🔑 id (PK)              SERIAL
    👤 user_id (FK)         INTEGER
    🎭 session_type         VARCHAR
    🎥 video_filename       VARCHAR
    🎯 confidence_threshold DECIMAL
    📊 total_detections     INTEGER
    ✅ safe_detections      INTEGER
    ❌ unsafe_detections    INTEGER
    ⏱️ session_duration     INTEGER
    📊 status               VARCHAR
    🕐 started_at           TIMESTAMP
    🏁 completed_at         TIMESTAMP"""
    
    ax.text(7.5, 4.2, sessions_text, fontsize=8, ha='center', va='center', 
            color='white', fontweight='bold')
    
    # Relationships arrows
    # Users to Activity Logs (1:N)
    arrow1 = ConnectionPatch((2, 6), (2, 5.2), "data", "data",
                            arrowstyle="->", shrinkA=5, shrinkB=5,
                            mutation_scale=20, fc="black", lw=2)
    ax.add_artist(arrow1)
    ax.text(1.3, 5.6, '1:N', fontsize=10, fontweight='bold', color=text_color)
    
    # Users to Detection Sessions (1:N)
    arrow2 = ConnectionPatch((3.5, 7), (6, 4.5), "data", "data",
                            arrowstyle="->", shrinkA=5, shrinkB=5,
                            mutation_scale=20, fc="black", lw=2)
    ax.add_artist(arrow2)
    ax.text(4.7, 5.8, '1:N', fontsize=10, fontweight='bold', color=text_color)
    
    # Self-reference (Users approved_by)
    arrow3 = ConnectionPatch((1, 8.5), (1, 7.5), "data", "data",
                            arrowstyle="->", shrinkA=5, shrinkB=5,
                            mutation_scale=20, fc="gray", lw=2)
    ax.add_artist(arrow3)
    ax.text(0.3, 8, 'Self\nRef', fontsize=8, fontweight='bold', color='gray')
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=primary_color, label='Users Entity'),
        mpatches.Patch(color=secondary_color, label='Activity Logs Entity'),
        mpatches.Patch(color=accent_color, label='Detection Sessions Entity'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    # Relationship explanations
    ax.text(5, 2, 'Relationship Types:', fontsize=14, fontweight='bold', ha='center', color=text_color)
    
    relationships_text = """
    • Users ↔ Activity Logs: One-to-Many (1:N) - One user can have multiple activity entries
    • Users ↔ Detection Sessions: One-to-Many (1:N) - One user can have multiple detection sessions  
    • Users ↔ Users: Self-Reference - Admin users can approve other users (approved_by field)
    
    Key Features:
    🔑 Primary Keys (PK)    📧 Unique Keys (UK)    🔗 Foreign Keys (FK)    🗑️ CASCADE DELETE
    """
    
    ax.text(5, 1.2, relationships_text, fontsize=10, ha='center', va='center', color=text_color)
    
    # Database info
    ax.text(5, 0.3, 'Database: PostgreSQL • Hosting: Neon.tech • Tables: 3 • Indexes: 4', 
            fontsize=10, ha='center', fontweight='bold', 
            bbox=dict(boxstyle="round,pad=0.3", facecolor=bg_color, edgecolor=primary_color))
    
    plt.tight_layout()
    return fig

def save_erd_diagram():
    """Save ERD diagram to file"""
    fig = create_erd_diagram()
    
    # Save as high-quality PNG
    fig.savefig('PPE_Database_ERD.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    # Save as PDF
    fig.savefig('PPE_Database_ERD.pdf', bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print("✅ ERD diagrams saved:")
    print("   • PPE_Database_ERD.png (High-resolution image)")
    print("   • PPE_Database_ERD.pdf (Vector format)")
    
    plt.show()

if __name__ == "__main__":
    # Create and save ERD diagram
    save_erd_diagram()
