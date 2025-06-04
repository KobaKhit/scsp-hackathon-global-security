import os
from openai import AsyncOpenAI
from typing import Dict, Any, List, AsyncGenerator
import json
import httpx
from .config import Config

class OpenAIService:
    def __init__(self):
        # Initialize OpenAI client using configuration
        self.client = AsyncOpenAI(
            api_key=Config.get_openai_api_key()
        )
        self.model = "gpt-4o"
        self.mcp_server_url = "http://localhost:8001"  # MCP server URL
        self.http_client = httpx.AsyncClient()
        self._cached_tools = None  # Cache for tools to avoid repeated API calls
    
    async def get_security_analysis_tools(self):
        """Dynamically fetch function tools from MCP server and convert to OpenAI format"""
        if self._cached_tools is not None:
            return self._cached_tools
            
        try:
            response = await self.http_client.get(f"{self.mcp_server_url}/tools")
            response.raise_for_status()
            
            mcp_tools = response.json()
            openai_tools = []
            
            for tool in mcp_tools.get("tools", []):
                openai_tool = self._convert_mcp_tool_to_openai_format(tool)
                openai_tools.append(openai_tool)
            
            self._cached_tools = openai_tools
            return openai_tools
            
        except Exception as e:
            print(f"Warning: Could not fetch tools from MCP server: {str(e)}")
            # Fallback to basic tools if MCP server is unavailable
            return self._get_fallback_tools()
    
    def _convert_mcp_tool_to_openai_format(self, mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP tool format to OpenAI function format"""
        tool_name = mcp_tool["name"]
        description = mcp_tool["description"]
        parameters = mcp_tool.get("parameters", [])
        
        # Define parameter schemas based on tool name and known parameters
        properties = {}
        required = []
        
        if tool_name == "analyze_security_events":
            properties = {
                "query_type": {
                    "type": "string",
                    "enum": ["summary", "threat_analysis", "regional_focus", "severity_breakdown", "trend_analysis", "specific_event"],
                    "description": "Type of analysis to perform"
                },
                "region_filter": {
                    "type": "string",
                    "description": "Filter events by region/location if specified"
                },
                "severity_filter": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Filter events by severity level"
                },
                "category_filter": {
                    "type": "string",
                    "enum": ["maritime", "climate", "supply-chain"],
                    "description": "Filter events by category"
                },
                "time_period": {
                    "type": "string",
                    "description": "Time period for analysis (e.g., 'last 7 days', 'recent')"
                }
            }
            required = ["query_type"]
            
        elif tool_name == "get_event_statistics":
            properties = {
                "stat_type": {
                    "type": "string",
                    "enum": ["count_by_severity", "count_by_region", "count_by_category", "recent_trends"],
                    "description": "Type of statistics to generate"
                }
            }
            required = ["stat_type"]
            
        elif tool_name == "get_critical_alerts":
            properties = {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of alerts to return (default: 5)"
                }
            }
            required = []
            
        elif tool_name == "search_events_by_location":
            properties = {
                "location": {
                    "type": "string",
                    "description": "Location to search for events"
                }
            }
            required = ["location"]
        
        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def _get_fallback_tools(self):
        """Fallback tools if MCP server is unavailable"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_security_events",
                    "description": "Analyze security events data with filtering options",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "enum": ["summary", "threat_analysis", "regional_focus", "severity_breakdown", "trend_analysis"],
                                "description": "Type of analysis to perform"
                            }
                        },
                        "required": ["query_type"]
                    }
                }
            }
        ]

    async def analyze_security_events(self, events_data: List[Dict], query_type: str, **filters) -> str:
        """Analyze security events using MCP server"""
        try:
            # Build payload, excluding None values
            payload = {"query_type": query_type}
            
            # Only include filters that have values
            if filters.get('region_filter'):
                payload["region_filter"] = filters.get('region_filter')
            if filters.get('severity_filter'):
                payload["severity_filter"] = filters.get('severity_filter')
            if filters.get('category_filter'):
                payload["category_filter"] = filters.get('category_filter')
            if filters.get('time_period'):
                payload["time_period"] = filters.get('time_period')
            
            response = await self.http_client.post(
                f"{self.mcp_server_url}/analyze-security-events",
                json=payload
            )
            response.raise_for_status()
            
            # MCP server returns analysis string directly
            result = response.json()
            if isinstance(result, str):
                return result
            else:
                return result.get("analysis", "No analysis available")
            
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.text
            except:
                pass
            return f"HTTP {e.response.status_code} error calling MCP server: {error_detail}"
        except Exception as e:
            return f"Error calling MCP server for analysis: {str(e)}"
    
    async def get_event_statistics(self, events_data: List[Dict], stat_type: str) -> Dict[str, Any]:
        """Get event statistics using MCP server"""
        try:
            payload = {
                "stat_type": stat_type
            }
            
            response = await self.http_client.post(
                f"{self.mcp_server_url}/get-event-statistics",
                json=payload
            )
            response.raise_for_status()
            
            # MCP server returns statistics dict directly
            return response.json()
            
        except Exception as e:
            return {"error": f"Error calling MCP server for statistics: {str(e)}"}
    
    async def get_critical_alerts(self, events_data: List[Dict], limit: int = 5) -> List[Dict]:
        """Get critical alerts using MCP server"""
        try:
            response = await self.http_client.get(
                f"{self.mcp_server_url}/get-critical-alerts"
            )
            response.raise_for_status()
            
            # MCP server returns alerts list directly
            return response.json()
            
        except Exception as e:
            return [{"error": f"Error calling MCP server for critical alerts: {str(e)}"}]
    
    async def search_events_by_location(self, events_data: List[Dict], location: str) -> List[Dict]:
        """Search events by location using MCP server"""
        try:
            payload = {
                "location": location
            }
            
            response = await self.http_client.post(
                f"{self.mcp_server_url}/search-events-by-location",
                json=payload
            )
            response.raise_for_status()
            
            # MCP server returns events list directly
            return response.json()
            
        except Exception as e:
            return [{"error": f"Error calling MCP server for location search: {str(e)}"}]

    async def chat_completion_stream(self, message: str, context: str = None, events_data: List[Dict] = None) -> AsyncGenerator[str, None]:
        """Streaming chat completion with function calling support using MCP server"""
        try:
            system_prompt = """You are an AI assistant for a Global Security Insights Platform. 
            You provide analysis on:
            - Maritime security and AIS tracking
            - Diplomatic intelligence
            - Supply chain disruptions
            - Trade and tariff impacts  
            - Social stability and happiness indices
            - Food security and climate risks
            
            You have access to real-time security events data through function tools that connect to an MCP server. Use these tools to provide accurate, data-driven insights and analysis. When users ask about events, patterns, or specific regions, call the appropriate function to analyze the current data.
            
            Provide concise, actionable intelligence insights. Be professional and analytical."""
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            if context:
                messages.append({"role": "user", "content": f"Context: {context}"})
            
            messages.append({"role": "user", "content": message})
            
            # Use function calling if events data is available
            if events_data:
                tools = await self.get_security_analysis_tools()  # Now dynamically fetched
                
                # First, check if we need to call functions
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=50  # Small response to check for function calls
                )
                
                # Handle function calls using MCP server
                if response.choices[0].message.tool_calls:
                    messages.append(response.choices[0].message)
                    
                    for tool_call in response.choices[0].message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        if function_name == "analyze_security_events":
                            result = await self.analyze_security_events(events_data, **function_args)
                        elif function_name == "get_event_statistics":
                            stats = await self.get_event_statistics(events_data, **function_args)
                            result = json.dumps(stats)
                        elif function_name == "get_critical_alerts":
                            alerts = await self.get_critical_alerts(events_data, **function_args)
                            result = json.dumps(alerts)
                        elif function_name == "search_events_by_location":
                            events = await self.search_events_by_location(events_data, **function_args)
                            result = json.dumps(events)
                        else:
                            result = "Function not found"
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result
                        })
                
                # Now stream the final response
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=800,
                    temperature=0.7,
                    stream=True
                )
            else:
                # Regular streaming without function calls
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7,
                    stream=True
                )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error generating response: {str(e)}"
    
    async def chat_completion(self, message: str, context: str = None) -> str:
        """General chat completion for intelligence analysis"""
        try:
            system_prompt = """You are an AI assistant for a Global Security Insights Platform. 
            You provide analysis on:
            - Maritime security and AIS tracking
            - Diplomatic intelligence
            - Supply chain disruptions
            - Trade and tariff impacts  
            - Social stability and happiness indices
            - Food security and climate risks
            
            Provide concise, actionable intelligence insights. Be professional and analytical."""
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            if context:
                messages.append({"role": "user", "content": f"Context: {context}"})
            
            messages.append({"role": "user", "content": message})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    async def generate_intelligence_summary(self, context: str) -> str:
        """Generate an intelligence summary based on current data"""
        try:
            prompt = f"""Based on the following security platform data, generate a concise intelligence summary:

{context}

Focus on:
1. Key threats or opportunities identified
2. Trends in the data
3. Recommended actions or areas requiring attention
4. Risk assessment

Keep the summary under 300 words and use professional intelligence language."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior intelligence analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating intelligence summary: {str(e)}"
    
    async def analyze_with_tools(self, query: str, available_data: Dict[str, Any]) -> str:
        """Advanced analysis using function calling"""
        try:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_security_threat",
                        "description": "Analyze potential security threats from event data",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "threat_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                                "threat_type": {"type": "string"},
                                "affected_regions": {"type": "array", "items": {"type": "string"}},
                                "recommended_actions": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    }
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI security analyst. Use the provided tools to analyze threats."},
                    {"role": "user", "content": f"Analyze this security data: {query}\n\nAvailable data: {json.dumps(available_data, indent=2)}"}
                ],
                tools=tools,
                tool_choice="auto",
                max_tokens=600
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error in advanced analysis: {str(e)}"
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client"""
        await self.http_client.aclose() 