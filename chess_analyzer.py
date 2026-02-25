"""
Chess Game Analyzer using Stockfish engine
"""

import chess
import chess.engine
import chess.pgn
from stockfish import Stockfish
import numpy as np
from typing import List, Dict, Tuple, Optional
import time
import os


class ChessAnalyzer:
    """Chess game analysis engine using Stockfish"""
    
    def __init__(self, stockfish_path: Optional[str] = None, depth: int = 15, time_limit: float = 2.0):
        """
        Initialize chess analyzer
        
        Args:
            stockfish_path: Path to Stockfish executable (auto-detects if None)
            depth: Analysis depth
            time_limit: Time limit per position analysis
        """
        self.depth = depth
        self.time_limit = time_limit
        self.stockfish_path = stockfish_path
        resolved_path = stockfish_path or "stockfish"
        
        # Initialize Stockfish
        try:
            self.stockfish = Stockfish(path=resolved_path)
            self.stockfish.set_depth(depth)
        except Exception as e:
            raise Exception(f"Failed to initialize Stockfish: {e}")
        
        # Initialize UCI engine for advanced features
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(
                resolved_path
            )
        except Exception as e:
            print(f"Warning: Could not initialize UCI engine: {e}")
            self.engine = None
    
    def analyze_position(self, fen: str) -> Dict:
        """
        Analyze a single position
        
        Args:
            fen: FEN string of the position
            
        Returns:
            Dictionary with analysis results
        """
        self.stockfish.set_fen_position(fen)
        
        # Get evaluation
        evaluation = self.stockfish.get_evaluation()
        best_move = self.stockfish.get_best_move()
        top_moves = self.stockfish.get_top_moves(5)
        
        return {
            'fen': fen,
            'evaluation': evaluation,
            'best_move': best_move,
            'top_moves': top_moves,
            'depth': self.depth
        }
    
    def analyze_game(self, game: chess.pgn.Game, 
                    analyze_mistakes: bool = True,
                    analyze_opening: bool = True) -> Dict:
        """
        Analyze a complete game
        
        Args:
            game: Chess game object
            analyze_mistakes: Whether to analyze for mistakes
            analyze_opening: Whether to analyze opening
            
        Returns:
            Dictionary with complete game analysis
        """
        board = game.board()
        analysis = {
            'game_info': self._extract_game_info(game),
            'moves_analysis': [],
            'mistakes': [],
            'opening_analysis': {},
            'summary': {}
        }
        
        move_number = 0
        evaluations = []
        
        for move in game.mainline_moves():
            move_number += 1
            board.push(move)
            
            # Analyze current position
            position_analysis = self.analyze_position(board.fen())
            position_analysis['move_number'] = move_number
            position_analysis['move'] = move.uci()
            
            analysis['moves_analysis'].append(position_analysis)
            
            # Store evaluation for trend analysis
            if position_analysis['evaluation']['type'] == 'cp':
                evaluations.append(position_analysis['evaluation']['value'])
            else:
                # Convert mate score to centipawns for trend analysis
                mate_score = position_analysis['evaluation']['value']
                cp_value = 10000 if mate_score > 0 else -10000
                evaluations.append(cp_value)
        
        # Analyze mistakes
        if analyze_mistakes:
            analysis['mistakes'] = self._find_mistakes(analysis['moves_analysis'])
        
        # Analyze opening
        if analyze_opening:
            analysis['opening_analysis'] = self._analyze_opening(game)
        
        # Generate summary
        analysis['summary'] = self._generate_summary(analysis, evaluations)
        
        return analysis
    
    def _find_mistakes(self, moves_analysis: List[Dict]) -> List[Dict]:
        """Find mistakes, blunders, and inaccuracies in the game"""
        mistakes = []
        
        for i, move_analysis in enumerate(moves_analysis):
            if i == 0:
                continue
            
            prev_eval = moves_analysis[i-1]['evaluation']
            curr_eval = move_analysis['evaluation']
            
            # Calculate evaluation change
            eval_change = self._calculate_eval_change(prev_eval, curr_eval)
            
            # Categorize mistakes based on evaluation change
            mistake_type = None
            if abs(eval_change) >= 300:
                mistake_type = "blunder"
            elif abs(eval_change) >= 150:
                mistake_type = "mistake"
            elif abs(eval_change) >= 50:
                mistake_type = "inaccuracy"
            
            if mistake_type:
                mistakes.append({
                    'move_number': move_analysis['move_number'],
                    'move': move_analysis['move'],
                    'type': mistake_type,
                    'eval_change': eval_change,
                    'evaluation_before': prev_eval,
                    'evaluation_after': curr_eval,
                    'fen': move_analysis['fen']
                })
        
        return mistakes
    
    def _calculate_eval_change(self, prev_eval: Dict, curr_eval: Dict) -> float:
        """Calculate the change in evaluation between two positions"""
        if prev_eval['type'] == 'cp' and curr_eval['type'] == 'cp':
            return curr_eval['value'] - prev_eval['value']
        elif prev_eval['type'] == 'mate' or curr_eval['type'] == 'mate':
            # Large change for mate situations
            return 1000.0
        else:
            return 0.0
    
    def _analyze_opening(self, game: chess.pgn.Game) -> Dict:
        """Analyze the opening of the game"""
        opening_info = {}
        
        # Extract opening info from game headers
        headers = game.headers
        opening_info['opening'] = headers.get('Opening', 'Unknown')
        opening_info['variation'] = headers.get('Variation', '')
        opening_info['eco'] = headers.get('ECO', '')
        
        # Analyze first few moves for opening patterns
        board = game.board()
        opening_moves = []
        
        for i, move in enumerate(game.mainline_moves()):
            if i >= 10:  # Analyze first 10 moves
                break
            board.push(move)
            opening_moves.append(move.uci())
        
        opening_info['moves'] = opening_moves
        opening_info['book_moves'] = self._check_opening_book(opening_moves)
        
        return opening_info
    
    def _check_opening_book(self, moves: List[str]) -> int:
        """Check how many moves are in opening book (simplified)"""
        # This is a simplified version - in practice, you'd use an opening book
        # For now, we'll assume first 5 moves are typically book moves
        return min(5, len(moves))
    
    def _extract_game_info(self, game: chess.pgn.Game) -> Dict:
        """Extract basic game information"""
        headers = game.headers
        return {
            'white': headers.get('White', 'Unknown'),
            'black': headers.get('Black', 'Unknown'),
            'white_elo': headers.get('WhiteElo', ''),
            'black_elo': headers.get('BlackElo', ''),
            'result': headers.get('Result', '*'),
            'time_control': headers.get('TimeControl', ''),
            'date': headers.get('Date', ''),
            'event': headers.get('Event', '')
        }
    
    def _generate_summary(self, analysis: Dict, evaluations: List[float]) -> Dict:
        """Generate a summary of the game analysis"""
        mistakes = analysis['mistakes']
        
        summary = {
            'total_moves': len(analysis['moves_analysis']),
            'blunders': len([m for m in mistakes if m['type'] == 'blunder']),
            'mistakes': len([m for m in mistakes if m['type'] == 'mistake']),
            'inaccuracies': len([m for m in mistakes if m['type'] == 'inaccuracy']),
            'accuracy': self._calculate_accuracy(evaluations),
            'average_centipawn_loss': self._calculate_avg_centipawn_loss(mistakes),
            'critical_moments': self._find_critical_moments(analysis['moves_analysis'])
        }
        
        return summary
    
    def _calculate_accuracy(self, evaluations: List[float]) -> float:
        """Calculate overall accuracy percentage"""
        if not evaluations:
            return 0.0
        
        # Simple accuracy calculation based on evaluation stability
        changes = [abs(evaluations[i] - evaluations[i-1]) for i in range(1, len(evaluations))]
        avg_change = np.mean(changes) if changes else 0
        
        # Convert to accuracy (lower changes = higher accuracy)
        accuracy = max(0, 100 - (avg_change / 10))
        return round(accuracy, 1)
    
    def _calculate_avg_centipawn_loss(self, mistakes: List[Dict]) -> float:
        """Calculate average centipawn loss from mistakes"""
        if not mistakes:
            return 0.0
        
        total_loss = sum(abs(m['eval_change']) for m in mistakes)
        return round(total_loss / len(mistakes), 1)
    
    def _find_critical_moments(self, moves_analysis: List[Dict]) -> List[Dict]:
        """Find critical moments in the game"""
        critical_moments = []
        
        for i, move_analysis in enumerate(moves_analysis):
            eval_data = move_analysis['evaluation']
            
            # Check for large evaluation swings
            if eval_data['type'] == 'cp' and abs(eval_data['value']) > 200:
                critical_moments.append({
                    'move_number': move_analysis['move_number'],
                    'type': 'significant_advantage',
                    'evaluation': eval_data['value'],
                    'description': f"{'White' if eval_data['value'] > 0 else 'Black'} gains significant advantage"
                })
            elif eval_data['type'] == 'mate':
                critical_moments.append({
                    'move_number': move_analysis['move_number'],
                    'type': 'mate_threat',
                    'mate_in': eval_data['value'],
                    'description': f"Mate in {abs(eval_data['value'])} for {'White' if eval_data['value'] > 0 else 'Black'}"
                })
        
        return critical_moments
    
    def generate_feedback(self, analysis: Dict) -> str:
        """Generate human-readable feedback from analysis"""
        feedback = []
        game_info = analysis['game_info']
        summary = analysis['summary']
        mistakes = analysis['mistakes']
        
        # Game overview
        feedback.append(f"Game Analysis: {game_info['white']} vs {game_info['black']}")
        feedback.append(f"Result: {game_info['result']}")
        feedback.append(f"Time Control: {game_info['time_control']}")
        feedback.append("")
        
        # Performance summary
        feedback.append("Performance Summary:")
        feedback.append(f"- Total Moves: {summary['total_moves']}")
        feedback.append(f"- Accuracy: {summary['accuracy']}%")
        feedback.append(f"- Blunders: {summary['blunders']}")
        feedback.append(f"- Mistakes: {summary['mistakes']}")
        feedback.append(f"- Inaccuracies: {summary['inaccuracies']}")
        feedback.append(f"- Average Centipawn Loss: {summary['average_centipawn_loss']}")
        feedback.append("")
        
        # Key mistakes
        if mistakes:
            feedback.append("Key Mistakes:")
            for mistake in mistakes[:3]:  # Show top 3 mistakes
                feedback.append(f"- Move {mistake['move_number']}: {mistake['move']} ({mistake['type']}, {mistake['eval_change']:.1f} cp loss)")
            feedback.append("")
        
        # Critical moments
        if summary['critical_moments']:
            feedback.append("Critical Moments:")
            for moment in summary['critical_moments'][:3]:
                feedback.append(f"- Move {moment['move_number']}: {moment['description']}")
            feedback.append("")
        
        # Recommendations
        feedback.append("Recommendations:")
        if summary['blunders'] > 0:
            feedback.append("- Focus on tactical calculation to avoid blunders")
        if summary['mistakes'] > 2:
            feedback.append("- Work on positional understanding to reduce mistakes")
        if summary['accuracy'] < 80:
            feedback.append("- Practice more puzzles to improve overall accuracy")
        feedback.append("- Review critical moments to learn from key positions")
        
        return "\n".join(feedback)
    
    def close(self):
        """Clean up resources"""
        if self.engine:
            self.engine.quit()
