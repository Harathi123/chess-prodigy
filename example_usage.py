"""
Example usage of the Chess Analysis Agent
"""

import os
from dotenv import load_dotenv
from game_analyzer import GameAnalysisSystem

def example_basic_analysis():
    """Example: Basic game analysis"""
    print("=== Basic Game Analysis Example ===")
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    # Initialize analyzer
    analyzer = GameAnalysisSystem(
        api_token=api_token,
        username=username,
        analysis_depth=12,  # Slightly faster for demo
        analysis_time=1.5
    )
    
    try:
        # Load user data
        analyzer.load_user_data()
        
        # Analyze last 5 games
        print("Analyzing last 5 games...")
        analyses = analyzer.analyze_recent_games(num_games=5)
        
        if analyses:
            # Show feedback for first game
            print("\n--- First Game Analysis ---")
            print(analyzer.analyzer.generate_feedback(analyses[0]))
            
            # Show overall report
            print("\n--- Overall Report ---")
            print(analyzer.generate_overall_report())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        analyzer.cleanup()

def example_specific_game():
    """Example: Analyze a specific game"""
    print("\n=== Specific Game Analysis Example ===")
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    analyzer = GameAnalysisSystem(api_token=api_token, username=username)
    
    try:
        # Example game ID (replace with actual game ID)
        game_id = "Qa7FJNk2"  # This is a sample game ID
        
        print(f"Analyzing game {game_id}...")
        analysis = analyzer.analyze_single_game(game_id)
        
        if analysis:
            print("\n--- Game Analysis ---")
            print(analyzer.analyzer.generate_feedback(analysis))
        else:
            print("Game not found or analysis failed")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        analyzer.cleanup()

def example_filtered_analysis():
    """Example: Analyze games with filters"""
    print("\n=== Filtered Analysis Example ===")
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    analyzer = GameAnalysisSystem(api_token=api_token, username=username)
    
    try:
        # Analyze only blitz games from last 7 days
        print("Analyzing blitz games from last 7 days...")
        analyses = analyzer.analyze_recent_games(
            num_games=10,
            time_control='blitz',
            days_back=7
        )
        
        if analyses:
            print(f"Found {len(analyses)} blitz games")
            
            # Show summary statistics
            total_blunders = sum(a['summary']['blunders'] for a in analyses)
            avg_accuracy = sum(a['summary']['accuracy'] for a in analyses) / len(analyses)
            
            print(f"Total blunders: {total_blunders}")
            print(f"Average accuracy: {avg_accuracy:.1f}%")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        analyzer.cleanup()

def example_export_and_visualize():
    """Example: Export data and create visualizations"""
    print("\n=== Export and Visualization Example ===")
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    analyzer = GameAnalysisSystem(api_token=api_token, username=username)
    
    try:
        # Analyze some games
        print("Analyzing games for visualization...")
        analyses = analyzer.analyze_recent_games(num_games=15)
        
        if analyses:
            # Create output directory
            os.makedirs('analysis_results', exist_ok=True)
            
            # Export to CSV
            csv_path = f"analysis_results/{username}_games.csv"
            analyzer.export_to_csv(csv_path)
            
            # Save analysis
            json_path = f"analysis_results/{username}_analysis.json"
            analyzer.save_analysis(json_path)
            
            # Create visualizations
            viz_path = f"analysis_results/{username}_performance.png"
            analyzer.create_visualizations(viz_path)
            
            print(f"Results saved to analysis_results/ folder")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        analyzer.cleanup()

def example_performance_tracking():
    """Example: Track performance over time"""
    print("\n=== Performance Tracking Example ===")
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    analyzer = GameAnalysisSystem(api_token=api_token, username=username)
    
    try:
        # Load user data including rating history
        analyzer.load_user_data()
        
        # Analyze games from different time periods
        print("Analyzing recent performance...")
        recent_games = analyzer.analyze_recent_games(num_games=20, days_back=7)
        
        print("Analyzing older performance...")
        # Note: This would require modifying the client to support date ranges
        # For now, we'll just analyze more games
        older_games = analyzer.analyze_recent_games(num_games=20, days_back=30)
        
        if recent_games and older_games:
            # Compare performance
            recent_accuracy = sum(g['summary']['accuracy'] for g in recent_games) / len(recent_games)
            older_accuracy = sum(g['summary']['accuracy'] for g in older_games) / len(older_games)
            
            print(f"Recent accuracy (last 7 days): {recent_accuracy:.1f}%")
            print(f"Older accuracy (last 30 days): {older_accuracy:.1f}%")
            
            if recent_accuracy > older_accuracy:
                print("✅ Your accuracy is improving!")
            else:
                print("⚠️  Consider focusing on tactics to improve accuracy")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        analyzer.cleanup()

if __name__ == "__main__":
    print("Chess Analysis Agent - Example Usage")
    print("=" * 50)
    
    # Run examples (comment out as needed)
    
    # Example 1: Basic analysis
    example_basic_analysis()
    
    # Example 2: Specific game analysis
    # example_specific_game()
    
    # Example 3: Filtered analysis
    # example_filtered_analysis()
    
    # Example 4: Export and visualization
    # example_export_and_visualize()
    
    # Example 5: Performance tracking
    # example_performance_tracking()
    
    print("\nExamples completed!")
    print("Modify this file to run specific examples or create your own.")
