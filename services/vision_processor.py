import os
import base64
from openai import AsyncOpenAI
from typing import Dict, Any
from .config import Config

class VisionProcessor:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=Config.get_openai_api_key()
        )
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for OpenAI API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    async def analyze_image(self, image_path: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze image using GPT-4 Vision"""
        try:
            base64_image = self.encode_image(image_path)
            
            # Create analysis prompt based on type
            prompts = {
                "satellite": """Analyze this satellite image for security-relevant features:
                - Infrastructure (ports, airports, military facilities)
                - Unusual activity or changes
                - Supply chain indicators (shipping, warehouses)
                - Environmental factors affecting security
                - Population or migration patterns
                Provide specific, actionable intelligence.""",
                
                "maritime": """Analyze this maritime image for:
                - Ship movements and types
                - Port congestion or unusual activity  
                - AIS gaps or suspicious vessel behavior
                - Supply chain bottlenecks
                - Environmental hazards to shipping
                Focus on security and economic implications.""",
                
                "infrastructure": """Examine this infrastructure image for:
                - Critical facility status and condition
                - Security vulnerabilities
                - Operational capacity indicators
                - Damage assessment
                - Strategic importance
                Provide security-focused analysis.""",
                
                "general": """Analyze this image for security-relevant information including:
                - Key infrastructure or strategic assets
                - Unusual activities or changes
                - Potential threats or vulnerabilities
                - Economic or supply chain implications
                Provide actionable intelligence insights."""
            }
            
            prompt = prompts.get(analysis_type, prompts["general"])
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=600
            )
            
            return {
                "analysis": response.choices[0].message.content,
                "analysis_type": analysis_type,
                "confidence": "high"  # You could implement confidence scoring
            }
            
        except Exception as e:
            return {
                "analysis": f"Error analyzing image: {str(e)}",
                "analysis_type": analysis_type,
                "confidence": "error"
            }

# Global instance
vision_processor = VisionProcessor()

async def process_satellite_image(image_path: str, analysis_type: str = "general") -> Dict[str, Any]:
    """Process satellite or security-relevant images"""
    return await vision_processor.analyze_image(image_path, analysis_type) 