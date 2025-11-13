#!/usr/bin/env python3
import argparse
import os
import sys
import time
import google.generativeai as genai
from rich.console import Console
from agent.core import ResuminiAgent
from agent.ui.terminal_ui import show_banner, typewriter

console = Console()


def masked_input(prompt=""):
    """Cross-platform input that masks characters with '*' (works on Windows & Unix)."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    password = ""

    if os.name == "nt":  # Windows
        import msvcrt
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                print()
                break
            elif ch == "\003":  # Ctrl+C
                raise KeyboardInterrupt
            elif ch == "\b":  # Backspace
                if len(password) > 0:
                    password = password[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            else:
                password += ch
                sys.stdout.write("*")
                sys.stdout.flush()
    else:  # macOS / Linux
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n'):
                    print()
                    break
                elif ch == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                elif ch == '\x7f':  # Backspace
                    if len(password) > 0:
                        password = password[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                else:
                    password += ch
                    sys.stdout.write('*')
                    sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return password


def setup_gemini():
    """Ask user for Gemini API key and model name interactively, validate key, and configure Gemini."""
    print("\n🚀 Welcome to Resumini - Your AI Resume Assistant\n")

    api_key = masked_input("🔑 Enter your Google Gemini API Key (press Enter to paste): ").strip()
    if not api_key:
        print("❌ API key is required. Visit https://ai.google.dev to create one.")
        sys.exit(1)

    model_name = input("🧠 Enter Gemini model name (default: gemini-2.0-flash): ").strip()
    if not model_name:
        model_name = "gemini-2.0-flash"

    # Configure Gemini
    try:
        print("\n⚙️  Validating your API key and initializing model...")
        genai.configure(api_key=api_key)
        test_model = genai.GenerativeModel(model_name)
        test_model.generate_content("Hello!")  # quick test request
        print(f"✅ Gemini model '{model_name}' connected successfully!\n")
        return api_key, model_name
    except Exception as e:
        print(f"❌ Failed to connect with Gemini API: {e}")
        print("👉 Get your valid API key from: https://ai.google.dev/")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Resumini - AI Resume Assistant CLI")
    parser.add_argument("--path", type=str, help="Path to your resume file (PDF/DOCX)")
    args = parser.parse_args()

    # 1️⃣ Setup Gemini interactively
    api_key, model_name = setup_gemini()

    # 2️⃣ Pass API key + model to environment (for all submodules)
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GEMINI_MODEL_NAME"] = model_name

    # 3️⃣ Launch the agent
    agent = ResuminiAgent()
    print("🤖 Starting interactive chat...\n")
    time.sleep(0.5)
    agent.start_chat()


if __name__ == "__main__":
    show_banner()
    console.print("\n🤖 [bold magenta]Resumini is ready![/bold magenta] Type [yellow]'help'[/yellow] or [yellow]'exit'[/yellow].\n")
    main()
