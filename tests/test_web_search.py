#!/usr/bin/env python3
"""
Test script for the web search functionality
"""

import asyncio
import json
from services.web_search_agent import WebSearchAgent

async def test_web_search():
    """Test the web search agent functionality"""
    
    print("🔍 Testing Web Search Agent...")
    
    # Initialize the web search agent
    async with WebSearchAgent() as agent:
        
        # Test 1: Basic web search
        print("\n📡 Test 1: Searching for 'Ukraine conflict'...")
        result1 = await agent.search_web_for_security_events("Ukraine conflict", max_events=3)
        
        if result1["success"]:
            print(f"✅ Found {result1['events_found']} events")
            for i, event in enumerate(result1["events"], 1):
                print(f"   {i}. {event['title']} - {event['location']} ({event['severity']})")
        else:
            print(f"❌ Search failed: {result1['error']}")
        
        # Test 2: Different search query
        print("\n📡 Test 2: Searching for 'South China Sea tensions'...")
        result2 = await agent.search_web_for_security_events("South China Sea tensions", max_events=2)
        
        if result2["success"]:
            print(f"✅ Found {result2['events_found']} events")
            for i, event in enumerate(result2["events"], 1):
                print(f"   {i}. {event['title']} - {event['location']} ({event['severity']})")
                print(f"      Coordinates: ({event['lat']}, {event['lon']})")
        else:
            print(f"❌ Search failed: {result2['error']}")
        
        # Test 3: Integration with existing events (dry run)
        if result1["success"] and result1["events"]:
            print("\n📊 Test 3: Testing event integration...")
            integration_result = await agent.integrate_events_with_existing(
                result1["events"][:1],  # Just add one event for testing
                "data/mock_events.json"
            )
            
            if integration_result["success"]:
                print(f"✅ Successfully integrated {integration_result['added_count']} events")
                print(f"   Total events in database: {integration_result['total_events']}")
            else:
                print(f"❌ Integration failed: {integration_result['error']}")

if __name__ == "__main__":
    asyncio.run(test_web_search()) 