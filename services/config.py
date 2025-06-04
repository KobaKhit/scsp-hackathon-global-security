import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for managing environment variables"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def validate(cls):
        """Validate that required environment variables are set"""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please create a .env file in the root directory with your OpenAI API key."
            )
    
    @classmethod
    def get_openai_api_key(cls):
        """Get OpenAI API key with validation"""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file."
            )
        return cls.OPENAI_API_KEY

# Initialize and validate configuration when module is imported
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Warning: {e}")
    print("Please create a .env file with the following format:")
    print("OPENAI_API_KEY=your_openai_api_key_here") 