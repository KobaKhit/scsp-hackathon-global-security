#!/usr/bin/env python3
"""
Startup script to run both the main FastAPI app and the MCP server separately.

This follows the fastapi-mcp documentation pattern for deploying separately.
"""

import subprocess
import sys
import time
import signal
import os
from multiprocessing import Process

def run_main_app():
    """Run the main FastAPI application"""
    print("🚀 Starting main FastAPI application on port 8000...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])

def run_mcp_server():
    """Run the MCP server"""
    print("🔧 Starting MCP server on port 8001...")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "mcp_server:mcp_app",
        "--host", "0.0.0.0", 
        "--port", "8001",
        "--reload"
    ])

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down servers...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🌟 AI Security Platform - Starting Services")
    print("=" * 50)
    
    try:
        # Start both processes
        main_process = Process(target=run_main_app)
        mcp_process = Process(target=run_mcp_server)
        
        main_process.start()
        time.sleep(2)  # Give main app time to start
        mcp_process.start()
        
        print("\n✅ Both servers started successfully!")
        print("📍 Main App: http://localhost:8000")
        print("🔧 MCP Server: http://localhost:8001")
        print("🛠️  MCP Tools: http://localhost:8001/tools")
        print("\nPress Ctrl+C to stop both servers")
        
        # Wait for processes
        main_process.join()
        mcp_process.join()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        main_process.terminate()
        mcp_process.terminate()
        main_process.join()
        mcp_process.join()
        print("✅ All servers stopped.")
    except Exception as e:
        print(f"❌ Error starting servers: {e}")
        sys.exit(1) 