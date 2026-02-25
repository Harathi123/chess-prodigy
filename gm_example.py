"""
Example usage of the GM Agent
"""

import os
from dotenv import load_dotenv
from gm_agent import GMAgent


def example_gm_conversation():
    """Example conversation with GM Agent"""
    print("🏆 GM Agent Example Conversation")
    print("=" * 50)
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    try:
        # Initialize GM Agent
        gm = GMAgent(api_token, username)
        
        # Example questions
        questions = [
            "How am I performing overall?",
            "What are my main weaknesses?",
            "What time control am I best at?",
            "How can I improve my tactical skills?",
            "What openings work best for me?",
            "Give me training recommendations"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*50}")
            print(f"Question {i}: {question}")
            print(f"{'='*50}")
            
            response = gm.ask(question)
            print(response)
            
            if i < len(questions):
                input("\nPress Enter to continue to next question...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        gm.cleanup()


def example_specific_scenarios():
    """Example specific analysis scenarios"""
    print("\n🏆 GM Agent - Specific Analysis Examples")
    print("=" * 50)
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    try:
        gm = GMAgent(api_token, username)
        
        # Scenario 1: Pre-tournament analysis
        print("\n📊 SCENARIO 1: Pre-Tournament Analysis")
        print("-" * 40)
        question = "I have a tournament tomorrow. How should I prepare based on my recent performance?"
        response = gm.ask(question)
        print(response)
        
        # Scenario 2: After a loss
        print("\n😔 SCENARIO 2: After a Tough Loss")
        print("-" * 40)
        question = "I just lost a tough game. What went wrong and how can I avoid this in the future?"
        response = gm.ask(question)
        print(response)
        
        # Scenario 3: Rating goal
        print("\n🎯 SCENARIO 3: Rating Goal Planning")
        print("-" * 40)
        question = "I want to reach 1800 rating. What do I need to work on?"
        response = gm.ask(question)
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        gm.cleanup()


def example_opponent_specific():
    """Example opponent-specific analysis"""
    print("\n🏆 GM Agent - Opponent Analysis Example")
    print("=" * 50)
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    try:
        gm = GMAgent(api_token, username)
        
        # Example opponent (replace with actual opponent)
        opponent = "chessmaster123"  # Replace with real opponent
        
        print(f"\n👥 Analyzing performance against {opponent}")
        print("-" * 40)
        
        questions = [
            f"How do I play against {opponent}?",
            f"Why do I struggle against {opponent}?",
            f"What's my record vs {opponent}?",
            f"How can I beat {opponent} next time?"
        ]
        
        for question in questions:
            print(f"\nQ: {question}")
            response = gm.ask(question)
            print(response)
            print("-" * 40)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        gm.cleanup()


def example_progress_tracking():
    """Example progress tracking over time"""
    print("\n🏆 GM Agent - Progress Tracking Example")
    print("=" * 50)
    
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token or not username:
        print("Please set up your .env file first!")
        return
    
    try:
        gm = GMAgent(api_token, username)
        
        progress_questions = [
            "How's my recent form?",
            "Am I improving over time?",
            "What progress have I made in the last month?",
            "Which areas have shown the most improvement?",
            "What still needs work?"
        ]
        
        for question in progress_questions:
            print(f"\n📈 {question}")
            print("-" * 40)
            response = gm.ask(question)
            print(response)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        gm.cleanup()


if __name__ == "__main__":
    print("🏆 GM Agent Examples")
    print("=" * 50)
    print("Choose an example to run:")
    print("1. Basic conversation examples")
    print("2. Specific analysis scenarios")
    print("3. Opponent-specific analysis")
    print("4. Progress tracking")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        example_gm_conversation()
    elif choice == '2':
        example_specific_scenarios()
    elif choice == '3':
        example_opponent_specific()
    elif choice == '4':
        example_progress_tracking()
    else:
        print("Running basic conversation examples...")
        example_gm_conversation()
    
    print("\n🏆 Examples completed!")
    print("To start your own session, run: python gm_interface.py")
