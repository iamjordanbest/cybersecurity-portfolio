import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.preprocess import ThreatDataPreprocessor
from src.model import ThreatDetectionModel
from src.visualize import ThreatVisualization
from src.api import app

def create_synthetic_data(filepath):
    """Create synthetic data for testing"""
    print("Creating synthetic data...")
    n_samples = 100
    data = {
        'Destination Port': np.random.randint(0, 65535, n_samples),
        'Flow Duration': np.random.randint(0, 1000000, n_samples),
        'Total Fwd Packets': np.random.randint(0, 100, n_samples),
        'Total Backward Packets': np.random.randint(0, 100, n_samples),
        'Total Length of Fwd Packets': np.random.randint(0, 10000, n_samples),
        'Total Length of Bwd Packets': np.random.randint(0, 10000, n_samples),
        'Fwd Packet Length Max': np.random.randint(0, 1500, n_samples),
        'Fwd Packet Length Min': np.random.randint(0, 100, n_samples),
        'Bwd Packet Length Max': np.random.randint(0, 1500, n_samples),
        'Bwd Packet Length Min': np.random.randint(0, 100, n_samples),
        'Flow Bytes/s': np.random.random(n_samples) * 1000,
        'Flow Packets/s': np.random.random(n_samples) * 100,
        'Flow IAT Mean': np.random.random(n_samples) * 100,
        'Flow IAT Std': np.random.random(n_samples) * 10,
        'Flow IAT Max': np.random.random(n_samples) * 1000,
        'Flow IAT Min': np.random.random(n_samples) * 10,
        'Fwd IAT Total': np.random.random(n_samples) * 1000,
        'Fwd IAT Mean': np.random.random(n_samples) * 100,
        'Fwd IAT Std': np.random.random(n_samples) * 10,
        'Fwd IAT Max': np.random.random(n_samples) * 1000,
        'Fwd IAT Min': np.random.random(n_samples) * 10,
        'Bwd IAT Total': np.random.random(n_samples) * 1000,
        'Bwd IAT Mean': np.random.random(n_samples) * 100,
        'Bwd IAT Std': np.random.random(n_samples) * 10,
        'Bwd IAT Max': np.random.random(n_samples) * 1000,
        'Bwd IAT Min': np.random.random(n_samples) * 10,
        'Fwd PSH Flags': np.random.randint(0, 2, n_samples),
        'Bwd PSH Flags': np.random.randint(0, 2, n_samples),
        'Fwd URG Flags': np.random.randint(0, 2, n_samples),
        'Bwd URG Flags': np.random.randint(0, 2, n_samples),
        'Fwd Header Length': np.random.randint(0, 100, n_samples),
        'Bwd Header Length': np.random.randint(0, 100, n_samples),
        'Fwd Packets/s': np.random.random(n_samples) * 100,
        'Bwd Packets/s': np.random.random(n_samples) * 100,
        'Min Packet Length': np.random.randint(0, 100, n_samples),
        'Max Packet Length': np.random.randint(0, 1500, n_samples),
        'Packet Length Mean': np.random.random(n_samples) * 1000,
        'Packet Length Std': np.random.random(n_samples) * 100,
        'Packet Length Variance': np.random.random(n_samples) * 10000,
        'FIN Flag Count': np.random.randint(0, 2, n_samples),
        'SYN Flag Count': np.random.randint(0, 2, n_samples),
        'RST Flag Count': np.random.randint(0, 2, n_samples),
        'PSH Flag Count': np.random.randint(0, 2, n_samples),
        'ACK Flag Count': np.random.randint(0, 2, n_samples),
        'URG Flag Count': np.random.randint(0, 2, n_samples),
        'CWE Flag Count': np.random.randint(0, 2, n_samples),
        'ECE Flag Count': np.random.randint(0, 2, n_samples),
        'Down/Up Ratio': np.random.random(n_samples) * 10,
        'Average Packet Size': np.random.random(n_samples) * 1000,
        'Avg Fwd Segment Size': np.random.random(n_samples) * 1000,
        'Avg Bwd Segment Size': np.random.random(n_samples) * 1000,
        'Fwd Header Length.1': np.random.randint(0, 100, n_samples),
        'Fwd Avg Bytes/Bulk': np.random.randint(0, 1000, n_samples),
        'Fwd Avg Packets/Bulk': np.random.randint(0, 100, n_samples),
        'Fwd Avg Bulk Rate': np.random.randint(0, 1000, n_samples),
        'Bwd Avg Bytes/Bulk': np.random.randint(0, 1000, n_samples),
        'Bwd Avg Packets/Bulk': np.random.randint(0, 100, n_samples),
        'Bwd Avg Bulk Rate': np.random.randint(0, 1000, n_samples),
        'Subflow Fwd Packets': np.random.randint(0, 100, n_samples),
        'Subflow Fwd Bytes': np.random.randint(0, 10000, n_samples),
        'Subflow Bwd Packets': np.random.randint(0, 100, n_samples),
        'Subflow Bwd Bytes': np.random.randint(0, 10000, n_samples),
        'Init_Win_bytes_forward': np.random.randint(0, 65535, n_samples),
        'Init_Win_bytes_backward': np.random.randint(0, 65535, n_samples),
        'act_data_pkt_fwd': np.random.randint(0, 100, n_samples),
        'min_seg_size_forward': np.random.randint(0, 100, n_samples),
        'Active Mean': np.random.random(n_samples) * 1000,
        'Active Std': np.random.random(n_samples) * 100,
        'Active Max': np.random.random(n_samples) * 1000,
        'Active Min': np.random.random(n_samples) * 100,
        'Idle Mean': np.random.random(n_samples) * 1000,
        'Idle Std': np.random.random(n_samples) * 100,
        'Idle Max': np.random.random(n_samples) * 1000,
        'Idle Min': np.random.random(n_samples) * 100,
        'Label': np.random.choice(['BENIGN', 'DDoS'], n_samples)
    }
    df = pd.DataFrame(data)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Synthetic data saved to {filepath}")
    return df

