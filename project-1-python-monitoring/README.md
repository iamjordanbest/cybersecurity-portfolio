# Cybersecurity Threat Detection with XGBoost

A comprehensive machine learning project for detecting cybersecurity threats using XGBoost, with feature importance analysis and Grafana dashboard integration.

## 📋 Project Overview

This project implements an end-to-end machine learning pipeline that:
1. Loads and preprocesses raw cybersecurity data
2. Trains an XGBoost classifier to detect threats
3. Evaluates model performance with comprehensive metrics
4. Analyzes false positives and false negatives
5. Identifies the most important features for threat detection
6. Exports metrics to a Grafana dashboard for visualization

## 🎯 Key Features

- **Robust Data Preprocessing**: Handles missing values, duplicates, encoding, and scaling
- **XGBoost Model**: State-of-the-art gradient boosting for threat detection
- **Comprehensive Evaluation**: Accuracy, Precision, Recall, F1-Score, ROC AUC, Confusion Matrix
- **Error Analysis**: Deep dive into false positives and false negatives
- **Feature Importance**: Understand which features drive threat detection
- **Grafana Integration**: Real-time dashboard for monitoring model performance

## 📁 Project Structure

```
threat-detection-project/
│
├── data/
│   └── raw_data.csv              # Your cybersecurity dataset
│
├── notebooks/
│   ├── 1_data_preprocessing.ipynb
│   ├── 2_model_training.ipynb
│   ├── 3_analysis_visuals.ipynb
│   └── threat_detection.ipynb     # Main comprehensive notebook
│
├── src/
│   ├── __init__.py
│   ├── preprocess.py              # Data preprocessing module
│   ├── model.py                   # XGBoost model training and evaluation
│   └── visualize.py               # Visualization and dashboard export
│
├── dashboard/
│   ├── grafana_setup.md           # Grafana setup instructions
│   └── metrics_summary.json       # Exported metrics for Grafana
│
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Jupyter Notebook
- Grafana (optional, for dashboard)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/threat-detection-project.git
   cd threat-detection-project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your data**
   - Place your raw cybersecurity data in `data/raw_data.csv`
   - Ensure it has a target column (e.g., 'threat', 'label', 'class')

### Quick Start

#### Option 1: Using the Comprehensive Notebook

1. Open Jupyter Notebook:
   ```bash
   jupyter notebook
   ```

2. Navigate to `notebooks/threat_detection.ipynb`

3. Update the `target_col` variable to match your dataset's target column name

4. Run all cells to execute the complete pipeline

#### Option 2: Using Python Scripts

```python
from src.preprocess import ThreatDataPreprocessor
from src.model import ThreatDetectionModel
from src.visualize import ThreatVisualization

# 1. Preprocess data
preprocessor = ThreatDataPreprocessor()
X_train, X_test, y_train, y_test, features = preprocessor.preprocess_pipeline(
    filepath='data/raw_data.csv',
    target_col='threat'  # Adjust to your dataset
)

# 2. Train model
model = ThreatDetectionModel(random_state=42)
model.train_model(X_train, y_train)

# 3. Evaluate
metrics = model.evaluate_model(X_test, y_test)

# 4. Analyze errors
fp, fn = model.analyze_false_positives_negatives(X_test, y_test)

# 5. Feature importance
importance = model.get_feature_importance(top_n=20)
model.plot_feature_importance(top_n=20)

# 6. Export for Grafana
viz = ThreatVisualization()
viz.create_dashboard_summary(
    metrics=metrics,
    feature_importance=importance,
    fp_count=len(fp),
    fn_count=len(fn),
    output_path='dashboard/metrics_summary.json'
)
```

## 📊 Workflow Details

### 1. Data Preprocessing (`src/preprocess.py`)

The preprocessing module handles:
- **Loading data** from CSV
- **Exploratory analysis** (missing values, data types, distributions)
- **Handling missing values** (median for numeric, mode for categorical)
- **Removing duplicates**
- **Identifying column types** (categorical vs numerical)
- **Label encoding** for categorical variables
- **Robust scaling** for numerical features (handles outliers better)
- **Train-test split** with stratification

Key methods:
```python
preprocessor = ThreatDataPreprocessor()
X_train, X_test, y_train, y_test, features = preprocessor.preprocess_pipeline(
    filepath='data/raw_data.csv',
    target_col='threat',
    test_size=0.2,
    random_state=42
)
```

### 2. Model Training (`src/model.py`)

The model module provides:
- **XGBoost training** with optimized hyperparameters
- **Model evaluation** with comprehensive metrics
- **False positive/negative analysis**
- **Feature importance** extraction
- **Visualization** (confusion matrix, ROC curve)
- **Model persistence** (save/load)

Key methods:
```python
model = ThreatDetectionModel(random_state=42)
model.train_model(X_train, y_train)
metrics = model.evaluate_model(X_test, y_test)
importance = model.get_feature_importance(top_n=20)
```

### 3. Visualization (`src/visualize.py`)

The visualization module creates:
- **Class distribution plots**
- **Metrics comparison charts**
- **Prediction distribution histograms**
- **False positive/negative analysis**
- **Comprehensive dashboards**
- **JSON export for Grafana**

Key methods:
```python
viz = ThreatVisualization()
viz.plot_comprehensive_dashboard(metrics, feature_importance, y_true, y_pred, y_pred_proba)
viz.create_dashboard_summary(metrics, feature_importance, fp_count, fn_count)
```

## 📈 Model Evaluation Metrics

The project evaluates the model using:

| Metric | Description | Importance |
|--------|-------------|------------|
| **Accuracy** | Overall correctness | General performance indicator |
| **Precision** | True positives / (True positives + False positives) | Minimizing false alarms |
| **Recall** | True positives / (True positives + False negatives) | Detecting all actual threats |
| **F1-Score** | Harmonic mean of precision and recall | Balanced performance |
| **ROC AUC** | Area under ROC curve | Model discrimination ability |
| **Confusion Matrix** | Detailed breakdown of predictions | Understanding error patterns |

### Understanding the Metrics

- **High Precision**: Few false alarms (normal traffic misclassified as threats)
- **High Recall**: Most threats are detected (few threats slip through)
- **False Positives**: Normal traffic flagged as threats (annoying but safer)
- **False Negatives**: Actual threats missed (dangerous, should minimize)

## 🔍 Feature Importance Analysis

The project identifies which features are most critical for threat detection:

```python
# Get top 20 features by importance
importance_df = model.get_feature_importance(top_n=20)

