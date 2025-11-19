"""
Threat Detection Model Training and Evaluation Module
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import pickle
import warnings
warnings.filterwarnings('ignore')


class ThreatDetectionModel:
    """XGBoost-based threat detection model."""
    
    def __init__(self, random_state=42):
        self.model = None
        self.random_state = random_state
        self.feature_names = None
        self.best_params = None
        
    def train_model(self, X_train, y_train, X_val=None, y_val=None, params=None):
        """Train XGBoost model."""
        print("\n=== Training XGBoost Model ===")
        
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
        
        if params:
            default_params.update(params)
        
        self.best_params = default_params
        self.model = xgb.XGBClassifier(**default_params)
        
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))
        
        self.model.fit(X_train, y_train, eval_set=eval_set, verbose=False)
        
        if isinstance(X_train, pd.DataFrame):
            self.feature_names = X_train.columns.tolist()
        else:
            self.feature_names = [f"feature_{i}" for i in range(X_train.shape[1])]
        
        print(f"Model trained with {len(self.feature_names)} features")
        print(f"Best iteration: {self.model.best_iteration}")
        
        return self.model
    
    def predict(self, X):
        if self.model is None:
            raise ValueError("Model not trained yet.")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        if self.model is None:
            raise ValueError("Model not trained yet.")
        return self.model.predict_proba(X)
    
    def evaluate_model(self, X_test, y_test, dataset_name="Test"):
        """Evaluate model performance."""
        print(f"\n=== Evaluating on {dataset_name} Set ===")
        
        y_pred = self.predict(X_test)
        y_pred_proba = self.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        try:
            roc_auc = roc_auc_score(y_test, y_pred_proba)
        except:
            roc_auc = None
        
        cm = confusion_matrix(y_test, y_pred)
        
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1-Score:  {f1:.4f}")
        if roc_auc:
            print(f"ROC AUC:   {roc_auc:.4f}")
        
        return {
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
    
    def analyze_false_positives_negatives(self, X_test, y_test, feature_names=None):
        """Analyze prediction errors."""
        print("\n=== Analyzing Errors ===")
        
        y_pred = self.predict(X_test)
        y_pred_proba = self.predict_proba(X_test)[:, 1]
        
        if not isinstance(X_test, pd.DataFrame):
            if feature_names is None:
                feature_names = self.feature_names
            X_test_df = pd.DataFrame(X_test, columns=feature_names)
        else:
            X_test_df = X_test.copy()
        
        X_test_df['y_true'] = y_test.values if hasattr(y_test, 'values') else y_test
        X_test_df['y_pred'] = y_pred
        X_test_df['threat_probability'] = y_pred_proba
        
        fp = X_test_df[(X_test_df['y_true'] == 0) & (X_test_df['y_pred'] == 1)]
        fn = X_test_df[(X_test_df['y_true'] == 1) & (X_test_df['y_pred'] == 0)]
        
        print(f"False Positives: {len(fp)}")
        print(f"False Negatives: {len(fn)}")
        
        return fp, fn
    
    def get_feature_importance(self, top_n=20, importance_type='weight'):
        """Get feature importance."""
        if self.model is None:
            raise ValueError("Model not trained yet.")
        
        scores = self.model.get_booster().get_score(importance_type=importance_type)
        
        df = pd.DataFrame({
            'feature': list(scores.keys()),
            'importance': list(scores.values())
        })
        
        if self.feature_names:
            df['feature'] = df['feature'].apply(
                lambda x: self.feature_names[int(x.replace('f', ''))] if x.startswith('f') else x
            )
        
        return df.sort_values('importance', ascending=False).reset_index(drop=True).head(top_n)
    
    def save_model(self, filepath='threat_detection_model.pkl'):
        if self.model is None:
            raise ValueError("No model to save.")
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'best_params': self.best_params
            }, f)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath='threat_detection_model.pkl'):
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
            self.model = state['model']
            self.feature_names = state['feature_names']
            self.best_params = state.get('best_params')
        print(f"Model loaded from {filepath}")

if __name__ == "__main__":
    # Simple test if run directly
    print("Model module loaded.")

