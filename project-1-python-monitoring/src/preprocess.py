"""
Threat Detection Data Preprocessing Module
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.model_selection import train_test_split
import pickle
import warnings
warnings.filterwarnings('ignore')

class ThreatDataPreprocessor:
    """Preprocesses cybersecurity threat detection data."""
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = None
        self.feature_columns = None
        self.categorical_columns = []
        self.numerical_columns = []
        
    def load_data(self, filepath):
        filepath = os.path.normpath(filepath)
        df = pd.read_csv(filepath)
        # Fix: Strip whitespace from column names
        df.columns = df.columns.str.strip()
        print(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        return df
    
    def explore_data(self, df):
        print("\n=== Data Overview ===")
        print(df.info())
        print("\n=== Missing Values ===")
        print(df.isnull().sum())
        
    def handle_missing_values(self, df):
        print("\n=== Handling Missing Values ===")
        df_clean = df.copy()
        df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        missing_cols = df_clean.columns[df_clean.isnull().any()].tolist()
        if not missing_cols:
            print("No missing values found.")
            return df_clean
        
        cols_to_drop = []
        for col in missing_cols:
            missing_pct = (df_clean[col].isnull().sum() / len(df_clean)) * 100
            if missing_pct > 50:
                print(f"Dropping {col} (>50% missing)")
                cols_to_drop.append(col)
            elif df_clean[col].dtype in ['int64', 'float64']:
                df_clean[col].fillna(df_clean[col].median(), inplace=True)
            else:
                mode_val = df_clean[col].mode()[0] if not df_clean[col].mode().empty else 'Unknown'
                df_clean[col].fillna(mode_val, inplace=True)
        
        # Drop all columns at once for better performance
        if cols_to_drop:
            df_clean.drop(columns=cols_to_drop, inplace=True)
        
        return df_clean
    
    def identify_column_types(self, df, target_col='threat'):
        feature_cols = [col for col in df.columns if col != target_col]
        for col in feature_cols:
            if df[col].dtype == 'object' or df[col].nunique() < 10:
                self.categorical_columns.append(col)
            else:
                self.numerical_columns.append(col)
    
    def encode_categorical(self, df, fit=True):
        df_encoded = df.copy()
        for col in self.categorical_columns:
            if col not in df_encoded.columns:
                continue
            
            if fit:
                le = LabelEncoder()
                df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
                self.label_encoders[col] = le
            else:
                le = self.label_encoders.get(col)
                if le:
                    # Create a mapping dict for better performance
                    mapping = {cls: idx for idx, cls in enumerate(le.classes_)}
                    df_encoded[col] = df_encoded[col].astype(str).map(
                        lambda x: mapping.get(x, -1)
                    )
        return df_encoded
    
    def scale_numerical(self, df, fit=True):
        df_scaled = df.copy()
        if not self.numerical_columns:
            return df_scaled
            
        cols_to_scale = [col for col in self.numerical_columns if col in df_scaled.columns]
        if not cols_to_scale:
            return df_scaled
        
        # Handle infinite values before scaling - vectorized operation
        df_scaled[cols_to_scale] = df_scaled[cols_to_scale].replace([np.inf, -np.inf], np.nan)
        
        # Fill NaN with median values - more efficient
        medians = df_scaled[cols_to_scale].median()
        df_scaled[cols_to_scale] = df_scaled[cols_to_scale].fillna(medians)
            
        if fit:
            self.scaler = RobustScaler()
            df_scaled[cols_to_scale] = self.scaler.fit_transform(df_scaled[cols_to_scale])
        elif self.scaler:
            df_scaled[cols_to_scale] = self.scaler.transform(df_scaled[cols_to_scale])
            
        return df_scaled
    
    def preprocess_pipeline(self, filepath, target_col='threat', test_size=0.2, random_state=42):
        """Complete preprocessing pipeline."""
        df = self.load_data(filepath)
        self.explore_data(df)
        
        df = df.drop_duplicates()
        df = self.handle_missing_values(df)
        self.identify_column_types(df, target_col)
        
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found")
            
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        if y.dtype == 'object':
            le_target = LabelEncoder()
            y = le_target.fit_transform(y)
            self.label_encoders['target'] = le_target
            
        X = self.encode_categorical(X, fit=True)
        X = self.scale_numerical(X, fit=True)
        
        self.feature_columns = X.columns.tolist()
        
        print("\n=== Splitting Data ===")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        return X_train, X_test, y_train, y_test, self.feature_columns
    
    def save_preprocessor(self, filepath='preprocessor.pkl'):
        with open(filepath, 'wb') as f:
            pickle.dump({
                'label_encoders': self.label_encoders,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'categorical_columns': self.categorical_columns,
                'numerical_columns': self.numerical_columns
            }, f)
        print(f"Preprocessor saved to {filepath}")
    
    def load_preprocessor(self, filepath='preprocessor.pkl'):
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
            self.label_encoders = state['label_encoders']
            self.scaler = state['scaler']
            self.feature_columns = state['feature_columns']
            self.categorical_columns = state.get('categorical_columns', [])
            self.numerical_columns = state.get('numerical_columns', [])
            
    def transform_single(self, input_data):
        """Preprocess a single input dictionary for inference."""
        df = pd.DataFrame([input_data])
        
        # Add missing columns with 0
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
                
        # Encode categorical columns
        for col in self.categorical_columns:
            if col in df.columns:
                le = self.label_encoders.get(col)
                if le:
                    # Create mapping dict for better performance
                    mapping = {cls: idx for idx, cls in enumerate(le.classes_)}
                    df[col] = df[col].astype(str).map(lambda x: mapping.get(x, -1))
        
        # Scale numerical columns
        cols_to_scale = [col for col in self.numerical_columns if col in df.columns]
        if cols_to_scale and self.scaler:
            df[cols_to_scale] = self.scaler.transform(df[cols_to_scale])
             
        return df[self.feature_columns]

if __name__ == "__main__":
    print("Preprocessor module loaded.")