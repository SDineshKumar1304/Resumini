from pyfiglet import Figlet
from rich.console import Console
from rich.text import Text
import time, sys

console = Console()

def show_banner():
    f = Figlet(font="slant")
    banner = f.renderText("RESUMINI✨")
    gradient = Text(banner, style="bold magenta")
    console.print(gradient)
    console.print("[bold cyan]Tips for getting started:[/bold cyan]")
    console.print("1. Type [green]help[/green] for available commands.")
    console.print("2. Ask about your resume, job match, or optimization.")
    console.print("3. Type [red]exit[/red] to quit.\n")

def typewriter(text, delay=0.01):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()




