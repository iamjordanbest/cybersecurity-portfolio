"""FastAPI endpoint for real-time threat predictions."""
import pickle
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import uvicorn
import logging

from preprocess import ThreatDataPreprocessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the trained model and preprocessor
MODEL_PATH = Path(__file__).parent / "threat_detection_model.pkl"
PREPROCESSOR_PATH = Path(__file__).parent / "preprocessor.pkl"

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    preprocessor = ThreatDataPreprocessor()
    preprocessor.load_preprocessor(PREPROCESSOR_PATH)
    
    print("✓ Model and preprocessor loaded successfully")
except FileNotFoundError as e:
    print(f"Error: Model files not found. Please run training first: python run_project_1.py")
    raise

app = FastAPI(
    title="DDoS Threat Detection API",
    description="Real-time threat prediction using XGBoost",
    version="1.0.0"
)

class PredictionRequest(BaseModel):
    features: Dict[str, Any]
    
    class Config:
        # Add input validation
        schema_extra = {
            "example": {
                "features": {
                    "Flow Duration": 12000,
                    "Total Fwd Packets": 8,
                    "Total Backward Packets": 0
                }
            }
        }

class PredictionResponse(BaseModel):
    prediction: int
    probability: float
    threat_level: str

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "model": "XGBoost Threat Detector",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """
    Predict whether network traffic is a threat.
    
    Args:
        request: Dictionary of feature values
        
    Returns:
        Prediction (0=Normal, 1=Threat), probability, and threat level
    """
    try:
        # Preprocess using the dedicated inference method
        X_processed = preprocessor.transform_single(request.features)
        
        # Predict
        prediction = int(model.predict(X_processed)[0])
        probability = float(model.predict_proba(X_processed)[0][1])
        
        # Determine threat level
        if probability < 0.3:
            threat_level = "Low"
        elif probability < 0.7:
            threat_level = "Medium"
        else:
            threat_level = "High"
        
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            threat_level=threat_level
        )
        
    except Exception as e:
        # Security fix: Don't expose detailed error information
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid input data provided")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Starting DDoS Threat Detection API...")
    print("="*50)
    print("\n📍 Endpoints:")
    print("  - http://localhost:8001/")
    print("  - http://localhost:8001/health")
    print("  - http://localhost:8001/predict (POST)")
    print("  - http://localhost:8001/docs (Interactive)")
    print("\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
