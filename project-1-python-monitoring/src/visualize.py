"""
Threat Detection Visualization Module
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ThreatVisualization:
    """Create visualizations and export metrics for model analysis."""
    
    def __init__(self, style='darkgrid'):
        sns.set_style(style)
        self.colors = {
            'threat': '#e74c3c',
            'normal': '#2ecc71',
            'primary': '#3498db',
            'warning': '#f39c12',
            'danger': '#e74c3c'
        }
    
    def plot_class_distribution(self, y_train, y_test, figsize=(10, 5), save_path=None, show_plot=True):
        """Plot distribution of classes in train and test sets."""
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        for idx, (data, title) in enumerate([(y_train, 'Training Set'), (y_test, 'Test Set')]):
            counts = pd.Series(data).value_counts()
            axes[idx].bar(counts.index, counts.values, 
                        color=[self.colors['normal'], self.colors['threat']])
            axes[idx].set_title(f'{title} Distribution', fontsize=12, fontweight='bold')
            axes[idx].set_xlabel('Class (0=Normal, 1=Threat)')
            axes[idx].set_ylabel('Count')
            axes[idx].set_xticks([0, 1])
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Class distribution plot saved to {save_path}")
        if show_plot:
            plt.show()
        plt.close()
    
    def plot_metrics_comparison(self, metrics_dict, figsize=(10, 6), save_path=None, show_plot=True):
        """Plot comparison of different metrics."""
        numeric_metrics = {k: v for k, v in metrics_dict.items() 
                          if isinstance(v, (int, float)) and v is not None}
        
        plt.figure(figsize=figsize)
        bars = plt.bar(numeric_metrics.keys(), numeric_metrics.values(), color=self.colors['primary'], alpha=0.7)
        
        for bar, val in zip(bars, numeric_metrics.values()):
            if val >= 0.9:
                bar.set_color(self.colors['normal'])
            elif val >= 0.7:
                bar.set_color(self.colors['warning'])
            else:
                bar.set_color(self.colors['danger'])
            plt.text(bar.get_x() + bar.get_width()/2., val + 0.02, f'{val:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.title('Model Performance Metrics', fontsize=14, fontweight='bold')
        plt.ylabel('Score', fontsize=12)
        plt.ylim([0, 1.1])
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Metrics comparison plot saved to {save_path}")
        if show_plot:
            plt.show()
        plt.close()
    
    def plot_prediction_distribution(self, y_true, y_pred_proba, figsize=(12, 5), save_path=None, show_plot=True):
        """Plot distribution of prediction probabilities."""
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        for idx, (label, color, title) in enumerate([(0, 'normal', 'Normal Traffic'), (1, 'threat', 'Threat Traffic')]):
            probs = y_pred_proba[y_true == label]
            axes[idx].hist(probs, bins=50, color=self.colors[color], alpha=0.7, edgecolor='black')
            axes[idx].axvline(0.5, color='red', linestyle='--', linewidth=2, label='Threshold (0.5)')
            axes[idx].set_title(f'Prediction Distribution - {title}', fontsize=12, fontweight='bold')
            axes[idx].set_xlabel('Predicted Threat Probability')
            axes[idx].set_ylabel('Frequency')
            axes[idx].legend()
            axes[idx].grid(alpha=0.3)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Prediction distribution plot saved to {save_path}")
        if show_plot:
            plt.show()
        plt.close()
    
    def create_dashboard_summary(self, metrics, feature_importance, fp_count, fn_count, output_path='dashboard/metrics_summary.json'):
        """Create JSON summary for model metrics."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'model_performance': {
                'accuracy': float(metrics.get('accuracy', 0)),
                'precision': float(metrics.get('precision', 0)),
                'recall': float(metrics.get('recall', 0)),
                'f1_score': float(metrics.get('f1_score', 0)),
                'roc_auc': float(metrics.get('roc_auc', 0)) if metrics.get('roc_auc') else None
            },
            'error_analysis': {
                'false_positives': int(fp_count),
                'false_negatives': int(fn_count),
                'total_errors': int(fp_count + fn_count)
            },
            'top_features': feature_importance.to_dict('records') if isinstance(feature_importance, pd.DataFrame) else [],
            'confusion_matrix': {
                'true_negatives': int(metrics['confusion_matrix'][0][0]),
                'false_positives': int(metrics['confusion_matrix'][0][1]),
                'false_negatives': int(metrics['confusion_matrix'][1][0]),
                'true_positives': int(metrics['confusion_matrix'][1][1])
            } if 'confusion_matrix' in metrics else {}
        }
        
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=4)
        
        print(f"\nDashboard summary saved to {output_path}")
        return summary

if __name__ == "__main__":
    print("Visualization module loaded.")
