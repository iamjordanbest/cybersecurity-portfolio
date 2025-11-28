import sys
import os
from pathlib import Path
import argparse
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.preprocess import ThreatDataPreprocessor
from src.model import ThreatDetectionModel
from src.visualize import ThreatVisualization

def main():
    parser = argparse.ArgumentParser(description="Run Project 1: Python Monitoring Pipeline")
    default_data_path = Path(__file__).parent / 'data' / 'raw_data.csv'
    parser.add_argument('--data', type=str, default=str(default_data_path), help='Path to raw data CSV')
    parser.add_argument('--target', type=str, default=' Label', help='Name of the target column')
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
        
        # Generate plots
        dashboard_dir = Path(__file__).parent / 'dashboard'
        dashboard_dir.mkdir(exist_ok=True)
        
        viz.plot_class_distribution(y_train, y_test, save_path=str(dashboard_dir / 'class_distribution.png'), show_plot=False)
        viz.plot_metrics_comparison(metrics, save_path=str(dashboard_dir / 'metrics_comparison.png'), show_plot=False)
        
        # Get predictions for distribution plot
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        viz.plot_prediction_distribution(y_test, y_pred_proba, save_path=str(dashboard_dir / 'prediction_distribution.png'), show_plot=False)
        
        viz.create_dashboard_summary(metrics, importance, len(fp), len(fn), output_path=str(dashboard_dir / 'metrics_summary.json'))
        
        # Save test predictions for interactive dashboard
        print("Saving test predictions for dashboard...")
        test_df = pd.DataFrame(X_test, columns=preprocessor.feature_names if hasattr(preprocessor, 'feature_names') else None)
        test_df['True Label'] = y_test.values if hasattr(y_test, 'values') else y_test
        test_df['Predicted Probability'] = y_pred_proba
        test_df['Predicted Label'] = (y_pred_proba > 0.5).astype(int)
        test_df.to_csv(dashboard_dir / 'test_predictions.csv', index=False)
        
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
