# Grafana Dashboard Setup for Threat Detection

## Overview
This guide will help you set up a Grafana dashboard to visualize your cybersecurity threat detection model metrics and insights.

## Prerequisites
- Grafana installed (https://grafana.com/grafana/download)
- Model metrics exported to JSON format
- Basic understanding of Grafana panels and queries

## Step 1: Install Grafana

### Windows
```powershell
# Download and install from https://grafana.com/grafana/download
# Or use Chocolatey
choco install grafana
```

### Mac
```bash
brew install grafana
```

### Linux
```bash
sudo apt-get install -y grafana
```

## Step 2: Start Grafana Service

```bash
# Windows
net start grafana

# Mac/Linux
sudo systemctl start grafana-server
```

Access Grafana at `http://localhost:3000` (default credentials: admin/admin)

## Step 3: Data Source Configuration

### Option 1: JSON API Data Source
1. Install the JSON API plugin:
   ```bash
   grafana-cli plugins install simpod-json-datasource
   ```

2. Create a simple Python API server to serve your metrics:
   ```python
   # In your project directory, create api_server.py
   from flask import Flask, jsonify
   import json
   
   app = Flask(__name__)
   
   @app.route('/metrics')
   def get_metrics():
       with open('dashboard/metrics_summary.json', 'r') as f:
           return jsonify(json.load(f))
   
   if __name__ == '__main__':
       app.run(port=5000)
   ```

3. Add data source in Grafana:
   - Go to Configuration → Data Sources
   - Add JSON API data source
   - URL: `http://localhost:5000`

### Option 2: CSV/JSON File Import
- Export metrics to CSV format
- Use Grafana's CSV plugin or import via Python script

## Step 4: Dashboard Panels

### Panel 1: Key Performance Metrics
**Type:** Stat Panel
- **Metrics:** Accuracy, Precision, Recall, F1-Score, ROC AUC
- **Query:** Extract from JSON: `model_performance.*`
- **Thresholds:**
  - Green: > 0.9
  - Yellow: 0.7 - 0.9
  - Red: < 0.7

### Panel 2: Confusion Matrix
**Type:** Table or Heatmap
- **Data:** True Positives, True Negatives, False Positives, False Negatives
- **Query:** Extract from JSON: `confusion_matrix.*`

### Panel 3: Error Analysis
**Type:** Pie Chart
- **Data:** False Positives vs False Negatives
- **Query:** Extract from JSON: `error_analysis.*`
- **Colors:** Red for FP, Orange for FN

### Panel 4: Feature Importance
**Type:** Bar Chart (Horizontal)
- **Data:** Top 10-20 most important features
- **Query:** Extract from JSON: `top_features`
- **Order:** Descending by importance score

### Panel 5: Threat Detection Rate
**Type:** Gauge
- **Metric:** Recall (True Positive Rate)
- **Query:** Extract from JSON: `model_performance.recall`
- **Thresholds:**
  - Green: > 0.95
  - Yellow: 0.85 - 0.95
  - Red: < 0.85

### Panel 6: False Positive Rate
**Type:** Gauge
- **Calculation:** FP / (FP + TN)
- **Query:** Calculate from confusion matrix
- **Thresholds:**
  - Green: < 0.05
  - Yellow: 0.05 - 0.15
  - Red: > 0.15

### Panel 7: Model Performance Over Time (if applicable)
**Type:** Time Series Graph
- **Data:** Track metrics across different model versions or time periods
- **Metrics:** All key performance indicators

## Step 5: Dashboard Layout Example

```
┌─────────────────────────────────────────────────────────────┐
│                  THREAT DETECTION DASHBOARD                  │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Accuracy    │  Precision   │   Recall     │   F1-Score     │
│   [0.956]    │   [0.943]    │   [0.962]    │   [0.952]      │
├──────────────┴──────────────┴──────────────┴────────────────┤
│                                                               │
│                    Confusion Matrix                           │
│              ┌─────────┬─────────┐                           │
│              │   TN    │   FP    │                           │
│              ├─────────┼─────────┤                           │
│              │   FN    │   TP    │                           │
│              └─────────┴─────────┘                           │
│                                                               │
├───────────────────────┬───────────────────────────────────────┤
│                       │                                       │
│  Feature Importance   │     Error Analysis                   │
│  (Top 10 Features)    │     (FP vs FN Breakdown)            │
│                       │                                       │
└───────────────────────┴───────────────────────────────────────┘
```

## Step 6: Automate Metrics Updates

Create a script to automatically update metrics after each model run:

```python
# update_dashboard.py
import json
from src.preprocess import ThreatDataPreprocessor
from src.model import ThreatDetectionModel
from src.visualize import ThreatVisualization

def update_metrics():
    # Load data and train model
    preprocessor = ThreatDataPreprocessor()
    X_train, X_test, y_train, y_test, features = preprocessor.preprocess_pipeline(
        filepath='data/raw_data.csv',
        target_col='threat'
    )
    
    model = ThreatDetectionModel()
    model.train_model(X_train, y_train)
    
    # Evaluate
    metrics = model.evaluate_model(X_test, y_test)
    fp, fn = model.analyze_false_positives_negatives(X_test, y_test)
    importance = model.get_feature_importance(top_n=20)
    
    # Create visualization and export
    viz = ThreatVisualization()
    viz.create_dashboard_summary(
        metrics=metrics,
        feature_importance=importance,
        fp_count=len(fp),
        fn_count=len(fn),
        output_path='dashboard/metrics_summary.json'
    )
    
    print("Dashboard metrics updated!")

if __name__ == "__main__":
    update_metrics()
```

## Step 7: Key Insights to Display

1. **Threat Detection Rate:** How many actual threats are caught
2. **False Positive Rate:** How many false alarms are generated
3. **Critical Features:** Which features are most important for detection
4. **Error Patterns:** Analysis of false positives and false negatives
5. **Model Confidence:** Distribution of prediction probabilities

## Step 8: Alerts Configuration

Set up alerts in Grafana for:
- Model accuracy drops below threshold (< 0.90)
- False positive rate exceeds threshold (> 0.10)
- False negative rate exceeds threshold (> 0.05)

## Additional Resources
- Grafana Documentation: https://grafana.com/docs/
- JSON API Plugin: https://grafana.com/grafana/plugins/simpod-json-datasource/
- Dashboard Examples: https://grafana.com/grafana/dashboards/

## Next Steps
1. Run your model and generate metrics
2. Export metrics to JSON using `visualize.py`
3. Set up Grafana data source
4. Create dashboard panels
5. Configure refresh intervals
6. Set up alerting rules

## Troubleshooting
- **Cannot connect to data source:** Ensure your API server is running
- **No data in panels:** Check JSON structure matches your queries
- **Grafana not starting:** Check if port 3000 is already in use
