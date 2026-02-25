"""
Lichess API Client for fetching chess games and user data
"""

import berserk
import chess.pgn
import io
from typing import Iterator, Dict, Any, List, Optional
from datetime import datetime, timedelta

class LichessClient:
    """Client for interacting with Lichess API"""
    
    def __init__(self, api_token: str):
        """
        Initialize Lichess client
        
        Args:
            api_token: Your Lichess API token
        """
        self.session = berserk.TokenSession(api_token)
        self.client = berserk.Client(session=self.session)
    
    def get_user_profile(self, username: str) -> Dict:
        """Get user profile information"""
        try:
            return self.client.users.get_public_data(username)
        except Exception as e:
            raise Exception(f"Failed to fetch user profile: {e}")
    
    def get_user_rating_history(self, username: str) -> List[Dict]:
        """Get user's rating history"""
        try:
            return self.client.users.get_rating_history(username)
        except Exception as e:
            raise Exception(f"Failed to fetch rating history: {e}")
    
    def get_games_by_username(self, username: str, 
                            max_games: int = 50,
                            time_control: Optional[str] = None,
                            rated: Optional[bool] = None,
                            opening: Optional[str] = None,
                            days_back: Optional[int] = None) -> Iterator[Dict]:
        """
        Get games by username with various filters
        
        Args:
            username: Lichess username
            max_games: Maximum number of games to fetch
            time_control: Filter by time control (e.g., 'blitz', 'rapid', 'classical')
            rated: Filter by rated/unrated games
            opening: Filter by opening name
            days_back: Only get games from last N days
            
        Returns:
            Iterator of game dictionaries
        """
        try:
            since_ts = self._get_timestamp(days_back) if days_back else None

            perf_type = None
            if time_control:
                perf_type = time_control

            games = self.client.games.export_by_player(
                username=username,
                max=max_games,
                since=since_ts,
                rated=rated,
                perf_type=perf_type,
                pgn_in_json=True,
                opening=True,
                clocks=True,
                evals=False,
            )

            if opening:
                opening_lower = opening.lower()

                def _opening_filter(it: Iterator[Dict]) -> Iterator[Dict]:
                    for g in it:
                        og = (g.get('opening') or {}).get('name')
                        if og and opening_lower in og.lower():
                            yield g

                return _opening_filter(games)

            return games
            
        except Exception as e:
            print(f"Error getting user data: {e}")
            return None
    
    def get_studies_by_username(self, username: str) -> Iterator[Dict[str, Any]]:
        """
        Get studies by username (studies the user contributes to)
        
        Args:
            username: Lichess username
            
        Returns:
            Iterator of study dictionaries
        """
        try:
            # Using berserk's studies export_by_username endpoint
            studies = self.client.studies.export_by_username(username)
            return studies
        except Exception as e:
            print(f"Error getting studies for {username}: {e}")
            return []
    
    def get_study_chapters(self, study_id: str) -> Iterator[Dict[str, Any]]:
        """
        Get chapters in a study
        
        Args:
            study_id: Study ID
            
        Returns:
            Iterator of chapter dictionaries
        """
        try:
            # For studies, chapters are part of the study export data
            # We'll need to parse from the study data itself
            study_data = self.client.studies.export(study_id)
            chapters = study_data.get('chapters', [])
            return chapters
        except Exception as e:
            print(f"Error getting chapters for study {study_id}: {e}")
            return []
    
    def get_study_by_id(self, study_id: str) -> Dict[str, Any]:
        """
        Get a specific study by ID
        
        Args:
            study_id: Study ID
            
        Returns:
            Study data dictionary
        """
        try:
            # The export method returns a generator of PGN strings
            # We need to parse the first PGN to get study info
            pgn_iterator = self.client.studies.export(study_id)
            pgn_list = list(pgn_iterator)
            
            if not pgn_list:
                return {}
            
            # Parse the first PGN to extract study metadata
            import io
            first_game = chess.pgn.read_game(io.StringIO(pgn_list[0]))
            
            study_info = {
                'id': study_id,
                'name': first_game.headers.get('Study', first_game.headers.get('Event', 'Unknown Study')),
                'chapters': []
            }
            
            # Create chapter entries for each PGN
            for i, pgn_text in enumerate(pgn_list):
                game = chess.pgn.read_game(io.StringIO(pgn_text))
                if game:
                    chapter = {
                        'id': f'chapter_{i+1}',
                        'name': game.headers.get('Round', f'Chapter {i+1}'),
                        'pgn': pgn_text,
                        'createdAt': game.headers.get('Date', ''),
                        'orientation': game.headers.get('Orientation', 'white')
                    }
                    study_info['chapters'].append(chapter)
            
            return study_info
            
        except Exception as e:
            print(f"Error getting study {study_id}: {e}")
            return {}
    
    def get_study_chapter(self, study_id: str, chapter_id: str) -> Dict[str, Any]:
        """
        Get a specific study chapter
        
        Args:
            study_id: Study ID
            chapter_id: Chapter ID
            
        Returns:
            Chapter data dictionary
        """
        try:
            chapter = self.client.studies.export_chapter(study_id, chapter_id)
            return chapter
        except Exception as e:
            print(f"Error getting chapter {chapter_id} from study {study_id}: {e}")
            return {}
    
    def get_game_by_id(self, game_id: str) -> Dict:
        """Get a specific game by ID"""
        try:
            return self.client.games.export(game_id)
        except Exception as e:
            raise Exception(f"Failed to fetch game {game_id}: {e}")
    
    def parse_pgn_game(self, pgn_text: str) -> chess.pgn.Game:
        """Parse PGN text into chess.pgn.Game object"""
        return chess.pgn.read_game(io.StringIO(pgn_text))
    
    def _get_timestamp(self, days_back: int) -> int:
        """Convert days back to timestamp"""
        date = datetime.now() - timedelta(days=days_back)
        return int(date.timestamp() * 1000)
    
    def get_user_stats(self, username: str) -> Dict:
        """Get user performance statistics"""
        try:
            return self.client.users.get_performance(username, 'blitz')  # Can change to other time controls
        except Exception as e:
            raise Exception(f"Failed to fetch user stats: {e}")


class GameFilter:
    """Helper class for filtering games"""
    
    @staticmethod
    def filter_by_time_control(games: Iterator[Dict], time_control: str) -> List[Dict]:
        """Filter games by time control"""
        return [game for game in games if game.get('perf') == time_control]
    
    @staticmethod
    def filter_by_result(games: Iterator[Dict], result: str) -> List[Dict]:
        """Filter games by result (win/loss/draw)"""
        return [game for game in games if game.get('result') == result]
    
    @staticmethod
    def filter_by_date_range(games: Iterator[Dict], 
                           start_date: datetime, 
                           end_date: datetime) -> List[Dict]:
        """Filter games by date range"""
        filtered = []
        for game in games:
            if 'createdAt' in game:
                game_date = datetime.fromtimestamp(game['createdAt'] / 1000)
                if start_date <= game_date <= end_date:
                    filtered.append(game)
        return filtered
    
    @staticmethod
    def get_recent_games(games: Iterator[Dict], days: int = 30) -> List[Dict]:
        """Get games from last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return GameFilter.filter_by_date_range(games, cutoff_date, datetime.now())
