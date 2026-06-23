import os
import time
from datetime import datetime, timedelta

def clean_old_logs(days_to_keep=7):
    """Очищаем логи старше N дней"""
    log_dir = "logs"
    
    if not os.path.exists(log_dir):
        print("❌ Папка logs не найдена")
        return
    
    # Вычисляем дату N дней назад
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    print(f"🧹 Очистка логов старше {days_to_keep} дней...")
    print(f"📅 Дата отсечения: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    deleted_files = []
    total_size = 0
    
    for filename in os.listdir(log_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(log_dir, filename)
            
            # Получаем дату модификации файла
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_time < cutoff_date:
                try:
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_files.append((filename, file_time, size))
                    total_size += size
                    print(f"🗑️ Удален: {filename} ({size} bytes)")
                except Exception as e:
                    print(f"❌ Ошибка удаления {filename}: {e}")
    
    print("=" * 50)
    if deleted_files:
        print(f"✅ Удалено файлов: {len(deleted_files)}")
        print(f"💾 Освобождено места: {total_size} bytes ({total_size/1024:.1f} KB)")
        
        print("\n📄 Удаленные файлы:")
        for filename, file_time, size in sorted(deleted_files):
            print(f"   {filename} - {file_time.strftime('%Y-%m-%d %H:%M:%S')} ({size} bytes)")
    else:
        print("✅ Старые логи не найдены")
    
    print("=" * 50)

def show_log_stats():
    """Показываем статистику логов"""
    log_dir = "logs"
    
    if not os.path.exists(log_dir):
        print("❌ Папка logs не найдена")
        return
    
    print("📊 Статистика логов:")
    print("=" * 50)
    
    total_files = 0
    total_size = 0
    file_types = {}
    
    for filename in os.listdir(log_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(log_dir, filename)
            size = os.path.getsize(file_path)
            total_files += 1
            total_size += size
            
            # Определяем тип файла
            if filename.startswith("bot_"):
                file_type = "Основные"
            elif filename.startswith("errors_"):
                file_type = "Ошибки"
            elif filename.startswith("system_"):
                file_type = "Системные"
            elif filename.startswith("discord_"):
                file_type = "Discord"
            elif filename.startswith("ollama_"):
                file_type = "Ollama"
            else:
                file_type = "Другие"
            
            if file_type not in file_types:
                file_types[file_type] = {"count": 0, "size": 0}
            
            file_types[file_type]["count"] += 1
            file_types[file_type]["size"] += size
    
    print(f"📁 Всего файлов: {total_files}")
    print(f"💾 Общий размер: {total_size} bytes ({total_size/1024:.1f} KB)")
    
    print("\n📋 По типам:")
    for file_type, stats in file_types.items():
        print(f"   {file_type}: {stats['count']} файлов, {stats['size']} bytes")
    
    print("=" * 50)

def main():
    """Главная функция"""
    print("🧹 ОЧИСТКА ЛОГОВ БОТА")
    print("=" * 50)
    
    # Показываем статистику
    show_log_stats()
    
    print("\nВыберите действие:")
    print("1. Очистить логи старше 7 дней")
    print("2. Очистить логи старше 30 дней")
    print("3. Очистить логи старше N дней")
    print("4. Показать статистику")
    print("0. Выход")
    
    choice = input("\n👉 Ваш выбор: ")
    
    if choice == "1":
        clean_old_logs(7)
    elif choice == "2":
        clean_old_logs(30)
    elif choice == "3":
        try:
            days = int(input("👉 Сколько дней хранить логи: "))
            clean_old_logs(days)
        except ValueError:
            print("❌ Неверное число")
    elif choice == "4":
        show_log_stats()
    elif choice == "0":
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
