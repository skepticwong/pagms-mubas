import subprocess
import sys
import os
import time

def start_backend():
    print("🚀 Starting PAGMS Backend Server...")
    
    # Change to backend directory
    backend_dir = r"e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend"
    os.chdir(backend_dir)
    print(f"Changed to directory: {os.getcwd()}")
    
    # Start the backend server
    try:
        # Use subprocess to start the server and capture output
        process = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("Backend server started!")
        print("Waiting for server to initialize...")
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Backend server is running on http://localhost:5000")
            print("📊 Health check: http://localhost:5000/health")
            print("🔐 Auth endpoint: http://localhost:5000/api/me")
            
            # Try to read some output
            try:
                stdout, stderr = process.communicate(timeout=5)
                if stdout:
                    print(f"Server output: {stdout}")
                if stderr:
                    print(f"Server errors: {stderr}")
            except subprocess.TimeoutExpired:
                print("Server is running (timeout reached while reading output)")
                process.terminate()
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server exited with code {process.returncode}")
            if stdout:
                print(f"Output: {stdout}")
            if stderr:
                print(f"Errors: {stderr}")
                
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    start_backend()
