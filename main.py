"""
Main entry point for Chess Analysis Agent
"""

import argparse
import sys
import os
from datetime import datetime

from config import Config
from game_analyzer import GameAnalysisSystem


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Chess Game Analysis Agent')
    parser.add_argument('--config', '-c', default='.env', help='Configuration file path')
    parser.add_argument('--username', '-u', help='Lichess username (overrides config)')
    parser.add_argument('--games', '-g', type=int, help='Number of games to analyze')
    parser.add_argument('--time-control', '-tc', help='Filter by time control (blitz, rapid, etc.)')
    parser.add_argument('--days', '-d', type=int, help='Analyze games from last N days')
    parser.add_argument('--game-id', help='Analyze specific game by ID')
    parser.add_argument('--report', action='store_true', help='Generate overall report')
    parser.add_argument('--visualize', action='store_true', help='Create visualizations')
    parser.add_argument('--export-csv', action='store_true', help='Export data to CSV')
    parser.add_argument('--save', action='store_true', help='Save analysis results')
    parser.add_argument('--load', help='Load analysis from file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config)
    if not config.validate():
        sys.exit(1)
    
    # Override config with command line arguments
    username = args.username or config.USERNAME
    num_games = args.games or config.DEFAULT_NUM_GAMES
    time_control = args.time_control or config.DEFAULT_TIME_CONTROL
    days_back = args.days or config.DEFAULT_DAYS_BACK
    
    # Initialize analysis system
    try:
        analyzer = GameAnalysisSystem(
            api_token=config.LICHESS_API_TOKEN,
            username=username,
            stockfish_path=config.get_stockfish_path(),
            analysis_depth=config.ANALYSIS_DEPTH,
            analysis_time=config.ANALYSIS_TIME
        )
        print(f"Chess Analysis System initialized for {username}")
    except Exception as e:
        print(f"Error initializing analyzer: {e}")
        sys.exit(1)
    
    try:
        # Load existing analysis if specified
        if args.load:
            analyzer.load_analysis(args.load)
            print(f"Loaded analysis from {args.load}")
        
        # Analyze specific game
        elif args.game_id:
            print(f"Analyzing game {args.game_id}...")
            analysis = analyzer.analyze_single_game(args.game_id)
            if analysis:
                print("\n" + "="*50)
                print("GAME ANALYSIS REPORT")
                print("="*50)
                print(analyzer.analyzer.generate_feedback(analysis))
            else:
                print("Failed to analyze game")
        
        # Analyze recent games
        else:
            print(f"Analyzing {num_games} recent games...")
            if time_control:
                print(f"Filter: {time_control} time control")
            if days_back:
                print(f"Filter: Last {days_back} days")
            
            analyses = analyzer.analyze_recent_games(
                num_games=num_games,
                time_control=time_control,
                days_back=days_back
            )
            
            if not analyses:
                print("No games found or analyzed")
                sys.exit(1)
            
            # Generate individual game feedback
            for i, analysis in enumerate(analyses):
                print(f"\n{'='*50}")
                print(f"GAME {i+1} ANALYSIS")
                print(f"{'='*50}")
                print(analyzer.analyzer.generate_feedback(analysis))
        
        # Generate overall report
        if args.report or len(analyzer.analyses) > 1:
            print(f"\n{'='*50}")
            print("OVERALL PERFORMANCE REPORT")
            print(f"{'='*50}")
            print(analyzer.generate_overall_report())
        
        # Create visualizations
        if args.visualize:
            print("\nGenerating visualizations...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            viz_path = f"chess_analysis_{username}_{timestamp}.png"
            analyzer.create_visualizations(viz_path)
        
        # Export to CSV
        if args.export_csv:
            print("\nExporting to CSV...")
            analyzer.export_to_csv()
        
        # Save analysis
        if args.save or config.SAVE_ANALYSIS:
            print("\nSaving analysis...")
            analyzer.save_analysis()
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        analyzer.cleanup()


def interactive_mode():
    """Interactive mode for the chess analyzer"""
    print("Chess Analysis Agent - Interactive Mode")
    print("=" * 40)
    
    # Get configuration
    config = Config()
    if not config.validate():
        print("Please set up your .env file first")
        return
    
    username = input(f"Enter Lichess username [{config.USERNAME}]: ").strip()
    if not username:
        username = config.USERNAME
    
    try:
        analyzer = GameAnalysisSystem(
            api_token=config.LICHESS_API_TOKEN,
            username=username,
            stockfish_path=config.get_stockfish_path(),
            analysis_depth=config.ANALYSIS_DEPTH,
            analysis_time=config.ANALYSIS_TIME
        )
        
        while True:
            print("\nOptions:")
            print("1. Analyze recent games")
            print("2. Analyze specific game")
            print("3. Generate overall report")
            print("4. Create visualizations")
            print("5. Export data")
            print("6. Load previous analysis")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                num_games = input("Number of games to analyze [10]: ").strip()
                num_games = int(num_games) if num_games.isdigit() else 10
                
                time_control = input("Time control filter (blitz/rapid/classical) [leave empty for all]: ").strip()
                time_control = time_control if time_control else None
                
                days = input("Analyze games from last N days [30]: ").strip()
                days = int(days) if days.isdigit() else 30
                
                analyzer.analyze_recent_games(num_games, time_control, days)
                print("Analysis complete!")
            
            elif choice == '2':
                game_id = input("Enter game ID: ").strip()
                if game_id:
                    analysis = analyzer.analyze_single_game(game_id)
                    if analysis:
                        print("\n" + analyzer.analyzer.generate_feedback(analysis))
            
            elif choice == '3':
                if analyzer.analyses:
                    print("\n" + analyzer.generate_overall_report())
                else:
                    print("No games analyzed yet")
            
            elif choice == '4':
                if analyzer.analyses:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    viz_path = f"chess_analysis_{username}_{timestamp}.png"
                    analyzer.create_visualizations(viz_path)
                else:
                    print("No games analyzed yet")
            
            elif choice == '5':
                if analyzer.analyses:
                    analyzer.export_to_csv()
                    analyzer.save_analysis()
                else:
                    print("No games analyzed yet")
            
            elif choice == '6':
                filename = input("Enter analysis file path: ").strip()
                if filename and os.path.exists(filename):
                    analyzer.load_analysis(filename)
                else:
                    print("File not found")
            
            elif choice == '7':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        analyzer.cleanup()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run interactive mode
        interactive_mode()
    else:
        # Run with command line arguments
        main()
