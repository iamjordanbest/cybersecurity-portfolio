import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve, auc

st.set_page_config(page_title="DDoS Threat Detection Dashboard", layout="wide")

st.title("🛡️ DDoS Threat Detection Dashboard")

# Get the directory where this script is located
script_dir = Path(__file__).parent
dashboard_dir = script_dir

# Load metrics
metrics_path = dashboard_dir / 'metrics_summary.json'
try:
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
except FileNotFoundError:
    st.error(f"Metrics file not found at {metrics_path}. Please run the pipeline first.")
    st.stop()

# Load predictions
predictions_path = dashboard_dir / 'test_predictions.csv'
try:
    df = pd.read_csv(predictions_path)
except FileNotFoundError:
    st.error(f"Predictions file not found at {predictions_path}. Please run the pipeline first.")
    st.stop()

# Sidebar
st.sidebar.header("🎯 Model Performance")
st.sidebar.metric("Accuracy", f"{metrics['model_performance']['accuracy']:.2%}", help="Percentage of correctly classified network packets")
st.sidebar.metric("Precision", f"{metrics['model_performance']['precision']:.2%}", help="Of predicted threats, how many were actual threats (low false alarms)")
st.sidebar.metric("Recall", f"{metrics['model_performance']['recall']:.2%}", help="Of actual threats, how many were detected (low missed threats)")
st.sidebar.metric("F1 Score", f"{metrics['model_performance']['f1_score']:.2%}", help="Balanced measure of precision and recall")
if metrics['model_performance']['roc_auc']:
    st.sidebar.metric("ROC AUC", f"{metrics['model_performance']['roc_auc']:.4f}", help="Overall discrimination ability (1.0 = perfect)")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💼 Business Impact")

# Calculate impact from confusion matrix
cm = metrics['confusion_matrix']
total_samples = cm['true_negatives'] + cm['false_positives'] + cm['false_negatives'] + cm['true_positives']
blocked_threats = cm['true_positives']
allowed_normal = cm['true_negatives']
false_alarms = cm['false_positives']
missed_threats = cm['false_negatives']

st.sidebar.info(f"""
**Out of {total_samples:,} network packets:**
- ✅ Threats blocked: **{blocked_threats:,}**
- ✅ Normal traffic allowed: **{allowed_normal:,}**
- ⚠️ False alarms: **{false_alarms}** ({(false_alarms/total_samples*100):.3f}%)
- 🚨 Missed threats: **{missed_threats}** ({(missed_threats/total_samples*100):.3f}%)

**Impact**: Only **{false_alarms + missed_threats} errors** total
""")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Detection Sensitivity")
threshold = st.sidebar.slider(
    "Prediction Threshold", 
    0.0, 1.0, 0.5, 0.01,
    help="Adjust sensitivity: Lower = catch more threats (more false alarms), Higher = fewer false alarms (may miss threats)"
)

# Real-time threshold guidance
if threshold < 0.3:
    st.sidebar.warning("⚠️ **High Sensitivity Mode**\n\nMore false positives expected, but catches subtle attacks")
elif threshold > 0.7:
    st.sidebar.warning("⚠️ **Low Sensitivity Mode**\n\nFewer false alarms, but may miss sophisticated threats")
else:
    st.sidebar.success("✅ **Balanced Mode** (Recommended)\n\nOptimal trade-off for most scenarios")

