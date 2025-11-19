#!/usr/bin/env python3
"""
🛡️ Cybersecurity Portfolio - Unified Runner
Run any project from a single entry point.
"""

import argparse
import subprocess
import sys
from pathlib import Path

def run_project_1():
    """Run Project 1: Python Monitoring"""
    print("\nLaunching Project 1: DDoS Threat Detection...")
    script_path = Path("project-1-python-monitoring/run_project_1.py")
    if not script_path.exists():
        print(f"Error: {script_path} not found.")
        return
    
    subprocess.run([sys.executable, str(script_path)])

def run_project_2():
    """Run Project 2: GRC Compliance"""
    print("\nLaunching Project 2: GRC Compliance API...")
    script_path = Path("project-2-grc-compliance/run_project_2.py")
    if not script_path.exists():
        print(f"Error: {script_path} not found.")
        return
    
    try:
        subprocess.run([sys.executable, str(script_path)])
    except KeyboardInterrupt:
        print("\nServer stopped.")

def run_project_1_api():
    """Run Project 1: DDoS Threat Detection API"""
    print("\nLaunching Project 1: DDoS Threat Detection API...")
    script_path = Path("project-1-python-monitoring/run_api.py")
    if not script_path.exists():
        print(f"Error: {script_path} not found.")
        return
    
    try:
        subprocess.run([sys.executable, str(script_path)])
    except KeyboardInterrupt:
        print("\nServer stopped.")

def main():
    parser = argparse.ArgumentParser(description="Cybersecurity Portfolio Runner")
    parser.add_argument('project', choices=['1', '1-api', '2', 'all'], nargs='?', help="Project to run")
    parser.add_argument('--list', action='store_true', help="List available projects")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available Projects:")
        print("  1.     DDoS Threat Detection (Batch Pipeline)")
        print("  1-api. DDoS Threat Detection (Real-time API)")
        print("  2.     GRC Compliance Platform (API/Backend)")
        return

    if args.project == '1':
        run_project_1()
    elif args.project == '1-api':
        run_project_1_api()
    elif args.project == '2':
        run_project_2()
    else:
        print("Welcome to Jordan Best's Cybersecurity Portfolio!")
        print("Please specify a project to run:")
        print("  python run_portfolio.py 1      -> Run Project 1 (Pipeline)")
        print("  python run_portfolio.py 1-api  -> Run Project 1 (API)")
        print("  python run_portfolio.py 2      -> Run Project 2 (API)")

if __name__ == "__main__":
    main()
