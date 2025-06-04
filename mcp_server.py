"""
MCP (Model Context Protocol) Server for AI Security Analysis Tools

This server provides security analysis functions as MCP tools that can be used
by AI assistants to analyze security events, generate statistics, and provide insights.
"""

from fastapi import FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from typing import Dict, Any, List
import json
import os
from pydantic import BaseModel

# Create the main API app (this could be imported from main.py if needed)
api_app = FastAPI(title="AI Security Platform API")

# Create a separate app for the MCP server
mcp_app = FastAPI(title="Security Analysis MCP Server")

# Initialize MCP from the API app
mcp = FastApiMCP(api_app)

@api_app.get("/")
async def api_root():
    """Main API root endpoint"""
    return {"message": "AI Security Platform API"}

# Mock data function (replace with actual data loading)
async def get_events_data() -> List[Dict]:
    """Get events data - this should be replaced with actual data loading logic"""
    try:
        with open('data/mock_events.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('events', [])
    except Exception as e:
        print(f"Error loading events data: {e}")
        return []

# Pydantic models for request bodies
class AnalyzeEventsRequest(BaseModel):
    query_type: str
    region_filter: str = None
    severity_filter: str = None
    category_filter: str = None
    time_period: str = None

class StatisticsRequest(BaseModel):
    stat_type: str

class LocationSearchRequest(BaseModel):
    location: str

# Security Analysis Tools as FastAPI endpoints (converted to MCP tools automatically)
@mcp_app.post("/analyze-security-events", 
    summary="Analyze Security Events",
    description="Analyze security events data to answer user questions about threats, patterns, and insights",
    operation_id="analyze_security_events"
)
async def analyze_security_events(request: AnalyzeEventsRequest) -> str:
    """
    Analyze security events data to answer user questions about threats, patterns, and insights.
    
    Args:
        request: Analysis request with query type and optional filters
    
    Returns:
        Analysis results as a formatted string
    """
    try:
        # Get events data
        events_data = await get_events_data()
        events = events_data.copy()
        
        # Apply filters
        if request.region_filter:
            events = [e for e in events if request.region_filter.lower() in e.get('location', '').lower()]
        
        if request.severity_filter:
            events = [e for e in events if e.get('severity') == request.severity_filter]
            
        if request.category_filter:
            events = [e for e in events if e.get('category') == request.category_filter]
        
        # Perform analysis based on query type
        if request.query_type == "summary":
            return _generate_summary(events)
        elif request.query_type == "threat_analysis":
            return _analyze_threats(events)
        elif request.query_type == "regional_focus":
            return _analyze_by_region(events)
        elif request.query_type == "severity_breakdown":
            return _analyze_by_severity(events)
        elif request.query_type == "trend_analysis":
            return _analyze_trends(events)
        else:
            return _generate_summary(events)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing security events: {str(e)}")

@mcp_app.post("/get-event-statistics",
    summary="Get Event Statistics", 
    description="Get statistical breakdown of security events",
    operation_id="get_event_statistics"
)
async def get_event_statistics(request: StatisticsRequest) -> Dict[str, Any]:
    """
    Get statistical breakdown of security events.
    
    Args:
        request: Statistics request with stat type
    
    Returns:
        Statistical data as a dictionary
    """
    try:
        # Get events data
        events_data = await get_events_data()
        events = events_data
        
        if request.stat_type == "count_by_severity":
            stats = {}
            for event in events:
                severity = event.get('severity', 'unknown')
                stats[severity] = stats.get(severity, 0) + 1
            return stats
            
        elif request.stat_type == "count_by_region":
            stats = {}
            for event in events:
                location = event.get('location', 'unknown').split(',')[0]
                stats[location] = stats.get(location, 0) + 1
            return stats
            
        elif request.stat_type == "count_by_category":
            stats = {}
            for event in events:
                category = event.get('category', 'unknown')
                stats[category] = stats.get(category, 0) + 1
            return stats
            
        return {"total_events": len(events)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@mcp_app.get("/get-critical-alerts",
    summary="Get Critical Alerts",
    description="Get all critical security alerts", 
    operation_id="get_critical_alerts"
)
async def get_critical_alerts() -> List[Dict[str, Any]]:
    """
    Get all critical security alerts.
    
    Returns:
        List of critical events with details
    """
    try:
        events_data = await get_events_data()
        critical_events = [e for e in events_data if e.get('severity') == 'critical']
        return critical_events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting critical alerts: {str(e)}")

@mcp_app.post("/search-events-by-location",
    summary="Search Events by Location",
    description="Search for security events in a specific location",
    operation_id="search_events_by_location" 
)
async def search_events_by_location(request: LocationSearchRequest) -> List[Dict[str, Any]]:
    """
    Search for security events in a specific location.
    
    Args:
        request: Location search request
    
    Returns:
        List of events in the specified location
    """
    try:
        events_data = await get_events_data()
        matching_events = [
            e for e in events_data 
            if request.location.lower() in e.get('location', '').lower()
        ]
        return matching_events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching events: {str(e)}")

# Helper functions (copied from openai_agent.py)
def _generate_summary(events: List[Dict]) -> str:
    """Generate a summary of security events"""
    if not events:
        return "No security events found matching the criteria."
    
    total = len(events)
    categories = {}
    severities = {}
    regions = set()
    
    for event in events:
        cat = event.get('category', 'unknown')
        sev = event.get('severity', 'unknown')
        loc = event.get('location', '').split(',')[0]
        
        categories[cat] = categories.get(cat, 0) + 1
        severities[sev] = severities.get(sev, 0) + 1
        regions.add(loc)
    
    summary = f"**Security Events Analysis**\n\n"
    summary += f"- **Total Events:** {total}\n"
    summary += f"- **Active Regions:** {len(regions)}\n\n"
    
    summary += "**By Category:**\n"
    for cat, count in categories.items():
        summary += f"- {cat.title()}: {count} events\n"
    
    summary += "\n**By Severity:**\n"
    for sev, count in severities.items():
        summary += f"- {sev.title()}: {count} events\n"
    
    # Highlight critical events
    critical_events = [e for e in events if e.get('severity') == 'critical']
    if critical_events:
        summary += f"\n**⚠️ Critical Alerts ({len(critical_events)}):**\n"
        for event in critical_events[:3]:  # Show first 3
            summary += f"- {event.get('title', 'Unknown event')} ({event.get('location', 'Unknown location')})\n"
    
    return summary

def _analyze_threats(events: List[Dict]) -> str:
    """Analyze threat patterns in events"""
    if not events:
        return "No threats detected in current data."
    
    high_priority = [e for e in events if e.get('severity') in ['critical', 'high']]
    
    analysis = "**Threat Analysis Report**\n\n"
    analysis += f"**High Priority Threats:** {len(high_priority)} out of {len(events)} total events\n\n"
    
    if high_priority:
        analysis += "**Key Threat Indicators:**\n"
        for event in high_priority[:5]:
            analysis += f"- **{event.get('title')}** ({event.get('severity').upper()})\n"
            analysis += f"  Location: {event.get('location')}\n"
            analysis += f"  Category: {event.get('category')}\n\n"
    
    return analysis

def _analyze_by_region(events: List[Dict]) -> str:
    """Analyze events by geographical region"""
    regional_data = {}
    for event in events:
        region = event.get('location', 'Unknown').split(',')[0]
        if region not in regional_data:
            regional_data[region] = []
        regional_data[region].append(event)
    
    analysis = "**Regional Security Analysis**\n\n"
    for region, region_events in sorted(regional_data.items()):
        severities = [e.get('severity') for e in region_events]
        critical_count = severities.count('critical')
        high_count = severities.count('high')
        
        analysis += f"**{region}** ({len(region_events)} events)\n"
        if critical_count:
            analysis += f"- ⚠️ Critical: {critical_count}\n"
        if high_count:
            analysis += f"- ⚡ High: {high_count}\n"
        analysis += f"- Categories: {', '.join(set([e.get('category', 'unknown') for e in region_events]))}\n\n"
    
    return analysis

def _analyze_by_severity(events: List[Dict]) -> str:
    """Analyze events by severity level"""
    severity_data = {}
    for event in events:
        severity = event.get('severity', 'unknown')
        if severity not in severity_data:
            severity_data[severity] = []
        severity_data[severity].append(event)
    
    analysis = "**Severity Level Analysis**\n\n"
    severity_order = ['critical', 'high', 'medium', 'low']
    
    for severity in severity_order:
        if severity in severity_data:
            events_list = severity_data[severity]
            analysis += f"**{severity.upper()}** ({len(events_list)} events)\n"
            
            categories = {}
            for event in events_list:
                cat = event.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            analysis += f"- Categories: {', '.join([f'{cat}: {count}' for cat, count in categories.items()])}\n"
            analysis += f"- Recent: {events_list[-1].get('title', 'Unknown')} ({events_list[-1].get('location', 'Unknown location')})\n\n"
    
    return analysis

def _analyze_trends(events: List[Dict]) -> str:
    """Analyze trends in security events"""
    if not events:
        return "No events available for trend analysis."
    
    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda x: x.get('timestamp', ''))
    
    analysis = "**Security Trends Analysis**\n\n"
    analysis += f"- **Total Events Analyzed:** {len(events)}\n"
    analysis += f"- **Time Range:** {sorted_events[0].get('timestamp', 'Unknown')} to {sorted_events[-1].get('timestamp', 'Unknown')}\n\n"
    
    # Category trends
    categories = {}
    for event in events:
        cat = event.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    analysis += "**Category Distribution:**\n"
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(events)) * 100
        analysis += f"- {cat.title()}: {count} events ({percentage:.1f}%)\n"
    
    return analysis

