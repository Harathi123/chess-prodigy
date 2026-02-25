"""Study game analyzer for Lichess studies"""

import chess
import chess.pgn
from datetime import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional

from lichess_client import LichessClient
from chess_analyzer import ChessAnalyzer
from analysis_cache import AnalysisCache


class StudyAnalyzer:
    """Analyzer for games from Lichess studies"""
    
    def __init__(self, lichess_client: LichessClient, chess_analyzer: ChessAnalyzer, no_analysis: bool = False, sample_size: Optional[int] = None):
        """
        Initialize study analyzer
        
        Args:
            lichess_client: Lichess API client
            chess_analyzer: Chess analysis engine
            no_analysis: If True, skip per-game engine analysis for faster reports
            sample_size: If set, analyze only this many representative games
        """
        self.lichess_client = lichess_client
        self.analyzer = chess_analyzer
        self.no_analysis = no_analysis
        self.sample_size = sample_size
        self.study_games = []
        self.study_metadata = []
        self.cache = AnalysisCache()
        self.analysis_depth = getattr(chess_analyzer, 'depth', 10)
        self.analysis_time = getattr(chess_analyzer, 'time_limit', 1.0)
    
    def fetch_study_games(self, username: str, study_name: Optional[str] = None, max_studies: int = 3, study_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch games from studies the user contributes to
        
        Args:
            username: Lichess username
            study_name: Specific study name to analyze (optional)
            max_studies: Maximum number of studies to analyze
            study_id: Specific study ID to analyze (optional)
            
        Returns:
            List of games from studies
        """
        print(f"Fetching study games for {username}...")
        
        try:
            # If study_id is provided, fetch that specific study
            if study_id:
                print(f"Fetching specific study ID: {study_id}")
                study_data = self.lichess_client.get_study_by_id(study_id)
                
                if not study_data:
                    print(f"Could not fetch study {study_id}")
                    return []
                
                print(f"Study name: {study_data.get('name', 'Unknown')}")
                chapters = study_data.get('chapters', [])
                print(f"Found {len(chapters)} chapters")
                
                all_games = []
                for chapter in chapters:
                    chapter_id = chapter.get('id')
                    chapter_name = chapter.get('name', 'Unknown Chapter')
                    
                    if chapter.get('pgn'):
                        game_data = {
                            'id': f"{study_id}_{chapter_id}",
                            'study_id': study_id,
                            'study_name': study_data.get('name', 'Unknown'),
                            'chapter_id': chapter_id,
                            'chapter_name': chapter_name,
                            'pgn': chapter['pgn'],
                            'createdAt': chapter.get('createdAt', ''),
                            'orientation': chapter.get('orientation', 'white'),
                            'is_study': True
                        }
                        all_games.append(game_data)
                
                print(f"Found {len(all_games)} games in study")
                self.study_games = all_games
                self.study_metadata = [study_data]
                return all_games
            
            # Original logic for fetching by username
            pgn_iterator = self.lichess_client.get_studies_by_username(username)
            
            all_games = []
            study_chapter_count = 0
            
            for i, pgn_text in enumerate(pgn_iterator):
                if max_studies and study_chapter_count >= max_studies * 10:  # Rough limit
                    print(f"  Reached limit of ~{max_studies} studies")
                    break
                
                if not pgn_text.strip():
                    continue
                
                # Parse the PGN to extract game data
                try:
                    import io
                    game = chess.pgn.read_game(io.StringIO(pgn_text))
                    if game:
                        # Extract study info from PGN headers if available
                        study_name_from_pgn = game.headers.get('Study', game.headers.get('Event', f'Study Chapter {i+1}'))
                        
                        game_data = {
                            'id': f"study_chapter_{i+1}",
                            'study_id': f"study_{i+1}",
                            'study_name': study_name_from_pgn,
                            'chapter_id': f"chapter_{i+1}",
                            'chapter_name': game.headers.get('Round', f'Chapter {i+1}'),
                            'pgn': pgn_text,
                            'createdAt': game.headers.get('Date', ''),
                            'orientation': game.headers.get('Orientation', 'white'),
                            'is_study': True
                        }
                        all_games.append(game_data)
                        study_chapter_count += 1
                        
                        if study_chapter_count % 10 == 0:
                            print(f"  Processed {study_chapter_count} chapters...")
                
                except Exception as e:
                    print(f"  Error parsing PGN chapter {i+1}: {e}")
                    continue
            
            print(f"Found {len(all_games)} games across studies")
            self.study_games = all_games
            self.study_metadata = [{'name': f'Study Collection', 'chapters': len(all_games)}]
            return all_games
            
        except Exception as e:
            if "404" in str(e):
                print(f"No accessible studies found for {username}")
                print("This could mean:")
                print("- You haven't created or contributed to any studies yet")
                print("- Your studies are private and not accessible via this API endpoint")
                print("- The studies are unlisted")
                print("\nTo use study analysis:")
                print("1. Create a study on Lichess: https://lichess.org/study/new")
                print("2. Add some games/positions to the study")
                print("3. Make sure the study is public or try again after a few minutes")
                print("4. Run this command again")
                print(f"\nOr use a specific study ID: --study-id YOUR_STUDY_ID")
            else:
                print(f"Error fetching study games: {e}")
            return []
    
    def analyze_opponent_patterns(self, username: str) -> Dict:
        """
        Analyze patterns against specific opponents in study games
        
        Args:
            username: Your username
            
        Returns:
            Dictionary with opponent-specific statistics
        """
        print("Analyzing opponent patterns in study games...")
        
        opponent_analysis = {
            'overall_record': defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0}),
            'common_openings': defaultdict(list),
            'time_control_performance': defaultdict(lambda: defaultdict(list)),
            'recent_results': defaultdict(list),
            'blunder_patterns': defaultdict(list),
            'study_contributions': defaultdict(list)  # Track which studies contributed
        }
        
        total_games = len(self.study_games)
        
        # Apply sampling if requested
        games_to_analyze = self.study_games
        if self.sample_size and self.sample_size < total_games:
            # Sample representative games (spread throughout the collection)
            step = total_games // self.sample_size
            games_to_analyze = [self.study_games[i] for i in range(0, total_games, step)][:self.sample_size]
            print(f"  Sampling {len(games_to_analyze)} representative games out of {total_games}")
        
        for i, game_data in enumerate(games_to_analyze):
            if not self.no_analysis and i % 5 == 0:
                print(f"  Progress: {i+1}/{len(games_to_analyze)} games analyzed...")
            
            try:
                # Parse game
                pgn_text = game_data.get('pgn', '')
                if not pgn_text:
                    continue
                
                game = self.lichess_client.parse_pgn_game(pgn_text)
                
                # Identify opponent
                white = game.headers.get('White', '')
                black = game.headers.get('Black', '')
                result = game.headers.get('Result', '')
                time_control = game.headers.get('TimeControl', '')
                opening = game.headers.get('Opening', '')
                study_name = game_data.get('study_name', 'Unknown Study')
                
                # Determine opponent and result
                if white.lower() == username.lower():
                    opponent = black
                    player_color = 'white'
                elif black.lower() == username.lower():
                    opponent = white
                    player_color = 'black'
                else:
                    # If user not found as a player, skip opponent analysis
                    continue
                
                # Update head-to-head record
                if result == '1-0':
                    if player_color == 'white':
                        opponent_analysis['overall_record'][opponent]['wins'] += 1
                    else:
                        opponent_analysis['overall_record'][opponent]['losses'] += 1
                elif result == '0-1':
                    if player_color == 'black':
                        opponent_analysis['overall_record'][opponent]['wins'] += 1
                    else:
                        opponent_analysis['overall_record'][opponent]['losses'] += 1
                elif result == '1/2-1/2':
                    opponent_analysis['overall_record'][opponent]['draws'] += 1
                
                # Track openings
                opponent_analysis['common_openings'][opponent].append(opening)
                
                # Track time control performance
                opponent_analysis['time_control_performance'][opponent][time_control].append(result)
                
                # Track which study this came from
                opponent_analysis['study_contributions'][opponent].append(study_name)
                
                # Analyze game for blunders (skip if no_analysis)
                if not self.no_analysis:
                    # Check cache first
                    cached_analysis = self.cache.get_cached_analysis(pgn_text, self.analysis_depth, self.analysis_time)
                    if cached_analysis:
                        game_analysis = cached_analysis
                    else:
                        game_analysis = self.analyzer.analyze_game(game)
                        # Cache the results
                        self.cache.cache_analysis(pgn_text, game_analysis, self.analysis_depth, self.analysis_time)
                    
                    # Find blunders against this opponent
                    for mistake in game_analysis['mistakes']:
                        if mistake['type'] == 'blunder':
                            blunder_info = {
                                'move_number': mistake['move_number'],
                                'move': mistake['move'],
                                'eval_change': mistake['eval_change'],
                                'fen': mistake['fen'],
                                'date': game_data.get('createdAt', ''),
                                'opening': opening,
                                'study': study_name,
                                'chapter': game_data.get('chapter_name', 'Unknown')
                            }
                            opponent_analysis['blunder_patterns'][opponent].append(blunder_info)
                
            except Exception as e:
                print(f"Error analyzing study game: {e}")
                continue
        
        return opponent_analysis
    
    def find_common_blunders(self, min_occurrences: int = 3) -> Dict:
        """
        Find common blunders across all study games
        
        Args:
            min_occurrences: Minimum occurrences to consider a pattern
            
        Returns:
            Dictionary with common blunder patterns
        """
        if self.no_analysis:
            print("Skipping blunder analysis (fast mode)")
            return {'position_patterns': {}, 'move_patterns': {}, 'opening_blunders': {}}
        
        print("Finding common blunders in study games...")
        
        position_patterns = defaultdict(list)
        move_patterns = defaultdict(list)
        opening_blunders = defaultdict(list)
        
        total_games = len(self.study_games)
        
        # Apply sampling if requested
        games_to_analyze = self.study_games
        if self.sample_size and self.sample_size < total_games:
            step = total_games // self.sample_size
            games_to_analyze = [self.study_games[i] for i in range(0, total_games, step)][:self.sample_size]
            print(f"  Sampling {len(games_to_analyze)} representative games out of {total_games}")
        
        for i, game_data in enumerate(games_to_analyze):
            if i % 5 == 0:
                print(f"  Progress: {i+1}/{len(games_to_analyze)} games analyzed for blunders...")
            
            try:
                pgn_text = game_data.get('pgn', '')
                if not pgn_text:
                    continue
                
                game = self.lichess_client.parse_pgn_game(pgn_text)
                
                # Check cache first
                cached_analysis = self.cache.get_cached_analysis(pgn_text, self.analysis_depth, self.analysis_time)
                if cached_analysis:
                    game_analysis = cached_analysis
                else:
                    game_analysis = self.analyzer.analyze_game(game)
                    # Cache the results
                    self.cache.cache_analysis(pgn_text, game_analysis, self.analysis_depth, self.analysis_time)
                
                opening = game.headers.get('Opening', '')
                study_name = game_data.get('study_name', 'Unknown')
                
                for mistake in game_analysis['mistakes']:
                    if mistake['type'] == 'blunder':
                        # Position-based patterns (first 3-4 moves)
                        board = chess.Board()
                        moves_played = []
                        
                        # Reconstruct position up to blunder
                        for i, move in enumerate(game.mainline_moves()):
                            if i >= mistake['move_number'] - 1:
                                break
                            board.push(move)
                            moves_played.append(move.uci())
                        
                        # Create position pattern (first 6 plies)
                        position_pattern = ' '.join(moves_played[:6])
                        position_patterns[position_pattern].append({
                            'blunder_move': mistake['move'],
                            'eval_change': mistake['eval_change'],
                            'game_id': game_data.get('id', ''),
                            'opening': opening,
                            'study': study_name,
                            'chapter': game_data.get('chapter_name', 'Unknown')
                        })
                        
                        # Move-based patterns
                        move_patterns[mistake['move']].append({
                            'position': position_pattern,
                            'eval_change': mistake['eval_change'],
                            'opening': opening,
                            'study': study_name
                        })
                        
                        # Opening-specific blunders
                        if opening:
                            opening_blunders[opening].append({
                                'move_number': mistake['move_number'],
                                'blunder_move': mistake['move'],
                                'eval_change': mistake['eval_change'],
                                'study': study_name
                            })
            
            except Exception as e:
                print(f"Error analyzing blunders in study game: {e}")
                continue
        
        # Filter by minimum occurrences
        common_positions = {k: v for k, v in position_patterns.items() 
                          if len(v) >= min_occurrences}
        common_moves = {k: v for k, v in move_patterns.items() 
                       if len(v) >= min_occurrences}
        common_opening_blunders = {k: v for k, v in opening_blunders.items() 
                                 if len(v) >= min_occurrences}
        
        return {
            'position_patterns': common_positions,
            'move_patterns': common_moves,
            'opening_blunders': common_opening_blunders
        }
    
    def generate_study_report(self, username: str, no_analysis: bool = False) -> str:
        """Generate comprehensive study analysis report"""
        report = []
        report.append("=" * 60)
        report.append(f"STUDY ANALYSIS REPORT FOR {username.upper()}")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Study Games Analyzed: {len(self.study_games)}")
        if no_analysis:
            report.append("Mode: Fast counts-only (no engine analysis)")
        report.append("")
        
        if not self.study_games:
            report.append("No study games found for analysis.")
            return "\n".join(report)
        
        # List studies analyzed
        if self.study_metadata:
            report.append("STUDIES ANALYZED:")
            for study in self.study_metadata:
                report.append(f"- {study.get('name', 'Unknown')}: {study.get('chapters', 0)} chapters")
            report.append("")
        
        # Overall performance in study games
        wins = sum(1 for g in self.study_games if self._get_game_result(g, username) == 'win')
        losses = sum(1 for g in self.study_games if self._get_game_result(g, username) == 'loss')
        draws = sum(1 for g in self.study_games if self._get_game_result(g, username) == 'draw')
        
        report.append("OVERALL STUDY PERFORMANCE:")
        report.append(f"Total Games: {len(self.study_games)}")
        report.append(f"Wins: {wins}")
        report.append(f"Losses: {losses}")
        report.append(f"Draws: {draws}")
        if len(self.study_games) > 0:
            report.append(f"Win Rate: {(wins/len(self.study_games)*100):.1f}%")
        report.append("")
        
        # Common blunders (only if analysis enabled)
        if not no_analysis:
            common_blunders = self.find_common_blunders()
            if common_blunders['move_patterns']:
                report.append("COMMON BLUNDER MOVES:")
                for move, occurrences in list(common_blunders['move_patterns'].items())[:5]:
                    avg_loss = sum(o['eval_change'] for o in occurrences) / len(occurrences)
                    report.append(f"- {move}: {len(occurrences)} occurrences, avg {avg_loss:.1f} cp loss")
                report.append("")
        
        # Opponent analysis
        opponent_patterns = self.analyze_opponent_patterns(username)
        if opponent_patterns['overall_record']:
            report.append("HEAD-TO-HEAD RECORDS:")
            # Show opponents with most games
            opponent_counts = {}
            for opponent, record in opponent_patterns['overall_record'].items():
                total = record['wins'] + record['losses'] + record['draws']
                opponent_counts[opponent] = total
            
            top_opponents = sorted(opponent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for opponent, total_games in top_opponents:
                record = opponent_patterns['overall_record'][opponent]
                win_rate = (record['wins'] / total_games) * 100 if total_games > 0 else 0
                report.append(f"- {opponent}: {record['wins']}-{record['losses']}-{record['draws']} ({win_rate:.1f}% win rate)")
                
                # Show which studies these games came from
                if opponent in opponent_patterns['study_contributions']:
                    studies = list(set(opponent_patterns['study_contributions'][opponent]))
                    report.append(f"  Studies: {', '.join(studies[:3])}")
            report.append("")
        
        # Recommendations
        report.append("STUDY RECOMMENDATIONS:")
        if wins < losses and len(self.study_games) > 0:
            report.append("- Focus on improving performance in study positions")
        if not no_analysis:
            report.append("- Study common blunder patterns to avoid repeating mistakes")
        report.append("- Review games against opponents you struggle against")
        report.append("- Use study chapters for targeted opening practice")
        if no_analysis:
            report.append("- Run without --no-analysis for detailed blunder and accuracy insights")
        
        return "\n".join(report)
    
    def _get_game_result(self, game_data: Dict, username: str) -> str:
        """Get the result of a game for the specified user"""
        # For study games, we need to parse the PGN to get player names
        try:
            pgn_text = game_data.get('pgn', '')
            if not pgn_text:
                return 'unknown'
            
            import io
            game = chess.pgn.read_game(io.StringIO(pgn_text))
            if not game:
                return 'unknown'
            
            white = game.headers.get('White', '')
            black = game.headers.get('Black', '')
            result = game.headers.get('Result', '')
            
            user_white = white.lower() == username.lower()
            user_black = black.lower() == username.lower()
            
            if result == '1-0' and user_white:
                return 'win'
            elif result == '0-1' and user_black:
                return 'win'
            elif result == '1/2-1/2':
                return 'draw'
            elif (result == '1-0' and user_black) or (result == '0-1' and user_white):
                return 'loss'
            
        except Exception:
            pass
        
        return 'unknown'
