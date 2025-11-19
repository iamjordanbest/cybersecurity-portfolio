import subprocess
import time
import sys
import os
import signal

def verify_dashboard_startup():
    print("Starting dashboard verification...")
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
    
    # Start Streamlit
    cmd = f'"{sys.executable}" -m streamlit run src/dashboard/app.py --server.headless=true'
    process = subprocess.Popen(
        cmd,
        shell=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"Dashboard process started with PID: {process.pid}")
    
    # Wait for a few seconds to let it initialize
    time.sleep(5)
    
    # Check if it's still running
    if process.poll() is None:
        print("[OK] Dashboard is running successfully.")
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        print("Dashboard stopped.")
        sys.exit(0)
    else:
        stdout, stderr = process.communicate()
        print("[FAIL] Dashboard failed to start.")
        print("STDOUT:", stdout.decode())
        print("STDERR:", stderr.decode())
        sys.exit(1)

if __name__ == "__main__":
    verify_dashboard_startup()
