"""
Threat Detection Model Training and Evaluation Module
Handles XGBoost model training, evaluation, and feature importance analysis
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import warnings
warnings.filterwarnings('ignore')


class ThreatDetectionModel:
    """
    XGBoost-based threat detection model with comprehensive evaluation
    """
    
    def __init__(self, random_state=42):
        """
        Initialize the model
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.model = None
        self.random_state = random_state
        self.feature_names = None
        self.best_params = None
        
    def train_model(self, X_train, y_train, X_val=None, y_val=None, params=None):
        """
        Train XGBoost model
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            params: Custom hyperparameters (optional)
            
        Returns:
            Trained model
        """
        print("\n=== Training XGBoost Model ===")
        
        # Default parameters optimized for cybersecurity threat detection
        default_params = {
            'objective': 'binary:logistic',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'gamma': 0.1,
            'min_child_weight': 1,
            'random_state': self.random_state,
            'eval_metric': 'logloss',
            'early_stopping_rounds': 20
        }
        
        # Update with custom parameters if provided
        if params:
            default_params.update(params)
        
        self.best_params = default_params
        
        # Create model
        self.model = xgb.XGBClassifier(**default_params)
        
        # Set up evaluation set if validation data provided
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))
        
        # Train model
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False
        )
        
        # Store feature names
        if isinstance(X_train, pd.DataFrame):
            self.feature_names = X_train.columns.tolist()
        else:
            self.feature_names = [f"feature_{i}" for i in range(X_train.shape[1])]
        
        print(f"Model trained with {len(self.feature_names)} features")
        print(f"Best iteration: {self.model.best_iteration}")
        
        return self.model
    
    def predict(self, X):
        """
        Make predictions
        
        Args:
            X: Features to predict
            
        Returns:
            Predicted labels
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """
        Predict probabilities
        
        Args:
            X: Features to predict
            
        Returns:
            Predicted probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        return self.model.predict_proba(X)
    
    def evaluate_model(self, X_test, y_test, dataset_name="Test"):
        """
        Comprehensive model evaluation
        
        Args:
            X_test: Test features
            y_test: Test labels
            dataset_name: Name of dataset being evaluated
            
        Returns:
            Dictionary of evaluation metrics
        """
        print(f"\n=== Evaluating on {dataset_name} Set ===")
        
        # Make predictions
        y_pred = self.predict(X_test)
        y_pred_proba = self.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # ROC AUC (if binary classification)
        try:
            roc_auc = roc_auc_score(y_test, y_pred_proba)
        except:
            roc_auc = None
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Print metrics
        print(f"\nAccuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1-Score:  {f1:.4f}")
        if roc_auc:
            print(f"ROC AUC:   {roc_auc:.4f}")
        
        print("\nConfusion Matrix:")
        print(cm)
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, zero_division=0))
        
        # Store metrics
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm,
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba,
            'y_true': y_test
        }
        
        return metrics
    
    def analyze_false_positives_negatives(self, X_test, y_test, feature_names=None):
        """
        Analyze false positives and false negatives
        
        Args:
            X_test: Test features
            y_test: Test labels
            feature_names: List of feature names
            
        Returns:
            DataFrames of false positives and false negatives
        """
        print("\n=== Analyzing False Positives and False Negatives ===")
        
        # Make predictions
        y_pred = self.predict(X_test)
        y_pred_proba = self.predict_proba(X_test)[:, 1]
        
        # Convert to DataFrame if not already
        if not isinstance(X_test, pd.DataFrame):
            if feature_names is None:
                feature_names = self.feature_names
            X_test_df = pd.DataFrame(X_test, columns=feature_names)
        else:
            X_test_df = X_test.copy()
        
        # Add predictions and labels
        X_test_df['y_true'] = y_test.values if hasattr(y_test, 'values') else y_test
        X_test_df['y_pred'] = y_pred
        X_test_df['threat_probability'] = y_pred_proba
        
        # Identify false positives and false negatives
        false_positives = X_test_df[(X_test_df['y_true'] == 0) & (X_test_df['y_pred'] == 1)]
        false_negatives = X_test_df[(X_test_df['y_true'] == 1) & (X_test_df['y_pred'] == 0)]
        
        print(f"\nFalse Positives: {len(false_positives)} ({len(false_positives)/len(X_test_df)*100:.2f}%)")
        print(f"False Negatives: {len(false_negatives)} ({len(false_negatives)/len(X_test_df)*100:.2f}%)")
        
        # Show samples
        if len(false_positives) > 0:
            print("\nSample False Positives (Top 5 by confidence):")
            print(false_positives.nlargest(5, 'threat_probability')[['y_true', 'y_pred', 'threat_probability']])
        
        if len(false_negatives) > 0:
            print("\nSample False Negatives (Top 5 by missed confidence):")
            print(false_negatives.nsmallest(5, 'threat_probability')[['y_true', 'y_pred', 'threat_probability']])
        
        return false_positives, false_negatives
    
    def get_feature_importance(self, top_n=20, importance_type='weight'):
        """
        Get feature importance from trained model
        
        Args:
            top_n: Number of top features to return
            importance_type: Type of importance ('weight', 'gain', 'cover')
            
        Returns:
            DataFrame of feature importances
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        print(f"\n=== Feature Importance (Top {top_n}) ===")
        
        # Get importance scores
        importance_scores = self.model.get_booster().get_score(importance_type=importance_type)
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            'feature': list(importance_scores.keys()),
            'importance': list(importance_scores.values())
        })
        
        # Map feature indices to names if available
        if self.feature_names:
            importance_df['feature'] = importance_df['feature'].apply(
                lambda x: self.feature_names[int(x.replace('f', ''))] if x.startswith('f') else x
            )
        
        # Sort by importance
        importance_df = importance_df.sort_values('importance', ascending=False).reset_index(drop=True)
        
        # Show top features
        print(importance_df.head(top_n))
        
        return importance_df.head(top_n)
    
    def plot_feature_importance(self, top_n=20, figsize=(10, 8), save_path=None):
        """
        Plot feature importance
        
        Args:
            top_n: Number of top features to plot
            figsize: Figure size
            save_path: Path to save plot (optional)
        """
        importance_df = self.get_feature_importance(top_n=top_n)
        
        plt.figure(figsize=figsize)
        sns.barplot(data=importance_df, x='importance', y='feature', palette='viridis')
        plt.title(f'Top {top_n} Most Important Features for Threat Detection', fontsize=14, fontweight='bold')
        plt.xlabel('Importance Score', fontsize=12)
        plt.ylabel('Feature', fontsize=12)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Feature importance plot saved to {save_path}")
        
        plt.show()
    
    def plot_confusion_matrix(self, cm, figsize=(8, 6), save_path=None):
        """
        Plot confusion matrix
        
        Args:
            cm: Confusion matrix
            figsize: Figure size
            save_path: Path to save plot (optional)
        """
        plt.figure(figsize=figsize)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True,
                    xticklabels=['Normal', 'Threat'], yticklabels=['Normal', 'Threat'])
        plt.title('Confusion Matrix', fontsize=14, fontweight='bold')
        plt.ylabel('True Label', fontsize=12)
        plt.xlabel('Predicted Label', fontsize=12)
        
        # Add percentages
        total = cm.sum()
        tn, fp, fn, tp = cm.ravel()
        plt.text(0.5, 0.5, f'{tn/total*100:.1f}%', ha='center', va='center', fontsize=10, color='gray')
        plt.text(1.5, 0.5, f'{fp/total*100:.1f}%', ha='center', va='center', fontsize=10, color='gray')
        plt.text(0.5, 1.5, f'{fn/total*100:.1f}%', ha='center', va='center', fontsize=10, color='gray')
        plt.text(1.5, 1.5, f'{tp/total*100:.1f}%', ha='center', va='center', fontsize=10, color='gray')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Confusion matrix plot saved to {save_path}")
        
        plt.show()
    
    def plot_roc_curve(self, y_test, y_pred_proba, figsize=(8, 6), save_path=None):
        """
        Plot ROC curve
        
        Args:
            y_test: True labels
            y_pred_proba: Predicted probabilities
            figsize: Figure size
            save_path: Path to save plot (optional)
        """
        fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        plt.figure(figsize=figsize)
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curve - Threat Detection', fontsize=14, fontweight='bold')
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"ROC curve plot saved to {save_path}")
        
        plt.show()
    
    def save_model(self, filepath='threat_detection_model.pkl'):
        """
        Save trained model
        
        Args:
            filepath: Path to save model
        """
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'best_params': self.best_params
            }, f)
        print(f"\nModel saved to {filepath}")
    
    def load_model(self, filepath='threat_detection_model.pkl'):
        """
        Load trained model
        
        Args:
            filepath: Path to load model from
        """
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
            self.model = state['model']
            self.feature_names = state['feature_names']
            self.best_params = state.get('best_params')
        print(f"Model loaded from {filepath}")


# Example usage
if __name__ == "__main__":
    # This assumes you have preprocessed data from preprocess.py
    from preprocess import ThreatDataPreprocessor
    
    # Load and preprocess data
    preprocessor = ThreatDataPreprocessor()
    X_train, X_test, y_train, y_test, feature_names = preprocessor.preprocess_pipeline(
        filepath='../data/raw_data.csv',
        target_col='threat'
    )
    
    # Initialize and train model
    model = ThreatDetectionModel(random_state=42)
    model.train_model(X_train, y_train)
    
    # Evaluate model
    metrics = model.evaluate_model(X_test, y_test)
    
    # Analyze false positives/negatives
    fp, fn = model.analyze_false_positives_negatives(X_test, y_test, feature_names)
    
    # Feature importance
    importance = model.get_feature_importance(top_n=20)
    model.plot_feature_importance(top_n=20)
    
    # Plot confusion matrix
    model.plot_confusion_matrix(metrics['confusion_matrix'])
    
    # Plot ROC curve
    model.plot_roc_curve(y_test, metrics['y_pred_proba'])
    
    # Save model
    model.save_model('../src/threat_detection_model.pkl')
