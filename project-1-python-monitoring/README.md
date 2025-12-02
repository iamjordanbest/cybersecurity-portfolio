# DDoS Threat Detection with Machine Learning

A professional machine learning pipeline for detecting cybersecurity threats using XGBoost. This project demonstrates complete data preprocessing, model training, and interactive visualization through a Streamlit dashboard.

## 🎯 Key Features

- **Complete Data Preprocessing Pipeline**: Automated handling of infinite values, missing data, and categorical encoding
- **XGBoost Classification**: High-performance gradient boosting model achieving 99.99% accuracy
- **Business Impact Analysis**: Quantifies the cost of errors and provides actionable decision support
- **Domain-Aware Feature Analysis**: Explains the cybersecurity context behind top threat indicators
- **Interactive Dashboard**: Streamlit web app with real-time sensitivity adjustment and error analysis

## 📁 Project Structure

```
project-1-python-monitoring/
├── data/
│   └── raw_data.csv           # Training dataset
├── dashboard/
│   ├── app.py                  # Streamlit dashboard
│   ├── metrics_summary.json    # Model performance metrics
│   └── test_predictions.csv    # Test set predictions
├── src/
│   ├── preprocess.py           # Data cleaning pipeline
│   ├── model.py                # XGBoost training & evaluation
│   └── visualize.py            # Visualization utilities
├── run_project_1.py            # Main training script
├── requirements.txt            # Python dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project-1-python-monitoring
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare Data**
   - Ensure `data/raw_data.csv` exists
   - Dataset should contain a target column (default: ` Label`) and feature columns

### Usage

#### 1. Train the Model

Run the complete pipeline to preprocess data, train the XGBoost model, and evaluate performance:

```bash
python run_project_1.py --data data/raw_data.csv --target " Label"
```

This will:
- Clean and preprocess the data
- Train the XGBoost classifier
- Generate performance metrics
- Save outputs to `dashboard/` directory

#### 2. Launch the Dashboard

Start the interactive Streamlit dashboard:

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501` with:
- **Overview Tab**: Confusion matrix, prediction distribution, feature importance
- **Model Analysis Tab**: ROC curve, Precision-Recall curve
- **Data Explorer Tab**: Filter and inspect predictions (false positives, false negatives, high confidence threats)

## 📊 Model Performance

- **Accuracy**: 99.99%
- **Precision**: 0.9998
- **Recall**: 0.9999
- **F1 Score**: 0.9999
- **ROC AUC**: 1.000
- **Test Errors**: 5 out of 44,623 samples

## 🔍 Key Insights

**Top Threat Indicators** (Feature Importance):
1. Destination Port
2. Init_Win_bytes_forward
3. Init_Win_bytes_backward
4. Total Length of Fwd Packets
5. Fwd Header Length

**Error Analysis**:
- False Positives: 1
- False Negatives: 4
- Model shows excellent discrimination between normal traffic and DDoS attacks

## 🏆 Recruiter's Perspective: Why This Matters

This project was built to demonstrate not just coding ability, but **cybersecurity domain expertise** and **business awareness**:

### 1. Business-First Context
- **Impact Quantification**: The dashboard translates technical metrics into business terms (e.g., "Only 5 errors out of 44k packets").
- **Cost Analysis**: Clearly distinguishes between the cost of false positives (blocked legitimate traffic) vs. false negatives (missed attacks).

### 2. Domain Expertise
- **Feature Explainability**: Goes beyond "feature importance" to explain *why* specific network attributes (like Destination Port or Window Size) are critical indicators of DDoS attacks.
- **Operational Relevance**: Designed for SOC analysts with actionable insights and clear decision thresholds.

### 3. Production Readiness
- **Real-Time API**: Includes a fully functional FastAPI endpoint for real-time inference.
- **Interactive Tooling**: A polished Streamlit dashboard that allows analysts to explore data and adjust sensitivity thresholds dynamically.
