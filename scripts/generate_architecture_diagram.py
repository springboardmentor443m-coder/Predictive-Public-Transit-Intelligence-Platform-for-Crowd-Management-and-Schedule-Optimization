"""
AI MetroFlow - Architecture Diagram Generator
Generates a publication-grade, professional system architecture diagram
illustrating data flow between all 8 core platform components.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Output paths
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "figures")
os.makedirs(REPORTS_DIR, exist_ok=True)
OUTPUT_PNG = os.path.join(REPORTS_DIR, "architecture_diagram.png")

def create_diagram():
    fig, ax = plt.subplots(figsize=(16, 9.5), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Background canvas
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    # Title Banner
    ax.text(8.0, 9.45, "AI MetroFlow: System Architecture & Data Flow Pipeline",
            fontsize=20, fontweight='bold', ha='center', va='center', color='#0F172A', fontfamily='sans-serif')
    ax.text(8.0, 9.1, "Predictive Public Transit Intelligence Platform for Crowd Management and Schedule Optimization",
            fontsize=11.5, fontstyle='italic', ha='center', va='center', color='#475569', fontfamily='sans-serif')

    # Color Palette
    c_data_bg, c_data_border, c_data_text = '#F0F9FF', '#0284C7', '#0369A1'
    c_ml_bg, c_ml_border, c_ml_text = '#EEF2FF', '#4F46E5', '#3730A3'
    c_api_bg, c_api_border, c_api_text = '#ECFDF5', '#059669', '#065F46'
    c_ui_bg, c_ui_border, c_ui_text = '#FFFBEB', '#D97706', '#92400E'

    def draw_box(x, y, w, h, title, subtitle, details, bg, border, title_color, badge=None):
        # Drop shadow
        shadow = patches.FancyBboxPatch((x + 0.05, y - 0.05), w, h,
                                       boxstyle="round,pad=0.12,rounding_size=0.15",
                                       facecolor='#CBD5E1', edgecolor='none', alpha=0.45, zorder=2)
        ax.add_patch(shadow)

        # Main box
        box = patches.FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.12,rounding_size=0.15",
                                    facecolor=bg, edgecolor=border, linewidth=2.0, zorder=3)
        ax.add_patch(box)

        # Title
        ax.text(x + w/2, y + h - 0.35, title, fontsize=12, fontweight='bold',
                ha='center', va='center', color=title_color, zorder=4)
        
        # Subtitle
        if subtitle:
            ax.text(x + w/2, y + h - 0.65, subtitle, fontsize=9.5, fontweight='semibold',
                    ha='center', va='center', color='#334155', zorder=4)

        # Details list
        start_y = y + h - 1.05
        for i, line in enumerate(details):
            ax.text(x + 0.18, start_y - (i * 0.28), line, fontsize=8.5,
                    ha='left', va='center', color='#475569', zorder=4)

        # Badge pill
        if badge:
            badge_box = patches.FancyBboxPatch((x + w/2 - 0.95, y + 0.12), 1.9, 0.32,
                                              boxstyle="round,pad=0.04,rounding_size=0.08",
                                              facecolor=border, edgecolor='none', zorder=4)
            ax.add_patch(badge_box)
            ax.text(x + w/2, y + 0.28, badge, fontsize=8.2, fontweight='bold',
                    ha='center', va='center', color='#FFFFFF', zorder=5)

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            '', xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(facecolor='#334155', edgecolor='#334155', width=2.2, headwidth=8.0, headlength=7.0, shrink=0.05),
            zorder=6
        )
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx, my + 0.18, label, fontsize=8.5, fontweight='bold', ha='center', va='center',
                    color='#1E293B', bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=1.0),
                    zorder=7)

    # =========================================================================
    # ROW 1: DATA PIPELINE (Top Row: Left to Right)
    # =========================================================================

    # 1. NYC Subway Dataset
    draw_box(
        0.8, 5.8, 3.0, 2.7,
        "1. NYC Subway Dataset",
        "Raw Data Source (2017–2021)",
        [
            "• Turnstile passenger traffic",
            "• 4,589,380 log records",
            "• 340+ transit stations",
            "• Attributes: Entries, Exits,",
            "  Datetime, Stop Name, Lines"
        ],
        c_data_bg, c_data_border, c_data_text,
        badge="4.58M RECORDS"
    )

    # 2. Data Cleaning
    draw_box(
        4.6, 5.8, 3.1, 2.7,
        "2. Data Cleaning",
        "src/data_cleaning.py",
        [
            "• Deduplication & integrity check",
            "• Datetime formatting & parsing",
            "• Null direction label cleanup",
            "• Outlier validation",
            "• Output: cleaned_data.csv"
        ],
        c_data_bg, c_data_border, c_data_text,
        badge="PREPROCESSED"
    )

    # 3. Feature Engineering
    draw_box(
        8.5, 5.8, 3.2, 2.7,
        "3. Feature Engineering",
        "src/feature_engineering.py",
        [
            "• Temporal: hour, day, month, DOW",
            "• Flags: is_weekend, is_peak_hour",
            "• Spatial: Lat, Long, Borough, Structure",
            "• Target: Congestion_Level",
            "  (Low: 33%, Med: 33%, High: 34%)"
        ],
        c_data_bg, c_data_border, c_data_text,
        badge="LEAKAGE-FREE"
    )

    # 4. Random Forest Model Training
    draw_box(
        12.4, 5.8, 3.1, 2.7,
        "4. Model Training",
        "src/train_model.py",
        [
            "• Random Forest Classifier",
            "• Stratified 80/20 train/test",
            "• 100 trees | Max depth: 16",
            "• Target leakage prevention",
            "• DT vs RF vs XGBoost benchmark"
        ],
        c_ml_bg, c_ml_border, c_ml_text,
        badge="88.07% ACCURACY"
    )

    # Row 1 Arrows
    draw_arrow(3.8, 7.15, 4.6, 7.15, "Raw CSV")
    draw_arrow(7.7, 7.15, 8.5, 7.15, "Cleaned Logs")
    draw_arrow(11.7, 7.15, 12.4, 7.15, "12 Features")

    # =========================================================================
    # ROW 2: SERVING & APPLICATION (Bottom Row: Right to Left)
    # =========================================================================

    # Connect Row 1 to Row 2
    draw_arrow(13.95, 5.8, 13.95, 4.2, "Save Bundle")

    # 5. congestion_model.pkl
    draw_box(
        12.4, 1.5, 3.1, 2.7,
        "5. Model Artifact",
        "models/congestion_model.pkl",
        [
            "• Serialized model bundle",
            "• Fitted LabelEncoders",
            "• Feature schema alignment",
            "• Class labels & metadata",
            "• Evaluation metrics (F1: 0.88)"
        ],
        c_ml_bg, c_ml_border, c_ml_text,
        badge="JOBLIB BUNDLE"
    )

    # 6. FastAPI Backend
    draw_box(
        8.5, 1.5, 3.2, 2.7,
        "6. FastAPI Backend",
        "api/main.py",
        [
            "• REST API endpoints (/predict)",
            "• Pydantic v2 schema validation",
            "• Real-time confidence scores",
            "• Health checks (/health)",
            "• Swagger OpenAPI (/docs)"
        ],
        c_api_bg, c_api_border, c_api_text,
        badge="< 15ms LATENCY"
    )

    # 7. Streamlit Dashboard
    draw_box(
        4.6, 1.5, 3.1, 2.7,
        "7. Streamlit Dashboard",
        "dashboard/app.py",
        [
            "• Multi-page executive UI",
            "• Analytics & rush hour curves",
            "• Real-time prediction form",
            "• Quick demo scenario presets",
            "• Dual API & local fallback"
        ],
        c_ui_bg, c_ui_border, c_ui_text,
        badge="PORT 8501"
    )

    # 8. End User
    draw_box(
        0.8, 1.5, 3.0, 2.7,
        "8. End User",
        "Transit Operations & Commuters",
        [
            "• Transit dispatch operators",
            "• Subway schedule planners",
            "• Station crowd controllers",
            "• Mobile & Web dashboards",
            "• Actionable recommendations"
        ],
        c_ui_bg, c_ui_border, c_ui_text,
        badge="DECISION READY"
    )

    # Row 2 Arrows (Flowing backwards to user)
    draw_arrow(12.4, 2.85, 11.7, 2.85, "Load Weights")
    draw_arrow(8.5, 2.85, 7.7, 2.85, "HTTP / JSON")
    draw_arrow(4.6, 2.85, 3.8, 2.85, "Visual Insights")

    # Legend & Footer Info Box
    legend_rect = patches.FancyBboxPatch((0.8, 0.45), 14.7, 0.65,
                                        boxstyle="round,pad=0.08,rounding_size=0.1",
                                        facecolor='#FFFFFF', edgecolor='#E2E8F0', lw=1.2, zorder=2)
    ax.add_patch(legend_rect)
    ax.text(1.2, 0.78, "PIPELINE TIERS:", fontsize=8.5, fontweight='bold', color='#1E293B', va='center')
    
    # Legend color pills
    for idx, (label, color) in enumerate([
        ("Data Pipeline", c_data_border),
        ("ML & Artifacts", c_ml_border),
        ("REST Backend", c_api_border),
        ("UI & User", c_ui_border)
    ]):
        x_pos = 3.2 + (idx * 3.1)
        ax.plot([x_pos, x_pos + 0.35], [0.78, 0.78], color=color, lw=4.5, solid_capstyle='round')
        ax.text(x_pos + 0.45, 0.78, label, fontsize=8.2, fontweight='semibold', color='#475569', va='center')

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Architecture diagram successfully generated at: {OUTPUT_PNG}")

if __name__ == "__main__":
    create_diagram()
