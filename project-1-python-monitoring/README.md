# Cybersecurity Threat Detection with XGBoost

A professional machine learning pipeline for detecting cybersecurity threats using XGBoost. This project demonstrates an end-to-end workflow from raw data preprocessing to a real-time REST API for threat prediction.

## 🎯 Key Features

- **XGBoost Classification**: High-performance gradient boosting model for binary threat detection.
- **Robust Preprocessing**: Automated handling of missing values, scaling, and categorical encoding.
- **Comprehensive Evaluation**: Detailed metrics including Accuracy, Precision, Recall, F1-Score, and ROC AUC.
- **Error Analysis**: Automated analysis of false positives and false negatives to understand model weaknesses.
- **Real-time API**: FastAPI endpoint for serving predictions in real-time.
- **Visualization Dashboard**: Insightful plots for feature importance, confusion matrices, and class distributions.

## 📁 Project Structure

```
project-1-python-monitoring/
├── data/                  # Dataset storage
├── src/
│   ├── preprocess.py      # Data cleaning and transformation pipeline
│   ├── model.py           # XGBoost training and evaluation logic
│   ├── visualize.py       # Visualization utilities
│   └── api.py             # FastAPI prediction endpoint
├── notebooks/             # Jupyter notebooks for experimentation
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd project-1-python-monitoring
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Prepare Data**
    - Ensure `data/raw_data.csv` exists.
    - The dataset should contain a target column (default: `threat`) and feature columns.

### Usage

#### 1. Run the Full Pipeline

Use the unified entry point script to preprocess data, train the model, and evaluate performance.

```bash
python run_project_1.py --data data/raw_data.csv --target " Label"
```

This will:
- Train the XGBoost model
- Save artifacts to `src/`
- Generate a dashboard summary in `dashboard/`

Alternatively, you can import the classes in your own scripts:

```python
from src.preprocess import ThreatDataPreprocessor
from src.model import ThreatDetectionModel

# ... (custom implementation)
```

#### 2. Run Real-time API

Start the FastAPI server to serve predictions:

```bash
python src/api.py
```

- **Health Check**: `GET http://localhost:8001/health`
- **Predict**: `POST http://localhost:8001/predict`

Example Payload:
```json
{
  "features": {
    "Destination Port": 80,
    "Flow Duration": 1000,
    "Total Fwd Packets": 5
  }
}
```

## 📊 Metrics & Performance

The model is evaluated using standard cybersecurity metrics:
- **Precision**: Minimizing false alarms.
- **Recall**: Ensuring actual threats are detected.
- **ROC AUC**: Measuring overall discrimination capability.

## 📝 License

MIT License
