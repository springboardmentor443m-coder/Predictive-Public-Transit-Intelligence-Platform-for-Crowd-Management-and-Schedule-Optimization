"""
Generates publication-quality Before vs. After comparison graphic for AI MetroFlow:
Default Generic Streamlit vs. Transit Operations Command Center (OCC).
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'command_center_before_after.png')

fig = plt.figure(figsize=(19, 10.5), dpi=200, facecolor='#060913')

# Main Title Banner
fig.text(0.5, 0.965, 'AI MetroFlow: Transit Operations Command Center UI/UX Redesign',
         ha='center', va='center', fontsize=22, fontweight='bold', color='#F8FAFC', fontfamily='sans-serif')
fig.text(0.5, 0.93, 'Comparative Transformation: Default Generic Streamlit App  vs.  Mission-Critical Transit OCC Dispatch Console',
         ha='center', va='center', fontsize=12, color='#00D4AA', fontfamily='monospace')

# Two-panel Grid
gs = GridSpec(1, 2, left=0.035, right=0.965, top=0.89, bottom=0.04, wspace=0.07)

# -------------------------------------------------------------
# LEFT PANEL: BEFORE (Standard Streamlit UI)
# -------------------------------------------------------------
ax_before = fig.add_subplot(gs[0, 0])
ax_before.set_facecolor('#F3F4F6')
ax_before.set_xlim(0, 100)
ax_before.set_ylim(0, 100)
ax_before.axis('off')

# Outer border
ax_before.add_patch(patches.Rectangle((0, 0), 100, 100, linewidth=2, edgecolor='#D1D5DB', facecolor='#FAFAFA'))

# Panel Tag
ax_before.add_patch(patches.Rectangle((3, 93), 44, 4.5, facecolor='#EF4444', alpha=0.15))
ax_before.text(5, 95.2, 'BEFORE: Default Generic Streamlit', fontsize=11, fontweight='bold', color='#B91C1C', va='center')

# Sidebar Simulation
ax_before.add_patch(patches.Rectangle((0, 0), 22, 92, facecolor='#F3F4F6', edgecolor='#E5E7EB', linewidth=1))
ax_before.text(2, 88, 'AI MetroFlow', fontsize=11, fontweight='bold', color='#111827')
ax_before.text(2, 85, 'Public Transit App', fontsize=8, color='#6B7280')
ax_before.text(2, 79, 'o Home & Overview', fontsize=8, color='#374151')
ax_before.text(2, 74, 'o Real-Time Prediction', fontsize=8, color='#374151')
ax_before.text(2, 69, 'o Crowd Monitoring', fontsize=8, color='#374151')
ax_before.text(2, 64, 'o Train Tracking', fontsize=8, color='#374151')
ax_before.text(2, 59, 'o Schedule Optimization', fontsize=8, color='#374151')

# Main Body Simulation
ax_before.text(26, 88, 'AI MetroFlow Platform', fontsize=15, fontweight='bold', color='#1E3A8A')
ax_before.text(26, 84.5, 'Default Streamlit theme with standard typography and light background', fontsize=8.5, color='#4B5563')

# Standard metrics row
metric_xs = [26, 44, 62, 80]
m_labels = ['Total Volume', 'Stations', 'Accuracy', 'F1-Score']
m_vals = ['4.58M', '340+', '88.07%', '0.8799']
for x, lab, val in zip(metric_xs, m_labels, m_vals):
    ax_before.add_patch(patches.Rectangle((x, 72), 16, 9.5, facecolor='#FFFFFF', edgecolor='#E5E7EB', linewidth=1))
    ax_before.text(x+1.5, 78.5, lab, fontsize=7.5, color='#6B7280')
    ax_before.text(x+1.5, 74.5, val, fontsize=12, fontweight='bold', color='#111827')

# Standard plot preview
ax_before.add_patch(patches.Rectangle((26, 38), 70, 31, facecolor='#FFFFFF', edgecolor='#E5E7EB', linewidth=1))
ax_before.text(28, 65.5, 'Subway Passenger Traffic by Hour (Standard Plotly White)', fontsize=9.5, fontweight='bold', color='#111827')
hrs = [30, 38, 46, 54, 62, 70, 78, 86, 92]
vols = [42, 44, 58, 52, 48, 62, 60, 46, 42]
for i in range(len(hrs)-1):
    ax_before.plot([hrs[i], hrs[i+1]], [vols[i], vols[i+1]], color='#2563EB', linewidth=2)
    ax_before.plot(hrs[i], vols[i], 'o', color='#1D4ED8', markersize=4)

# Table preview
ax_before.add_patch(patches.Rectangle((26, 8), 70, 26, facecolor='#FFFFFF', edgecolor='#E5E7EB', linewidth=1))
ax_before.text(28, 30, 'Generic Data Table & Alert List', fontsize=9.5, fontweight='bold', color='#111827')
for y_t in [25, 20, 15, 10]:
    ax_before.plot([28, 92], [y_t, y_t], color='#F3F4F6', linewidth=1)
ax_before.text(28, 26, 'Station | Borough | Status | Recommendation', fontsize=8, color='#4B5563')
ax_before.text(28, 21.5, 'Grand Central | Manhattan | High | Increase Frequency', fontsize=7.5, color='#6B7280')
ax_before.text(28, 16.5, 'Times Square | Manhattan | High | Increase Frequency', fontsize=7.5, color='#6B7280')
ax_before.text(28, 11.5, 'Atlantic Av | Brooklyn | Medium | Monitor Density', fontsize=7.5, color='#6B7280')


# -------------------------------------------------------------
# RIGHT PANEL: AFTER (Transit Operations Command Center)
# -------------------------------------------------------------
ax_after = fig.add_subplot(gs[0, 1])
ax_after.set_facecolor('#0B1220')
ax_after.set_xlim(0, 100)
ax_after.set_ylim(0, 100)
ax_after.axis('off')

# Outer border with glowing accent
ax_after.add_patch(patches.Rectangle((0, 0), 100, 100, linewidth=2, edgecolor='#00D4AA', facecolor='#0B1220'))

# Panel Tag
ax_after.add_patch(patches.Rectangle((3, 93), 54, 4.5, facecolor='#00D4AA', alpha=0.18, edgecolor='#00D4AA', linewidth=1))
ax_after.text(5, 95.2, 'AFTER: Transit Operations Command Center (OCC)', fontsize=10.5, fontweight='bold', color='#00D4AA', va='center')

# OCC Sidebar Simulation
ax_after.add_patch(patches.Rectangle((0, 0), 22, 92, facecolor='#0D1627', edgecolor='#1E293B', linewidth=1))
ax_after.text(2, 88, 'AI METROFLOW', fontsize=10, fontweight='bold', color='#F8FAFC')
ax_after.text(2, 85.5, 'OPERATIONS CONTROL // OCC', fontsize=6.8, fontweight='bold', color='#00D4AA', fontfamily='monospace')
ax_after.text(2, 80, '[*] Overview & Console', fontsize=7.8, fontweight='bold', color='#06B6D4')
ax_after.text(2, 75.5, '[*] Crowd Heatmap', fontsize=7.8, color='#F97316')
ax_after.text(2, 71, '[*] Live Train Tracking', fontsize=7.8, color='#10B981')
ax_after.text(2, 66.5, '[*] Timetable Dispatch', fontsize=7.8, color='#059669')
ax_after.text(2, 62, '[*] Incident Alert Center', fontsize=7.8, color='#EF4444')
ax_after.text(2, 57.5, '[*] Real-Time Prediction', fontsize=7.8, color='#3B82F6')
ax_after.text(2, 53, '[*] Demand Forecasting', fontsize=7.8, color='#8B5CF6')

# Telemetry Health in Sidebar
ax_after.add_patch(patches.Rectangle((1.5, 39), 19, 11, facecolor='#111827', edgecolor='#1E293B', linewidth=1))
ax_after.text(2.5, 47, 'SYS: ONLINE 99.98%', fontsize=6.5, fontweight='bold', color='#10B981', fontfamily='monospace')
ax_after.text(2.5, 43.8, 'API: CONNECTED :8000', fontsize=6.5, fontweight='bold', color='#00D4AA', fontfamily='monospace')
ax_after.text(2.5, 40.6, 'ML: RF CHAMPION', fontsize=6.5, fontweight='bold', color='#38BDF8', fontfamily='monospace')

# Master Fixed Header & Telemetry Status Bar
ax_after.add_patch(patches.Rectangle((25, 82), 72, 9.8, facecolor='#111827', edgecolor='#00D4AA', alpha=0.4, linewidth=1.2))
ax_after.text(27, 88.5, 'AI MetroFlow OCC Console', fontsize=12, fontweight='bold', color='#F8FAFC')
ax_after.text(27, 85.5, 'TRANSIT OPERATIONS COMMAND CENTER // NYCT CONTROL CONSOLE', fontsize=7, fontweight='bold', color='#38BDF8', fontfamily='monospace')
ax_after.text(78, 88.5, 'UTC: LIVE SYNC ACTIVE', fontsize=7.5, fontweight='bold', color='#00D4AA', fontfamily='monospace')

# Telemetry Ribbon
rib_xs = [27, 44, 62, 80]
rib_titles = ['SYSTEM STATUS', 'API GATEWAY', 'MODEL ENGINE', 'DEMAND SYNC']
rib_vals = ['ONLINE (99.9%)', 'FASTAPI :8000', 'RF (R2: 0.854)', '24H SYNCED']
rib_colors = ['#10B981', '#10B981', '#00D4AA', '#8B5CF6']
for rx, rtitle, rval, rcol in zip(rib_xs, rib_titles, rib_vals, rib_colors):
    ax_after.add_patch(patches.Rectangle((rx, 82.5), 15.5, 4.2, facecolor='#0B1220', edgecolor='#1F2937', linewidth=0.8))
    ax_after.text(rx+1, 85.3, rtitle, fontsize=5.5, color='#94A3B8', fontfamily='monospace')
    ax_after.text(rx+1, 83.3, rval, fontsize=6.2, fontweight='bold', color=rcol, fontfamily='monospace')

# Glassmorphism KPI Cards
kpi_colors = ['#06B6D4', '#38BDF8', '#00D4AA', '#8B5CF6']
kpi_labels = ['DATASET VOLUME', 'STATIONS SCOPE', 'CHAMPION ACCURACY', 'WEIGHTED F1']
kpi_vals = ['4.58M+', '360+', '88.07%', '0.8799']
kpi_deltas = ['Turnstile Audit', 'NYC Subway Network', 'Random Forest Model', 'Multi-Tier Balance']
for x, col, lab, val, delta in zip(metric_xs, kpi_colors, kpi_labels, kpi_vals, kpi_deltas):
    ax_after.add_patch(patches.Rectangle((x, 70), 16, 10, facecolor='#111827', edgecolor='#1F2937', linewidth=1))
    ax_after.add_patch(patches.Rectangle((x, 79.2), 16, 0.8, facecolor=col))
    ax_after.text(x+1.5, 77.2, lab, fontsize=6.5, fontweight='bold', color='#94A3B8')
    ax_after.text(x+1.5, 73.2, val, fontsize=12, fontweight='bold', color='#F8FAFC', fontfamily='monospace')
    ax_after.text(x+1.5, 71, delta, fontsize=6.2, color=col, fontfamily='monospace')

# Carto Darkmatter Map / Telemetry Preview
ax_after.add_patch(patches.Rectangle((26, 38), 70, 29, facecolor='#0F172A', edgecolor='#1E293B', linewidth=1))
ax_after.text(28, 64, 'Live Carto-Darkmatter Subway Fleet & Heatmap [GEO-TELEMETRY]', fontsize=8.5, fontweight='bold', color='#F8FAFC', fontfamily='monospace')

# Simulated dark subway rail paths
ax_after.plot([30, 48, 60, 80, 92], [42, 45, 52, 58, 60], color='#10B981', linewidth=2.5, alpha=0.9)
ax_after.plot([34, 46, 58, 72, 88], [60, 56, 50, 45, 42], color='#38BDF8', linewidth=2.5, alpha=0.9)
ax_after.plot([40, 52, 65, 78, 86], [40, 48, 55, 52, 46], color='#F97316', linewidth=2.5, alpha=0.9)

# Glowing moving train markers
train_pts = [(48, 45, '#10B981', 'TR-101 (34 mph)'), (60, 52, '#EF4444', 'TR-103 [DELAY]'), (58, 50, '#10B981', 'TR-A01 (36 mph)'), (65, 55, '#F59E0B', 'TR-L02 [ARRIVING]')]
for tx, ty, tcol, ttxt in train_pts:
    ax_after.add_patch(patches.Circle((tx, ty), 1.2, facecolor=tcol, edgecolor='#F8FAFC', linewidth=1))
    ax_after.text(tx+1.8, ty, ttxt, fontsize=6.5, color='#F8FAFC', fontweight='bold', fontfamily='monospace')

# Incident & Dispatch Console Table
ax_after.add_patch(patches.Rectangle((26, 8), 70, 26, facecolor='#111827', edgecolor='#1E293B', linewidth=1))
ax_after.text(28, 30.5, 'Mission-Critical Dispatch Matrix & Alert Audit Deck', fontsize=8.5, fontweight='bold', color='#00D4AA', fontfamily='monospace')

# Colored Alert Cards Simulation
alert_entries = [
    (24.5, '#EF4444', '[HIGH OVERCROWD] Grand Central (98.2%) -> Headway: Every 2 Min (30 Trains/hr) [DISPATCHED]'),
    (19.0, '#EF4444', '[HIGH OVERCROWD] Times Square (96.5%) -> Surge Protocol Active (Standby Consists)'),
    (13.5, '#F59E0B', '[MODERATE WARN] Atlantic Av (89.4%) -> Monitoring Platform Passenger Inflow'),
    (8.0, '#10B981', '[NORMAL OPERATION] Flushing - Main St (94.1%) -> Standard 10 Min Headway Maintained'),
]
for ay, acol, atxt in alert_entries:
    ax_after.add_patch(patches.Rectangle((28, ay), 66, 4.2, facecolor='#162032', edgecolor=acol, linewidth=1))
    ax_after.add_patch(patches.Rectangle((28, ay), 1.5, 4.2, facecolor=acol))
    ax_after.text(30.5, ay+1.4, atxt, fontsize=6.8, color='#F8FAFC', fontfamily='monospace')

plt.savefig(out_path, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
plt.close()
print(f'Successfully generated {out_path}')
