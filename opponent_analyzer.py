"""
Advanced Opponent Analysis - Deep dive into specific opponent patterns and weaknesses
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import chess
import chess.pgn
from datetime import datetime, timedelta

from lichess_client import LichessClient
from chess_analyzer import ChessAnalyzer


class OpponentAnalyzer:
    """Advanced analyzer for specific opponent patterns and strategic analysis"""
    
    def __init__(self, lichess_client: LichessClient, chess_analyzer: ChessAnalyzer):
        """
        Initialize opponent analyzer
        
        Args:
            lichess_client: Lichess API client
            chess_analyzer: Chess analysis engine
        """
        self.lichess_client = lichess_client
        self.analyzer = chess_analyzer
    
    def analyze_opponent_comprehensive(self, username: str, opponent: str, 
                                     max_games: int = 50) -> Dict:
        """
        Comprehensive analysis of a specific opponent
        
        Args:
            username: Your username
            opponent: Opponent username to analyze
            max_games: Maximum games to analyze
            
        Returns:
            Comprehensive opponent analysis
        """
        print(f"Comprehensive analysis of games against {opponent}...")
        
        # Fetch games between the two players
        games = self._fetch_head_to_head_games(username, opponent, max_games)
        
        if not games:
            return {'error': f'No games found between {username} and {opponent}'}
        
        analysis = {
            'opponent': opponent,
            'username': username,
            'total_games': len(games),
            'head_to_head': {},
            'playing_patterns': {},
            'time_control_analysis': {},
            'opening_analysis': {},
            'tactical_patterns': {},
            'endgame_patterns': {},
            'psychological_factors': {},
            'strategic_recommendations': []
        }
        
        # Analyze each game
        detailed_games = []
        for game_data in games:
            try:
                detailed_analysis = self._analyze_single_game(game_data, username, opponent)
                if detailed_analysis:
                    detailed_games.append(detailed_analysis)
            except Exception as e:
                print(f"Error analyzing game: {e}")
                continue
        
        if not detailed_games:
            return {'error': 'Could not analyze any games'}
        
        # Compile comprehensive analysis
        analysis['head_to_head'] = self._analyze_head_to_head(detailed_games)
        analysis['playing_patterns'] = self._analyze_playing_patterns(detailed_games)
        analysis['time_control_analysis'] = self._analyze_time_control_patterns(detailed_games)
        analysis['opening_analysis'] = self._analyze_opening_patterns(detailed_games)
        analysis['tactical_patterns'] = self._analyze_tactical_patterns(detailed_games)
        analysis['endgame_patterns'] = self._analyze_endgame_patterns(detailed_games)
        analysis['psychological_factors'] = self._analyze_psychological_factors(detailed_games)
        analysis['strategic_recommendations'] = self._generate_strategic_recommendations(analysis)
        
        return analysis
    
    def _fetch_head_to_head_games(self, username: str, opponent: str, 
                                 max_games: int = 50) -> List[Dict]:
        """Fetch games between two specific players"""
        games = []
        
        try:
            # Fetch user's games
            user_games = list(self.lichess_client.get_games_by_username(
                username, max_games=max_games * 2  # Fetch more to filter
            ))
            
            # Filter for games against the specific opponent
            for game in user_games:
                white = game.get('players', {}).get('white', {}).get('user', {}).get('name', '')
                black = game.get('players', {}).get('black', {}).get('user', {}).get('name', '')
                
                if (white.lower() == opponent.lower() or black.lower() == opponent.lower()):
                    games.append(game)
                    if len(games) >= max_games:
                        break
        
        except Exception as e:
            print(f"Error fetching head-to-head games: {e}")
        
        return games
    
    def _analyze_single_game(self, game_data: Dict, username: str, opponent: str) -> Optional[Dict]:
        """Analyze a single game in detail"""
        try:
            pgn_text = game_data.get('pgn', '')
            if not pgn_text:
                return None
            
            game = self.lichess_client.parse_pgn_game(pgn_text)
            game_analysis = self.analyzer.analyze_game(game)
            
            # Extract game metadata
            white = game.headers.get('White', '')
            black = game.headers.get('Black', '')
            result = game.headers.get('Result', '')
            time_control = game.headers.get('TimeControl', '')
            opening = game.headers.get('Opening', '')
            
            # Determine player colors
            user_color = 'white' if white.lower() == username.lower() else 'black'
            opponent_color = 'black' if user_color == 'white' else 'white'
            
            # Analyze game phases
            game_phases = self._analyze_game_phases(game, game_analysis)
            
            # Analyze critical moments
            critical_moments = self._analyze_critical_moments(game_analysis, user_color)
            
            # Analyze time pressure (if available)
            time_pressure = self._analyze_time_pressure(game_data, user_color)
            
            return {
                'game_id': game_data.get('id', ''),
                'white': white,
                'black': black,
                'result': result,
                'user_color': user_color,
                'opponent_color': opponent_color,
                'time_control': time_control,
                'opening': opening,
                'date': game_data.get('createdAt', ''),
                'analysis': game_analysis,
                'phases': game_phases,
                'critical_moments': critical_moments,
                'time_pressure': time_pressure
            }
            
        except Exception as e:
            print(f"Error in single game analysis: {e}")
            return None
    
    def _analyze_game_phases(self, game: chess.pgn.Game, game_analysis: Dict) -> Dict:
        """Analyze different phases of the game"""
        phases = {
            'opening': {'moves': 0, 'mistakes': 0, 'blunders': 0},
            'middlegame': {'moves': 0, 'mistakes': 0, 'blunders': 0},
            'endgame': {'moves': 0, 'mistakes': 0, 'blunders': 0}
        }
        
        total_moves = len(game_analysis['moves_analysis'])
        
        for i, move_analysis in enumerate(game_analysis['moves_analysis']):
            # Determine phase
            if i < 10:  # First 10 moves = opening
                phase = 'opening'
            elif i < total_moves * 0.7:  # Until 70% of moves = middlegame
                phase = 'middlegame'
            else:  # Rest = endgame
                phase = 'endgame'
            
            phases[phase]['moves'] += 1
            
            # Check for mistakes in this phase
            for mistake in game_analysis['mistakes']:
                if mistake['move_number'] == move_analysis['move_number']:
                    if mistake['type'] == 'blunder':
                        phases[phase]['blunders'] += 1
                    elif mistake['type'] == 'mistake':
                        phases[phase]['mistakes'] += 1
        
        return phases
    
    def _analyze_critical_moments(self, game_analysis: Dict, user_color: str) -> List[Dict]:
        """Identify critical moments in the game"""
        critical_moments = []
        
        for i, move_analysis in enumerate(game_analysis['moves_analysis']):
            eval_data = move_analysis['evaluation']
            
            # Significant evaluation changes
            if i > 0:
                prev_eval = game_analysis['moves_analysis'][i-1]['evaluation']
                eval_change = abs(self._calculate_eval_change(prev_eval, eval_data))
                
                if eval_change > 200:  # Significant swing
                    critical_moments.append({
                        'move_number': move_analysis['move_number'],
                        'type': 'evaluation_swing',
                        'magnitude': eval_change,
                        'evaluation': eval_data
                    })
            
            # Mate threats
            if eval_data['type'] == 'mate':
                critical_moments.append({
                    'move_number': move_analysis['move_number'],
                    'type': 'mate_threat',
                    'mate_in': eval_data['value']
                })
        
        return critical_moments
    
    def _calculate_eval_change(self, prev_eval: Dict, curr_eval: Dict) -> float:
        """Calculate evaluation change"""
        if prev_eval['type'] == 'cp' and curr_eval['type'] == 'cp':
            return abs(curr_eval['value'] - prev_eval['value'])
        return 1000.0  # Large change for mate situations
    
    def _analyze_time_pressure(self, game_data: Dict, user_color: str) -> Dict:
        """Analyze time pressure patterns (if clock data available)"""
        # This would require access to move timestamps which may not be available
        # Placeholder for future enhancement
        return {
            'time_pressure_detected': False,
            'low_time_moves': 0,
            'time_trouble_blunders': 0
        }
    
    def _analyze_head_to_head(self, games: List[Dict]) -> Dict:
        """Analyze head-to-head record and patterns"""
        record = {'wins': 0, 'losses': 0, 'draws': 0}
        results_by_color = {'white': {'wins': 0, 'losses': 0, 'draws': 0},
                           'black': {'wins': 0, 'losses': 0, 'draws': 0}}
        
        for game in games:
            result = game['result']
            user_color = game['user_color']
            
            if result == '1-0':
                if user_color == 'white':
                    record['wins'] += 1
                    results_by_color['white']['wins'] += 1
                else:
                    record['losses'] += 1
                    results_by_color['black']['losses'] += 1
            elif result == '0-1':
                if user_color == 'black':
                    record['wins'] += 1
                    results_by_color['black']['wins'] += 1
                else:
                    record['losses'] += 1
                    results_by_color['white']['losses'] += 1
            elif result == '1/2-1/2':
                record['draws'] += 1
                results_by_color[user_color]['draws'] += 1
        
        total_games = len(games)
        return {
            'overall_record': record,
            'win_rate': (record['wins'] / total_games) * 100 if total_games > 0 else 0,
            'results_by_color': results_by_color,
            'total_games': total_games
        }
    
    def _analyze_playing_patterns(self, games: List[Dict]) -> Dict:
        """Analyze playing patterns and styles"""
        patterns = {
            'aggressive_games': 0,  # Games with many attacks/tactics
            'positional_games': 0,  # Games with slow maneuvering
            'tactical_complexity': [],
            'average_game_length': 0,
            'common_mistake_timing': []
        }
        
        total_moves = 0
        tactical_scores = []
        
        for game in games:
            analysis = game['analysis']
            game_moves = len(analysis['moves_analysis'])
            total_moves += game_moves
            
            # Calculate tactical complexity based on mistakes and critical moments
            tactical_score = len(analysis['mistakes']) + len(analysis['summary']['critical_moments'])
            tactical_scores.append(tactical_score)
            
            # Classify playing style
            if tactical_score > 5:
                patterns['aggressive_games'] += 1
            else:
                patterns['positional_games'] += 1
            
            # Track when mistakes typically occur
            for mistake in analysis['mistakes']:
                patterns['common_mistake_timing'].append(mistake['move_number'])
        
        patterns['average_game_length'] = total_moves / len(games) if games else 0
        patterns['tactical_complexity'] = tactical_scores
        
        return patterns
    
    def _analyze_time_control_patterns(self, games: List[Dict]) -> Dict:
        """Analyze performance by time control"""
        time_stats = defaultdict(lambda: {'games': 0, 'wins': 0, 'losses': 0, 'draws': 0})
        
        for game in games:
            tc = game['time_control']
            result = game['result']
            user_color = game['user_color']
            
            time_stats[tc]['games'] += 1
            
            if result == '1-0' and user_color == 'white':
                time_stats[tc]['wins'] += 1
            elif result == '0-1' and user_color == 'black':
                time_stats[tc]['wins'] += 1
            elif result == '1/2-1/2':
                time_stats[tc]['draws'] += 1
            elif (result == '1-0' and user_color == 'black') or (result == '0-1' and user_color == 'white'):
                time_stats[tc]['losses'] += 1
        
        # Calculate win rates
        for tc, stats in time_stats.items():
            if stats['games'] > 0:
                stats['win_rate'] = (stats['wins'] / stats['games']) * 100
        
        return dict(time_stats)
    
    def _analyze_opening_patterns(self, games: List[Dict]) -> Dict:
        """Analyze opening patterns and preparation"""
        openings = defaultdict(lambda: {'games': 0, 'wins': 0, 'losses': 0, 'draws': 0})
        opening_results = []
        
        for game in games:
            opening = game['opening']
            result = game['result']
            user_color = game['user_color']
            
            openings[opening]['games'] += 1
            
            if result == '1-0' and user_color == 'white':
                openings[opening]['wins'] += 1
                opening_results.append('win')
            elif result == '0-1' and user_color == 'black':
                openings[opening]['wins'] += 1
                opening_results.append('win')
            elif result == '1/2-1/2':
                openings[opening]['draws'] += 1
                opening_results.append('draw')
            else:
                openings[opening]['losses'] += 1
                opening_results.append('loss')
        
        # Calculate success rates
        for opening, stats in openings.items():
            if stats['games'] > 0:
                stats['success_rate'] = (stats['wins'] / stats['games']) * 100
        
        return {
            'opening_stats': dict(openings),
            'most_common': max(openings.keys(), key=lambda x: openings[x]['games']) if openings else None,
            'most_successful': max(openings.keys(), key=lambda x: openings[x]['success_rate']) if openings else None
        }
    
    def _analyze_tactical_patterns(self, games: List[Dict]) -> Dict:
        """Analyze tactical patterns and common mistakes"""
        tactical_patterns = {
            'common_blunder_moves': Counter(),
            'common_mistake_phases': Counter(),
            'tactical_themes': Counter(),
            'calculation_errors': []
        }
        
        for game in games:
            analysis = game['analysis']
            
            for mistake in analysis['mistakes']:
                # Track common blunder moves
                tactical_patterns['common_blunder_moves'][mistake['move']] += 1
                
                # Track which phase mistakes occur
                move_number = mistake['move_number']
                if move_number <= 10:
                    tactical_patterns['common_mistake_phases']['opening'] += 1
                elif move_number <= 25:
                    tactical_patterns['common_mistake_phases']['middlegame'] += 1
                else:
                    tactical_patterns['common_mistake_phases']['endgame'] += 1
                
                # Store calculation errors
                if mistake['type'] in ['blunder', 'mistake']:
                    tactical_patterns['calculation_errors'].append({
                        'move': mistake['move'],
                        'move_number': mistake['move_number'],
                        'eval_change': mistake['eval_change'],
                        'phase': 'opening' if move_number <= 10 else 'middlegame' if move_number <= 25 else 'endgame'
                    })
        
        return tactical_patterns
    
    def _analyze_endgame_patterns(self, games: List[Dict]) -> Dict:
        """Analyze endgame patterns and technique"""
        endgame_patterns = {
            'endgame_results': Counter(),
            'common_endgame_mistakes': [],
            'time_trouble_endgames': 0,
            'endgame_accuracy': []
        }
        
        for game in games:
            analysis = game['analysis']
            phases = game['phases']
            
            # Endgame accuracy
            if phases['endgame']['moves'] > 0:
                endgame_mistakes = phases['endgame']['mistakes'] + phases['endgame']['blunders']
                endgame_accuracy = max(0, 100 - (endgame_mistakes / phases['endgame']['moves'] * 100))
                endgame_patterns['endgame_accuracy'].append(endgame_accuracy)
            
            # Track endgame result
            result = game['result']
            endgame_patterns['endgame_results'][result] += 1
            
            # Common endgame mistakes
            for mistake in analysis['mistakes']:
                if mistake['move_number'] > 25:  # Assume endgame starts after move 25
                    endgame_patterns['common_endgame_mistakes'].append({
                        'move': mistake['move'],
                        'move_number': mistake['move_number'],
                        'type': mistake['type']
                    })
        
        return endgame_patterns
    
    def _analyze_psychological_factors(self, games: List[Dict]) -> Dict:
        """Analyze psychological factors in the matchup"""
        psychological = {
            'momentum_shifts': [],
            'revenge_factor': 0,  # Performance after losses
            'confidence_factor': 0,  # Performance after wins
            'pressure_situations': []
        }
        
        # Sort games by date to analyze momentum
        sorted_games = sorted(games, key=lambda x: x.get('date', ''))
        
        for i, game in enumerate(sorted_games):
            if i == 0:
                continue
            
            prev_game = sorted_games[i-1]
            prev_result = prev_game['result']
            curr_result = game['result']
            
            # Analyze performance after previous result
            user_won_prev = ((prev_result == '1-0' and prev_game['user_color'] == 'white') or
                            (prev_result == '0-1' and prev_game['user_color'] == 'black'))
            
            user_won_curr = ((curr_result == '1-0' and game['user_color'] == 'white') or
                            (curr_result == '0-1' and game['user_color'] == 'black'))
            
            if user_won_prev and user_won_curr:
                psychological['confidence_factor'] += 1
            elif not user_won_prev and user_won_curr:
                psychological['revenge_factor'] += 1
        
        return psychological
    
    def _generate_strategic_recommendations(self, analysis: Dict) -> List[str]:
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        
        # Head-to-head recommendations
        h2h = analysis['head_to_head']
        if h2h['win_rate'] < 40:
            recommendations.append(f"Focus on studying {analysis['opponent']}'s games - you have a losing record")
        elif h2h['win_rate'] > 60:
            recommendations.append(f"You play well against {analysis['opponent']} - maintain your current strategy")
        
        # Time control recommendations
        tc_analysis = analysis['time_control_analysis']
        worst_tc = None
        worst_win_rate = 100
        
        for tc, stats in tc_analysis.items():
            if stats['games'] >= 3 and stats['win_rate'] < worst_win_rate:
                worst_tc = tc
                worst_win_rate = stats['win_rate']
        
        if worst_tc:
            recommendations.append(f"Improve performance in {worst_tc} time control - current win rate: {worst_win_rate:.1f}%")
        
        # Opening recommendations
        opening_analysis = analysis['opening_analysis']
        if opening_analysis['most_common']:
            most_common = opening_analysis['most_common']
            stats = opening_analysis['opening_stats'][most_common]
            if stats['success_rate'] < 50:
                recommendations.append(f"Consider alternatives to {most_common} opening - success rate only {stats['success_rate']:.1f}%")
        
        # Tactical recommendations
        tactical = analysis['tactical_patterns']
        if tactical['common_mistake_phases']:
            worst_phase = tactical['common_mistake_phases'].most_common(1)[0][0]
            recommendations.append(f"Focus on {worst_phase} tactics - most mistakes occur in this phase")
        
        # Endgame recommendations
        endgame = analysis['endgame_patterns']
        if endgame['endgame_accuracy']:
            avg_endgame_accuracy = sum(endgame['endgame_accuracy']) / len(endgame['endgame_accuracy'])
            if avg_endgame_accuracy < 80:
                recommendations.append("Improve endgame technique - current accuracy below 80%")
        
        # Psychological recommendations
        psych = analysis['psychological_factors']
        if psych['revenge_factor'] > psych['confidence_factor']:
            recommendations.append("You perform better after losses - use this mental strength")
        elif psych['confidence_factor'] > psych['revenge_factor']:
            recommendations.append("Build on wins - maintain confidence and momentum")
        
        return recommendations
    
    def generate_opponent_report(self, analysis: Dict) -> str:
        """Generate comprehensive opponent analysis report"""
        if 'error' in analysis:
            return f"Error: {analysis['error']}"
        
        report = []
        report.append("=" * 70)
        report.append(f"COMPREHENSIVE OPPONENT ANALYSIS: {analysis['opponent'].upper()}")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Games Analyzed: {analysis['total_games']}")
        report.append("")
        
        # Head-to-head record
        h2h = analysis['head_to_head']
        report.append("HEAD-TO-HEAD RECORD:")
        report.append(f"Overall: {h2h['overall_record']['wins']}-{h2h['overall_record']['losses']}-{h2h['overall_record']['draws']}")
        report.append(f"Win Rate: {h2h['win_rate']:.1f}%")
        
        if h2h['results_by_color']['white']['games'] > 0:
            white_wr = (h2h['results_by_color']['white']['wins'] / h2h['results_by_color']['white']['games']) * 100
            report.append(f"As White: {h2h['results_by_color']['white']['wins']}-{h2h['results_by_color']['white']['losses']}-{h2h['results_by_color']['white']['draws']} ({white_wr:.1f}%)")
        
        if h2h['results_by_color']['black']['games'] > 0:
            black_wr = (h2h['results_by_color']['black']['wins'] / h2h['results_by_color']['black']['games']) * 100
            report.append(f"As Black: {h2h['results_by_color']['black']['wins']}-{h2h['results_by_color']['black']['losses']}-{h2h['results_by_color']['black']['draws']} ({black_wr:.1f}%)")
        report.append("")
        
        # Playing patterns
        patterns = analysis['playing_patterns']
        report.append("PLAYING PATTERNS:")
        report.append(f"Average Game Length: {patterns['average_game_length']:.1f} moves")
        report.append(f"Aggressive Games: {patterns['aggressive_games']}")
        report.append(f"Positional Games: {patterns['positional_games']}")
        
        if patterns['common_mistake_timing']:
            avg_mistake_move = sum(patterns['common_mistake_timing']) / len(patterns['common_mistake_timing'])
            report.append(f"Average Mistake Move: {avg_mistake_move:.1f}")
        report.append("")
        
        # Time control analysis
        tc_analysis = analysis['time_control_analysis']
        if tc_analysis:
            report.append("TIME CONTROL PERFORMANCE:")
            for tc, stats in tc_analysis.items():
                if stats['games'] >= 2:
                    report.append(f"{tc}: {stats['wins']}-{stats['losses']}-{stats['draws']} ({stats['win_rate']:.1f}% win rate)")
            report.append("")
        
        # Opening analysis
        opening_analysis = analysis['opening_analysis']
        if opening_analysis['most_common']:
            report.append("OPENING PATTERNS:")
            report.append(f"Most Common: {opening_analysis['most_common']}")
            if opening_analysis['most_successful']:
                report.append(f"Most Successful: {opening_analysis['most_successful']}")
            
            # Show top 3 openings with results
            opening_stats = opening_analysis['opening_stats']
            sorted_openings = sorted(opening_stats.items(), key=lambda x: x[1]['games'], reverse=True)[:3]
            for opening, stats in sorted_openings:
                report.append(f"  {opening}: {stats['games']} games, {stats['success_rate']:.1f}% success rate")
            report.append("")
        
        # Tactical patterns
        tactical = analysis['tactical_patterns']
        if tactical['common_blunder_moves']:
            report.append("TACTICAL PATTERNS:")
            most_common_blunders = tactical['common_blunder_moves'].most_common(3)
            for move, count in most_common_blunders:
                report.append(f"Common Blunder Move: {move} ({count} times)")
            
            if tactical['common_mistake_phases']:
                worst_phase = tactical['common_mistake_phases'].most_common(1)[0][0]
                report.append(f"Mistakes Most Common In: {worst_phase} phase")
            report.append("")
        
        # Strategic recommendations
        recommendations = analysis['strategic_recommendations']
        if recommendations:
            report.append("STRATEGIC RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        return "\n".join(report)
