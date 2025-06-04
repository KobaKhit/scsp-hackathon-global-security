#!/usr/bin/env python3
"""
Script to run only the MCP server for testing or standalone use.
"""

if __name__ == "__main__":
    import uvicorn
    
    print("🔧 Starting AI Security Analysis MCP Server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("🛠️  Available tools:")
    print("   - analyze_security_events")
    print("   - get_event_statistics")
    print("   - get_critical_alerts")
    print("   - search_events_by_location")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        "mcp_server:mcp_app", 
        host="0.0.0.0", 
        port=8001,
        reload=True
    ) 