import pickle
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from preprocess import ThreatDataPreprocessor

PREPROCESSOR_PATH = Path("src/preprocessor.pkl")

try:
    with open(PREPROCESSOR_PATH, 'rb') as f:
        preprocessor = pickle.load(f)
    
    print("Feature Columns:")
    for col in preprocessor.feature_columns:
        print(f"'{col}'")
        
except Exception as e:
    print(f"Error: {e}")