def test_pipeline():
    print("Starting pipeline test...")
    
    # 1. Setup Data
    data_path = project_root / 'data' / 'test_data.csv'
    create_synthetic_data(str(data_path))
    
    # 2. Test Preprocessing
    print("\nTesting Preprocessing...")
    preprocessor = ThreatDataPreprocessor()
    X_train, X_test, y_train, y_test, features = preprocessor.preprocess_pipeline(
        filepath=str(data_path),
        target_col='Label'
    )
    assert X_train.shape[0] > 0
    assert X_test.shape[0] > 0
    print("Preprocessing successful.")
    
    # 3. Test Model Training
    print("\nTesting Model Training...")
    model = ThreatDetectionModel()
    model.train_model(X_train, y_train)
    print("Model training successful.")
    
    # 4. Test Evaluation
    print("\nTesting Evaluation...")
    metrics = model.evaluate_model(X_test, y_test)
    assert 'accuracy' in metrics
    print("Evaluation successful.")
    
    # 5. Test Visualization
    print("\nTesting Visualization...")
    viz = ThreatVisualization()
    viz.create_dashboard_summary(metrics, model.get_feature_importance(), 0, 0)
    print("Visualization successful.")
    
    # 6. Test Saving
    print("\nTesting Artifact Saving...")
    preprocessor.save_preprocessor(str(project_root / 'src' / 'preprocessor.pkl'))
    model.save_model(str(project_root / 'src' / 'threat_detection_model.pkl'))
    assert (project_root / 'src' / 'preprocessor.pkl').exists()
    assert (project_root / 'src' / 'threat_detection_model.pkl').exists()
    print("Artifact saving successful.")
    
    # 7. Test API
    print("\nTesting API...")
    with TestClient(app) as client:
        # Health check
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'
        
        # Prediction
        # Create a sample feature dict from the test data
        sample_features = {col: 0 for col in features} # Dummy features
        response = client.post("/predict", json={"features": sample_features})
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert "prediction" in response.json()
    print("API testing successful.")
    
    print("\nALL TESTS PASSED!")
    
    # Cleanup
    if data_path.exists():
        os.remove(data_path)

if __name__ == "__main__":
    test_pipeline()