# Mount the MCP server to the separate app
mcp.mount(mcp_app)

# Add a root endpoint for the MCP app
@mcp_app.get("/")
async def mcp_root():
    """MCP Server root endpoint"""
    return {
        "message": "Security Analysis MCP Server",
        "description": "Model Context Protocol server for AI security analysis tools",
        "tools_available": [
            "analyze_security_events",
            "get_event_statistics", 
            "get_critical_alerts",
            "search_events_by_location"
        ]
    }

# Add endpoint to get tools information
@mcp_app.get("/tools")
async def list_mcp_tools():
    """List available MCP tools"""
    return {
        "tools": [
            {
                "name": "analyze_security_events",
                "description": "Analyze security events data with filtering options",
                "parameters": ["query_type", "region_filter", "severity_filter", "category_filter", "time_period"]
            },
            {
                "name": "get_event_statistics", 
                "description": "Get statistical breakdown of security events",
                "parameters": ["stat_type"]
            },
            {
                "name": "get_critical_alerts",
                "description": "Get all critical security alerts",
                "parameters": []
            },
            {
                "name": "search_events_by_location",
                "description": "Search for security events in a specific location", 
                "parameters": ["location"]
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting MCP Server...")
    print("Available tools:")
    print("- analyze_security_events")
    print("- get_event_statistics")
    print("- get_critical_alerts") 
    print("- search_events_by_location")
    uvicorn.run(mcp_app, host="0.0.0.0", port=8001) 