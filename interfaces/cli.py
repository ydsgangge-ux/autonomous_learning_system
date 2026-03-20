"""
Simple CLI for the Autonomous Learning System.
Usage: python -m interfaces.cli
"""
import asyncio
import sys
from db.session import init_db, get_async_session
from qa.qa_system import answer_question
from qa.dialogue import new_session_key
from core.utils import get_logger

logger = get_logger(__name__)


async def interactive_qa():
    """Interactive Q&A loop in the terminal."""
    await init_db()
    session_key = new_session_key()
    print("🧠 Autonomous Learning System - Q&A Mode")
    print("Type 'exit' or 'quit' to leave.\n")

    async with get_async_session() as session:
        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if question.lower() in ("exit", "quit"):
                break
            if not question:
                continue

            print("AI: ", end="", flush=True)
            try:
                answer = await answer_question(question, session, session_key)
                print(answer)
            except Exception as e:
                print(f"[Error: {e}]")
            print()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "qa":
        asyncio.run(interactive_qa())
    else:
        print("Usage: python -m interfaces.cli qa")


if __name__ == "__main__":
    main()