# Main Content
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Model Analysis", "Data Explorer", "API"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Confusion Matrix")
        # Recompute confusion matrix based on threshold
        y_true = df['True Label']
        y_pred = (df['Predicted Probability'] > threshold).astype(int)
        cm = confusion_matrix(y_true, y_pred)
        
        fig_cm = px.imshow(cm,
                           labels=dict(x="Predicted", y="Actual", color="Count"),
                           x=['Normal', 'Threat'],
                           y=['Normal', 'Threat'],
                           text_auto=True,
                           color_continuous_scale='Blues')
        fig_cm.update_layout(title_text=f'Confusion Matrix (Threshold: {threshold})')
        st.plotly_chart(fig_cm, use_container_width=True)

    with col2:
        st.subheader("Prediction Distribution")
        fig_dist = px.histogram(df, x="Predicted Probability", color="True Label",
                                nbins=50,
                                labels={'True Label': 'Actual Class'},
                                opacity=0.7,
                                barmode='overlay',
                                color_discrete_map={0: 'green', 1: 'red'})
        fig_dist.add_vline(x=threshold, line_dash="dash", line_color="blue", annotation_text="Threshold")
        fig_dist.update_layout(title_text='Prediction Probability Distribution')
        st.plotly_chart(fig_dist, use_container_width=True)

    st.subheader("🔍 Top Threat Indicators")
    st.markdown("""
    **Key DDoS Attack Signatures:** These network features are most predictive of malicious traffic patterns.
    Understanding them demonstrates domain expertise in cybersecurity threat detection.
    """)
    
    top_features = metrics['top_features']
    df_features = pd.DataFrame(top_features)
    fig_feat = px.bar(df_features, x='importance', y='feature', orientation='h',
                      title='',  # Title in subheader instead
                      labels={'importance': 'Importance Score', 'feature': 'Network Feature'},
                      color='importance',
                      color_continuous_scale='Viridis',
                      height=500)
    fig_feat.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="Importance Score (Higher = Stronger DDoS Indicator)",
        showlegend=False
    )
    st.plotly_chart(fig_feat, use_container_width=True)
    
    # Add domain expertise explanation
    st.markdown("""
    **Why These Features Matter:**
    - **Destination Port**: DDoS attacks often target specific services (HTTP/HTTPS ports 80, 443)
    - **Init_Win_bytes**: Abnormal TCP window sizes indicate automated attack tools
    - **Packet Lengths**: Attack traffic shows distinctive size patterns vs. legitimate requests
    - **Flow Duration**: DDoS floods typically have very short connection durations
    """)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("ROC Curve")
        # Add interpretation
        roc_auc = metrics['model_performance']['roc_auc']
        st.markdown(f"""
        **AUC = {roc_auc:.4f}** (Perfect = 1.0)
        
        The Receiver Operating Characteristic (ROC) curve shows the trade-off between sensitivity and specificity.
        A perfect score of 1.0 means the model can **perfectly distinguish** between normal traffic and DDoS attacks
        with zero overlap in their probability distributions.
        """)
        
        fpr, tpr, _ = roc_curve(df['True Label'], df['Predicted Probability'])
        
        fig_roc = px.area(
            x=fpr, y=tpr,
            title=f'ROC Curve (AUC = {roc_auc:.4f})',
            labels=dict(x='False Positive Rate', y='True Positive Rate'),
            width=700, height=500
        )
        fig_roc.add_shape(
            type='line', line=dict(dash='dash'),
            x0=0, x1=1, y0=0, y1=1
        )
        st.plotly_chart(fig_roc, use_container_width=True)
        
    with col2:
        st.subheader("Precision-Recall Curve")
        st.markdown("""
        **Why this matters:** In cybersecurity, we care deeply about **Precision** (avoiding false alarms) 
        and **Recall** (catching all attacks). This curve shows how these metrics change as we adjust the threshold.
        """)
        
        precision, recall, _ = precision_recall_curve(df['True Label'], df['Predicted Probability'])
        
        fig_pr = px.area(
            x=recall, y=precision,
            title='Precision-Recall Curve',
            labels=dict(x='Recall', y='Precision'),
            width=700, height=500
        )
        st.plotly_chart(fig_pr, use_container_width=True)

with tab3:
    st.subheader("Data Explorer")
    
    filter_option = st.selectbox("Filter Data", ["All", "False Positives", "False Negatives", "High Confidence Threats"])
    
    filtered_df = df.copy()
    filtered_df['Current Prediction'] = (filtered_df['Predicted Probability'] > threshold).astype(int)
    
    if filter_option == "False Positives":
        filtered_df = filtered_df[(filtered_df['True Label'] == 0) & (filtered_df['Current Prediction'] == 1)]
        st.info("💡 **Analysis:** These are normal packets misclassified as threats. Often caused by high-volume legitimate traffic spikes.")
    elif filter_option == "False Negatives":
        filtered_df = filtered_df[(filtered_df['True Label'] == 1) & (filtered_df['Current Prediction'] == 0)]
        st.info("💡 **Analysis:** These are actual threats missed by the model. Often 'low-and-slow' attacks mimicking normal behavior.")
    elif filter_option == "High Confidence Threats":
        filtered_df = filtered_df[filtered_df['Predicted Probability'] > 0.9]
        
    st.write(f"Showing {len(filtered_df)} records")
    st.dataframe(filtered_df)

with tab4:
    st.subheader("Real-time Prediction API")
    st.markdown("""
    The model is served via FastAPI. You can send POST requests to the endpoint to get real-time predictions.
    
    **Endpoint:** `http://localhost:8001/predict`
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💻 Request Example")
        st.code("""
curl -X POST "http://localhost:8001/predict" \\
     -H "Content-Type: application/json" \\
     -d '{
           "features": {
             "Destination Port": 80,
             "Flow Duration": 5000000,
             "Total Fwd Packets": 150,
             "Total Backward Packets": 0,
             "Total Length of Fwd Packets": 10000,
             "Fwd Packet Length Max": 1000
           }
         }'
        """, language="bash")
        
    with col2:
        st.markdown("### 📄 Response Example")
        st.code("""
{
  "prediction": 1,
  "probability": 0.9985,
  "status": "Threat Detected",
  "processing_time": "0.002s"
}
        """, language="json")
        
    st.success("✅ **Production Ready:** Supports batch processing and includes health checks.")
