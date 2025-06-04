# 🚀 Global AI Security Insights Platform

AI-powered security intelligence platform with real-time monitoring, interactive mapping, and multimodal analysis capabilities.

## Demo

Watch a quick overview of the platform in action:

## Features

- **Interactive World Map** - Real-time security event visualization with clickable markers
- **AI Intelligence Suite** - GPT-4o chat, vision analysis, audio transcription, web search
- **Autonomous Search Agent Swarm** - Deploy multiple independent agents for continuous event search and monitoring
- **Event Management** - Add, view, and delete security events with streaming web search
- **Security Events MCP Integration** - Connect with Model Context Protocol for enhanced AI assistant capabilities when analyzing global security events and opportunities

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### Setup & Run
```bash
# Clone and install
git clone <repository-url>
cd scsp-hackathon-global-security
pip install -r requirements.txt

# Configure API key
echo "OPENAI_API_KEY=your_key_here" > .env

# Run both main app + MCP server
python start_servers.py

# Or MCP server only
python run_mcp_only.py
```

Application available at: `http://localhost:8000`

MCP server available at: `http://localhost:8001`

## 🤖 Search Agent Swarm

The platform features an **autonomous search agent swarm** for continuous global security monitoring:

### How It Works
- **Multi-Agent Architecture**: Deploy multiple independent agents, one per search term
- **Continuous Monitoring**: Each agent searches independently
- **Real-Time Updates**: New events appear on the map as agents discover them for a given set of terms
- **Individual Control**: Stop/start specific agents or manage the entire swarm


## 🛠️ Tech Stack
- **Backend**: FastAPI, OpenAI API (GPT-4o, Vision, Whisper)
- **Frontend**: Vanilla JavaScript, Leaflet.js, Chart.js
- **Data**: JSON files for demo data, public and private APIs in production 

## Usage
1. **Map View** - Explore security events on interactive world map
2. **Upload Intelligence** - Analyze satellite images or audio files
3. **AI Chat** - Ask security questions, get analysis and operationalize intelligence
4. **Curated Web Search** - Find, inspect and add new events with AI-powered search
5. **Deploy Search Agent Swarm** - Launch autonomous agents for continuous monitoring or world events:
   - Enter comma-separated search terms: `"NBA, Taylor Swift, tariffs"`
   - Agents search continuosly and independently
   - Real-time status with event counters
   - Stop individual agents or entire swarm
6. **Events List** - View, manage, filter, and delete events

## Key API Endpoints

### Main App (Port 8000)
- `GET /api/events` - Get security events
- `POST /api/chat-stream` - Chat with AI assistant
- `POST /api/web-search-stream` - Stream web search results
- `POST /api/deploy-search-agents` - Deploy autonomous search agent swarm
- `POST /api/stop-search-agents` - Stop all search agents
- `POST /api/stop-single-agent` - Stop individual search agent
- `GET /api/agent-status` - Get real-time agent status and event counts
- `DELETE /api/delete-event/{id}` - Delete events

### MCP Server (Port 8001)
- `GET /tools` - List available MCP tools
- `POST /call` - Execute MCP tool calls
- **Tools**: `analyze_security_events`, `get_event_statistics`, `get_critical_alerts`, `search_events_by_location`

