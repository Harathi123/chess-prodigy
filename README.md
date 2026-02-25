# Chess Analysis Agent

A comprehensive chess game analysis system that connects to your Lichess account, retrieves your past games, and provides detailed analysis and feedback using Stockfish engine.

## Features

- **Game Retrieval**: Fetch games from your Lichess account via API
- **Engine Analysis**: Analyze games using Stockfish chess engine
- **Mistake Detection**: Identify blunders, mistakes, and inaccuracies
- **Performance Metrics**: Calculate accuracy, centipawn loss, and other statistics
- **Tournament Analysis**: Specialized analysis for tournament games
- **Opponent Analysis**: Deep dive into specific opponent patterns and weaknesses
- **Common Blunder Detection**: Find recurring mistakes across your games
- **Head-to-Head Statistics**: Track performance against specific opponents
- **GM Agent**: Personal AI chess coach that answers questions about your performance
- **Conversational Interface**: Chat with your GM coach about your game
- **Intelligent Insights**: Get personalized recommendations based on your playing patterns
- **Visual Reports**: Generate charts and graphs showing performance trends
- **Personalized Feedback**: Get actionable recommendations for improvement
- **Data Export**: Export analysis results to CSV and JSON formats

## Installation

1. Clone or download this repository
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Stockfish chess engine:
   - **Windows**: Download from [stockfishchess.org](https://stockfishchess.org/download/) and add to PATH
   - **macOS**: `brew install stockfish`
   - **Linux**: `sudo apt-get install stockfish` or `sudo yum install stockfish`

## Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` file with your configuration:
```env
# Get your API token from: https://lichess.org/account/oauth/token
LICHESS_API_TOKEN=your_lichess_api_token_here
USERNAME=your_lichess_username

# Optional: Specify Stockfish path if not in PATH
STOCKFISH_PATH=

# Analysis settings
ANALYSIS_DEPTH=15
ANALYSIS_TIME=2.0
```

3. Get your Lichess API token:
   - Go to [https://lichess.org/account/oauth/token](https://lichess.org/account/oauth/token)
   - Create a new token with read permissions
   - Copy the token to your `.env` file

## Usage

### Interactive Mode

Simply run the script without arguments:
```bash
python main.py
```

### Tournament and Opponent Analysis

For specialized tournament and opponent analysis:
```bash
# Interactive tournament analysis
python tournament_main.py --interactive

# Analyze specific opponent
python tournament_main.py --opponent "opponent_username" --username "your_username"

# Analyze tournament games only
python tournament_main.py --tournament --username "your_username" --max-games 20

# Find common blunders across all games
python tournament_main.py --common-blunders --username "your_username" --max-games 50

# Comprehensive analysis with report
python tournament_main.py --opponent "opponent_username" --report --save
```

This will launch an interactive menu where you can:
- Analyze recent games
- Analyze specific games by ID
- Generate reports
- Create visualizations
- Export data

### GM Agent - Personal Chess Coach

For intelligent conversation-based analysis with your personal GM Coach:
```bash
# Start interactive GM Coach session
python gm_interface.py

# Run GM Agent examples
python gm_example.py
```

The GM Agent can answer questions like:
- "How am I performing overall?"
- "What are my weaknesses?" 
- "How do I play against [opponent]?"
- "What openings should I focus on?"
- "Am I making too many blunders?"
- "Give me training recommendations"

### Cascade-ready context export

To ask Cascade questions with your real performance context, export a compact JSON context pack and paste it into Cascade.

```bash
# Export 30 recent games into a context pack
python export_cascade_context.py --out analysis_results/cascade_context.json --games 30
```

You can also export from inside the GM chat:

```text
export
export analysis_results/cascade_context.json 30
```

```bash
# Analyze last 10 games
python main.py --games 10

# Analyze last 20 blitz games from past 7 days
python main.py --games 20 --time-control blitz --days 7

# Analyze specific game
python main.py --game-id "Qa7FJNk2"

# Generate report with visualizations
python main.py --games 5 --report --visualize --save

# Export data to CSV
python main.py --games 10 --export-csv
```

### Command Line Options

- `--config, -c`: Configuration file path (default: `.env`)
- `--username, -u`: Override Lichess username
- `--games, -g`: Number of games to analyze
- `--time-control, -tc`: Filter by time control (blitz, rapid, classical, bullet)
- `--days, -d`: Analyze games from last N days
- `--game-id`: Analyze specific game by ID
- `--report`: Generate overall performance report
- `--visualize`: Create performance visualizations
- `--export-csv`: Export data to CSV format
- `--save`: Save analysis results to file
- `--load`: Load previous analysis from file

## Example Output

### Game Analysis
```
==================================================
GAME ANALYSIS REPORT
==================================================
Game Analysis: MagnusCarlsen vs Hikaru
Result: 1-0
Time Control: 600+0

Performance Summary:
- Total Moves: 45
- Accuracy: 92.3%
- Blunders: 0
- Mistakes: 1
- Inaccuracies: 2
- Average Centipawn Loss: 23.4

Key Mistakes:
- Move 23: Nf3 (mistake, -156.0 cp loss)
- Move 31: Be3 (inaccuracy, -52.0 cp loss)

Critical Moments:
- Move 28: White gains significant advantage
- Move 42: Mate in 3 for White

Recommendations:
- Work on positional understanding to reduce mistakes
- Review critical moments to learn from key positions
```

### Overall Report
```
==================================================
CHESS ANALYSIS REPORT FOR USERNAME
==================================================
Generated: 2024-01-15 14:30:22
Games Analyzed: 25

PLAYER PROFILE:
Username: chessmaster
Blitz Rating: 1850
Rapid Rating: 1920

OVERALL PERFORMANCE:
Total Games: 25
Average Accuracy: 87.2%
Average Cp Loss: 45.3
Total Blunders: 8
Win Rate: 68.0%

RECOMMENDATIONS:
- Focus on tactical puzzles to reduce blunders
- Good accuracy! Focus on positional understanding
- Study fundamental endgames and opening principles
```

## Project Structure

```
chess-prodigy/
├── main.py                 # Main application entry point
├── tournament_main.py      # Tournament and opponent analysis
├── gm_interface.py         # Interactive GM Coach interface
├── gm_agent.py            # AI GM Coach agent
├── config.py              # Configuration management
├── lichess_client.py      # Lichess API client
├── chess_analyzer.py      # Chess analysis engine
├── game_analyzer.py       # Main analysis system
├── tournament_analyzer.py # Tournament-specific analysis
├── opponent_analyzer.py   # Detailed opponent analysis
├── example_usage.py       # Usage examples
├── gm_example.py         # GM Agent examples
├── tournament_example.py  # Tournament analysis examples
├── requirements.txt       # Python dependencies
├── .env.example          # Configuration template
└── README.md             # This file
```

## How It Works

1. **Authentication**: Uses your Lichess API token to securely access your game data
2. **Game Retrieval**: Fetches games from Lichess using the berserk library
3. **Position Analysis**: Uses Stockfish engine to analyze each position
4. **Mistake Detection**: Identifies blunders, mistakes, and inaccuracies based on evaluation changes
5. **Feedback Generation**: Provides personalized recommendations based on your performance patterns
6. **Visualization**: Creates charts showing accuracy trends, mistake patterns, and results distribution

## Customization

You can customize the analysis parameters in the `.env` file:

- `ANALYSIS_DEPTH`: Stockfish analysis depth (higher = more accurate but slower)
- `ANALYSIS_TIME`: Time limit per position analysis in seconds
- `DEFAULT_NUM_GAMES`: Default number of games to analyze
- `DEFAULT_TIME_CONTROL`: Default time control filter
- `DEFAULT_DAYS_BACK`: Default number of days to look back

## Troubleshooting

### Stockfish Not Found
If you get an error about Stockfish not being found:
1. Make sure Stockfish is installed
2. Add Stockfish to your system PATH, or
3. Set `STOCKFISH_PATH` in your `.env` file to the full path of the executable

### API Token Issues
If you get authentication errors:
1. Verify your API token is correct
2. Ensure the token has the necessary permissions
3. Check that your username is spelled correctly

### Performance Issues
If analysis is slow:
1. Reduce `ANALYSIS_DEPTH` in the configuration
2. Reduce `ANALYSIS_TIME` for faster but less thorough analysis
3. Analyze fewer games at once

## Contributing

This is an open-source project. Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests

## License

This project is released under the MIT License.

## Dependencies

- **berserk**: Lichess API client
- **chess**: Python chess library
- **stockfish**: Stockfish engine interface
- **python-dotenv**: Environment variable management
- **pandas**: Data manipulation
- **matplotlib**: Plotting and visualization
- **seaborn**: Statistical visualization

## Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Ensure all dependencies are properly installed
3. Verify your configuration is correct
4. Feel free to open an issue on the project repository
#   c h e s s - p r o d i g y  
 