import os
import sys
from datetime import datetime

def clear_screen():
    """Очищаем экран"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_menu():
    """Показываем меню"""
    clear_screen()
    print("=" * 60)
    print("📊 ПРОСМОТР ЛОГОВ БОТА")
    print("=" * 60)
    
    # Показываем доступные логи
    log_dir = "logs"
    if os.path.exists(log_dir):
        files = [f for f in os.listdir(log_dir) if f.endswith('.txt')]
        if files:
            print("📁 Доступные файлы логов:")
            for i, file in enumerate(sorted(files), 1):
                size = os.path.getsize(os.path.join(log_dir, file))
                print(f"   {i}. {file} ({size} bytes)")
        else:
            print("❌ Логи не найдены")
            return
    else:
        print("❌ Папка logs не найдена")
        return
    
    print("\n" + "=" * 60)
    print("Выберите действие:")
    print("1. Показать все логи за сегодня")
    print("2. Показать ошибки")
    print("3. Показать системные события")
    print("4. Показать Discord события")
    print("5. Показать Ollama события")
    print("6. Показать последние N строк")
    print("7. Поиск по тексту")
    print("8. Показать все файлы")
    print("0. Выход")
    
    choice = input("\n👉 Ваш выбор: ")
    return choice

def show_log_file(filename, lines=None, search_text=None):
    """Показываем содержимое лог файла"""
    log_file = os.path.join("logs", filename)
    
    if not os.path.exists(log_file):
        print(f"❌ Файл {log_file} не найден")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        print(f"\n📄 Содержимое файла: {filename}")
        print("=" * 60)
        
        if search_text:
            # Фильтруем по поисковому тексту
            filtered_lines = [line for line in content if search_text.lower() in line.lower()]
            if filtered_lines:
                for line in filtered_lines:
                    print(line.rstrip())
            else:
                print(f"❌ Текст '{search_text}' не найден")
        
        elif lines:
            # Показываем последние N строк
            for line in content[-lines:]:
                print(line.rstrip())
        
        else:
            # Показываем все строки
            for line in content:
                print(line.rstrip())
    
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")

def get_today_logs():
    """Получаем логи за сегодня"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_files = []
    
    for log_type in ["bot", "errors", "system", "discord", "ollama"]:
        filename = f"{log_type}_{today}.txt"
        log_files.append(filename)
    
    return log_files

def main():
    """Главная функция"""
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("👋 До свидания!")
            break
        
        elif choice == "1":
            # Показать все логи за сегодня
            today_logs = get_today_logs()
            for log_file in today_logs:
                show_log_file(log_file)
                input("\nНажмите Enter для продолжения...")
        
        elif choice == "2":
            # Показать ошибки
            today = datetime.now().strftime("%Y-%m-%d")
            show_log_file(f"errors_{today}.txt")
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "3":
            # Показать системные события
            today = datetime.now().strftime("%Y-%m-%d")
            show_log_file(f"system_{today}.txt")
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "4":
            # Показать Discord события
            today = datetime.now().strftime("%Y-%m-%d")
            show_log_file(f"discord_{today}.txt")
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "5":
            # Показать Ollama события
            today = datetime.now().strftime("%Y-%m-%d")
            show_log_file(f"ollama_{today}.txt")
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "6":
            # Показать последние N строк
            try:
                lines = int(input("👉 Сколько строк показать: "))
                today = datetime.now().strftime("%Y-%m-%d")
                show_log_file(f"bot_{today}.txt", lines=lines)
                input("\nНажмите Enter для продолжения...")
            except ValueError:
                print("❌ Неверное число")
                input("\nНажмите Enter для продолжения...")
        
        elif choice == "7":
            # Поиск по тексту
            search_text = input("👉 Введите текст для поиска: ")
            today = datetime.now().strftime("%Y-%m-%d")
            show_log_file(f"bot_{today}.txt", search_text=search_text)
            input("\nНажмите Enter для продолжения...")
        
        elif choice == "8":
            # Показать все файлы
            log_dir = "logs"
            if os.path.exists(log_dir):
                files = [f for f in os.listdir(log_dir) if f.endswith('.txt')]
                for file in sorted(files):
                    show_log_file(file)
                    input(f"\n📄 {file} - Нажмите Enter для следующего файла...")
        
        else:
            print("❌ Неверный выбор")
            input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    main()
