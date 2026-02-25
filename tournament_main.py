"""
Main application for tournament and opponent-specific analysis
"""

import argparse
import sys
import os
from datetime import datetime

from config import Config
from lichess_client import LichessClient
from chess_analyzer import ChessAnalyzer
from tournament_analyzer import TournamentAnalyzer
from study_analyzer import StudyAnalyzer
from opponent_analyzer import OpponentAnalyzer


def main():
    """Main function for tournament analysis"""
    parser = argparse.ArgumentParser(description='Tournament and Opponent Analysis Tool')
    parser.add_argument('--config', '-c', default='.env', help='Configuration file path')
    parser.add_argument('--username', '-u', help='Lichess username (overrides config)')
    parser.add_argument('--opponent', '-o', help='Specific opponent to analyze')
    parser.add_argument('--tournament', '-t', action='store_true', help='Analyze tournament games only')
    parser.add_argument('--max-games', '-g', type=int, default=50, help='Maximum games to analyze')
    parser.add_argument('--common-blunders', '-b', action='store_true', help='Find common blunders')
    parser.add_argument('--report', '-r', action='store_true', help='Generate detailed report')
    parser.add_argument('--save', '-s', action='store_true', help='Save analysis results')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--no-analysis', action='store_true', help='Skip per-game engine analysis (faster, counts-only report)')
    parser.add_argument('--fast', action='store_true', help='Fast mode: skip engine analysis for quick insights')
    parser.add_argument('--sample', type=int, help='Analyze only N representative games for quick insights')
    parser.add_argument('--study', help='Analyze games from Lichess studies you contribute to')
    parser.add_argument('--study-name', help='Analyze a specific study by name')
    parser.add_argument('--study-id', help='Analyze a specific study by ID')
    parser.add_argument('--max-studies', type=int, default=3, help='Maximum studies to analyze (default 3)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config)
    if not config.validate():
        sys.exit(1)
    
    # Override config with command line arguments
    username = args.username or config.USERNAME
    
    # Initialize components
    try:
        lichess_client = LichessClient(config.LICHESS_API_TOKEN)
        chess_analyzer = ChessAnalyzer(
            stockfish_path=config.get_stockfish_path(),
            depth=config.ANALYSIS_DEPTH,
            time_limit=config.ANALYSIS_TIME
        )
        
        print("Tournament Analysis System initialized")
    except Exception as e:
        print(f"Error initializing system: {e}")
        sys.exit(1)
    
    try:
        if args.interactive:
            interactive_mode(lichess_client, chess_analyzer, username, config)
        elif args.opponent:
            analyze_specific_opponent(lichess_client, chess_analyzer, username, args.opponent, args)
        elif args.tournament:
            analyze_tournament_games(lichess_client, chess_analyzer, username, args)
        elif args.study or args.study_name or args.study_id:
            analyze_study_games(lichess_client, chess_analyzer, username, args)
        elif args.common_blunders:
            find_common_blunders(lichess_client, chess_analyzer, username, args)
        else:
            print("Please specify an analysis mode. Use --help for options.")
            print("Try --interactive for guided analysis.")
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        chess_analyzer.close()


def analyze_specific_opponent(lichess_client, chess_analyzer, username, opponent, args):
    """Analyze games against a specific opponent"""
    print(f"Analyzing games between {username} and {opponent}...")
    
    # Use comprehensive opponent analyzer
    opponent_analyzer = OpponentAnalyzer(lichess_client, chess_analyzer)
    
    analysis = opponent_analyzer.analyze_opponent_comprehensive(
        username=username,
        opponent=opponent,
        max_games=args.max_games
    )
    
    if 'error' in analysis:
        print(f"Error: {analysis['error']}")
        return
    
    # Generate report
    report = opponent_analyzer.generate_opponent_report(analysis)
    print("\n" + report)
    
    # Save analysis if requested
    if args.save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"opponent_analysis_{opponent}_{timestamp}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"\nAnalysis saved to {filename}")


def analyze_tournament_games(lichess_client, chess_analyzer, username, args):
    """Analyze tournament games"""
    print(f"Analyzing tournament games for {username}...")
    
    tournament_analyzer = TournamentAnalyzer(lichess_client, chess_analyzer, no_analysis=args.no_analysis)
    
    # Fetch tournament games
    games = tournament_analyzer.fetch_tournament_games(
        username=username,
        max_games=args.max_games,
        tournament_only=True
    )
    
    if not games:
        print("No tournament games found")
        return
    
    # Analyze opponent patterns (skips engine analysis if --no-analysis)
    opponent_patterns = tournament_analyzer.analyze_opponent_patterns(username)
    
    # Find common blunders (skipped if --no-analysis)
    common_blunders = tournament_analyzer.find_common_blunders() if not args.no_analysis else {'move_patterns': {}, 'position_patterns': {}, 'opening_blunders': {}}
    
    # Generate tournament report
    report = tournament_analyzer.generate_tournament_report(username, no_analysis=args.no_analysis)
    print("\n" + report)
    
    # Show common blunders (only if analysis enabled)
    if not args.no_analysis and common_blunders['move_patterns']:
        print("\nCOMMON BLUNDER PATTERNS:")
        for move, occurrences in list(common_blunders['move_patterns'].items())[:5]:
            avg_loss = sum(o['eval_change'] for o in occurrences) / len(occurrences)
            print(f"- {move}: {len(occurrences)} times, average {avg_loss:.1f} cp loss")
    
    # Show opponents you struggle against
    if opponent_patterns['overall_record']:
        print("\nOPPONENTS YOU STRUGGLE AGAINST:")
        struggling_opponents = []
        for opponent, record in opponent_patterns['overall_record'].items():
            total = record['wins'] + record['losses'] + record['draws']
            if total >= 3:  # At least 3 games
                win_rate = (record['wins'] / total) * 100
                if win_rate < 40:  # Less than 40% win rate
                    struggling_opponents.append((opponent, record, win_rate))
        
        struggling_opponents.sort(key=lambda x: x[2])  # Sort by win rate
        
        for opponent, record, win_rate in struggling_opponents[:5]:
            total = record['wins'] + record['losses'] + record['draws']
            print(f"- {opponent}: {record['wins']}-{record['losses']}-{record['draws']} ({win_rate:.1f}% win rate)")
    
    # Save analysis if requested
    if args.save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tournament_analysis_{username}_{timestamp}.json"
        
        import json
        data = {
            'username': username,
            'timestamp': datetime.now().isoformat(),
            'games_count': len(games),
            'opponent_patterns': opponent_patterns,
            'common_blunders': common_blunders
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\nAnalysis saved to {filename}")


def analyze_study_games(lichess_client, chess_analyzer, username, args):
    """Analyze games from Lichess studies"""
    print(f"Analyzing study games for {username}...")
    
    study_analyzer = StudyAnalyzer(lichess_client, chess_analyzer, no_analysis=args.no_analysis or args.fast, sample_size=args.sample)
    
    # Fetch study games
    games = study_analyzer.fetch_study_games(
        username=username,
        study_name=args.study_name,
        max_studies=args.max_studies,
        study_id=args.study_id
    )
    
    if not games:
        print("No study games found")
        return
    
    # Analyze opponent patterns (skips engine analysis if --no-analysis)
    opponent_patterns = study_analyzer.analyze_opponent_patterns(username)
    
    # Find common blunders (skipped if no-analysis or fast mode)
    common_blunders = study_analyzer.find_common_blunders() if not (args.no_analysis or args.fast) else {'move_patterns': {}, 'position_patterns': {}, 'opening_blunders': {}}
    
    # Generate study report
    report = study_analyzer.generate_study_report(username, no_analysis=args.no_analysis or args.fast)
    print("\n" + report)
    
    # Show common blunders (only if analysis enabled)
    if not args.no_analysis and common_blunders['move_patterns']:
        print("\nCOMMON BLUNDER PATTERNS:")
        for move, occurrences in list(common_blunders['move_patterns'].items())[:5]:
            avg_loss = sum(o['eval_change'] for o in occurrences) / len(occurrences)
            print(f"- {move}: {len(occurrences)} times, average {avg_loss:.1f} cp loss")
    
    # Show opponents you struggle against
    if opponent_patterns['overall_record']:
        print("\nOPPONENTS YOU STRUGGLE AGAINST:")
        struggling_opponents = []
        for opponent, record in opponent_patterns['overall_record'].items():
            total = record['wins'] + record['losses'] + record['draws']
            if total >= 3:  # At least 3 games
                win_rate = (record['wins'] / total) * 100
                if win_rate < 40:  # Less than 40% win rate
                    struggling_opponents.append((opponent, record, win_rate))
        
        struggling_opponents.sort(key=lambda x: x[2])  # Sort by win rate
        
        for opponent, record, win_rate in struggling_opponents[:5]:
            total = record['wins'] + record['losses'] + record['draws']
            print(f"- {opponent}: {record['wins']}-{record['losses']}-{record['draws']} ({win_rate:.1f}% win rate)")
    
    # Save analysis if requested
    if args.save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"study_analysis_{username}_{timestamp}.json"
        
        import json
        data = {
            'username': username,
            'timestamp': datetime.now().isoformat(),
            'games_count': len(games),
            'studies_analyzed': len(study_analyzer.study_metadata),
            'study_names': [s.get('name', 'Unknown') for s in study_analyzer.study_metadata],
            'opponent_patterns': opponent_patterns,
            'common_blunders': common_blunders,
            'report': report
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\nAnalysis saved to {filename}")
    
    # Also save the report as text file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"study_report_{username}_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Study report saved to {report_filename}")


def find_common_blunders(lichess_client, chess_analyzer, username, args):
    """Find common blunders across all games"""
    print(f"Finding common blunders for {username}...")
    
    tournament_analyzer = TournamentAnalyzer(lichess_client, chess_analyzer)
    
    # Fetch games (not just tournament)
    games = tournament_analyzer.fetch_tournament_games(
        username=username,
        max_games=args.max_games,
        tournament_only=False
    )
    
    if not games:
        print("No games found")
        return
    
    # Find common blunders
    common_blunders = tournament_analyzer.find_common_blunders(min_occurrences=2)
    
    print("\nCOMMON BLUNDER ANALYSIS")
    print("=" * 50)
    
    # Position patterns
    if common_blunders['position_patterns']:
        print("\nPOSITION PATTERNS (where blunders commonly occur):")
        for position, occurrences in list(common_blunders['position_patterns'].items())[:5]:
            avg_loss = sum(o['eval_change'] for o in occurrences) / len(occurrences)
            print(f"\nPosition: {position}")
            print(f"  Occurrences: {len(occurrences)}")
            print(f"  Average loss: {avg_loss:.1f} centipawns")
            print(f"  Common blunder moves: {[o['blunder_move'] for o in occurrences[:3]]}")
    
    # Move patterns
    if common_blunders['move_patterns']:
        print("\nBLUNDER MOVES (most common blunder moves):")
        sorted_moves = sorted(common_blunders['move_patterns'].items(), 
                            key=lambda x: len(x[1]), reverse=True)
        
        for move, occurrences in sorted_moves[:10]:
            avg_loss = sum(o['eval_change'] for o in occurrences) / len(occurrences)
            print(f"- {move}: {len(occurrences)} times, average {avg_loss:.1f} cp loss")
    
    # Opening-specific blunders
    if common_blunders['opening_blunders']:
        print("\nOPENING-SPECIFIC BLUNDERS:")
        for opening, blunders in list(common_blunders['opening_blunders'].items())[:5]:
            avg_move = sum(b['move_number'] for b in blunders) / len(blunders)
            avg_loss = sum(b['eval_change'] for b in blunders) / len(blunders)
            print(f"- {opening}: {len(blunders)} blunders, avg move {avg_move:.1f}, avg loss {avg_loss:.1f} cp")
    
    # Save if requested
    if args.save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"blunders_analysis_{username}_{timestamp}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump(common_blunders, f, indent=2, default=str)
        
        print(f"\nBlunder analysis saved to {filename}")


def interactive_mode(lichess_client, chess_analyzer, username, config):
    """Interactive mode for guided analysis"""
    print("Tournament and Opponent Analysis - Interactive Mode")
    print("=" * 60)
    
    while True:
        print("\nSelect analysis type:")
        print("1. Analyze specific opponent")
        print("2. Analyze tournament games")
        print("3. Find common blunders")
        print("4. Comprehensive tournament analysis")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            opponent = input("Enter opponent username: ").strip()
            if opponent:
                max_games = input("Maximum games to analyze [50]: ").strip()
                max_games = int(max_games) if max_games.isdigit() else 50
                
                # Create args object
                class Args:
                    def __init__(self):
                        self.max_games = max_games
                        self.save = True
                
                analyze_specific_opponent(lichess_client, chess_analyzer, username, opponent, Args())
        
        elif choice == '2':
            max_games = input("Maximum tournament games to analyze [50]: ").strip()
            max_games = int(max_games) if max_games.isdigit() else 50
            
            class Args:
                def __init__(self):
                    self.max_games = max_games
                    self.save = True
            
            analyze_tournament_games(lichess_client, chess_analyzer, username, Args())
        
        elif choice == '3':
            max_games = input("Maximum games to analyze for blunders [100]: ").strip()
            max_games = int(max_games) if max_games.isdigit() else 100
            
            class Args:
                def __init__(self):
                    self.max_games = max_games
                    self.save = True
            
            find_common_blunders(lichess_client, chess_analyzer, username, Args())
        
        elif choice == '4':
            print("Running comprehensive tournament analysis...")
            
            # Tournament analysis
            tournament_analyzer = TournamentAnalyzer(lichess_client, chess_analyzer)
            games = tournament_analyzer.fetch_tournament_games(username, max_games=100)
            
            if games:
                # Generate tournament report
                report = tournament_analyzer.generate_tournament_report(username)
                print("\n" + report)
                
                # Find common blunders
                common_blunders = tournament_analyzer.find_common_blunders()
                if common_blunders['move_patterns']:
                    print("\nTOP 5 COMMON BLUNDERS:")
                    sorted_moves = sorted(common_blunders['move_patterns'].items(), 
                                        key=lambda x: len(x[1]), reverse=True)
                    for move, occurrences in sorted_moves[:5]:
                        avg_loss = sum(o['eval_change'] for o in occurrences) / len(occurrences)
                        print(f"- {move}: {len(occurrences)} times, avg {avg_loss:.1f} cp loss")
                
                # Save comprehensive analysis
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                import json
                data = {
                    'username': username,
                    'timestamp': datetime.now().isoformat(),
                    'tournament_report': report,
                    'common_blunders': common_blunders,
                    'games_analyzed': len(games)
                }
                
                filename = f"comprehensive_analysis_{username}_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                
                print(f"\nComprehensive analysis saved to {filename}")
            else:
                print("No tournament games found")
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main()
