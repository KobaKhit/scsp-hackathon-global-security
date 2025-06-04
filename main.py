from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import asyncio
from pathlib import Path

# Import our service modules
from services.openai_agent import OpenAIService
from services.vision_processor import process_satellite_image
from services.whisper_transcribe import transcribe_audio
from services.web_search_agent import WebSearchAgent
from services.search_agent_manager import search_agent_manager

app = FastAPI(title="Global AI Security Insights Platform", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
openai_service = OpenAIService()
web_search_agent = WebSearchAgent()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load mock data
def load_mock_events():
    try:
        with open("data/mock_events.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"events": []}

def load_geo_data():
    try:
        with open("data/geo_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"features": []}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main application page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Welcome to AI Security Platform</h1><p>Frontend not found</p>")

@app.get("/api/events")
async def get_events():
    """Get current security events for the map and event list"""
    events = load_mock_events()
    return JSONResponse(content=events)

@app.get("/api/geo-data")
async def get_geo_data():
    """Get geographical overlay data for the map"""
    geo_data = load_geo_data()
    return JSONResponse(content=geo_data)

@app.post("/api/chat-stream")
async def chat_stream(message: str = Form(...)):
    """Streaming chat with the OpenAI agent for real-time responses with access to events data"""
    async def generate():
        try:
            # Load current events data for AI analysis
            events_data = load_mock_events()
            events_list = events_data.get('events', [])
            
            async for chunk in openai_service.chat_completion_stream(message, events_data=events_list):
                # Send each chunk as Server-Sent Event
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/api/chat")
async def chat_with_ai(message: str = Form(...)):
    """Chat with the OpenAI agent for intelligence analysis"""
    try:
        response = await openai_service.chat_completion(message)
        return JSONResponse(content={
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    analysis_type: str = Form(default="general")
):
    """Analyze satellite or other security-relevant images"""
    try:
        # Save uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process with vision AI
        analysis = await process_satellite_image(file_path, analysis_type)
        
        # Clean up temporary file
        os.remove(file_path)
        
        return JSONResponse(content={
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "image_name": file.filename
        })
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe-audio")
async def transcribe_meeting(file: UploadFile = File(...)):
    """Transcribe diplomatic meetings or audio intelligence"""
    try:
        # Save uploaded audio file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Transcribe with Whisper
        transcription = await transcribe_audio(file_path)
        
        # Clean up temporary file
        os.remove(file_path)
        
        return JSONResponse(content={
            "transcription": transcription,
            "timestamp": datetime.now().isoformat(),
            "audio_file": file.filename
        })
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence-summary")
async def get_intelligence_summary():
    """Get AI-generated intelligence summary"""
    try:
        events = load_mock_events()
        geo_data = load_geo_data()
        
        # Generate summary using OpenAI
        context = f"Current events: {len(events.get('events', []))} events detected. Geographic data: {len(geo_data.get('features', []))} regions monitored."
        summary = await openai_service.generate_intelligence_summary(context)
        
        return JSONResponse(content={
            "summary": summary,
            "event_count": len(events.get('events', [])),
            "regions_monitored": len(geo_data.get('features', [])),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-event")
async def update_event(event_data: Dict[str, Any]):
    """Update or add a new security event"""
    try:
        events = load_mock_events()
        
        # Add timestamp if not provided
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.now().isoformat()
        
        # Add new event
        events["events"].append(event_data)
        
        # Save back to file
        with open("data/mock_events.json", "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        return JSONResponse(content={"success": True, "message": "Event added successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete-event/{event_id}")
async def delete_event(event_id: int):
    """Delete a security event by ID"""
    try:
        events = load_mock_events()
        
        # Find and remove the event with matching ID
        original_count = len(events["events"])
        events["events"] = [event for event in events["events"] if event.get("id") != event_id]
        
        # Check if event was found and deleted
        if len(events["events"]) == original_count:
            raise HTTPException(status_code=404, detail=f"Event with ID {event_id} not found")
        
        # Save back to file
        with open("data/mock_events.json", "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        return JSONResponse(content={
            "success": True, 
            "message": f"Event {event_id} deleted successfully",
            "deleted_id": event_id
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/web-search-stream")
async def web_search_security_events_stream(query: str = Form(...), max_events: int = Form(default=5)):
    """Stream web search results for security events in real-time"""
    async def generate():
        try:
            async for result in web_search_agent.search_web_for_security_events_stream(query, max_events):
                # Send each result as Server-Sent Event
                yield f"data: {json.dumps(result)}\n\n"
        except Exception as e:
            # Send error as SSE
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/api/web-search")
async def web_search_security_events(
    query: str = Form(...),
    max_events: int = Form(default=5),
    add_to_database: bool = Form(default=True)
):
    """Search the web for security events based on user query and optionally add them to the database"""
    try:
        # Perform web search
        search_results = await web_search_agent.search_web_for_security_events(query, max_events)
        
        if not search_results["success"]:
            return JSONResponse(content=search_results, status_code=400)
        
        # Optionally add events to the existing database
        integration_result = None
        if add_to_database and search_results["events"]:
            integration_result = await web_search_agent.integrate_events_with_existing(
                search_results["events"]
            )
        
        response = {
            "search_results": search_results,
            "integration_result": integration_result,
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/web-search-preview")
async def web_search_preview(query: str = Form(...), max_events: int = Form(default=3)):
    """Preview web search results without adding them to the database"""
    try:
        # Perform web search but don't integrate with existing data
        search_results = await web_search_agent.search_web_for_security_events(query, max_events)
        
        return JSONResponse(content={
            "preview": search_results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integrate-search-events")
async def integrate_search_events(events: List[Dict[str, Any]]):
    """Integrate specific events from web search into the main database"""
    try:
        integration_result = await web_search_agent.integrate_events_with_existing(events)
        
        return JSONResponse(content={
            "integration_result": integration_result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deploy-search-agents")
async def deploy_search_agents(request: Dict[str, Any]):
    """Deploy continuous search agents for the given search terms"""
    try:
        search_terms = request.get("search_terms", [])
        if not search_terms:
            raise HTTPException(status_code=400, detail="No search terms provided")
        
        result = search_agent_manager.deploy_agents(search_terms)
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop-search-agents")
async def stop_search_agents():
    """Stop all active search agents"""
    try:
        result = search_agent_manager.stop_all_agents()
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop-single-agent")
async def stop_single_agent(request: Dict[str, Any]):
    """Stop a single search agent"""
    try:
        search_term = request.get("search_term")
        if not search_term:
            raise HTTPException(status_code=400, detail="No search term provided")
        
        result = search_agent_manager.stop_single_agent(search_term)
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent-status")
async def get_agent_status():
    """Get status of all active search agents"""
    try:
        result = search_agent_manager.get_agent_status()
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "openai": "connected",
            "web_search": "available",
            "data": "loaded"
        }
    })

if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("static", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("services", exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 