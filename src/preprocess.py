"""
Threat Detection Data Preprocessing Module
Handles loading, cleaning, encoding, and scaling of raw cyber data
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

class ThreatDataPreprocessor:
    """
    Preprocesses cybersecurity threat detection data
    """
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = None
        self.feature_columns = None
        self.categorical_columns = []
        self.numerical_columns = []
        
    def load_data(self, filepath):
        """
        Load raw data from CSV
        
        Args:
            filepath: Path to raw data CSV file
            
        Returns:
            DataFrame with loaded data
        """
        # Normalize path to handle different OS
        filepath = os.path.normpath(filepath)
        df = pd.read_csv(filepath)
        print(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        return df
    
    def explore_data(self, df):
        """
        Initial data exploration
        
        Args:
            df: Input DataFrame
        """
        print("\n=== Data Overview ===")
        print(df.info())
        print("\n=== Missing Values ===")
        print(df.isnull().sum())
        print("\n=== Statistical Summary ===")
        print(df.describe())
        print("\n=== Target Distribution ===")
        if 'threat' in df.columns or 'label' in df.columns:
            target_col = 'threat' if 'threat' in df.columns else 'label'
            print(df[target_col].value_counts())
        
    def handle_missing_values(self, df):
        """
        Handle missing values and infinite values in the dataset
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with missing values handled
        """
        print("\n=== Handling Missing Values and Infinite Values ===")
        
        df_clean = df.copy()
        
        # Replace infinite values with NaN first
        df_clean.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # Identify columns with missing values
        missing_cols = df_clean.columns[df_clean.isnull().any()].tolist()
        
        if not missing_cols:
            print("No missing values found.")
            return df_clean
        
        for col in missing_cols:
            missing_pct = (df_clean[col].isnull().sum() / len(df_clean)) * 100
            print(f"{col}: {missing_pct:.2f}% missing")
            
            # Drop column if >50% missing
            if missing_pct > 50:
                print(f"  -> Dropping {col} (too many missing values)")
                df_clean = df_clean.drop(columns=[col])
            # Fill numerical with median
            elif df_clean[col].dtype in ['int64', 'float64']:
                median_val = df_clean[col].median()
                df_clean[col].fillna(median_val, inplace=True)
                print(f"  -> Filled with median: {median_val}")
            # Fill categorical with mode
            else:
                mode_val = df_clean[col].mode()[0] if not df_clean[col].mode().empty else 'Unknown'
                df_clean[col].fillna(mode_val, inplace=True)
                print(f"  -> Filled with mode: {mode_val}")
        
        return df_clean
    
    def identify_column_types(self, df, target_col='threat'):
        """
        Identify categorical and numerical columns
        
        Args:
            df: Input DataFrame
            target_col: Name of target column
        """
        print("\n=== Identifying Column Types ===")
        
        # Exclude target column
        feature_cols = [col for col in df.columns if col != target_col]
        
        for col in feature_cols:
            # Categorical: object type or few unique values
            if df[col].dtype == 'object' or df[col].nunique() < 10:
                self.categorical_columns.append(col)
            else:
                self.numerical_columns.append(col)
        
        print(f"Categorical columns ({len(self.categorical_columns)}): {self.categorical_columns}")
        print(f"Numerical columns ({len(self.numerical_columns)}): {self.numerical_columns}")
    
    def encode_categorical(self, df, fit=True):
        """
        Encode categorical variables using Label Encoding
        
        Args:
            df: Input DataFrame
            fit: Whether to fit encoders (True for training, False for test)
            
        Returns:
            DataFrame with encoded categorical variables
        """
        print("\n=== Encoding Categorical Variables ===")
        df_encoded = df.copy()
        
        for col in self.categorical_columns:
            if col not in df_encoded.columns:
                continue
                
            if fit:
                # Create and fit label encoder
                le = LabelEncoder()
                df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
                self.label_encoders[col] = le
                print(f"{col}: {len(le.classes_)} unique values encoded")
            else:
                # Use existing encoder
                le = self.label_encoders[col]
                # Handle unseen categories
                df_encoded[col] = df_encoded[col].astype(str).map(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1
                )
        
        return df_encoded
    
    def scale_numerical(self, df, fit=True):
        """
        Scale numerical features using RobustScaler (better for outliers)
        
        Args:
            df: Input DataFrame
            fit: Whether to fit scaler (True for training, False for test)
            
        Returns:
            DataFrame with scaled numerical features
        """
        print("\n=== Scaling Numerical Features ===")
        df_scaled = df.copy()
        
        if not self.numerical_columns:
            print("No numerical columns to scale.")
            return df_scaled
        
        # Only scale columns that exist in dataframe
        cols_to_scale = [col for col in self.numerical_columns if col in df_scaled.columns]
        
        # Replace any remaining infinite values with NaN, then fill with median
        print("Checking for infinite values before scaling...")
        for col in cols_to_scale:
            inf_count = np.isinf(df_scaled[col]).sum()
            if inf_count > 0:
                print(f"  {col}: {inf_count} infinite values found, replacing with median")
                df_scaled[col].replace([np.inf, -np.inf], np.nan, inplace=True)
                median_val = df_scaled[col].median()
                df_scaled[col].fillna(median_val, inplace=True)
        
        if fit:
            self.scaler = RobustScaler()
            df_scaled[cols_to_scale] = self.scaler.fit_transform(df_scaled[cols_to_scale])
            print(f"Scaled {len(cols_to_scale)} numerical columns")
        else:
            df_scaled[cols_to_scale] = self.scaler.transform(df_scaled[cols_to_scale])
        
        return df_scaled
    
    def remove_duplicates(self, df):
        """
        Remove duplicate rows
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame without duplicates
        """
        print("\n=== Removing Duplicates ===")
        initial_rows = len(df)
        df_clean = df.drop_duplicates()
        removed = initial_rows - len(df_clean)
        print(f"Removed {removed} duplicate rows ({(removed/initial_rows)*100:.2f}%)")
        return df_clean
    
    def preprocess_pipeline(self, filepath, target_col='threat', test_size=0.2, random_state=42):
        """
        Complete preprocessing pipeline
        
        Args:
            filepath: Path to raw data
            target_col: Name of target column
            test_size: Proportion of test set
            random_state: Random seed
            
        Returns:
            X_train, X_test, y_train, y_test, feature_names
        """
        # Load data
        df = self.load_data(filepath)
        
        # Explore
        self.explore_data(df)
        
        # Remove duplicates
        df = self.remove_duplicates(df)
        
        # Handle missing values
        df = self.handle_missing_values(df)
        
        # Identify column types
        self.identify_column_types(df, target_col)
        
        # Separate features and target
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset")
        
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # Encode target if categorical
        if y.dtype == 'object':
            print(f"\n=== Encoding Target Variable ===")
            le_target = LabelEncoder()
            y = le_target.fit_transform(y)
            self.label_encoders['target'] = le_target
            print(f"Target classes: {le_target.classes_}")
        
        # Encode categorical features
        X = self.encode_categorical(X, fit=True)
        
        # Scale numerical features
        X = self.scale_numerical(X, fit=True)
        
        # Store feature names
        self.feature_columns = X.columns.tolist()
        
        # Train-test split
        print(f"\n=== Splitting Data ===")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        print(f"Training set: {X_train.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        
        return X_train, X_test, y_train, y_test, self.feature_columns
    
    def save_preprocessor(self, filepath='preprocessor.pkl'):
        """
        Save preprocessor state
        
        Args:
            filepath: Path to save preprocessor
        """
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump({
                'label_encoders': self.label_encoders,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'categorical_columns': self.categorical_columns,
                'numerical_columns': self.numerical_columns
            }, f)
        print(f"\nPreprocessor saved to {filepath}")
    
    def load_preprocessor(self, filepath='preprocessor.pkl'):
        """
        Load preprocessor state
        
        Args:
            filepath: Path to load preprocessor from
        """
        import pickle
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
            self.label_encoders = state['label_encoders']
            self.scaler = state['scaler']
            self.feature_columns = state['feature_columns']
            self.categorical_columns = state['categorical_columns']
            self.numerical_columns = state['numerical_columns']
        print(f"Preprocessor loaded from {filepath}")


# Example usage
if __name__ == "__main__":
    preprocessor = ThreatDataPreprocessor()
    
    # Run preprocessing pipeline
    X_train, X_test, y_train, y_test, features = preprocessor.preprocess_pipeline(
        filepath= 'C:/Users/19738/Desktop/cybersecurity-portfolio\project-1-python-monitoring\data\raw_data.csv',
        target_col='threat'  # Adjust based on your dataset
    )
    
    print("\n=== Preprocessing Complete ===")
    print(f"Features: {len(features)}")
    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    
    # Save preprocessor for later use
    preprocessor.save_preprocessor('../src/preprocessor.pkl')