import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from src.loader import download_data
from src.physics import calculate_square_root_law
from src.storage import load_ticker_data
from src.trader.bot import SandboxBot

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_header():
    clear_screen()
    console.print(Panel.fit(
        "[bold cyan] ECONOPHYSICS TRADING TERMINAL v1.0[/bold cyan]\n"
        "[dim]Научный подход к рынку MOEX & Crypto[/dim]",
        border_style="cyan"
    ))

def mode_collection():
    ticker = Prompt.ask("Введите тикер", default="SELG")
    days = int(Prompt.ask("Сколько дней качать?", default="60"))
    with console.status(f"[bold green]Загрузка данных по {ticker}..."):
        download_data(ticker, days_back=days)
    console.print("[bold green] Готово![/bold green]")
    Prompt.ask("\nНажмите Enter для меню...")

def mode_analysis():
    ticker = Prompt.ask("Введите тикер для физики", default="SELG")
    df = load_ticker_data(ticker)
    if df.empty:
        console.print("[red]Нет данных![/red]")
        return
    
    res = calculate_square_root_law(df)
    if res:
        console.print(f"\n[bold]Результаты {ticker}:[/bold]")
        console.print(f"   Alpha: [cyan]{res['alpha']:.4f}[/cyan] (Норма ~0.44)")
        console.print(f"   R2:    [cyan]{res['r2']:.4f}[/cyan]")
        
        status = "CONFIRMED" if res['r2'] > 0.9 else "⚠️ ANOMALY"
        color = "green" if res['r2'] > 0.9 else "red"
        console.print(f"   Status: [{color}]{status}[/{color}]")
    else:
        console.print("[red]Ошибка расчета модели[/red]")
    
    Prompt.ask("\nНажмите Enter для меню...")

def mode_sandbox():
    try:
        ticker = Prompt.ask("Каким тикером торгуем?", default="SELG")
        console.print(f"[yellow]Запуск бота в ПЕСОЧНИЦЕ для {ticker}...[/yellow]")
        console.print("[dim]Лог сделок пишется в logs/sandbox_trades.csv[/dim]")
        
        if Confirm.ask("Запустить?"):
            from src.trader.bot import SandboxBot
            
            bot = SandboxBot(ticker)
            bot.run()
            
    except Exception as e:
        console.print(f"\n[bold red]КРИТИЧЕСКАЯ ОШИБКА:[/bold red] {e}")
        
        import traceback
        traceback.print_exc()
        
    finally:
        Prompt.ask("\n[bold reverse] Нажмите Enter, чтобы вернуться в меню... [/bold reverse]")

def main_menu():
    while True:
        show_header()
        console.print("[1] Сбор данных (Download Data)")
        console.print("[2] Проверка физики (Analysis)")
        console.print("[3] Обучение Нейросети (Train AI)")
        console.print("[4] [bold yellow]Запуск Трейдинга (SANDBOX)[/bold yellow]")
        console.print("[q] Выход")
        
        choice = Prompt.ask("\nВыберите действие", choices=["1", "2", "3", "4", "q"])
        
        if choice == "1":
            mode_collection()
        elif choice == "2":
            mode_analysis()
        elif choice == "3":
            os.system("python run_training.py")
            Prompt.ask("\nНажмите Enter...")
        elif choice == "4":
            mode_sandbox()
        elif choice == "q":
            console.print("До свидания!")
            sys.exit()

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        sys.exit()