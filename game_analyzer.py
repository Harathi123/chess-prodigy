"""
Main Game Analysis System - Combines Lichess client and Chess Analyzer
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

from lichess_client import LichessClient, GameFilter
from chess_analyzer import ChessAnalyzer
import chess.pgn
import io


class GameAnalysisSystem:
    """Main system for analyzing chess games from Lichess"""
    
    def __init__(self, api_token: str, username: str, 
                 stockfish_path: Optional[str] = None,
                 analysis_depth: int = 15,
                 analysis_time: float = 2.0):
        """
        Initialize the game analysis system
        
        Args:
            api_token: Lichess API token
            username: Lichess username to analyze
            stockfish_path: Path to Stockfish executable
            analysis_depth: Depth for engine analysis
            analysis_time: Time limit per position
        """
        self.username = username
        self.lichess_client = LichessClient(api_token)
        self.analyzer = ChessAnalyzer(
            stockfish_path=stockfish_path,
            depth=analysis_depth,
            time_limit=analysis_time
        )
        
        # Storage for analyses
        self.analyses = []
        self.user_profile = None
        self.rating_history = None
    
    def load_user_data(self):
        """Load user profile and rating history"""
        try:
            self.user_profile = self.lichess_client.get_user_profile(self.username)
            self.rating_history = self.lichess_client.get_user_rating_history(self.username)
            print(f"Loaded data for {self.username}")
        except Exception as e:
            print(f"Error loading user data: {e}")
    
    def analyze_recent_games(self, num_games: int = 10, 
                           time_control: Optional[str] = None,
                           days_back: Optional[int] = None) -> List[Dict]:
        """
        Analyze recent games
        
        Args:
            num_games: Number of games to analyze
            time_control: Filter by time control
            days_back: Only analyze games from last N days
            
        Returns:
            List of game analyses
        """
        print(f"Fetching {num_games} recent games for {self.username}...")
        
        try:
            # Fetch games
            games = list(self.lichess_client.get_games_by_username(
                self.username,
                max_games=num_games,
                time_control=time_control,
                days_back=days_back
            ))
            
            print(f"Found {len(games)} games. Analyzing...")
            
            # Analyze each game
            analyses = []
            for i, game_data in enumerate(games):
                print(f"Analyzing game {i+1}/{len(games)}...")
                
                try:
                    # Parse PGN
                    pgn_text = game_data.get('pgn', '')
                    if not pgn_text:
                        print(f"Warning: No PGN data for game {i+1}")
                        continue
                    
                    game = self.lichess_client.parse_pgn_game(pgn_text)
                    
                    # Analyze game
                    analysis = self.analyzer.analyze_game(game)
                    analysis['raw_data'] = game_data
                    
                    analyses.append(analysis)
                    
                except Exception as e:
                    print(f"Error analyzing game {i+1}: {e}")
                    continue
            
            self.analyses.extend(analyses)
            print(f"Successfully analyzed {len(analyses)} games")
            
            return analyses
            
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []
    
    def analyze_single_game(self, game_id: str) -> Optional[Dict]:
        """Analyze a single game by ID"""
        try:
            print(f"Fetching game {game_id}...")
            game_data = self.lichess_client.get_game_by_id(game_id)
            
            pgn_text = game_data.get('pgn', '')
            if not pgn_text:
                print("No PGN data found for this game")
                return None
            
            game = self.lichess_client.parse_pgn_game(pgn_text)
            analysis = self.analyzer.analyze_game(game)
            analysis['raw_data'] = game_data
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing game {game_id}: {e}")
            return None
    
    def generate_overall_report(self) -> str:
        """Generate overall performance report"""
        if not self.analyses:
            return "No games analyzed yet. Run analyze_recent_games() first."
        
        report = []
        report.append("=" * 50)
        report.append(f"CHESS ANALYSIS REPORT FOR {self.username.upper()}")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Games Analyzed: {len(self.analyses)}")
        report.append("")
        
        # User profile info
        if self.user_profile:
            report.append("PLAYER PROFILE:")
            report.append(f"Username: {self.user_profile.get('username', 'N/A')}")
            report.append(f"Joined: {self.user_profile.get('createdAt', 'N/A')}")
            report.append(f"Play Time: {self.user_profile.get('playTime', {}).get('total', 'N/A')} minutes")
            
            # Rating info
            perfs = self.user_profile.get('perfs', {})
            for time_control in ['blitz', 'rapid', 'classical', 'bullet']:
                if time_control in perfs:
                    rating = perfs[time_control].get('rating', 'N/A')
                    report.append(f"{time_control.capitalize()} Rating: {rating}")
            report.append("")
        
        # Overall statistics
        report.append("OVERALL PERFORMANCE:")
        stats = self._calculate_overall_stats()
        for key, value in stats.items():
            report.append(f"{key.replace('_', ' ').title()}: {value}")
        report.append("")
        
        # Common mistakes
        report.append("COMMON MISTAKES:")
        common_mistakes = self._find_common_mistakes()
        for mistake_type, count in common_mistakes.items():
            report.append(f"- {mistake_type.title()}: {count}")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            report.append(f"- {rec}")
        report.append("")
        
        # Recent games summary
        report.append("RECENT GAMES SUMMARY:")
        for i, analysis in enumerate(self.analyses[-5:]):  # Last 5 games
            game_info = analysis['game_info']
            summary = analysis['summary']
            report.append(f"{i+1}. {game_info['white']} vs {game_info['black']} - {game_info['result']}")
            report.append(f"   Accuracy: {summary['accuracy']}%, Blunders: {summary['blunders']}")
        
        return "\n".join(report)
    
    def _calculate_overall_stats(self) -> Dict:
        """Calculate overall statistics across all analyzed games"""
        if not self.analyses:
            return {}
        
        total_games = len(self.analyses)
        total_moves = sum(a['summary']['total_moves'] for a in self.analyses)
        total_blunders = sum(a['summary']['blunders'] for a in self.analyses)
        total_mistakes = sum(a['summary']['mistakes'] for a in self.analyses)
        total_inaccuracies = sum(a['summary']['inaccuracies'] for a in self.analyses)
        
        avg_accuracy = sum(a['summary']['accuracy'] for a in self.analyses) / total_games
        avg_cp_loss = sum(a['summary']['average_centipawn_loss'] for a in self.analyses) / total_games
        
        # Win/loss/draw record
        results = {'1-0': 0, '0-1': 0, '1/2-1/2': 0}
        for analysis in self.analyses:
            result = analysis['game_info']['result']
            if result in results:
                results[result] += 1
        
        return {
            'total_games': total_games,
            'total_moves': total_moves,
            'average_accuracy': f"{avg_accuracy:.1f}%",
            'average_cp_loss': f"{avg_cp_loss:.1f}",
            'total_blunders': total_blunders,
            'total_mistakes': total_mistakes,
            'total_inaccuracies': total_inaccuracies,
            'wins': results['1-0'],
            'losses': results['0-1'],
            'draws': results['1/2-1/2'],
            'win_rate': f"{(results['1-0'] / total_games * 100):.1f}%"
        }
    
    def _find_common_mistakes(self) -> Dict:
        """Find most common types of mistakes"""
        mistake_counts = {'blunder': 0, 'mistake': 0, 'inaccuracy': 0}
        
        for analysis in self.analyses:
            for mistake in analysis['mistakes']:
                mistake_type = mistake['type']
                if mistake_type in mistake_counts:
                    mistake_counts[mistake_type] += 1
        
        return mistake_counts
    
    def _generate_recommendations(self) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        stats = self._calculate_overall_stats()
        
        # Based on blunders
        if stats.get('total_blunders', 0) > stats.get('total_games', 1):
            recommendations.append("Focus on tactical puzzles to reduce blunders")
        
        # Based on accuracy
        avg_acc = float(stats.get('average_accuracy', '0%').rstrip('%'))
        if avg_acc < 75:
            recommendations.append("Work on calculation skills to improve accuracy")
        elif avg_acc < 85:
            recommendations.append("Good accuracy! Focus on positional understanding")
        
        # Based on win rate
        win_rate = float(stats.get('win_rate', '0%').rstrip('%'))
        if win_rate < 40:
            recommendations.append("Study fundamental endgames and opening principles")
        elif win_rate > 60:
            recommendations.append("Excellent results! Challenge stronger opponents")
        
        # Based on mistakes pattern
        common_mistakes = self._find_common_mistakes()
        if common_mistakes['inaccuracy'] > common_mistakes['blunder']:
            recommendations.append("Pay attention to positional details to reduce inaccuracies")
        
        if not recommendations:
            recommendations.append("Continue your current training regimen")
        
        return recommendations
    
    def save_analysis(self, filename: str = None):
        """Save analysis results to file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"chess_analysis_{self.username}_{timestamp}.json"
        
        data = {
            'username': self.username,
            'timestamp': datetime.now().isoformat(),
            'user_profile': self.user_profile,
            'rating_history': self.rating_history,
            'analyses': self.analyses,
            'overall_stats': self._calculate_overall_stats()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Analysis saved to {filename}")
    
    def load_analysis(self, filename: str):
        """Load analysis results from file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.username = data['username']
        self.user_profile = data['user_profile']
        self.rating_history = data['rating_history']
        self.analyses = data['analyses']
        
        print(f"Loaded analysis from {filename}")
    
    def create_visualizations(self, save_path: str = None):
        """Create visualization plots"""
        if not self.analyses:
            print("No data to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Chess Performance Analysis - {self.username}', fontsize=16)
        
        # 1. Accuracy over games
        accuracies = [a['summary']['accuracy'] for a in self.analyses]
        axes[0, 0].plot(range(1, len(accuracies) + 1), accuracies, 'o-')
        axes[0, 0].set_title('Accuracy per Game')
        axes[0, 0].set_xlabel('Game Number')
        axes[0, 0].set_ylabel('Accuracy (%)')
        axes[0, 0].grid(True)
        
        # 2. Mistakes breakdown
        mistake_types = ['blunders', 'mistakes', 'inaccuracies']
        mistake_counts = [sum(a['summary'][m] for a in self.analyses) for m in mistake_types]
        axes[0, 1].bar(mistake_types, mistake_counts, color=['red', 'orange', 'yellow'])
        axes[0, 1].set_title('Total Mistakes by Type')
        axes[0, 1].set_ylabel('Count')
        
        # 3. Results distribution
        results = {'Wins': 0, 'Losses': 0, 'Draws': 0}
        for analysis in self.analyses:
            result = analysis['game_info']['result']
            if result == '1-0':
                results['Wins'] += 1
            elif result == '0-1':
                results['Losses'] += 1
            elif result == '1/2-1/2':
                results['Draws'] += 1
        
        axes[1, 0].pie(results.values(), labels=results.keys(), autopct='%1.1f%%')
        axes[1, 0].set_title('Game Results Distribution')
        
        # 4. Average centipawn loss
        cp_losses = [a['summary']['average_centipawn_loss'] for a in self.analyses]
        axes[1, 1].hist(cp_losses, bins=10, alpha=0.7, edgecolor='black')
        axes[1, 1].set_title('Average Centipawn Loss Distribution')
        axes[1, 1].set_xlabel('Average CP Loss')
        axes[1, 1].set_ylabel('Frequency')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Visualizations saved to {save_path}")
        else:
            plt.show()
    
    def export_to_csv(self, filename: str = None):
        """Export analysis data to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"chess_analysis_{self.username}_{timestamp}.csv"
        
        data = []
        for analysis in self.analyses:
            game_info = analysis['game_info']
            summary = analysis['summary']
            
            row = {
                'Date': game_info.get('date', ''),
                'White': game_info.get('white', ''),
                'Black': game_info.get('black', ''),
                'Result': game_info.get('result', ''),
                'Time_Control': game_info.get('time_control', ''),
                'Total_Moves': summary.get('total_moves', 0),
                'Accuracy': summary.get('accuracy', 0),
                'Blunders': summary.get('blunders', 0),
                'Mistakes': summary.get('mistakes', 0),
                'Inaccuracies': summary.get('inaccuracies', 0),
                'Avg_CP_Loss': summary.get('average_centipawn_loss', 0)
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data exported to {filename}")
    
    def cleanup(self):
        """Clean up resources"""
        self.analyzer.close()
