"""
Threat Detection Visualization Module
Creates visualizations for Grafana dashboard and analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ThreatVisualization:
    """
    Create visualizations and export metrics for Grafana dashboard
    """
    
    def __init__(self, style='darkgrid'):
        """
        Initialize visualization settings
        
        Args:
            style: Seaborn style ('darkgrid', 'whitegrid', 'dark', 'white', 'ticks')
        """
        sns.set_style(style)
        self.colors = {
            'threat': '#e74c3c',
            'normal': '#2ecc71',
            'primary': '#3498db',
            'warning': '#f39c12',
            'danger': '#e74c3c'
        }
    
    def plot_class_distribution(self, y_train, y_test, figsize=(10, 5), save_path=None):
        """
        Plot distribution of classes in train and test sets
        
        Args:
            y_train: Training labels
            y_test: Test labels
            figsize: Figure size
            save_path: Path to save plot
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        # Train set
        train_counts = pd.Series(y_train).value_counts()
        axes[0].bar(train_counts.index, train_counts.values, 
                    color=[self.colors['normal'], self.colors['threat']])
        axes[0].set_title('Training Set Distribution', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Class (0=Normal, 1=Threat)')
        axes[0].set_ylabel('Count')
        axes[0].set_xticks([0, 1])
        
        # Test set
        test_counts = pd.Series(y_test).value_counts()
        axes[1].bar(test_counts.index, test_counts.values,
                    color=[self.colors['normal'], self.colors['threat']])
        axes[1].set_title('Test Set Distribution', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Class (0=Normal, 1=Threat)')
        axes[1].set_ylabel('Count')
        axes[1].set_xticks([0, 1])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Class distribution plot saved to {save_path}")
        
        plt.show()
    
    def plot_metrics_comparison(self, metrics_dict, figsize=(10, 6), save_path=None):
        """
        Plot comparison of different metrics
        
        Args:
            metrics_dict: Dictionary of metrics (e.g., {'accuracy': 0.95, 'precision': 0.92, ...})
            figsize: Figure size
            save_path: Path to save plot
        """
        # Filter out non-numeric metrics
        numeric_metrics = {k: v for k, v in metrics_dict.items() 
                          if isinstance(v, (int, float)) and v is not None}
        
        metrics_names = list(numeric_metrics.keys())
        metrics_values = list(numeric_metrics.values())
        
        plt.figure(figsize=figsize)
        bars = plt.bar(metrics_names, metrics_values, color=self.colors['primary'], alpha=0.7)
        
        # Color bars based on value
        for i, bar in enumerate(bars):
            if metrics_values[i] >= 0.9:
                bar.set_color(self.colors['normal'])
            elif metrics_values[i] >= 0.7:
                bar.set_color(self.colors['warning'])
            else:
                bar.set_color(self.colors['danger'])
        
        plt.title('Model Performance Metrics', fontsize=14, fontweight='bold')
        plt.ylabel('Score', fontsize=12)
        plt.ylim([0, 1.0])
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on bars
        for i, v in enumerate(metrics_values):
            plt.text(i, v + 0.02, f'{v:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Metrics comparison plot saved to {save_path}")
        
        plt.show()
    
    def plot_prediction_distribution(self, y_true, y_pred_proba, figsize=(12, 5), save_path=None):
        """
        Plot distribution of prediction probabilities
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            figsize: Figure size
            save_path: Path to save plot
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        # Separate by true class
        normal_probs = y_pred_proba[y_true == 0]
        threat_probs = y_pred_proba[y_true == 1]
        
        # Histogram for normal class
        axes[0].hist(normal_probs, bins=50, color=self.colors['normal'], alpha=0.7, edgecolor='black')
        axes[0].axvline(0.5, color='red', linestyle='--', linewidth=2, label='Threshold (0.5)')
        axes[0].set_title('Prediction Distribution - Normal Traffic', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Predicted Threat Probability')
        axes[0].set_ylabel('Frequency')
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # Histogram for threat class
        axes[1].hist(threat_probs, bins=50, color=self.colors['threat'], alpha=0.7, edgecolor='black')
        axes[1].axvline(0.5, color='red', linestyle='--', linewidth=2, label='Threshold (0.5)')
        axes[1].set_title('Prediction Distribution - Threat Traffic', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Predicted Threat Probability')
        axes[1].set_ylabel('Frequency')
        axes[1].legend()
        axes[1].grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Prediction distribution plot saved to {save_path}")
        
        plt.show()
    
    def plot_false_positive_negative_analysis(self, fp_df, fn_df, top_features=5, figsize=(14, 6), save_path=None):
        """
        Analyze characteristics of false positives and false negatives
        
        Args:
            fp_df: DataFrame of false positives
            fn_df: DataFrame of false negatives
            top_features: Number of top features to analyze
            figsize: Figure size
            save_path: Path to save plot
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        # Analyze false positives
        if len(fp_df) > 0:
            fp_features = fp_df.drop(columns=['y_true', 'y_pred', 'threat_probability'], errors='ignore')
            fp_std = fp_features.std().sort_values(ascending=False).head(top_features)
            
            axes[0].barh(range(len(fp_std)), fp_std.values, color=self.colors['danger'])
            axes[0].set_yticks(range(len(fp_std)))
            axes[0].set_yticklabels(fp_std.index)
            axes[0].set_title(f'False Positives - Most Variable Features\n(Count: {len(fp_df)})', 
                            fontsize=12, fontweight='bold')
            axes[0].set_xlabel('Standard Deviation')
        else:
            axes[0].text(0.5, 0.5, 'No False Positives', ha='center', va='center', fontsize=14)
            axes[0].set_title('False Positives', fontsize=12, fontweight='bold')
        
        # Analyze false negatives
        if len(fn_df) > 0:
            fn_features = fn_df.drop(columns=['y_true', 'y_pred', 'threat_probability'], errors='ignore')
            fn_std = fn_features.std().sort_values(ascending=False).head(top_features)
            
            axes[1].barh(range(len(fn_std)), fn_std.values, color=self.colors['warning'])
            axes[1].set_yticks(range(len(fn_std)))
            axes[1].set_yticklabels(fn_std.index)
            axes[1].set_title(f'False Negatives - Most Variable Features\n(Count: {len(fn_df)})', 
                            fontsize=12, fontweight='bold')
            axes[1].set_xlabel('Standard Deviation')
        else:
            axes[1].text(0.5, 0.5, 'No False Negatives', ha='center', va='center', fontsize=14)
            axes[1].set_title('False Negatives', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"FP/FN analysis plot saved to {save_path}")
        
        plt.show()
    
    def create_dashboard_summary(self, metrics, feature_importance, fp_count, fn_count, output_path='dashboard/metrics_summary.json'):
        """
        Create JSON summary for Grafana dashboard
        
        Args:
            metrics: Dictionary of model metrics
            feature_importance: DataFrame of feature importance
            fp_count: Number of false positives
            fn_count: Number of false negatives
            output_path: Path to save JSON file
        """
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
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=4)
        
        print(f"\nDashboard summary saved to {output_path}")
        return summary
    
    def plot_comprehensive_dashboard(self, metrics, feature_importance, y_true, y_pred, y_pred_proba, 
                                    figsize=(16, 12), save_path=None):
        """
        Create comprehensive visualization dashboard
        
        Args:
            metrics: Dictionary of model metrics
            feature_importance: DataFrame of feature importance
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities
            figsize: Figure size
            save_path: Path to save plot
        """
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Confusion Matrix (top-left)
        ax1 = fig.add_subplot(gs[0, 0])
        cm = metrics['confusion_matrix']
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, ax=ax1,
                    xticklabels=['Normal', 'Threat'], yticklabels=['Normal', 'Threat'])
        ax1.set_title('Confusion Matrix', fontweight='bold')
        ax1.set_ylabel('True Label')
        ax1.set_xlabel('Predicted Label')
        
        # 2. Metrics Bar Chart (top-middle)
        ax2 = fig.add_subplot(gs[0, 1])
        metric_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        metric_values = [metrics['accuracy'], metrics['precision'], metrics['recall'], metrics['f1_score']]
        bars = ax2.bar(metric_names, metric_values, color=self.colors['primary'], alpha=0.7)
        for i, bar in enumerate(bars):
            if metric_values[i] >= 0.9:
                bar.set_color(self.colors['normal'])
            elif metric_values[i] >= 0.7:
                bar.set_color(self.colors['warning'])
        ax2.set_title('Performance Metrics', fontweight='bold')
        ax2.set_ylim([0, 1])
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. ROC Curve (top-right)
        ax3 = fig.add_subplot(gs[0, 2])
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
        ax3.plot(fpr, tpr, color=self.colors['primary'], lw=2, label=f"AUC = {metrics.get('roc_auc', 0):.3f}")
        ax3.plot([0, 1], [0, 1], 'k--', lw=1, label='Random')
        ax3.set_title('ROC Curve', fontweight='bold')
        ax3.set_xlabel('False Positive Rate')
        ax3.set_ylabel('True Positive Rate')
        ax3.legend(loc='lower right')
        ax3.grid(alpha=0.3)
        
        # 4. Feature Importance (middle row, spanning 2 columns)
        ax4 = fig.add_subplot(gs[1, :2])
        top_features = feature_importance.head(10)
        ax4.barh(range(len(top_features)), top_features['importance'].values, color=self.colors['primary'])
        ax4.set_yticks(range(len(top_features)))
        ax4.set_yticklabels(top_features['feature'].values)
        ax4.set_title('Top 10 Feature Importance', fontweight='bold')
        ax4.set_xlabel('Importance Score')
        ax4.invert_yaxis()
        
        # 5. Class Distribution (middle-right)
        ax5 = fig.add_subplot(gs[1, 2])
        class_counts = pd.Series(y_true).value_counts()
        ax5.pie(class_counts.values, labels=['Normal', 'Threat'], autopct='%1.1f%%',
                colors=[self.colors['normal'], self.colors['threat']], startangle=90)
        ax5.set_title('Class Distribution', fontweight='bold')
        
        # 6. Prediction Distribution - Normal (bottom-left)
        ax6 = fig.add_subplot(gs[2, 0])
        normal_probs = y_pred_proba[y_true == 0]
        ax6.hist(normal_probs, bins=30, color=self.colors['normal'], alpha=0.7, edgecolor='black')
        ax6.axvline(0.5, color='red', linestyle='--', linewidth=2)
        ax6.set_title('Normal Traffic Predictions', fontweight='bold')
        ax6.set_xlabel('Threat Probability')
        ax6.set_ylabel('Frequency')
        
        # 7. Prediction Distribution - Threat (bottom-middle)
        ax7 = fig.add_subplot(gs[2, 1])
        threat_probs = y_pred_proba[y_true == 1]
        ax7.hist(threat_probs, bins=30, color=self.colors['threat'], alpha=0.7, edgecolor='black')
        ax7.axvline(0.5, color='red', linestyle='--', linewidth=2)
        ax7.set_title('Threat Traffic Predictions', fontweight='bold')
        ax7.set_xlabel('Threat Probability')
        ax7.set_ylabel('Frequency')
        
        # 8. Error Summary (bottom-right)
        ax8 = fig.add_subplot(gs[2, 2])
        tn, fp, fn, tp = cm.ravel()
        error_data = ['True\nNegatives', 'False\nPositives', 'False\nNegatives', 'True\nPositives']
        error_counts = [tn, fp, fn, tp]
        error_colors = [self.colors['normal'], self.colors['danger'], self.colors['warning'], self.colors['normal']]
        bars = ax8.bar(error_data, error_counts, color=error_colors, alpha=0.7)
        ax8.set_title('Prediction Breakdown', fontweight='bold')
        ax8.set_ylabel('Count')
        ax8.tick_params(axis='x', labelsize=8)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax8.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        plt.suptitle('Threat Detection Model - Comprehensive Dashboard', 
                    fontsize=16, fontweight='bold', y=0.995)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Comprehensive dashboard saved to {save_path}")
        
        plt.show()


# Example usage
if __name__ == "__main__":
    print("Visualization module loaded. Import and use in your main script.")
