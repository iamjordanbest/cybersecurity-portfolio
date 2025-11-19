import os
import sys
import subprocess
from pathlib import Path

def main():
    """
    Unified entry point for Project 2: GRC Compliance.
    Orchestrates data generation and dashboard launch.
    """
    project_root = Path(__file__).parent.absolute()
    
    print("="*50)
    print("🛡️  Project 2: GRC Compliance Dashboard")
    print("="*50)
    
    # 1. Generate Mock Data
    print("\n[1/2] Checking/Generating Mock Data...")
    data_script = project_root / "scripts" / "generate_mock_compliance_data.py"
    if not data_script.exists():
        print(f"Error: Data generation script not found at {data_script}")
        return
        
    try:
        subprocess.run([sys.executable, str(data_script)], check=True)
        print("✅ Data generation complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Data generation failed: {e}")
        return

    # 2. Launch Dashboard
    print("\n[2/2] Launching Streamlit Dashboard...")
    dashboard_script = project_root / "src" / "dashboard" / "app.py"
    if not dashboard_script.exists():
        print(f"Error: Dashboard script not found at {dashboard_script}")
        return

    print(f"Running: streamlit run {dashboard_script}")
    print("Press Ctrl+C to stop the dashboard.")
    
    # Set PYTHONPATH to include src
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    
    try:
        subprocess.run(["streamlit", "run", str(dashboard_script)], env=env, check=True)
    except KeyboardInterrupt:
        print("\nDashboard stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Dashboard failed: {e}")

if __name__ == "__main__":
    main()
