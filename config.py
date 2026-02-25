"""
Configuration management for chess analysis system
"""

import os
from dotenv import load_dotenv
from typing import Optional


class Config:
    """Configuration class for chess analysis system"""
    
    def __init__(self, env_file: str = '.env'):
        """
        Initialize configuration
        
        Args:
            env_file: Path to environment file
        """
        load_dotenv(env_file, override=True)
        
        # Lichess API settings
        self.LICHESS_API_TOKEN = os.getenv('LICHESS_API_TOKEN')
        self.USERNAME = os.getenv('USERNAME')
        
        # Stockfish settings
        self.STOCKFISH_PATH = os.getenv('STOCKFISH_PATH')
        self.ANALYSIS_DEPTH = int(os.getenv('ANALYSIS_DEPTH', '15'))
        self.ANALYSIS_TIME = float(os.getenv('ANALYSIS_TIME', '2.0'))
        
        # Default settings
        self.DEFAULT_NUM_GAMES = int(os.getenv('DEFAULT_NUM_GAMES', '10'))
        self.DEFAULT_TIME_CONTROL = os.getenv('DEFAULT_TIME_CONTROL')
        self.DEFAULT_DAYS_BACK = int(os.getenv('DEFAULT_DAYS_BACK', '30'))
        
        # Output settings
        self.OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'analysis_results')
        self.SAVE_ANALYSIS = os.getenv('SAVE_ANALYSIS', 'true').lower() == 'true'
        self.CREATE_VISUALIZATIONS = os.getenv('CREATE_VISUALIZATIONS', 'true').lower() == 'true'
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.LICHESS_API_TOKEN:
            print("Error: LICHESS_API_TOKEN is required")
            return False
        
        if not self.USERNAME:
            print("Error: USERNAME is required")
            return False
        
        return True
    
    def get_stockfish_path(self) -> Optional[str]:
        """Get Stockfish path, return None if not specified"""
        return self.STOCKFISH_PATH if self.STOCKFISH_PATH else None
