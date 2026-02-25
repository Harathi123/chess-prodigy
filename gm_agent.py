"""
GM (Grandmaster) Agent - Intelligent Chess Coach and Performance Analyst
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd

from lichess_client import LichessClient
from chess_analyzer import ChessAnalyzer
from game_analyzer import GameAnalysisSystem
from tournament_analyzer import TournamentAnalyzer
from opponent_analyzer import OpponentAnalyzer


@dataclass
class PerformanceInsight:
    """Store performance insights and recommendations"""
    category: str
    insight: str
    confidence: float
    data_support: List[str]
    actionable_advice: str


class GMAgent:
    """Intelligent Chess Coach Agent"""
    
    def __init__(self, api_token: str, username: str):
        """
        Initialize GM Agent
        
        Args:
            api_token: Lichess API token
            username: Player username to analyze
        """
        self.username = username
        self.lichess_client = LichessClient(api_token)
        self.chess_analyzer = ChessAnalyzer()
        self.game_system = GameAnalysisSystem(api_token, username)
        self.tournament_analyzer = TournamentAnalyzer(self.lichess_client, self.chess_analyzer)
        self.opponent_analyzer = OpponentAnalyzer(self.lichess_client, self.chess_analyzer)
        
        # Cache for performance data
        self.performance_cache = {}
        self.last_analysis_time = None
        
        # GM Agent personality and knowledge base
        self.knowledge_base = self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self) -> Dict:
        """Initialize GM Agent's knowledge base"""
        return {
            'opening_principles': {
                'control_center': 'Control the center with pawns and pieces',
                'develop_pieces': 'Develop knights before bishops, pieces before pawns',
                'king_safety': 'Castle early, usually before move 10',
                'pawn_structure': 'Avoid pawn weaknesses, maintain flexibility'
            },
            'middlegame_concepts': {
                'piece_activity': 'Place pieces on active squares',
                'tactical_awareness': 'Always look for tactics (checks, captures, threats)',
                'positional_play': 'Control key squares and files',
                'planning': 'Have a plan based on position features'
            },
            'endgame_technique': {
                'king_activity': 'Activate your king in endgames',
                'pawn_promotion': 'Create passed pawns and support them',
                'piece_coordination': 'Coordinate pieces effectively',
                'calculation': 'Calculate accurately in tactical endgames'
            },
            'psychological_factors': {
                'time_management': 'Use time wisely, avoid time trouble',
                'confidence': 'Play confidently but respect opponent',
                'recovery': 'Recover well from mistakes',
                'adaptation': 'Adapt to opponent\'s style'
            }
        }
    
    def ask(self, question: str) -> str:
        """
        Ask the GM Agent a question about your performance
        
        Args:
            question: Natural language question about chess performance
            
        Returns:
            GM Agent's response
        """
        # Update performance data if needed
        self._update_performance_data()
        
        # Parse and classify the question
        question_type = self._classify_question(question)
        
        # Generate response based on question type
        if question_type == 'overall_performance':
            return self._answer_overall_performance(question)
        elif question_type == 'specific_opponent':
            return self._answer_opponent_question(question)
        elif question_type == 'opening_advice':
            return self._answer_opening_question(question)
        elif question_type == 'tactical_improvement':
            return self._answer_tactical_question(question)
        elif question_type == 'tournament_performance':
            return self._answer_tournament_question(question)
        elif question_type == 'recent_form':
            return self._answer_recent_form_question(question)
        elif question_type == 'weaknesses':
            return self._answer_weaknesses_question(question)
        elif question_type == 'strengths':
            return self._answer_strengths_question(question)
        elif question_type == 'time_control':
            return self._answer_time_control_question(question)
        elif question_type == 'recommendations':
            return self._answer_recommendations_question(question)
        else:
            return self._answer_general_question(question)

    def export_cascade_context(self, output_path: str, num_games: int = 20) -> Dict[str, Any]:
        """Export a compact JSON context pack suitable for pasting into Cascade."""
        self._update_performance_data()

        if not self.performance_cache.get('recent_games') or len(self.performance_cache['recent_games']) < num_games:
            try:
                self.game_system.load_user_data()
                recent_games = self.game_system.analyze_recent_games(num_games=num_games)
                self.performance_cache['recent_games'] = recent_games
                self.performance_cache['user_profile'] = self.game_system.user_profile
                self.performance_cache['timestamp'] = datetime.now()
                self.last_analysis_time = self.performance_cache['timestamp']
            except Exception:
                pass

        context_pack = self._build_cascade_context(num_games=num_games)

        parent = os.path.dirname(output_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(context_pack, f, indent=2, ensure_ascii=False, default=str)

        return context_pack

    def _build_cascade_context(self, num_games: int = 20) -> Dict[str, Any]:
        """Build a compact context pack for Cascade."""
        games = (self.performance_cache.get('recent_games') or [])[:num_games]
        profile = self.performance_cache.get('user_profile') or {}
        generated_at = datetime.now().isoformat()

        overall = self._summarize_overall(games)
        time_controls = self._summarize_time_controls(games)
        openings = self._summarize_openings(games)
        opponents = self._summarize_opponents(games)
        blunders = self._summarize_blunders(games)

        perfs = (profile.get('perfs') or {})
        ratings = {}
        for tc in ['bullet', 'blitz', 'rapid', 'classical']:
            if tc in perfs and isinstance(perfs[tc], dict):
                ratings[tc] = {
                    'rating': perfs[tc].get('rating'),
                    'games': perfs[tc].get('games'),
                    'rd': perfs[tc].get('rd'),
                    'prog': perfs[tc].get('prog'),
                }

        return {
            'schema': 'chess-prodigy.cascade_context',
            'schema_version': 1,
            'generated_at': generated_at,
            'username': self.username,
            'sample': {
                'games_requested': num_games,
                'games_included': len(games),
                'source': 'lichess (recent games export)',
            },
            'ratings': ratings,
            'overall': overall,
            'time_controls': time_controls,
            'openings': openings,
            'opponents': opponents,
            'blunders': blunders,
            'how_to_use_in_cascade': {
                'instructions': (
                    'Paste this JSON into Cascade and ask questions like: '
                    '"What are my biggest weaknesses?", "Which openings should I stop playing?", '
                    '"What blunder patterns repeat?", "Why am I losing to my worst opponent?"'
                )
            }
        }

    def _summarize_overall(self, games: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not games:
            return {}

        results = [self._get_user_result_from_analysis(g) for g in games]
        wins = sum(1 for r in results if r == 'win')
        losses = sum(1 for r in results if r == 'loss')
        draws = sum(1 for r in results if r == 'draw')
        total = len(results)

        avg_accuracy = sum(g.get('summary', {}).get('accuracy', 0) for g in games) / total
        avg_cp_loss = sum(g.get('summary', {}).get('average_centipawn_loss', 0) for g in games) / total
        blunders = sum(g.get('summary', {}).get('blunders', 0) for g in games)
        mistakes = sum(g.get('summary', {}).get('mistakes', 0) for g in games)
        inaccuracies = sum(g.get('summary', {}).get('inaccuracies', 0) for g in games)

        return {
            'record': {'wins': wins, 'losses': losses, 'draws': draws, 'total': total},
            'win_rate_pct': round((wins / total) * 100, 1) if total else 0.0,
            'avg_accuracy_pct': round(avg_accuracy, 1),
            'avg_centipawn_loss': round(avg_cp_loss, 1),
            'total_blunders': blunders,
            'total_mistakes': mistakes,
            'total_inaccuracies': inaccuracies,
        }

    def _summarize_time_controls(self, games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not games:
            return []

        buckets: Dict[str, Dict[str, Any]] = {}
        for g in games:
            tc = (g.get('game_info', {}).get('time_control') or 'Unknown')
            if tc not in buckets:
                buckets[tc] = {'time_control': tc, 'games': 0, 'wins': 0, 'losses': 0, 'draws': 0, 'avg_accuracy': 0.0}
            buckets[tc]['games'] += 1
            r = self._get_user_result_from_analysis(g)
            buckets[tc][r + 's'] = buckets[tc].get(r + 's', 0) + 1
            buckets[tc]['avg_accuracy'] += float(g.get('summary', {}).get('accuracy', 0))

        out = []
        for tc, s in buckets.items():
            games_n = s['games']
            avg_acc = s['avg_accuracy'] / games_n if games_n else 0
            win_rate = (s['wins'] / games_n) * 100 if games_n else 0
            out.append({
                'time_control': tc,
                'games': games_n,
                'wins': s['wins'],
                'losses': s['losses'],
                'draws': s['draws'],
                'win_rate_pct': round(win_rate, 1),
                'avg_accuracy_pct': round(avg_acc, 1),
            })

        out.sort(key=lambda x: x['games'], reverse=True)
        return out

    def _summarize_openings(self, games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not games:
            return []

        stats: Dict[str, Dict[str, Any]] = {}
        for g in games:
            opening = g.get('opening_analysis', {}).get('opening')
            if not opening:
                opening = g.get('game_info', {}).get('opening')
            opening = opening or 'Unknown'

            if opening not in stats:
                stats[opening] = {'opening': opening, 'games': 0, 'wins': 0, 'losses': 0, 'draws': 0, 'avg_accuracy': 0.0}
            stats[opening]['games'] += 1

            r = self._get_user_result_from_analysis(g)
            stats[opening][r + 's'] += 1
            stats[opening]['avg_accuracy'] += float(g.get('summary', {}).get('accuracy', 0))

        out = []
        for opening, s in stats.items():
            n = s['games']
            out.append({
                'opening': opening,
                'games': n,
                'wins': s['wins'],
                'losses': s['losses'],
                'draws': s['draws'],
                'win_rate_pct': round((s['wins'] / n) * 100, 1) if n else 0.0,
                'avg_accuracy_pct': round((s['avg_accuracy'] / n), 1) if n else 0.0,
            })

        out.sort(key=lambda x: x['games'], reverse=True)
        return out[:12]

    def _summarize_opponents(self, games: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not games:
            return {'by_opponent': [], 'worst_opponents': [], 'best_opponents': []}

        by_opp: Dict[str, Dict[str, Any]] = {}
        for g in games:
            gi = g.get('game_info', {})
            white = (gi.get('white') or '').strip()
            black = (gi.get('black') or '').strip()
            if not white or not black:
                continue

            user_is_white = white.lower() == self.username.lower()
            opponent = black if user_is_white else white
            opponent = opponent or 'Unknown'

            if opponent not in by_opp:
                by_opp[opponent] = {'opponent': opponent, 'games': 0, 'wins': 0, 'losses': 0, 'draws': 0, 'avg_accuracy': 0.0}
            by_opp[opponent]['games'] += 1
            r = self._get_user_result_from_analysis(g)
            by_opp[opponent][r + 's'] += 1
            by_opp[opponent]['avg_accuracy'] += float(g.get('summary', {}).get('accuracy', 0))

        items = []
        for opp, s in by_opp.items():
            n = s['games']
            win_rate = (s['wins'] / n) * 100 if n else 0
            items.append({
                'opponent': opp,
                'games': n,
                'wins': s['wins'],
                'losses': s['losses'],
                'draws': s['draws'],
                'win_rate_pct': round(win_rate, 1),
                'avg_accuracy_pct': round((s['avg_accuracy'] / n), 1) if n else 0.0,
            })

        items.sort(key=lambda x: x['games'], reverse=True)

        eligible = [x for x in items if x['games'] >= 2]
        worst = sorted(eligible, key=lambda x: (x['win_rate_pct'], -x['games']))[:5]
        best = sorted(eligible, key=lambda x: (-x['win_rate_pct'], -x['games']))[:5]

        return {'by_opponent': items[:15], 'worst_opponents': worst, 'best_opponents': best}

    def _summarize_blunders(self, games: List[Dict[str, Any]]) -> Dict[str, Any]:
        blunders = []
        for g in games:
            for m in (g.get('mistakes') or []):
                if m.get('type') == 'blunder':
                    blunders.append(m)

        by_move = {}
        for b in blunders:
            mv = b.get('move') or 'Unknown'
            by_move.setdefault(mv, {'move': mv, 'count': 0, 'avg_cp_loss': 0.0})
            by_move[mv]['count'] += 1
            by_move[mv]['avg_cp_loss'] += abs(float(b.get('eval_change') or 0))

        common_moves = []
        for mv, s in by_move.items():
            common_moves.append({
                'move': mv,
                'count': s['count'],
                'avg_cp_loss': round((s['avg_cp_loss'] / s['count']), 1) if s['count'] else 0.0,
            })
        common_moves.sort(key=lambda x: (-x['count'], -x['avg_cp_loss']))

        timing = [int(b.get('move_number') or 0) for b in blunders if b.get('move_number')]
        phase = {'opening': 0, 'middlegame': 0, 'endgame': 0}
        for t in timing:
            if t <= 10:
                phase['opening'] += 1
            elif t <= 25:
                phase['middlegame'] += 1
            else:
                phase['endgame'] += 1

        return {
            'total_blunders': len(blunders),
            'blunders_by_phase': phase,
            'most_common_blunder_moves': common_moves[:10],
        }
    
    def _classify_question(self, question: str) -> str:
        """Classify the type of question"""
        question_lower = question.lower()
        
        # Keywords for different question types
        keywords = {
            'overall_performance': ['overall', 'general', 'how am i doing', 'performance', 'rating'],
            'specific_opponent': ['opponent', 'against', 'beat', 'lose to', 'struggle with'],
            'opening_advice': ['opening', 'openings', 'start', 'beginning', 'book'],
            'tactical_improvement': ['tactics', 'tactical', 'blunders', 'mistakes', 'calculation'],
            'tournament_performance': ['tournament', 'competition', 'serious', 'important'],
            'recent_form': ['recent', 'lately', 'now', 'current', 'last few'],
            'weaknesses': ['weakness', 'weak', 'improve', 'bad', 'problem'],
            'strengths': ['strength', 'strong', 'good at', 'excel'],
            'time_control': ['bullet', 'blitz', 'rapid', 'classical', 'time'],
            'recommendations': ['recommend', 'suggest', 'advice', 'should i', 'what should']
        }
        
        for q_type, words in keywords.items():
            if any(word in question_lower for word in words):
                return q_type
        
        return 'general'
    
    def _update_performance_data(self):
        """Update cached performance data"""
        current_time = datetime.now()
        
        # Update if cache is empty or more than 1 hour old
        if (not self.last_analysis_time or 
            current_time - self.last_analysis_time > timedelta(hours=1)):
            
            print("GM Agent: Updating performance data...")
            try:
                # Load recent games for analysis
                self.game_system.load_user_data()
                recent_games = self.game_system.analyze_recent_games(num_games=20)
                
                # Cache the data
                self.performance_cache = {
                    'recent_games': recent_games,
                    'user_profile': self.game_system.user_profile,
                    'timestamp': current_time
                }
                self.last_analysis_time = current_time
                
            except Exception as e:
                print(f"Error updating performance data: {e}")
    
    def _answer_overall_performance(self, question: str) -> str:
        """Answer questions about overall performance"""
        if not self.performance_cache.get('recent_games'):
            return "I need to analyze your recent games first. Let me gather that data..."
        
        games = self.performance_cache['recent_games']
        profile = self.performance_cache['user_profile']
        
        # Calculate overall statistics
        total_games = len(games)
        wins = sum(1 for g in games if g['game_info']['result'] == '1-0' and 
                   g['game_info']['white'] == self.username) + \
                sum(1 for g in games if g['game_info']['result'] == '0-1' and 
                   g['game_info']['black'] == self.username)
        
        losses = sum(1 for g in games if g['game_info']['result'] == '0-1' and 
                    g['game_info']['white'] == self.username) + \
                 sum(1 for g in games if g['game_info']['result'] == '1-0' and 
                    g['game_info']['black'] == self.username)
        
        draws = total_games - wins - losses
        win_rate = (wins / total_games * 100) if total_games > 0 else 0
        
        avg_accuracy = sum(g['summary']['accuracy'] for g in games) / total_games if total_games > 0 else 0
        avg_blunders = sum(g['summary']['blunders'] for g in games) / total_games if total_games > 0 else 0
        
        response = f"**Overall Performance Analysis**\n\n"
        response += f"Based on your last {total_games} games:\n\n"
        response += f"📊 **Record**: {wins}-{losses}-{draws} ({win_rate:.1f}% win rate)\n"
        response += f"🎯 **Average Accuracy**: {avg_accuracy:.1f}%\n"
        response += f"❌ **Average Blunders**: {avg_blunders:.1f} per game\n\n"
        
        # Add rating information if available
        if profile and profile.get('perfs'):
            response += "**Current Ratings**:\n"
            for time_control in ['blitz', 'rapid', 'classical']:
                if time_control in profile['perfs']:
                    rating = profile['perfs'][time_control]['rating']
                    response += f"• {time_control.capitalize()}: {rating}\n"
        
        # Add assessment
        if win_rate >= 60:
            response += f"\n🌟 **Assessment**: Excellent performance! You're winning consistently."
        elif win_rate >= 50:
            response += f"\n👍 **Assessment**: Good performance. Room for improvement in consistency."
        elif win_rate >= 40:
            response += f"\n📈 **Assessment**: Decent performance. Focus on reducing blunders."
        else:
            response += f"\n🎯 **Assessment**: Performance needs improvement. Let's work on fundamentals."
        
        return response
    
    def _answer_opponent_question(self, question: str) -> str:
        """Answer questions about specific opponents"""
        # Extract opponent name from question
        opponent_match = re.search(r'(?:against|vs|beat|lose to|struggle with)\s+([a-zA-Z0-9_-]+)', question, re.IGNORECASE)
        
        if not opponent_match:
            return "I need to know which opponent you're asking about. Could you specify their username?"
        
        opponent = opponent_match.group(1)
        
        try:
            analysis = self.opponent_analyzer.analyze_opponent_comprehensive(
                self.username, opponent, max_games=20
            )
            
            if 'error' in analysis:
                return f"I couldn't find enough games against {opponent}. You might need more games together for meaningful analysis."
            
            h2h = analysis['head_to_head']
            
            response = f"**Analysis vs {opponent}**\n\n"
            response += f"📊 **Head-to-Head**: {h2h['overall_record']['wins']}-{h2h['overall_record']['losses']}-{h2h['overall_record']['draws']}\n"
            response += f"📈 **Win Rate**: {h2h['win_rate']:.1f}%\n\n"
            
            # Add strategic insights
            if h2h['win_rate'] >= 60:
                response += f"💡 **Insight**: You play very well against {opponent}! Your current strategy works.\n"
            elif h2h['win_rate'] <= 40:
                response += f"⚠️ **Challenge**: {opponent} is a tough matchup for you. Let's analyze why...\n"
                
                # Add specific recommendations
                if analysis.get('opening_analysis', {}).get('most_common'):
                    common_opening = analysis['opening_analysis']['most_common']
                    response += f"📚 **Opening Note**: They often play {common_opening}. Prepare specific lines.\n"
                
                if analysis.get('tactical_patterns', {}).get('common_mistake_phases'):
                    worst_phase = analysis['tactical_patterns']['common_mistake_phases'].most_common(1)[0][0]
                    response += f"🎯 **Tactical Focus**: Be extra careful in the {worst_phase}.\n"
            
            return response
            
        except Exception as e:
            return f"I encountered an error analyzing your games against {opponent}: {str(e)}"
    
    def _answer_opening_question(self, str) -> str:
        """Answer questions about openings"""
        if not self.performance_cache.get('recent_games'):
            return "Let me analyze your recent games to understand your opening patterns..."
        
        games = self.performance_cache['recent_games']
        opening_stats = {}
        
        # Analyze opening performance
        for game in games:
            opening = game['game_info'].get('opening', 'Unknown')
            result = game['game_info']['result']
            
            if opening not in opening_stats:
                opening_stats[opening] = {'games': 0, 'wins': 0, 'losses': 0, 'draws': 0}
            
            opening_stats[opening]['games'] += 1
            
            # Determine if user won
            white = game['game_info']['white']
            black = game['game_info']['black']
            user_white = white.lower() == self.username.lower()
            
            if (result == '1-0' and user_white) or (result == '0-1' and not user_white):
                opening_stats[opening]['wins'] += 1
            elif result == '1/2-1/2':
                opening_stats[opening]['draws'] += 1
            else:
                opening_stats[opening]['losses'] += 1
        
        # Generate response
        response = "**Opening Performance Analysis**\n\n"
        
        # Sort by frequency
        sorted_openings = sorted(opening_stats.items(), key=lambda x: x[1]['games'], reverse=True)
        
        response += "📚 **Most Frequently Played Openings**:\n"
        for opening, stats in sorted_openings[:5]:
            win_rate = (stats['wins'] / stats['games']) * 100 if stats['games'] > 0 else 0
            response += f"• {opening}: {stats['games']} games, {win_rate:.1f}% win rate\n"
        
        # Find best and worst performing openings
        if opening_stats:
            best_opening = max(opening_stats.items(), key=lambda x: (x[1]['wins'] / x[1]['games']) if x[1]['games'] >= 3 else 0)
            worst_opening = min(opening_stats.items(), key=lambda x: (x[1]['wins'] / x[1]['games']) if x[1]['games'] >= 3 else 100)
            
            if best_opening[1]['games'] >= 3:
                best_wr = (best_opening[1]['wins'] / best_opening[1]['games']) * 100
                response += f"\n🌟 **Best Opening**: {best_opening[0]} ({best_wr:.1f}% win rate)\n"
            
            if worst_opening[1]['games'] >= 3:
                worst_wr = (worst_opening[1]['wins'] / worst_opening[1]['games']) * 100
                response += f"⚠️ **Needs Work**: {worst_opening[0]} ({worst_wr:.1f}% win rate)\n"
        
        response += f"\n💡 **GM Advice**: Focus on mastering 2-3 openings rather than playing many different ones."
        
        return response
    
    def _answer_tactical_question(self, question: str) -> str:
        """Answer questions about tactics and blunders"""
        if not self.performance_cache.get('recent_games'):
            return "Let me analyze your recent games to identify tactical patterns..."
        
        games = self.performance_cache['recent_games']
        
        # Analyze tactical patterns
        total_blunders = sum(g['summary']['blunders'] for g in games)
        total_mistakes = sum(g['summary']['mistakes'] for g in games)
        total_moves = sum(g['summary']['total_moves'] for g in games)
        
        # Analyze when blunders occur
        blunder_timing = []
        for game in games:
            for mistake in game['mistakes']:
                if mistake['type'] == 'blunder':
                    blunder_timing.append(mistake['move_number'])
        
        response = "**Tactical Performance Analysis**\n\n"
        response += f"❌ **Total Blunders**: {total_blunders} across {len(games)} games\n"
        response += f"⚠️ **Total Mistakes**: {total_mistakes} across {len(games)} games\n"
        response += f"📊 **Blunder Rate**: {(total_blunders/total_moves*1000):.1f} per 1000 moves\n\n"
        
        # Analyze timing
        if blunder_timing:
            avg_blunder_move = sum(blunder_timing) / len(blunder_timing)
            response += f"🎯 **Average Blunder Move**: {avg_blunder_move:.1f}\n"
            
            # Categorize by game phase
            opening_blunders = len([t for t in blunder_timing if t <= 10])
            middlegame_blunders = len([t for t in blunder_timing if 10 < t <= 25])
            endgame_blunders = len([t for t in blunder_timing if t > 25])
            
            response += f"📈 **Blunders by Phase**:\n"
            response += f"• Opening: {opening_blunders}\n"
            response += f"• Middlegame: {middlegame_blunders}\n"
            response += f"• Endgame: {endgame_blunders}\n\n"
        
        # Provide advice
        if total_blunders > len(games):
            response += "💡 **GM Advice**: You're blundering more than once per game on average.\n"
            response += "🎯 **Training Focus**: Daily tactical puzzles (10-15 minutes)\n"
            response += "📚 **Study**: 'Chess Tactics for Champions' by Susan Polgar\n"
        elif total_blunders > 0:
            response += "👍 **GM Advice**: Blunders are under control but can be reduced.\n"
            response += "🎯 **Training Focus**: Pattern recognition exercises\n"
        else:
            response += "🌟 **GM Advice**: Excellent tactical discipline!\n"
            response += "🎯 **Training Focus**: Advanced calculation techniques\n"
        
        return response
    
    def _answer_tournament_question(self, question: str) -> str:
        """Answer questions about tournament performance"""
        try:
            # Fetch tournament games
            tournament_games = self.tournament_analyzer.fetch_tournament_games(
                self.username, max_games=30, tournament_only=True
            )
            
            if not tournament_games:
                return "I couldn't find any tournament games to analyze. Make sure you've played in tournaments."
            
            # Analyze tournament performance
            wins = sum(1 for g in tournament_games if self._get_user_result(g) == 'win')
            losses = sum(1 for g in tournament_games if self._get_user_result(g) == 'loss')
            draws = sum(1 for g in tournament_games if self._get_user_result(g) == 'draw')
            
            win_rate = (wins / len(tournament_games) * 100) if tournament_games else 0
            
            response = "**Tournament Performance Analysis**\n\n"
            response += f"🏆 **Tournament Games**: {len(tournament_games)}\n"
            response += f"📊 **Record**: {wins}-{losses}-{draws}\n"
            response += f"📈 **Win Rate**: {win_rate:.1f}%\n\n"
            
            # Compare with overall performance
            if self.performance_cache.get('recent_games'):
                overall_wr = self._calculate_overall_win_rate()
                if win_rate > overall_wr + 5:
                    response += "🌟 **Excellent**: You perform better in tournaments than casual games!\n"
                elif win_rate < overall_wr - 5:
                    response += "⚠️ **Note**: Tournament performance is lower than casual play.\n"
                    response += "💡 **GM Advice**: Tournament pressure affects you. Practice stress management.\n"
                else:
                    response += "📊 **Consistent**: Tournament performance matches your overall level.\n"
            
            return response
            
        except Exception as e:
            return f"I encountered an error analyzing tournament performance: {str(e)}"
    
    def _answer_recent_form_question(self, question: str) -> str:
        """Answer questions about recent form"""
        if not self.performance_cache.get('recent_games'):
            return "Let me analyze your recent games to check your current form..."
        
        games = self.performance_cache['recent_games']
        
        # Split into recent (last 5) and older (previous 15)
        recent_games = games[:5] if len(games) >= 5 else games
        older_games = games[5:20] if len(games) > 5 else []
        
        def calculate_win_rate(game_list):
            if not game_list:
                return 0
            wins = sum(1 for g in game_list if self._get_user_result_from_analysis(g) == 'win')
            return (wins / len(game_list)) * 100
        
        def calculate_accuracy(game_list):
            if not game_list:
                return 0
            return sum(g['summary']['accuracy'] for g in game_list) / len(game_list)
        
        recent_wr = calculate_win_rate(recent_games)
        older_wr = calculate_win_rate(older_games) if older_games else recent_wr
        recent_acc = calculate_accuracy(recent_games)
        older_acc = calculate_accuracy(older_games) if older_games else recent_acc
        
        response = "**Recent Form Analysis**\n\n"
        response += f"📅 **Last 5 Games**: {recent_wr:.1f}% win rate, {recent_acc:.1f}% accuracy\n"
        
        if older_games:
            response += f"📊 **Previous 15 Games**: {older_wr:.1f}% win rate, {older_acc:.1f}% accuracy\n\n"
            
            # Compare trends
            wr_trend = recent_wr - older_wr
            acc_trend = recent_acc - older_acc
            
            if wr_trend > 10:
                response += "📈 **Win Rate**: Improving significantly! (+{:.1f}%)\n".format(wr_trend)
            elif wr_trend < -10:
                response += "📉 **Win Rate**: Declining recently. (-{:.1f}%)\n".format(abs(wr_trend))
            else:
                response += "➡️ **Win Rate**: Stable\n"
            
            if acc_trend > 5:
                response += "🎯 **Accuracy**: Getting sharper! (+{:.1f}%)\n".format(acc_trend)
            elif acc_trend < -5:
                response += "⚠️ **Accuracy**: Dropping recently. (-{:.1f}%)\n".format(abs(acc_trend))
            else:
                response += "➡️ **Accuracy**: Consistent\n"
        
        return response
    
    def _answer_weaknesses_question(self, question: str) -> str:
        """Answer questions about weaknesses"""
        if not self.performance_cache.get('recent_games'):
            return "Let me analyze your games to identify areas for improvement..."
        
        games = self.performance_cache['recent_games']
        
        # Analyze various weakness indicators
        total_blunders = sum(g['summary']['blunders'] for g in games)
        total_mistakes = sum(g['summary']['mistakes'] for g in games)
        avg_accuracy = sum(g['summary']['accuracy'] for g in games) / len(games)
        
        # Identify specific weakness patterns
        weaknesses = []
        
        if total_blunders > len(games):
            weaknesses.append("Tactical blunders - you're blundering more than once per game")
        
        if avg_accuracy < 80:
            weaknesses.append("Overall accuracy - below 80% indicates room for improvement")
        
        if total_mistakes > len(games) * 2:
            weaknesses.append("Consistency - too many mistakes affecting game quality")
        
        # Analyze time control performance if available
        time_control_issues = self._analyze_time_control_weaknesses(games)
        if time_control_issues:
            weaknesses.extend(time_control_issues)
        
        response = "**Areas for Improvement**\n\n"
        
        if weaknesses:
            for i, weakness in enumerate(weaknesses, 1):
                response += f"{i}. {weakness}\n"
        else:
            response = "🌟 **Great News**: I don't see any major weaknesses in your recent games!\n"
            response += "Keep up the good work and focus on fine-tuning your skills.\n"
            return response
        
        response += "\n💡 **GM Recommendations**:\n"
        
        if "Tactical blunders" in str(weaknesses):
            response += "• Daily tactical puzzles (chess.com, lichess puzzles)\n"
            response += "• '1001 Chess Exercises for Beginners' by Franco Masetti\n"
        
        if "accuracy" in str(weaknesses):
            response += "• Slower, more careful calculation\n"
            response += "• Double-check moves before playing\n"
        
        if "Consistency" in str(weaknesses):
            response += "• Regular practice schedule\n"
            response += "• Focus on maintaining concentration\n"
        
        return response
    
    def _answer_strengths_question(self, question: str) -> str:
        """Answer questions about strengths"""
        if not self.performance_cache.get('recent_games'):
            return "Let me analyze your games to identify your strengths..."
        
        games = self.performance_cache['recent_games']
        
        # Analyze strength indicators
        total_blunders = sum(g['summary']['blunders'] for g in games)
        avg_accuracy = sum(g['summary']['accuracy'] for g in games) / len(games)
        win_rate = self._calculate_overall_win_rate()
        
        strengths = []
        
        if total_blunders <= len(games) // 2:
            strengths.append("Tactical discipline - you avoid blunders well")
        
        if avg_accuracy >= 85:
            strengths.append("High accuracy - precise and careful play")
        
        if win_rate >= 60:
            strengths.append("Strong results - consistent winning performance")
        
        if avg_accuracy >= 80 and total_blunders <= len(games):
            strengths.append("Solid foundation - good balance of accuracy and safety")
        
        response = "**Your Chess Strengths**\n\n"
        
        if strengths:
            for i, strength in enumerate(strengths, 1):
                response += f"🌟 {strength}\n"
        else:
            response = "Keep playing more games so I can better identify your strengths!\n"
            return response
        
        response += "\n💡 **GM Advice**: Build on these strengths while working on other areas.\n"
        
        # Add specific recommendations based on strengths
        if "Tactical discipline" in str(strengths):
            response += "🎯 **Next Level**: Test your tactics in more complex positions\n"
        
        if "High accuracy" in str(strengths):
            response += "🎯 **Next Level**: Play faster time controls to challenge your precision\n"
        
        if "Strong results" in str(strengths):
            response += "🎯 **Next Level**: Compete against stronger opponents\n"
        
        return response
    
    def _answer_time_control_question(self, question: str) -> str:
        """Answer questions about time control performance"""
        if not self.performance_cache.get('recent_games'):
            return "Let me analyze your games across different time controls..."
        
        games = self.performance_cache['recent_games']
        
        # Group by time control
        time_control_stats = {}
        
        for game in games:
            tc = game['game_info'].get('time_control', 'Unknown')
            if tc not in time_control_stats:
                time_control_stats[tc] = {'games': 0, 'wins': 0}
            
            time_control_stats[tc]['games'] += 1
            if self._get_user_result_from_analysis(game) == 'win':
                time_control_stats[tc]['wins'] += 1
        
        response = "**Time Control Performance**\n\n"
        
        for tc, stats in time_control_stats.items():
            if stats['games'] >= 3:  # Only show with sufficient data
                win_rate = (stats['wins'] / stats['games']) * 100
                response += f"⏱️ **{tc}**: {stats['games']} games, {win_rate:.1f}% win rate\n"
        
        # Identify best and worst time controls
        valid_tcs = {tc: stats for tc, stats in time_control_stats.items() if stats['games'] >= 3}
        
        if valid_tcs:
            best_tc = max(valid_tcs.items(), key=lambda x: x[1]['wins'] / x[1]['games'])
            worst_tc = min(valid_tcs.items(), key=lambda x: x[1]['wins'] / x[1]['games'])
            
            best_wr = (best_tc[1]['wins'] / best_tc[1]['games']) * 100
            worst_wr = (worst_tc[1]['wins'] / worst_tc[1]['games']) * 100
            
            response += f"\n🌟 **Best Time Control**: {best_tc[0]} ({best_wr:.1f}% win rate)\n"
            response += f"⚠️ **Needs Work**: {worst_tc[0]} ({worst_wr:.1f}% win rate)\n"
        
        return response
    
    def _answer_recommendations_question(self, question: str) -> str:
        """Provide personalized recommendations"""
        if not self.performance_cache.get('recent_games'):
            return "Let me analyze your games first to give personalized recommendations..."
        
        games = self.performance_cache['recent_games']
        
        # Generate comprehensive recommendations
        recommendations = []
        
        # Based on recent performance
        avg_accuracy = sum(g['summary']['accuracy'] for g in games) / len(games)
        total_blunders = sum(g['summary']['blunders'] for g in games)
        win_rate = self._calculate_overall_win_rate()
        
        if avg_accuracy < 80:
            recommendations.append({
                'priority': 'High',
                'area': 'Accuracy',
                'action': 'Practice tactical puzzles daily (15-20 minutes)',
                'reason': 'Your accuracy is below 80%, indicating room for improvement'
            })
        
        if total_blunders > len(games):
            recommendations.append({
                'priority': 'High',
                'area': 'Tactics',
                'action': 'Focus on blunder prevention - double-check critical moves',
                'reason': 'You\'re averaging more than one blunder per game'
            })
        
        if win_rate < 50:
            recommendations.append({
                'priority': 'Medium',
                'area': 'Strategy',
                'action': 'Study fundamental endgames and opening principles',
                'reason': 'Below 50% win rate suggests need for strategic improvement'
            })
        
        if not recommendations:
            recommendations.append({
                'priority': 'Maintenance',
                'area': 'All Areas',
                'action': 'Continue current training regimen, gradually increase difficulty',
                'reason': 'Your performance is solid - focus on consistency'
            })
        
        # Format response
        response = "**Personalized Training Recommendations**\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            response += f"{i}. **{rec['area']}** (Priority: {rec['priority']})\n"
            response += f"   📋 Action: {rec['action']}\n"
            response += f"   💡 Why: {rec['reason']}\n\n"
        
        response += "📚 **GM Recommended Resources**:\n"
        response += "• Books: 'My System' by Aron Nimzowitsch\n"
        response += "• Training: chess.com/learn, lichess.org/training\n"
        response += "• Analysis: Review your games with this GM Agent regularly!\n"
        
        return response
    
    def _answer_general_question(self, question: str) -> str:
        """Answer general chess questions"""
        question_lower = question.lower()
        
        # Check for specific topics
        if 'how to improve' in question_lower or 'get better' in question_lower:
            return self._answer_recommendations_question(question)
        
        elif 'rating' in question_lower:
            return self._answer_overall_performance(question)
        
        elif 'advice' in question_lower or 'suggest' in question_lower:
            return self._answer_recommendations_question(question)
        
        else:
            return ("I'm here to help analyze your chess performance! You can ask me about:\n\n"
                   "• Overall performance and rating\n"
                   "• Specific opponents and head-to-head records\n"
                   "• Opening performance and recommendations\n"
                   "• Tactical improvements and blunder analysis\n"
                   "• Tournament performance\n"
                   "• Recent form and trends\n"
                   "• Strengths and weaknesses\n"
                   "• Time control performance\n"
                   "• Personalized training recommendations\n\n"
                   "What would you like to know about your chess game?")
    
    # Helper methods
    def _get_user_result(self, game_data: Dict) -> str:
        """Get user's result from game data"""
        white = game_data.get('players', {}).get('white', {}).get('user', {}).get('name', '')
        black = game_data.get('players', {}).get('black', {}).get('user', {}).get('name', '')
        result = game_data.get('status', '')
        
        user_white = white.lower() == self.username.lower()
        
        if result == 'whiteWin' and user_white:
            return 'win'
        elif result == 'blackWin' and not user_white:
            return 'win'
        elif result == 'draw':
            return 'draw'
        else:
            return 'loss'
    
    def _get_user_result_from_analysis(self, game_analysis: Dict) -> str:
        """Get user's result from game analysis"""
        game_info = game_analysis['game_info']
        white = game_info['white']
        black = game_info['black']
        result = game_info['result']
        
        user_white = white.lower() == self.username.lower()
        
        if (result == '1-0' and user_white) or (result == '0-1' and not user_white):
            return 'win'
        elif result == '1/2-1/2':
            return 'draw'
        else:
            return 'loss'
    
    def _calculate_overall_win_rate(self) -> float:
        """Calculate overall win rate from cached games"""
        if not self.performance_cache.get('recent_games'):
            return 0
        
        games = self.performance_cache['recent_games']
        wins = sum(1 for g in games if self._get_user_result_from_analysis(g) == 'win')
        return (wins / len(games)) * 100 if games else 0
    
    def _analyze_time_control_weaknesses(self, games: List[Dict]) -> List[str]:
        """Analyze time control specific weaknesses"""
        time_control_stats = {}
        weaknesses = []
        
        for game in games:
            tc = game['game_info'].get('time_control', 'Unknown')
            if tc not in time_control_stats:
                time_control_stats[tc] = {'games': 0, 'wins': 0, 'blunders': 0}
            
            time_control_stats[tc]['games'] += 1
            if self._get_user_result_from_analysis(game) == 'win':
                time_control_stats[tc]['wins'] += 1
            time_control_stats[tc]['blunders'] += game['summary']['blunders']
        
        # Identify problematic time controls
        for tc, stats in time_control_stats.items():
            if stats['games'] >= 5:  # Only consider with sufficient data
                win_rate = (stats['wins'] / stats['games']) * 100
                blunder_rate = stats['blunders'] / stats['games']
                
                if win_rate < 40:
                    weaknesses.append(f"Poor performance in {tc} time control")
                if blunder_rate > 1.5:
                    weaknesses.append(f"Too many blunders in {tc} time control")
        
        return weaknesses
    
    def get_performance_summary(self) -> str:
        """Get a comprehensive performance summary"""
        return self.ask("How am I performing overall?")
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'chess_analyzer'):
            self.chess_analyzer.close()
        if hasattr(self, 'game_system'):
            self.game_system.cleanup()
