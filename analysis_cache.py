"""Analysis caching system for faster re-runs"""

import os
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path


class AnalysisCache:
    """Cache system for chess analysis results"""
    
    def __init__(self, cache_dir: str = ".analysis_cache"):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory to store cached analysis
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, pgn_text: str, analysis_depth: int, analysis_time: float) -> str:
        """Generate cache key for a game"""
        # Create hash based on PGN and analysis settings
        content = f"{pgn_text}_{analysis_depth}_{analysis_time}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_analysis(self, pgn_text: str, analysis_depth: int, analysis_time: float) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis for a game
        
        Args:
            pgn_text: PGN text of the game
            analysis_depth: Analysis depth used
            analysis_time: Analysis time used
            
        Returns:
            Cached analysis or None if not found
        """
        cache_key = self._get_cache_key(pgn_text, analysis_depth, analysis_time)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                # Cache corrupted, delete it
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def cache_analysis(self, pgn_text: str, analysis: Dict[str, Any], analysis_depth: int, analysis_time: float) -> None:
        """
        Cache analysis results for a game
        
        Args:
            pgn_text: PGN text of the game
            analysis: Analysis results to cache
            analysis_depth: Analysis depth used
            analysis_time: Analysis time used
        """
        cache_key = self._get_cache_key(pgn_text, analysis_depth, analysis_time)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(analysis, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to cache analysis: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached analysis"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)
        print("Analysis cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "cache_files": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir)
        }
