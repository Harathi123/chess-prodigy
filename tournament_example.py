"""
Example usage of tournament and opponent analysis features
"""

import os
from dotenv import load_dotenv
from tournament_main import analyze_specific_opponent, analyze_tournament_games, find_common_blunders
from lichess_client import LichessClient
from chess_analyzer import ChessAnalyzer
from tournament_analyzer import TournamentAnalyzer
from opponent_analyzer import OpponentAnalyzer


def example_tournament_analysis():
    """Example: Analyze tournament games"""
    print("=== Tournament Analysis Example ===")
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    try:
        # Initialize components
        lichess_client = LichessClient(api_token)
        chess_analyzer = ChessAnalyzer(analysis_depth=12, analysis_time=1.5)
        
        # Create tournament analyzer
        tournament_analyzer = TournamentAnalyzer(lichess_client, chess_analyzer)
        
        # Fetch tournament games
        print("Fetching tournament games...")
        games = tournament_analyzer.fetch_tournament_games(username, max_games=20)
        
        if games:
            # Generate tournament report
            report = tournament_analyzer.generate_tournament_report(username)
            print("\n" + report)
            
            # Find common blunders in tournament games
            common_blunders = tournament_analyzer.find_common_blunders(min_occurrences=2)
            
            if common_blunders['move_patterns']:
                print("\nCOMMON TOURNAMENT BLUNDERS:")
                for move, occurrences in list(common_blunders['move_patterns'].items())[:5]:
                    avg_loss = sum(o['eval_change'] for o in occurrences) / len(occurrences)
                    print(f"- {move}: {len(occurrences)} times, avg {avg_loss:.1f} cp loss")
        else:
            print("No tournament games found")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        chess_analyzer.close()


def example_opponent_analysis():
    """Example: Analyze specific opponent"""
    print("\n=== Opponent Analysis Example ===")
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    # Example opponent (replace with actual opponent)
    opponent = "MagnusCarlsen"  # Replace with real opponent username
    
    try:
        # Initialize components
        lichess_client = LichessClient(api_token)
        chess_analyzer = ChessAnalyzer(analysis_depth=12, analysis_time=1.5)
        
        # Create opponent analyzer
        opponent_analyzer = OpponentAnalyzer(lichess_client, chess_analyzer)
        
        # Analyze opponent
        print(f"Analyzing games against {opponent}...")
        analysis = opponent_analyzer.analyze_opponent_comprehensive(
            username=username,
            opponent=opponent,
            max_games=20
        )
        
        if 'error' not in analysis:
            # Generate detailed report
            report = opponent_analyzer.generate_opponent_report(analysis)
            print("\n" + report)
        else:
            print(f"Could not analyze opponent: {analysis['error']}")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        chess_analyzer.close()


def example_common_blunders():
    """Example: Find common blunders across all games"""
    print("\n=== Common Blunders Analysis Example ===")
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    try:
        # Initialize components
        lichess_client = LichessClient(api_token)
        chess_analyzer = ChessAnalyzer(analysis_depth=10, analysis_time=1.0)
        
        # Create tournament analyzer (works for all games)
        tournament_analyzer = TournamentAnalyzer(lichess_client, chess_analyzer)
        
        # Fetch games
        print("Fetching games for blunder analysis...")
        games = tournament_analyzer.fetch_tournament_games(username, max_games=50, tournament_only=False)
        
        if games:
            # Find common blunders
            common_blunders = tournament_analyzer.find_common_blunders(min_occurrences=3)
            
            print("\nMOST COMMON BLUNDER MOVES:")
            if common_blunders['move_patterns']:
                sorted_moves = sorted(common_blunders['move_patterns'].items(), 
                                    key=lambda x: len(x[1]), reverse=True)
                
                for move, occurrences in sorted_moves[:10]:
                    avg_loss = sum(o['eval_change'] for o in occurrences) / len(occurrences)
                    print(f"{len(occurrences):2d}. {move}: avg {avg_loss:6.1f} cp loss")
            else:
                print("No common blunder patterns found")
            
            print("\nOPENING-SPECIFIC BLUNDERS:")
            if common_blunders['opening_blunders']:
                for opening, blunders in list(common_blunders['opening_blunders'].items())[:5]:
                    avg_move = sum(b['move_number'] for b in blunders) / len(blunders)
                    avg_loss = sum(b['eval_change'] for b in blunders) / len(blunders)
                    print(f"- {opening}: {len(blunders)} blunders, avg move {avg_move:.1f}, avg loss {avg_loss:.1f} cp")
            else:
                print("No opening-specific blunder patterns found")
        else:
            print("No games found for analysis")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        chess_analyzer.close()


def example_head_to_head_comparison():
    """Example: Compare performance against multiple opponents"""
    print("\n=== Head-to-Head Comparison Example ===")
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    # List of opponents to compare (replace with actual opponents)
    opponents = [
        "opponent1",  # Replace with real usernames
        "opponent2",
        "opponent3"
    ]
    
    try:
        # Initialize components
        lichess_client = LichessClient(api_token)
        chess_analyzer = ChessAnalyzer(analysis_depth=10, analysis_time=1.0)
        
        opponent_analyzer = OpponentAnalyzer(lichess_client, chess_analyzer)
        
        print("Comparing performance against multiple opponents...")
        
        results = []
        for opponent in opponents:
            print(f"\nAnalyzing {opponent}...")
            analysis = opponent_analyzer.analyze_opponent_comprehensive(
                username=username,
                opponent=opponent,
                max_games=10
            )
            
            if 'error' not in analysis:
                h2h = analysis['head_to_head']
                results.append({
                    'opponent': opponent,
                    'games': h2h['total_games'],
                    'wins': h2h['overall_record']['wins'],
                    'losses': h2h['overall_record']['losses'],
                    'draws': h2h['overall_record']['draws'],
                    'win_rate': h2h['win_rate']
                })
            else:
                print(f"Could not analyze {opponent}: {analysis['error']}")
        
        # Display comparison table
        if results:
            print("\n" + "="*60)
            print("HEAD-TO-HEAD COMPARISON")
            print("="*60)
            print(f"{'Opponent':<15} {'Games':<6} {'W-L-D':<9} {'Win Rate':<9}")
            print("-"*60)
            
            for result in sorted(results, key=lambda x: x['win_rate'], reverse=True):
                wld = f"{result['wins']}-{result['losses']}-{result['draws']}"
                print(f"{result['opponent']:<15} {result['games']:<6} {wld:<9} {result['win_rate']:<9.1f}%")
            
            # Find opponents you struggle against
            struggling = [r for r in results if r['win_rate'] < 40]
            if struggling:
                print(f"\nOpponents you struggle against (win rate < 40%):")
                for result in struggling:
                    print(f"- {result['opponent']}: {result['win_rate']:.1f}% win rate")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        chess_analyzer.close()


if __name__ == "__main__":
    print("Tournament and Opponent Analysis Examples")
    print("=" * 50)
    
    # Run examples (comment out as needed)
    
    # Example 1: Tournament analysis
    example_tournament_analysis()
    
    # Example 2: Specific opponent analysis
    # example_opponent_analysis()
    
    # Example 3: Common blunders analysis
    # example_common_blunders()
    
    # Example 4: Head-to-head comparison
    # example_head_to_head_comparison()
    
    print("\nExamples completed!")
    print("Modify this file to run specific examples or add your own opponents.")
