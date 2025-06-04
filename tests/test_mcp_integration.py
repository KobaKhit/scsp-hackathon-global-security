#!/usr/bin/env python3
"""
Test script to verify MCP integration with OpenAI agent
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.openai_agent import OpenAIService

# Sample security events data for testing
SAMPLE_EVENTS = [
    {
        "id": "1",
        "title": "Suspicious Maritime Activity",
        "description": "Unidentified vessel detected near shipping lane",
        "severity": "high",
        "category": "maritime",
        "location": "South China Sea, Asia",
        "timestamp": "2024-01-15T10:30:00Z"
    },
    {
        "id": "2", 
        "title": "Supply Chain Disruption",
        "description": "Major port strike affecting cargo operations",
        "severity": "critical",
        "category": "supply-chain",
        "location": "Los Angeles, California, USA",
        "timestamp": "2024-01-15T08:45:00Z"
    },
    {
        "id": "3",
        "title": "Climate Risk Alert",
        "description": "Severe storm system approaching agricultural regions",
        "severity": "medium",
        "category": "climate",
        "location": "Queensland, Australia", 
        "timestamp": "2024-01-15T12:00:00Z"
    }
]

async def test_mcp_integration():
    """Test the MCP integration with OpenAI agent"""
    print("🧪 Testing MCP Integration with OpenAI Agent\n")
    
    try:
        # Initialize OpenAI service
        service = OpenAIService()
        
        # Test 1: Fetch tools from MCP server
        print("1️⃣ Testing dynamic tool fetching from MCP server...")
        tools = await service.get_security_analysis_tools()
        print(f"✅ Successfully fetched {len(tools)} tools from MCP server")
        
        # Print available tools
        for i, tool in enumerate(tools, 1):
            tool_name = tool['function']['name']
            tool_desc = tool['function']['description']
            print(f"   {i}. {tool_name}: {tool_desc}")
        
        print()
        
        # Test 2: Test direct function calls to MCP server
        print("2️⃣ Testing direct function calls to MCP server...")
        
        # Test analyze_security_events
        analysis_result = await service.analyze_security_events(
            SAMPLE_EVENTS, 
            query_type="summary"
        )
        print(f"✅ Analysis result: {analysis_result[:100]}...")
        
        # Test get_event_statistics
        stats_result = await service.get_event_statistics(
            SAMPLE_EVENTS,
            stat_type="count_by_severity"
        )
        print(f"✅ Statistics result: {stats_result}")
        
        # Test get_critical_alerts
        alerts_result = await service.get_critical_alerts(
            SAMPLE_EVENTS,
            limit=2
        )
        print(f"✅ Critical alerts: {len(alerts_result)} alerts found")
        
        print()
        
        # Test 3: Test chat completion with function calling
        print("3️⃣ Testing chat completion with function calling...")
        
        response_parts = []
        async for chunk in service.chat_completion_stream(
            message="Give me a summary of the current security events and show me statistics by severity",
            events_data=SAMPLE_EVENTS
        ):
            response_parts.append(chunk)
        
        full_response = "".join(response_parts)
        print(f"✅ Chat completion response: {full_response[:200]}...")
        
        print()
        print("🎉 All tests passed! MCP integration is working correctly.")
        
        # Close the HTTP client
        await service.http_client.aclose()
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if MCP server is running first
    import httpx
    
    async def check_mcp_server():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8001/tools")
                if response.status_code == 200:
                    print("✅ MCP server is running on localhost:8001")
                    return True
        except Exception as e:
            print(f"❌ MCP server is not accessible: {str(e)}")
            print("Please make sure to run: python run_mcp_only.py")
            return False
        return False
    
    async def main():
        server_running = await check_mcp_server()
        if server_running:
            await test_mcp_integration()
        else:
            print("\n💡 Start the MCP server first, then run this test again.")
    
    asyncio.run(main()) 