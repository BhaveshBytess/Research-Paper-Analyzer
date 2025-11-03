#!/usr/bin/env python
"""
Comprehensive Visualization for Batch Evaluation Results
Generates charts, graphs, and analysis visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import json

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Paths
RESULTS_CSV = Path("batch_eval_results/results.csv")
OUTPUT_DIR = Path("batch_eval_results/visualizations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*60)
print("BATCH EVALUATION - COMPREHENSIVE VISUALIZATION")
print("="*60)
print()

# Load data
df = pd.read_csv(RESULTS_CSV)
print(f"✓ Loaded {len(df)} papers")
print()

# Clean paper names for display
df['short_name'] = df['paper_id'].apply(lambda x: x[:30] + '...' if len(x) > 30 else x)

# ============================================================================
# FIGURE 1: Overall Metrics Bar Chart
# ============================================================================
print("Creating Figure 1: Overall Metrics...")

fig, ax = plt.subplots(figsize=(12, 6))

metrics = ['json_validity', 'evidence_precision', 'field_coverage', 
           'numeric_consistency', 'summary_alignment']
metric_names = ['JSON Validity', 'Evidence\nPrecision', 'Field\nCoverage', 
                'Numeric\nConsistency', 'Summary\nAlignment']

averages = [df[m].mean() for m in metrics]
colors = ['#2ecc71' if avg >= 0.9 else '#f39c12' if avg >= 0.7 else '#e74c3c' 
          for avg in averages]

bars = ax.bar(metric_names, averages, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.2f}',
            ha='center', va='bottom', fontsize=12, fontweight='bold')

ax.set_ylim(0, 1.1)
ax.set_ylabel('Average Score', fontsize=12, fontweight='bold')
ax.set_title('Batch Evaluation - Overall Metrics (10 Papers)', 
             fontsize=14, fontweight='bold', pad=20)
ax.axhline(y=1.0, color='green', linestyle='--', alpha=0.3, label='Perfect (1.0)')
ax.axhline(y=0.8, color='orange', linestyle='--', alpha=0.3, label='Good (0.8)')
ax.grid(axis='y', alpha=0.3)
ax.legend()

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "01_overall_metrics.png", dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: 01_overall_metrics.png")
plt.close()

# ============================================================================
# FIGURE 2: Per-Paper Metrics Heatmap
# ============================================================================
print("Creating Figure 2: Per-Paper Heatmap...")

fig, ax = plt.subplots(figsize=(14, 10))

# Prepare data for heatmap
heatmap_data = df[metrics].values
paper_names = df['short_name'].values

# Create heatmap
im = ax.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

# Set ticks
ax.set_xticks(np.arange(len(metric_names)))
ax.set_yticks(np.arange(len(paper_names)))
ax.set_xticklabels(metric_names, fontsize=10)
ax.set_yticklabels(paper_names, fontsize=9)

# Rotate x labels
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# Add text annotations
for i in range(len(paper_names)):
    for j in range(len(metrics)):
        value = heatmap_data[i, j]
        text = ax.text(j, i, f'{value:.2f}',
                      ha="center", va="center", color="black" if value > 0.5 else "white",
                      fontsize=8, fontweight='bold')

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Score', rotation=270, labelpad=20, fontsize=11, fontweight='bold')

ax.set_title('Per-Paper Metrics Heatmap', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "02_per_paper_heatmap.png", dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: 02_per_paper_heatmap.png")
plt.close()

# ============================================================================
# FIGURE 3: Metric Distribution Box Plot
# ============================================================================
print("Creating Figure 3: Metric Distributions...")

fig, ax = plt.subplots(figsize=(12, 7))

# Prepare data for box plot
data_for_box = [df[m].values for m in metrics]

bp = ax.boxplot(data_for_box, labels=metric_names, patch_artist=True,
                showmeans=True, meanline=True)

# Color boxes
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

ax.set_ylabel('Score', fontsize=12, fontweight='bold')
ax.set_title('Metric Distribution Across All Papers', fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(-0.05, 1.15)
ax.axhline(y=1.0, color='green', linestyle='--', alpha=0.3, label='Perfect')
ax.axhline(y=0.8, color='orange', linestyle='--', alpha=0.3, label='Good')
ax.grid(axis='y', alpha=0.3)
ax.legend()

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "03_metric_distributions.png", dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: 03_metric_distributions.png")
plt.close()

# ============================================================================
# FIGURE 4: Top Performers Radar Chart
# ============================================================================
print("Creating Figure 4: Top Performers Radar...")

# Get top 3 papers by average score
df['avg_score'] = df[metrics].mean(axis=1)
top_papers = df.nlargest(3, 'avg_score')

fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
angles += angles[:1]  # Complete the circle

for idx, (_, paper) in enumerate(top_papers.iterrows()):
    values = [paper[m] for m in metrics]
    values += values[:1]  # Complete the circle
    
    ax.plot(angles, values, 'o-', linewidth=2, label=paper['short_name'], alpha=0.8)
    ax.fill(angles, values, alpha=0.15)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(metric_names, fontsize=10)
ax.set_ylim(0, 1)
ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=9)
ax.grid(True)
ax.set_title('Top 3 Performers - Radar Chart', fontsize=14, fontweight='bold', pad=30)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "04_top_performers_radar.png", dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: 04_top_performers_radar.png")
plt.close()

# ============================================================================
# FIGURE 5: Paper Rankings
# ============================================================================
print("Creating Figure 5: Paper Rankings...")

fig, ax = plt.subplots(figsize=(12, 8))

# Sort by average score
df_sorted = df.sort_values('avg_score', ascending=True)

y_pos = np.arange(len(df_sorted))
colors_rank = ['#2ecc71' if x >= 0.9 else '#f39c12' if x >= 0.7 else '#e74c3c' 
               for x in df_sorted['avg_score']]

bars = ax.barh(y_pos, df_sorted['avg_score'], color=colors_rank, alpha=0.8, edgecolor='black')

# Add value labels
for i, (bar, val) in enumerate(zip(bars, df_sorted['avg_score'])):
    ax.text(val + 0.02, bar.get_y() + bar.get_height()/2, f'{val:.3f}',
            va='center', fontsize=9, fontweight='bold')

ax.set_yticks(y_pos)
ax.set_yticklabels(df_sorted['short_name'], fontsize=9)
ax.set_xlabel('Average Score', fontsize=12, fontweight='bold')
ax.set_xlim(0, 1.1)
ax.set_title('Paper Rankings by Average Score', fontsize=14, fontweight='bold', pad=20)
ax.axvline(x=1.0, color='green', linestyle='--', alpha=0.3, label='Perfect')
ax.axvline(x=0.9, color='blue', linestyle='--', alpha=0.3, label='Excellent')
ax.axvline(x=0.8, color='orange', linestyle='--', alpha=0.3, label='Good')
ax.grid(axis='x', alpha=0.3)
ax.legend()

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "05_paper_rankings.png", dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: 05_paper_rankings.png")
plt.close()

# ============================================================================
# FIGURE 6: Correlation Matrix
# ============================================================================
print("Creating Figure 6: Metric Correlations...")

fig, ax = plt.subplots(figsize=(10, 8))

correlation = df[metrics].corr()

# Create heatmap
sns.heatmap(correlation, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8},
            xticklabels=metric_names, yticklabels=metric_names, ax=ax)

ax.set_title('Metric Correlation Matrix', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "06_correlation_matrix.png", dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: 06_correlation_matrix.png")
plt.close()

# ============================================================================
# FIGURE 7: Score Distribution Histogram
# ============================================================================
print("Creating Figure 7: Score Distribution...")

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, (metric, name) in enumerate(zip(metrics, metric_names)):
    ax = axes[idx]
    
    values = df[metric].values
    ax.hist(values, bins=10, alpha=0.7, color=colors[idx], edgecolor='black')
    ax.axvline(values.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {values.mean():.2f}')
    ax.set_xlabel('Score', fontsize=10)
    ax.set_ylabel('Frequency', fontsize=10)
    ax.set_title(f'{name} Distribution', fontsize=11, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)

# Remove extra subplot
axes[-1].remove()

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "07_score_distributions.png", dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: 07_score_distributions.png")
plt.close()

# ============================================================================
# FIGURE 8: Perfect Scores Count
# ============================================================================
print("Creating Figure 8: Perfect Scores Analysis...")

fig, ax = plt.subplots(figsize=(12, 7))

perfect_counts = [sum(df[m] == 1.0) for m in metrics]
good_counts = [sum((df[m] >= 0.8) & (df[m] < 1.0)) for m in metrics]
moderate_counts = [sum((df[m] >= 0.6) & (df[m] < 0.8)) for m in metrics]
poor_counts = [sum(df[m] < 0.6) for m in metrics]

x = np.arange(len(metric_names))
width = 0.6

p1 = ax.bar(x, perfect_counts, width, label='Perfect (1.0)', color='#2ecc71', alpha=0.9)
p2 = ax.bar(x, good_counts, width, bottom=perfect_counts, label='Good (0.8-0.99)', color='#3498db', alpha=0.9)
p3 = ax.bar(x, moderate_counts, width, bottom=np.array(perfect_counts)+np.array(good_counts), 
            label='Moderate (0.6-0.79)', color='#f39c12', alpha=0.9)
p4 = ax.bar(x, poor_counts, width, 
            bottom=np.array(perfect_counts)+np.array(good_counts)+np.array(moderate_counts),
            label='Below 0.6', color='#e74c3c', alpha=0.9)

ax.set_ylabel('Number of Papers', fontsize=12, fontweight='bold')
ax.set_title('Score Distribution by Metric', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(metric_names, fontsize=10)
ax.legend()
ax.grid(axis='y', alpha=0.3)

# Add count labels
for i, (p, g, m, po) in enumerate(zip(perfect_counts, good_counts, moderate_counts, poor_counts)):
    if p > 0:
        ax.text(i, p/2, str(p), ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    if g > 0:
        ax.text(i, p + g/2, str(g), ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    if m > 0:
        ax.text(i, p + g + m/2, str(m), ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    if po > 0:
        ax.text(i, p + g + m + po/2, str(po), ha='center', va='center', fontsize=10, fontweight='bold', color='white')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "08_score_distribution_stacked.png", dpi=300, bbox_inches='tight')
print(f"  ✓ Saved: 08_score_distribution_stacked.png")
plt.close()

# ============================================================================
# Generate Summary Statistics
# ============================================================================
print()
print("Generating summary statistics...")

summary_stats = {
    "total_papers": len(df),
    "metrics": {},
    "top_performers": [],
    "perfect_scores": {}
}

for metric, name in zip(metrics, metric_names):
    summary_stats["metrics"][name] = {
        "mean": float(df[metric].mean()),
        "std": float(df[metric].std()),
        "min": float(df[metric].min()),
        "max": float(df[metric].max()),
        "perfect_count": int(sum(df[metric] == 1.0))
    }

# Top performers
for _, paper in df.nlargest(3, 'avg_score').iterrows():
    summary_stats["top_performers"].append({
        "name": paper['paper_id'],
        "average_score": float(paper['avg_score']),
        "metrics": {m: float(paper[m]) for m in metrics}
    })

# Papers with perfect scores
for _, paper in df[df['avg_score'] == 1.0].iterrows():
    summary_stats["perfect_scores"][paper['paper_id']] = {
        "all_metrics_perfect": True
    }

# Save stats
with open(OUTPUT_DIR / "summary_statistics.json", 'w') as f:
    json.dump(summary_stats, f, indent=2)

print(f"  ✓ Saved: summary_statistics.json")

# ============================================================================
# Summary
# ============================================================================
print()
print("="*60)
print("VISUALIZATION COMPLETE")
print("="*60)
print(f"✓ Generated 8 visualizations")
print(f"✓ Saved to: {OUTPUT_DIR}")
print()
print("Files created:")
print("  1. 01_overall_metrics.png - Bar chart of average scores")
print("  2. 02_per_paper_heatmap.png - Heatmap of all papers")
print("  3. 03_metric_distributions.png - Box plots")
print("  4. 04_top_performers_radar.png - Top 3 radar chart")
print("  5. 05_paper_rankings.png - Horizontal bar rankings")
print("  6. 06_correlation_matrix.png - Metric correlations")
print("  7. 07_score_distributions.png - Histograms")
print("  8. 08_score_distribution_stacked.png - Stacked bar chart")
print("  9. summary_statistics.json - JSON stats")
print()
print("="*60)
