"""Launch the FastAPI prediction endpoint."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api import app
import uvicorn

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
