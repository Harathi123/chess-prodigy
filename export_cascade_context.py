"""\
Export a Cascade-ready context pack (JSON) that summarizes your recent games.

Usage:
  python export_cascade_context.py --out analysis_results/cascade_context.json --games 30
"""

import argparse
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from gm_agent import GMAgent


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Cascade-ready chess context")
    parser.add_argument("--env", default=".env", help="Path to .env file")
    parser.add_argument("--out", default=None, help="Output JSON path")
    parser.add_argument("--games", type=int, default=20, help="Number of recent games to include")

    args = parser.parse_args()

    load_dotenv(args.env)

    api_token = os.getenv("LICHESS_API_TOKEN")
    username = os.getenv("USERNAME")

    if not api_token:
        print("Error: LICHESS_API_TOKEN not set in environment/.env")
        return 1

    if not username:
        print("Error: USERNAME not set in environment/.env")
        return 1

    if args.out is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.out = os.path.join("analysis_results", f"cascade_context_{username}_{ts}.json")

    agent = GMAgent(api_token=api_token, username=username)
    try:
        context_pack = agent.export_cascade_context(output_path=args.out, num_games=args.games)
        print(f"Wrote Cascade context pack: {args.out}")
        print(f"Games included: {context_pack.get('sample', {}).get('games_included')}")
        return 0
    finally:
        agent.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