# Visualize
model.plot_feature_importance(top_n=20)
```

This helps you:
- Understand what drives threat detection
- Focus security monitoring on critical indicators
- Validate model decisions
- Guide future feature engineering

## 📊 Grafana Dashboard Setup

See `dashboard/grafana_setup.md` for detailed instructions on:
1. Installing Grafana
2. Configuring data sources
3. Creating dashboard panels
4. Setting up alerts
5. Automating metric updates

Key dashboard panels:
- **Performance Metrics** (Accuracy, Precision, Recall, F1)
- **Confusion Matrix** (TP, TN, FP, FN)
- **Feature Importance** (Top predictive features)
- **Error Analysis** (False positive/negative breakdown)
- **Threat Detection Rate** (Real-time monitoring)

## 🎓 Data Requirements

Your `raw_data.csv` should contain:
- **Target column**: Binary classification (0=Normal, 1=Threat)
- **Feature columns**: Network traffic features, system metrics, etc.

Example features (based on typical cybersecurity datasets):
- Source/Destination IP, Port
- Protocol type
- Packet size, byte count
- Duration, flow metrics
- Flag counts
- Connection state
- Service type

### Kaggle Dataset Reference

This project is inspired by the approach in:
https://www.kaggle.com/code/rohullahakbari12/threat-detection-in-cybersecurity/notebook

You can use similar datasets from Kaggle:
- NSL-KDD dataset
- UNSW-NB15 dataset
- CICIDS2017 dataset
- Custom network traffic logs

## 🔧 Customization

### Adjusting Hyperparameters

Edit the parameters in the notebook or when calling `train_model()`:

```python
custom_params = {
    'max_depth': 6,           # Tree depth
    'learning_rate': 0.1,     # Step size
    'n_estimators': 200,      # Number of trees
    'subsample': 0.8,         # Sample ratio
    'colsample_bytree': 0.8,  # Feature ratio
    'gamma': 0.1,             # Regularization
    'min_child_weight': 1
}

model.train_model(X_train, y_train, params=custom_params)
```

### Feature Selection

After preprocessing, select specific features:

```python
selected_features = ['feature1', 'feature2', 'feature3']
X_train = X_train[selected_features]
X_test = X_test[selected_features]
```

### Handling Imbalanced Data

If your dataset is highly imbalanced, consider:

```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
```

## 🐛 Troubleshooting

### Common Issues

1. **ImportError: No module named 'xgboost'**
   ```bash
   pip install xgboost
   ```

2. **FileNotFoundError: raw_data.csv not found**
   - Ensure your data file is in the `data/` directory
   - Update the filepath in the notebook/script

3. **ValueError: Target column not found**
   - Update `target_col` to match your dataset's target column name

4. **Memory Error with large datasets**
   - Use data sampling: `df = df.sample(frac=0.1, random_state=42)`
   - Reduce `n_estimators` in model parameters

## 📚 Dependencies

Core libraries:
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `scikit-learn` - Preprocessing and metrics
- `xgboost` - Gradient boosting model
- `matplotlib` & `seaborn` - Visualization
- `jupyter` - Interactive notebooks

See `requirements.txt` for complete list with versions.

## 🎯 Results Interpretation

### Good Model Indicators:
- ✅ Accuracy > 90%
- ✅ Precision > 85% (few false alarms)
- ✅ Recall > 90% (most threats caught)
- ✅ F1-Score > 0.87
- ✅ ROC AUC > 0.95

### Warning Signs:
- ⚠️ High false negatives (threats missed) - Most critical
- ⚠️ Very high false positives (many false alarms) - Operational burden
- ⚠️ Large gap between train and test performance - Overfitting

## 🔄 Next Steps

After completing the initial pipeline:

1. **Model Optimization**
   - Hyperparameter tuning with Optuna or Grid Search
   - Try ensemble methods (Random Forest + XGBoost)
   - Implement cross-validation

2. **Advanced Analysis**
   - SHAP values for explainability
   - Feature interaction analysis
   - Time-based validation (if temporal data)

3. **Production Deployment**
   - Create REST API (Flask/FastAPI)
   - Implement real-time inference
   - Set up monitoring and logging
   - Configure alerting rules

4. **Continuous Improvement**
   - Monitor for concept drift
   - Implement automated retraining
   - Collect feedback on predictions
   - Update feature engineering

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Happy Threat Hunting! 🛡️🔍**
