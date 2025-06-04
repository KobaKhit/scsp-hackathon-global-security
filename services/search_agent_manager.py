import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
import threading
import time
from pathlib import Path

from services.web_search_agent import WebSearchAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAgentManager:
    def __init__(self):
        self.active_agents: Dict[str, dict] = {}
        self.agent_threads: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, threading.Event] = {}
        self.web_search_agent = WebSearchAgent()
        self.data_file = Path("data/mock_events.json")
        self.last_event_counts: Dict[str, int] = {}
        
    def deploy_agents(self, search_terms: List[str]) -> dict:
        """Deploy search agents for the given terms"""
        try:
            deployed_count = 0
            
            for term in search_terms:
                if term not in self.active_agents:
                    # Create stop flag for this agent
                    stop_flag = threading.Event()
                    self.stop_flags[term] = stop_flag
                    
                    # Create and start agent thread
                    agent_thread = threading.Thread(
                        target=self._run_agent,
                        args=(term, stop_flag),
                        daemon=True
                    )
                    
                    # Store agent info
                    self.active_agents[term] = {
                        'term': term,
                        'status': 'active',
                        'events_found': 0,
                        'deployed_at': datetime.now().isoformat(),
                        'last_search': None
                    }
                    
                    self.agent_threads[term] = agent_thread
                    self.last_event_counts[term] = 0
                    
                    # Start the agent
                    agent_thread.start()
                    deployed_count += 1
                    
                    logger.info(f"Deployed search agent for term: {term}")
            
            return {
                'success': True,
                'deployed_count': deployed_count,
                'total_active': len(self.active_agents)
            }
            
        except Exception as e:
            logger.error(f"Error deploying agents: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_all_agents(self) -> dict:
        """Stop all active search agents"""
        try:
            stopped_count = 0
            
            # Set stop flags for all agents
            for term in list(self.active_agents.keys()):
                if term in self.stop_flags:
                    self.stop_flags[term].set()
                stopped_count += 1
            
            # Wait a moment for threads to stop gracefully
            time.sleep(1)
            
            # Clear all agent data
            self.active_agents.clear()
            self.agent_threads.clear()
            self.stop_flags.clear()
            self.last_event_counts.clear()
            
            logger.info(f"Stopped {stopped_count} search agents")
            
            return {
                'success': True,
                'stopped_count': stopped_count
            }
            
        except Exception as e:
            logger.error(f"Error stopping agents: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_single_agent(self, search_term: str) -> dict:
        """Stop a single search agent"""
        try:
            if search_term not in self.active_agents:
                return {
                    'success': False,
                    'error': f'Agent for term "{search_term}" not found'
                }
            
            # Set stop flag
            if search_term in self.stop_flags:
                self.stop_flags[search_term].set()
            
            # Remove from tracking
            self.active_agents.pop(search_term, None)
            self.agent_threads.pop(search_term, None)
            self.stop_flags.pop(search_term, None)
            self.last_event_counts.pop(search_term, None)
            
            logger.info(f"Stopped search agent for term: {search_term}")
            
            return {
                'success': True,
                'remaining_agents': len(self.active_agents)
            }
            
        except Exception as e:
            logger.error(f"Error stopping single agent: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_agent_status(self) -> dict:
        """Get status of all active agents"""
        try:
            agents_status = []
            new_events_total = 0
            
            for term, agent_info in self.active_agents.items():
                # Count current events for this term
                current_count = self._count_events_for_term(term)
                previous_count = self.last_event_counts.get(term, 0)
                new_events = max(0, current_count - previous_count)
                new_events_total += new_events
                
                # Update the stored count
                self.last_event_counts[term] = current_count
                agent_info['events_found'] = current_count
                
                agents_status.append({
                    'term': term,
                    'status': agent_info['status'],
                    'events_found': current_count,
                    'deployed_at': agent_info['deployed_at'],
                    'last_search': agent_info['last_search']
                })
            
            return {
                'success': True,
                'agents': agents_status,
                'total_active': len(self.active_agents),
                'new_events_count': new_events_total
            }
            
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _run_agent(self, search_term: str, stop_flag: threading.Event):
        """Run a single search agent continuously"""
        logger.info(f"Starting search agent for term: {search_term}")
        
        # Initial delay to prevent immediate overwhelming
        time.sleep(5)
        
        while not stop_flag.is_set():
            try:
                # Update last search time
                if search_term in self.active_agents:
                    self.active_agents[search_term]['last_search'] = datetime.now().isoformat()
                
                # Perform web search
                logger.info(f"Agent searching for: {search_term}")
                
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    search_result = loop.run_until_complete(
                        self.web_search_agent.search_web_for_security_events(
                            query=search_term,
                            max_events=3  # Smaller batches for continuous monitoring
                        )
                    )
                    
                    if search_result.get('success') and search_result.get('events'):
                        events = search_result['events']
                        
                        # Integrate new events into database
                        integration_result = loop.run_until_complete(
                            self.web_search_agent.integrate_events_with_existing(events)
                        )
                        
                        if integration_result.get('added_count', 0) > 0:
                            logger.info(f"Agent '{search_term}' found {integration_result['added_count']} new events")
                            
                            # Update agent statistics
                            if search_term in self.active_agents:
                                current_count = self._count_events_for_term(search_term)
                                self.active_agents[search_term]['events_found'] = current_count
                    
                except Exception as search_error:
                    logger.error(f"Search error for agent '{search_term}': {search_error}")
                finally:
                    loop.close()
                
                # Wait before next search (5 minutes)
                for _ in range(300):  # 300 seconds = 5 minutes
                    if stop_flag.is_set():
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in agent '{search_term}': {e}")
                # Wait a bit before retrying on error
                for _ in range(30):  # 30 seconds
                    if stop_flag.is_set():
                        break
                    time.sleep(1)
        
        logger.info(f"Search agent for term '{search_term}' stopped")
    
    def _count_events_for_term(self, search_term: str) -> int:
        """Count events that match the search term"""
        try:
            if not self.data_file.exists():
                return 0
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            events = data.get('events', [])
            count = 0
            
            # Count events that contain the search term in title or description
            search_lower = search_term.lower()
            for event in events:
                title = event.get('title', '').lower()
                description = event.get('description', '').lower()
                location = event.get('location', '').lower()
                
                if (search_lower in title or 
                    search_lower in description or 
                    search_lower in location):
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting events for term '{search_term}': {e}")
            return 0

# Global instance
search_agent_manager = SearchAgentManager() 