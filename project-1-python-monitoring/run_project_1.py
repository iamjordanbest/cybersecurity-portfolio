import sys
import os
from pathlib import Path
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.preprocess import ThreatDataPreprocessor
from src.model import ThreatDetectionModel
from src.visualize import ThreatVisualization

def main():
    parser = argparse.ArgumentParser(description="Run Project 1: Python Monitoring Pipeline")
    parser.add_argument('--data', type=str, default='data/raw_data.csv', help='Path to raw data CSV')
    parser.add_argument('--target', type=str, default='threat', help='Name of the target column')
    args = parser.parse_args()

    print("Starting Project 1: Python Monitoring Pipeline...")
    
    # Define paths
    data_path = Path(args.data)
    
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        print(f"Please place your dataset in {data_path} or specify --data path/to/file.csv")
        return

    try:
        # 1. Preprocess
        print("\n1. Preprocessing Data...")
        preprocessor = ThreatDataPreprocessor()
        X_train, X_test, y_train, y_test, features = preprocessor.preprocess_pipeline(
            filepath=str(data_path),
            target_col=args.target
        )
        
        # 2. Train
        print("\n2. Training Model...")
        model = ThreatDetectionModel()
        model.train_model(X_train, y_train)
        
        # 3. Evaluate
        print("\n3. Evaluating Model...")
        metrics = model.evaluate_model(X_test, y_test)
        print("\nKey Metrics:")
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"{k}: {v:.4f}")
        
        # 4. Analyze Errors
        print("\n4. Analyzing Errors...")
        fp, fn = model.analyze_false_positives_negatives(X_test, y_test)
        print(f"False Positives: {len(fp)}")
        print(f"False Negatives: {len(fn)}")
        
        # 5. Visualize
        print("\n5. Generating Visualizations...")
        viz = ThreatVisualization()
        importance = model.get_feature_importance()
        viz.create_dashboard_summary(metrics, importance, len(fp), len(fn))
        
        # 6. Save Artifacts
        print("\n6. Saving Artifacts...")
        src_dir = Path(__file__).parent / 'src'
        preprocessor.save_preprocessor(str(src_dir / 'preprocessor.pkl'))
        model.save_model(str(src_dir / 'threat_detection_model.pkl'))
        
        print("\nPipeline completed successfully!")
        print("To run the API: python src/api.py")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
