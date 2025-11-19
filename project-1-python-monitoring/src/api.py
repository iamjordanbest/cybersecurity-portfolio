"""
Threat Detection API
"""

import sys
import contextlib
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Add src to path to import local modules
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from preprocess import ThreatDataPreprocessor
from model import ThreatDetectionModel

# Global variables
ml_components = {}

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML components on startup."""
    try:
        print("Loading ML components...")
        project_root = Path(__file__).parent.parent
        
        # Paths
        preprocessor_path = project_root / 'src' / 'preprocessor.pkl'
        model_path = project_root / 'src' / 'threat_detection_model.pkl'
        
        # Load Preprocessor
        if not preprocessor_path.exists():
            print(f"Warning: Preprocessor not found at {preprocessor_path}")
        else:
            preprocessor = ThreatDataPreprocessor()
            preprocessor.load_preprocessor(str(preprocessor_path))
            ml_components['preprocessor'] = preprocessor
            
        # Load Model
        if not model_path.exists():
            print(f"Warning: Model not found at {model_path}")
        else:
            model = ThreatDetectionModel()
            model.load_model(str(model_path))
            ml_components['model'] = model
            
        if 'preprocessor' in ml_components and 'model' in ml_components:
            print("ML components loaded successfully.")
        else:
            print("Warning: Some ML components failed to load.")
            
        yield
    except Exception as e:
        print(f"Error loading ML components: {e}")
        yield
    finally:
        ml_components.clear()

app = FastAPI(
    title="DDoS Threat Detection API",
    description="Real-time threat detection using XGBoost",
    version="1.0.0",
    lifespan=lifespan
)

class PredictionRequest(BaseModel):
    features: Dict[str, Any]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "features": {
                        " Destination Port": 80,
                        " Flow Duration": 1000000,
                        " Total Fwd Packets": 10,
                        " Total Backward Packets": 8
                    }
                }
            ]
        }
    }

class PredictionResponse(BaseModel):
    prediction: int
    threat_probability: float
    status: str

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "model_loaded": "model" in ml_components,
        "preprocessor_loaded": "preprocessor" in ml_components
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    if 'model' not in ml_components or 'preprocessor' not in ml_components:
        raise HTTPException(status_code=503, detail="ML components not fully loaded")
    
    try:
        preprocessor = ml_components['preprocessor']
        model = ml_components['model']
        
        # Preprocess
        X_input = preprocessor.transform_single(request.features)
        
        # Predict
        prob = model.model.predict_proba(X_input)[0][1]
        pred = int(prob > 0.5)
        
        return PredictionResponse(
            prediction=pred,
            threat_probability=float(prob),
            status="THREAT DETECTED" if pred == 1 else "Normal Traffic"
        )
        
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
