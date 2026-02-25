"""
GM Agent Interface - Interactive chat interface for the GM Agent
"""

import os
import sys
from dotenv import load_dotenv
from gm_agent import GMAgent


class GMInterface:
    """Interactive interface for GM Agent"""
    
    def __init__(self, api_token: str, username: str):
        """Initialize GM Interface"""
        self.gm_agent = GMAgent(api_token, username)
        self.username = username
        
        # Welcome message and help
        self.welcome_message = f"""
🏆 Welcome to your Personal GM Coach, {username}!

I'm here to help you improve your chess game through personalized analysis and advice.

You can ask me questions like:
• "How am I performing overall?"
• "What are my weaknesses?"
• "How do I play against [opponent]?"
• "What openings should I focus on?"
• "Am I making too many blunders?"
• "How's my tournament performance?"
• "What time control am I best at?"
• "Give me training recommendations"

Type 'help' for more options, 'quit' to exit.
Type 'export' to generate a Cascade-ready context JSON.
"""
        
        self.help_message = """
🎯 GM Coach Help - Available Questions:

PERFORMANCE ANALYSIS:
• "How am I performing overall?"
• "What's my current rating?"
• "How's my recent form?"
• "Am I improving?"

OPPONENT ANALYSIS:
• "How do I play against [opponent]?"
• "Why do I lose to [opponent]?"
• "What's my record vs [opponent]?"

TACTICAL ANALYSIS:
• "Am I making too many blunders?"
• "What are my tactical weaknesses?"
• "How can I improve my calculation?"

OPENING ANALYSIS:
• "What openings should I play?"
• "Which openings work best for me?"
• "How's my opening performance?"

TIME CONTROL:
• "What time control am I best at?"
• "How do I perform in blitz/rapid/classical?"

TOURNAMENT PERFORMANCE:
• "How do I perform in tournaments?"
• "Am I better in tournaments or casual games?"

TRAINING ADVICE:
• "What should I work on?"
• "Give me training recommendations"
• "How can I reach [rating]?"

GENERAL:
• "What are my strengths?"
• "What are my weaknesses?"
• "help" - Show this help message
• "export" - Export a Cascade-ready context pack JSON (paste into Cascade)
• "quit" - Exit the GM Coach

💡 Tip: Ask in natural language - I understand conversational questions!
"""
    
    def start(self):
        """Start the interactive GM Coach session"""
        print(self.welcome_message)
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n🏆 GM Coach ({self.username}): ").strip()
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Good luck with your chess training! Your GM Coach is always here to help.")
                    break
                
                elif user_input.lower() in ['help', 'h', '?']:
                    print(self.help_message)
                    continue

                elif user_input.lower().startswith('export'):
                    parts = user_input.split()
                    out_path = parts[1] if len(parts) >= 2 else os.path.join('analysis_results', 'cascade_context.json')
                    games = 20
                    if len(parts) >= 3:
                        try:
                            games = int(parts[2])
                        except ValueError:
                            games = 20

                    print(f"\nExporting Cascade context to: {out_path} (games={games})")
                    context_pack = self.gm_agent.export_cascade_context(output_path=out_path, num_games=games)
                    included = context_pack.get('sample', {}).get('games_included')
                    print(f"Done. Games included: {included}")
                    print("Open the JSON file, copy-paste it into Cascade, then ask your questions.")
                    continue
                
                elif not user_input:
                    print("Please ask me a question about your chess performance. Type 'help' for examples.")
                    continue
                
                # Get GM Agent response
                print("\n🤔 Analyzing your games...")
                response = self.gm_agent.ask(user_input)
                
                print(f"\n🏆 GM Coach Response:")
                print("-" * 50)
                print(response)
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n\n👋 Training session interrupted. Good luck!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try asking your question differently.")
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'gm_agent'):
            self.gm_agent.cleanup()


def main():
    """Main function for GM Interface"""
    print("🏆 GM Chess Coach - Initializing...")
    
    # Load environment
    load_dotenv()
    
    api_token = os.getenv('LICHESS_API_TOKEN')
    username = os.getenv('USERNAME')
    
    if not api_token:
        print("❌ Error: LICHESS_API_TOKEN not found in .env file")
        print("Please set up your .env file with your Lichess API token.")
        sys.exit(1)
    
    if not username:
        print("❌ Error: USERNAME not found in .env file")
        print("Please set up your .env file with your Lichess username.")
        sys.exit(1)
    
    try:
        # Initialize and start interface
        interface = GMInterface(api_token, username)
        interface.start()
        
    except Exception as e:
        print(f"❌ Error initializing GM Coach: {e}")
        print("Please check your API token and internet connection.")
        sys.exit(1)
    finally:
        if 'interface' in locals():
            interface.cleanup()


if __name__ == "__main__":
    main()
