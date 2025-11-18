#!/usr/bin/env python3
"""
Launch script for GRC Analytics Dashboard
"""

import subprocess
import sys
from pathlib import Path
import os

def check_dependencies():
    """Check if required packages are installed."""
    required = ['streamlit', 'plotly', 'pandas', 'yaml']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package if package != 'yaml' else 'pyyaml')
    
    return missing

def check_database():
    """Check if database exists."""
    db_path = Path(__file__).parent / 'data' / 'processed' / 'grc_analytics.db'
    return db_path.exists()

def main():
    """Launch the Streamlit dashboard."""
    dashboard_path = Path(__file__).parent / 'src' / 'dashboard' / 'app.py'
    
    print("=" * 70)
    print("🛡️  GRC Analytics Platform - Dashboard Launcher")
    print("=" * 70)
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    missing = check_dependencies()
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)
    print("✅ All dependencies installed")
    
    # Check database
    print("\n💾 Checking database...")
    if not check_database():
        print("❌ Database not found!")
        print("\nInitialize with:")
        print("  python scripts/initialize_database.py")
        print("  python src/ingestion/run_all_ingestion.py")
        print("  python scripts/generate_mock_compliance_data.py")
        sys.exit(1)
    print("✅ Database found")
    
    # Launch dashboard
    print("\n🚀 Starting Streamlit dashboard...")
    print(f"📊 Dashboard URL: http://localhost:8501")
    print(f"📁 Dashboard file: {dashboard_path}")
    print("\n💡 Tips:")
    print("  - Press 'R' to refresh the dashboard")
    print("  - Use sidebar to navigate between views")
    print("  - Press Ctrl+C to stop the server")
    print("\n" + "=" * 70)
    print()
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run',
            str(dashboard_path),
            '--server.port', '8501',
            '--server.headless', 'false',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("✅ Dashboard stopped successfully")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify Streamlit installation: pip install streamlit")
        print("  2. Check port 8501 is not in use")
        print("  3. Try: streamlit run src/dashboard/app.py")
        print("  4. See DASHBOARD_GUIDE.md for more help")
        sys.exit(1)

if __name__ == '__main__':
    main()
