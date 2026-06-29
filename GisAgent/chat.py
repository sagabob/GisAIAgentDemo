"""Interactive CLI for the GIS agent."""

import sys

from agent import GisAgent
from config import get_gis_api_base_url


def main() -> int:
    agent = GisAgent()
    print("GIS Agent")
    print(f"API: {get_gis_api_base_url()}")
    print("Ask questions about Christchurch places. Type 'exit' or 'quit' to stop.\n")

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                break
            if user_input.lower() == "reset":
                agent.reset()
                print("Conversation reset.\n")
                continue

            print("\nAgent:")
            try:
                answer = agent.ask(user_input)
                print(answer)
            except Exception as exc:
                print(f"Error: {exc}")
            print()

    finally:
        agent.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
