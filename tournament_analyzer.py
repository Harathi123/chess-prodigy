"""
Tournament Game Analyzer - Focus on specific opponent analysis and common blunders
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import chess
import chess.pgn
from datetime import datetime

from lichess_client import LichessClient
from chess_analyzer import ChessAnalyzer


class TournamentAnalyzer:
    """Specialized analyzer for tournament games and opponent-specific patterns"""
    
    def __init__(self, lichess_client: LichessClient, chess_analyzer: ChessAnalyzer, no_analysis: bool = False):
        """
        Initialize tournament analyzer
        
        Args:
            lichess_client: Lichess API client
            chess_analyzer: Chess analysis engine
            no_analysis: If True, skip per-game engine analysis for faster reports
        """
        self.lichess_client = lichess_client
        self.analyzer = chess_analyzer
        self.no_analysis = no_analysis
        self.tournament_games = []
        self.opponent_stats = defaultdict(dict)
        self.common_blunders = defaultdict(list)
        self.opening_patterns = defaultdict(list)
    
    def fetch_tournament_games(self, username: str, 
                              max_games: int = 100,
                              tournament_only: bool = True) -> List[Dict]:
        """
        Fetch tournament games for analysis
        
        Args:
            username: Lichess username
            max_games: Maximum number of games to fetch
            tournament_only: Only fetch tournament games
            
        Returns:
            List of tournament games
        """
        print(f"Fetching tournament games for {username}...")
        
        try:
            # Fetch games
            games = list(self.lichess_client.get_games_by_username(
                username,
                max_games=max_games
            ))
            
            # Filter for tournament games
            tournament_games = []
            for game in games:
                # Check if it's a tournament game
                is_tournament = self._is_tournament_game(game)
                
                if tournament_only and not is_tournament:
                    continue
                
                game['is_tournament'] = is_tournament
                tournament_games.append(game)
            
            print(f"Found {len(tournament_games)} tournament games")
            self.tournament_games = tournament_games
            return tournament_games
            
        except Exception as e:
            print(f"Error fetching tournament games: {e}")
            return []
    
    def _is_tournament_game(self, game_data: Dict) -> bool:
        """Check if a game is from a tournament"""
        # Check various indicators of tournament games
        event = game_data.get('event', '').lower()
        source = game_data.get('source', '').lower()
        
        tournament_indicators = [
            'tournament', 'arena', 'swiss', 'cup', 'championship',
            'olympiad', 'match', 'league'
        ]
        
        # Check event name
        for indicator in tournament_indicators:
            if indicator in event:
                return True
        
        # Check source
        if 'tournament' in source:
            return True
        
        # Check if it has tournament-specific fields
        if 'tournament' in game_data:
            return True
        
        return False
    
    def analyze_opponent_patterns(self, username: str) -> Dict:
        """
        Analyze patterns against specific opponents
        
        Args:
            username: Your username
            
        Returns:
            Dictionary with opponent-specific statistics
        """
        print("Analyzing opponent patterns...")
        
        opponent_analysis = {
            'overall_record': defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0}),
            'common_openings': defaultdict(list),
            'time_control_performance': defaultdict(lambda: defaultdict(list)),
            'recent_results': defaultdict(list),
            'blunder_patterns': defaultdict(list)
        }
        
        for game_data in self.tournament_games:
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
                
                # Determine opponent and result
                if white.lower() == username.lower():
                    opponent = black
                    player_color = 'white'
                elif black.lower() == username.lower():
                    opponent = white
                    player_color = 'black'
                else:
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
                
                # Analyze game for blunders (skip if no_analysis)
                if not self.no_analysis:
                    game_analysis = self.analyzer.analyze_game(game)
                    
                    # Find blunders against this opponent
                    for mistake in game_analysis['mistakes']:
                        if mistake['type'] == 'blunder':
                            blunder_info = {
                                'move_number': mistake['move_number'],
                                'move': mistake['move'],
                                'eval_change': mistake['eval_change'],
                                'fen': mistake['fen'],
                                'date': game_data.get('createdAt', ''),
                                'opening': opening
                            }
                            opponent_analysis['blunder_patterns'][opponent].append(blunder_info)
                
            except Exception as e:
                print(f"Error analyzing game: {e}")
                continue
        
        return opponent_analysis
    
    def find_common_blunders(self, min_occurrences: int = 3) -> Dict:
        """
        Find common blunders across all tournament games
        
        Args:
            min_occurrences: Minimum occurrences to consider a pattern
            
        Returns:
            Dictionary with common blunder patterns
        """
        if self.no_analysis:
            print("Skipping blunder analysis (no-analysis mode)")
            return {'position_patterns': {}, 'move_patterns': {}, 'opening_blunders': {}}
        
        print("Finding common blunders...")
        
        position_patterns = defaultdict(list)
        move_patterns = defaultdict(list)
        opening_blunders = defaultdict(list)
        
        for game_data in self.tournament_games:
            try:
                pgn_text = game_data.get('pgn', '')
                if not pgn_text:
                    continue
                
                game = self.lichess_client.parse_pgn_game(pgn_text)
                game_analysis = self.analyzer.analyze_game(game)
                
                opening = game.headers.get('Opening', '')
                
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
                            'opening': opening
                        })
                        
                        # Move-based patterns
                        move_patterns[mistake['move']].append({
                            'position': position_pattern,
                            'eval_change': mistake['eval_change'],
                            'opening': opening
                        })
                        
                        # Opening-specific blunders
                        if opening:
                            opening_blunders[opening].append({
                                'move_number': mistake['move_number'],
                                'blunder_move': mistake['move'],
                                'eval_change': mistake['eval_change']
                            })
            
            except Exception as e:
                print(f"Error analyzing blunders: {e}")
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
    
    def analyze_specific_opponent(self, username: str, opponent: str) -> Dict:
        """
        Detailed analysis against a specific opponent
        
        Args:
            username: Your username
            opponent: Opponent username to analyze
            
        Returns:
            Detailed analysis against this opponent
        """
        print(f"Analyzing games against {opponent}...")
        
        opponent_games = []
        
        # Find games against this opponent
        for game_data in self.tournament_games:
            white = game_data.get('players', {}).get('white', {}).get('user', {}).get('name', '')
            black = game_data.get('players', {}).get('black', {}).get('user', {}).get('name', '')
            
            if (white.lower() == opponent.lower() or black.lower() == opponent.lower()):
                opponent_games.append(game_data)
        
        if not opponent_games:
            return {'error': f'No games found against {opponent}'}
        
        analysis = {
            'opponent': opponent,
            'total_games': len(opponent_games),
            'games': [],
            'common_patterns': {},
            'blunder_analysis': {},
            'opening_stats': {},
            'recommendations': []
        }
        
        # Analyze each game
        for game_data in opponent_games:
            try:
                pgn_text = game_data.get('pgn', '')
                if not pgn_text:
                    continue
                
                game = self.lichess_client.parse_pgn_game(pgn_text)
                game_analysis = self.analyzer.analyze_game(game)
                
                game_summary = {
                    'game_id': game_data.get('id', ''),
                    'result': game.headers.get('Result', ''),
                    'white': game.headers.get('White', ''),
                    'black': game.headers.get('Black', ''),
                    'opening': game.headers.get('Opening', ''),
                    'time_control': game.headers.get('TimeControl', ''),
                    'date': game_data.get('createdAt', ''),
                    'blunders': len([m for m in game_analysis['mistakes'] if m['type'] == 'blunder']),
                    'mistakes': len([m for m in game_analysis['mistakes'] if m['type'] == 'mistake']),
                    'accuracy': game_analysis['summary']['accuracy']
                }
                
                analysis['games'].append(game_summary)
                
            except Exception as e:
                print(f"Error analyzing game against {opponent}: {e}")
                continue
        
        # Calculate overall statistics
        if analysis['games']:
            wins = len([g for g in analysis['games'] if self._is_win(g, username)])
            losses = len([g for g in analysis['games'] if self._is_loss(g, username)])
            draws = len([g for g in analysis['games'] if g['result'] == '1/2-1/2'])
            
            analysis['record'] = {
                'wins': wins,
                'losses': losses,
                'draws': draws,
                'win_rate': (wins / len(analysis['games'])) * 100 if analysis['games'] else 0
            }
            
            # Common openings
            openings = [g['opening'] for g in analysis['games'] if g['opening']]
            opening_counts = Counter(openings)
            analysis['opening_stats'] = dict(opening_counts.most_common(5))
            
            # Average performance
            avg_accuracy = sum(g['accuracy'] for g in analysis['games']) / len(analysis['games'])
            total_blunders = sum(g['blunders'] for g in analysis['games'])
            
            analysis['performance'] = {
                'average_accuracy': avg_accuracy,
                'total_blunders': total_blunders,
                'blunders_per_game': total_blunders / len(analysis['games'])
            }
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_opponent_recommendations(
                analysis, username
            )
        
        return analysis
    
    def _is_win(self, game_summary: Dict, username: str) -> bool:
        """Check if the game is a win for the user"""
        white = game_summary['white'].lower()
        black = game_summary['black'].lower()
        user = username.lower()
        result = game_summary['result']
        
        if white == user and result == '1-0':
            return True
        elif black == user and result == '0-1':
            return True
        return False
    
    def _is_loss(self, game_summary: Dict, username: str) -> bool:
        """Check if the game is a loss for the user"""
        white = game_summary['white'].lower()
        black = game_summary['black'].lower()
        user = username.lower()
        result = game_summary['result']
        
        if white == user and result == '0-1':
            return True
        elif black == user and result == '1-0':
            return True
        return False
    
    def _generate_opponent_recommendations(self, analysis: Dict, username: str) -> List[str]:
        """Generate specific recommendations for playing against this opponent"""
        recommendations = []
        
        record = analysis.get('record', {})
        performance = analysis.get('performance', {})
        
        # Based on head-to-head record
        if record.get('losses', 0) > record.get('wins', 0):
            recommendations.append(f"You have a losing record against {analysis['opponent']}. Study their playing style carefully.")
        
        # Based on blunders
        if performance.get('blunders_per_game', 0) > 2:
            recommendations.append("You tend to blunder frequently against this opponent. Focus on tactical calculation.")
        
        # Based on openings
        opening_stats = analysis.get('opening_stats', {})
        if opening_stats:
            most_common_opening = max(opening_stats, key=opening_stats.get)
            recommendations.append(f"Your opponent frequently plays {most_common_opening}. Prepare specific lines against this opening.")
        
        # Based on accuracy
        if performance.get('average_accuracy', 0) < 80:
            recommendations.append("Your accuracy drops against this opponent. Consider playing more solidly and avoiding complications.")
        
        return recommendations
    
    def generate_tournament_report(self, username: str, no_analysis: bool = False) -> str:
        """Generate comprehensive tournament analysis report"""
        report = []
        report.append("=" * 60)
        report.append(f"TOURNAMENT ANALYSIS REPORT FOR {username.upper()}")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Tournament Games Analyzed: {len(self.tournament_games)}")
        if no_analysis:
            report.append("Mode: Fast counts-only (no engine analysis)")
        report.append("")
        
        if not self.tournament_games:
            report.append("No tournament games found for analysis.")
            return "\n".join(report)
        
        # Overall tournament performance
        wins = sum(1 for g in self.tournament_games if self._get_game_result(g, username) == 'win')
        losses = sum(1 for g in self.tournament_games if self._get_game_result(g, username) == 'loss')
        draws = sum(1 for g in self.tournament_games if self._get_game_result(g, username) == 'draw')
        
        report.append("OVERALL TOURNAMENT PERFORMANCE:")
        report.append(f"Total Games: {len(self.tournament_games)}")
        report.append(f"Wins: {wins}")
        report.append(f"Losses: {losses}")
        report.append(f"Draws: {draws}")
        report.append(f"Win Rate: {(wins/len(self.tournament_games)*100):.1f}%")
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
            report.append("")
        
        # Recommendations
        report.append("TOURNAMENT RECOMMENDATIONS:")
        if wins < losses:
            report.append("- Focus on improving overall tournament performance")
        if not no_analysis:
            # We would have common_blunders in scope here, but to keep it simple, omit detailed blunder rec
            report.append("- Study common blunder patterns to avoid repeating mistakes")
        report.append("- Analyze specific opponents you struggle against")
        report.append("- Prepare opening repertoire for tournament play")
        if no_analysis:
            report.append("- Run without --no-analysis for detailed blunder and accuracy insights")
        
        return "\n".join(report)
    
    def _get_game_result(self, game_data: Dict, username: str) -> str:
        """Get the result of a game for the specified user"""
        white = game_data.get('players', {}).get('white', {}).get('user', {}).get('name', '')
        black = game_data.get('players', {}).get('black', {}).get('user', {}).get('name', '')
        result = game_data.get('status', '')
        
        user_white = white.lower() == username.lower()
        user_black = black.lower() == username.lower()
        
        if result == 'whiteWin' and user_white:
            return 'win'
        elif result == 'blackWin' and user_black:
            return 'win'
        elif result == 'draw':
            return 'draw'
        elif (result == 'whiteWin' and user_black) or (result == 'blackWin' and user_white):
            return 'loss'
        
        return 'unknown'
