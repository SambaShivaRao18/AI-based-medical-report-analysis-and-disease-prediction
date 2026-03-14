# ~/Desktop/4th Major/project/medical-report-analysis/run_servers.py
import subprocess
import os
import sys

def run_flask(module_path, port, name):
    """Run a Flask app in a subprocess"""
    env = os.environ.copy()
    env['PYTHONPATH'] = module_path
    
    cmd = [sys.executable, 'app_integrated.py' if 'chatbot' in module_path else 'app.py', '--port', str(port)]
    
    return subprocess.Popen(
        cmd,
        cwd=module_path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

if __name__ == '__main__':
    print("🚀 Starting all Python Flask servers...")
    
    # Start Module 1 (Report Analyzer) on port 5001
    p1 = run_flask(
        'modules/report_analyzer',
        5001,
        'Report Analyzer'
    )
    print("✅ Report Analyzer starting on port 5001")
    
    # Start Module 2 (Health Chatbot) on port 5002
    p2 = run_flask(
        'modules/health_chatbot',
        5002,
        'Health Chatbot'
    )
    print("✅ Health Chatbot starting on port 5002")
    
    print("\n📝 Press Ctrl+C to stop all servers\n")
    
    try:
        # Wait for processes
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all servers...")
        p1.terminate()
        p2.terminate()