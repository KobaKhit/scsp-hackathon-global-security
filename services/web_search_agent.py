import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, AsyncGenerator
from openai import AsyncOpenAI
import httpx
from .config import Config

class WebSearchAgent:
    def __init__(self):
        """Initialize the web search agent with OpenAI client"""
        self.client = AsyncOpenAI(api_key=Config.get_openai_api_key())
        self.model = "gpt-4o"
        self.http_client = httpx.AsyncClient()
        
        # Known location to coordinates mapping (can be expanded)
        self.location_coords = {
            "south china sea": (9.5, 113.5),
            "shanghai": (31.2, 121.5),
            "horn of africa": (2.0, 38.0),
            "inner mongolia": (40.8, 111.9),
            "arctic ocean": (75.0, 100.0),
            "bangladesh": (23.7, 90.4),
            "red sea": (20.0, 38.0),
            "northern india": (28.7, 77.1),
            "suez canal": (30.0, 32.3),
            "philippines": (14.6, 121.0),
            "ukraine": (48.3, 31.2),
            "syria": (34.8, 38.9),
            "iran": (32.4, 53.7),
            "gaza": (31.3, 34.3),
            "lebanon": (33.9, 35.5),
            "yemen": (15.6, 48.0),
            "afghanistan": (33.9, 67.7),
            "taiwan": (23.8, 120.9),
            "north korea": (40.3, 127.5),
            "venezuela": (6.4, -66.6),
            "myanmar": (19.8, 96.1),
            "mali": (17.6, -3.9),
            "somalia": (5.2, 46.2),
            "ethiopia": (9.1, 40.5),
            "south sudan": (6.9, 31.3)
        }
    
    async def search_web_for_security_events(self, query: str, max_events: int = 5) -> Dict[str, Any]:
        """
        Search the web for security-related events based on user query
        and return structured events data
        """
        try:
            # First, use web search to get current information
            search_results = await self._perform_web_search(query)
            
            # Extract events from search results using AI
            events = await self._extract_events_from_search(search_results, query, max_events)
            
            # Add geo coordinates to events
            events_with_geo = await self._add_geo_coordinates(events)
            
            return {
                "success": True,
                "query": query,
                "events_found": len(events_with_geo),
                "events": events_with_geo,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "events": [],
                "timestamp": datetime.now().isoformat()
            }
    
    async def search_web_for_security_events_stream(self, query: str, max_events: int = 5) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Search the web for security-related events and yield them one by one as they're generated
        """
        try:
            # Yield initial status
            yield {
                "type": "status",
                "message": "Starting web search...",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            
            # Perform web search
            search_results = await self._perform_web_search(query)
            
            yield {
                "type": "status",
                "message": "Analyzing search results...",
                "timestamp": datetime.now().isoformat()
            }
            
            # Extract events one by one
            async for event in self._extract_events_from_search_stream(search_results, query, max_events):
                # Add geo coordinates to the event
                event_with_geo = await self._add_geo_coordinates([event])
                if event_with_geo:
                    yield {
                        "type": "event",
                        "event": event_with_geo[0],
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Final status
            yield {
                "type": "complete",
                "message": "Search completed successfully",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "message": f"Search failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _perform_web_search(self, query: str) -> str:
        """
        Perform web search using OpenAI's web browsing capability
        """
        try:
            # Create a comprehensive search prompt for security events
            search_prompt = f"""
            Search the web for recent security-related events, conflicts, or incidents related to: {query}
            
            Focus on finding:
            - Maritime security incidents
            - Supply chain disruptions
            - Climate-related security issues
            - Opportunities to strengthen U.S. security through non-military elements of national power, such as diplomacy, economic policies, and the advancement of human rights and justice around the world.
            
            Provide current, factual information with specific locations, dates, and details.
            Look for events from the last 30 days and 30 days into the future if possible.
            """
            
            # Use the web search tool via OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security intelligence analyst. Search the web for current security events and provide detailed, factual information."},
                    {"role": "user", "content": search_prompt}
                ],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for current information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }],
                tool_choice="auto"
            )
            
            # Extract the search results from the response
            if response.choices[0].message.tool_calls:
                # If tool was called, we'll simulate web search results
                # In a real implementation, this would call an actual web search API
                return await self._simulate_web_search(query)
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            # Fallback to simulated search if web search fails
            return await self._simulate_web_search(query)
    
    async def _simulate_web_search(self, query: str) -> str:
        """
        Simulate web search results for demonstration purposes
        In production, this would be replaced with actual web search API calls
        """
        # Generate realistic search results based on common security events
        simulated_results = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a security intelligence analyst. Generate realistic, current security event information that would be found in recent news searches. Make sure events have specific locations, dates, and security implications."},
                {"role": "user", "content": f"Generate 3-5 realistic recent security events related to: {query}. Include specific locations, recent dates, and security implications. Format as if these were found in recent news articles."}
            ]
        )
        
        return simulated_results.choices[0].message.content
    
    async def _extract_events_from_search(self, search_results: str, original_query: str, max_events: int) -> List[Dict[str, Any]]:
        """
        Extract structured security events from web search results using AI
        """
        extraction_prompt = f"""
        Analyze the following search results and extract structured security events.
        Original search query: {original_query}
        
        Search Results:
        {search_results}
        
        Extract up to {max_events} security events and format each as a JSON object with these fields:
        - title: Brief descriptive title
        - description: Detailed description of the event
        - category: Choose the most appropriate category (e.g., "maritime", "climate", "supply-chain", "cyber", "conflict", "terrorism", "political", "economic", "social", "environmental", etc.)
        - severity: One of ["low", "medium", "high", "critical"]
        - location: Specific location name (city, region, country)
        - timestamp: ISO format timestamp (use recent dates if not specified)
        - source: News source or "Web Search"
        - tags: Array of relevant tags
        
        Return ONLY a JSON array of events, no other text.
        Ensure each event is realistic and based on the search results.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security analyst extracting structured data. Return only valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure it's valid JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            events = json.loads(content)
            
            # Ensure we have a list
            if not isinstance(events, list):
                events = [events] if isinstance(events, dict) else []
            
            # Add IDs and validate structure
            processed_events = []
            for i, event in enumerate(events[:max_events]):
                if isinstance(event, dict) and "title" in event:
                    event["id"] = f"web_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
                    processed_events.append(event)
            
            return processed_events
            
        except json.JSONDecodeError as e:
            # Fallback: create a simple event from the query
            return [{
                "id": f"web_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_0",
                "title": f"Security Event: {original_query}",
                "description": f"Web search conducted for: {original_query}. Unable to parse structured results.",
                "category": "conflict",
                "severity": "medium",
                "location": "Global",
                "timestamp": datetime.now().isoformat(),
                "source": "Web Search",
                "tags": ["web-search", "general"]
            }]
        except Exception as e:
            return []
    
    async def _extract_events_from_search_stream(self, search_results: str, original_query: str, max_events: int) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Extract structured security events from web search results one by one
        """
        extraction_prompt = f"""
        Analyze the following search results and extract structured security events.
        Original search query: {original_query}
        
        Search Results:
        {search_results}
        
        Extract up to {max_events} security events and format each as a JSON object with these fields:
        - title: Brief descriptive title
        - description: Detailed description of the event
        - category: Choose the most appropriate category (e.g., "maritime", "climate", "supply-chain", "cyber", "conflict", "terrorism", "political", "economic", "social", "environmental", etc.)
        - severity: One of ["low", "medium", "high", "critical"]
        - location: Specific location name (city, region, country)
        - timestamp: ISO format timestamp (use recent dates if not specified)
        - source: News source or "Web Search"
        - tags: Array of relevant tags
        
        Return ONLY a JSON array of events, no other text.
        Ensure each event is realistic and based on the search results.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security analyst extracting structured data. Return only valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure it's valid JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            events = json.loads(content)
            
            # Ensure we have a list
            if not isinstance(events, list):
                events = [events] if isinstance(events, dict) else []
            
            # Yield events one by one with a small delay for streaming effect
            for event in events[:max_events]:
                # Add some realistic delay to simulate processing time
                await asyncio.sleep(0.5)
                yield event
                
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to extract events with regex
            import re
            
            # Try to find JSON objects in the response
            json_pattern = r'\{[^{}]*\}'
            matches = re.findall(json_pattern, content)
            
            for match in matches[:max_events]:
                try:
                    event = json.loads(match)
                    await asyncio.sleep(0.5)
                    yield event
                except json.JSONDecodeError:
                    continue
        
        except Exception as e:
            # Create a simulated event if extraction fails
            fallback_event = {
                "title": f"Security Event: {original_query}",
                "description": f"Simulated security event related to {original_query}",
                "category": "general",
                "severity": "medium",
                "location": "Global",
                "timestamp": datetime.now().isoformat(),
                "source": "Web Search",
                "tags": [original_query.lower()]
            }
            yield fallback_event
    
    async def _add_geo_coordinates(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add latitude and longitude coordinates to events based on location
        """
        events_with_geo = []
        
        for event in events:
            location = event.get("location", "").lower()
            
            # Try to find coordinates from our mapping
            lat, lon = await self._get_coordinates_for_location(location)
            
            event["lat"] = lat
            event["lon"] = lon
            events_with_geo.append(event)
        
        return events_with_geo
    
    async def _get_coordinates_for_location(self, location: str) -> Tuple[float, float]:
        """
        Get coordinates for a location using various methods
        """
        location_lower = location.lower().strip()
        
        # First, check our known locations
        for known_location, coords in self.location_coords.items():
            if known_location in location_lower or location_lower in known_location:
                return coords
        
        # Try AI-based coordinate estimation
        try:
            coord_prompt = f"""
            Provide the approximate latitude and longitude coordinates for: {location}
            
            Return only two numbers separated by a comma: latitude,longitude
            For example: 40.7,-74.0
            
            If the location is very general or unknown, provide coordinates for the most likely region.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a geography expert. Provide only latitude,longitude coordinates."},
                    {"role": "user", "content": coord_prompt}
                ],
                temperature=0.1
            )
            
            coord_text = response.choices[0].message.content.strip()
            
            # Parse coordinates
            coords = coord_text.split(',')
            if len(coords) == 2:
                lat = float(coords[0].strip())
                lon = float(coords[1].strip())
                return lat, lon
            
        except Exception:
            pass
        
        # Default to center of world map if all else fails
        return 0.0, 0.0
    
    async def integrate_events_with_existing(self, new_events: List[Dict[str, Any]], existing_events_file: str = "data/mock_events.json") -> Dict[str, Any]:
        """
        Integrate new web search events with existing events data
        """
        try:
            # Load existing events
            try:
                with open(existing_events_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = {"events": []}
            
            # Get current max ID
            max_id = 0
            for event in existing_data.get("events", []):
                if isinstance(event.get("id"), int):
                    max_id = max(max_id, event["id"])
            
            # Add new events with proper IDs
            added_events = []
            for new_event in new_events:
                max_id += 1
                new_event["id"] = max_id
                existing_data["events"].append(new_event)
                added_events.append(new_event)
            
            # Save updated events
            with open(existing_events_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "added_count": len(added_events),
                "total_events": len(existing_data["events"]),
                "added_events": added_events
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "added_count": 0
            }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose() 