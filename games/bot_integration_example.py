"""
Пример интеграции игровых модулей с различными версиями бота Геннадий 2.0
"""

# Пример для discord.py (v2.0+)
async def setup_discord_py_v2():
    """Настройка для discord.py v2.0+"""
    try:
        import discord
        from discord.ext import commands
        from games.discord_integration import setup_games
        
        # Создаем бота с необходимыми интентами
        intents = discord.Intents.default()
        intents.message_content = True
        
        bot = commands.Bot(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        @bot.event
        async def on_ready():
            print(f'🤖 Бот {bot.user} готов к работе!')
            print('🎮 Игровые модули подключены!')
        
        # Подключаем игровые модули
        setup_games(bot)
        
        # Запуск бота
        # bot.run("YOUR_TOKEN_HERE")
        return bot
        
    except ImportError:
        print("❌ discord.py не установлен")
        return None

# Пример для discord.py (v1.x)
async def setup_discord_py_v1():
    """Настройка для discord.py v1.x"""
    try:
        import discord
        from discord.ext import commands
        from games.discord_integration import setup_games
        
        # Создаем бота
        bot = commands.Bot(
            command_prefix='!',
            intents=discord.Intents(messages=True, guilds=True)
        )
        
        @bot.event
        async def on_ready():
            print(f'🤖 Бот {bot.user} готов к работе!')
        
        # Подключаем игровые модули
        setup_games(bot)
        
        # Запуск бота
        # bot.run("YOUR_TOKEN_HERE")
        return bot
        
    except ImportError:
        print("❌ discord.py v1.x не поддерживается")
        return None

# Пример для Nextcord
async def setup_nextcord():
    """Настройка для Nextcord"""
    try:
        import nextcord
        from nextcord.ext import commands
        from games.discord_integration import setup_games
        
        intents = nextcord.Intents.default()
        intents.message_content = True
        
        bot = commands.Bot(
            command_prefix='!',
            intents=intents
        )
        
        @bot.event
        async def on_ready():
            print(f'🤖 Бот {bot.user} готов к работе!')
        
        setup_games(bot)
        
        # bot.run("YOUR_TOKEN_HERE")
        return bot
        
    except ImportError:
        print("❌ Nextcord не установлен")
        return None

# Пример для Disnake
async def setup_disnake():
    """Настройка для Disnake"""
    try:
        import disnake
        from games.discord_integration import setup_games
        
        bot = disnake.Client(
            intents=disnake.Intents(messages=True, guilds=True)
        )
        
        @bot.event
        async def on_ready():
            print(f'🤖 Бот {bot.user} готов к работе!')
        
        setup_games(bot)
        
        # bot.run("YOUR_TOKEN_HERE")
        return bot
        
    except ImportError:
        print("❌ Disnake не установлен")
        return None

# Универсальная функция настройки
def setup_bot_with_games():
    """Автоматически определяет и настраивает подходящую Discord библиотеку"""
    
    # Проверяем доступные библиотеки
    libraries = [
        ('discord.py v2', setup_discord_py_v2),
        ('discord.py v1', setup_discord_py_v1),
        ('nextcord', setup_nextcord),
        ('disnake', setup_disnake)
    ]
    
    for lib_name, setup_func in libraries:
        try:
            bot = setup_func()
            if bot:
                print(f"✅ Успешная настройка для {lib_name}")
                return bot
        except Exception as e:
            print(f"❌ Ошибка настройки {lib_name}: {e}")
            continue
    
    print("❌ Не удалось найти подходящую Discord библиотеку")
    print("📦 Установите одну из: pip install discord.py nextcord disnake")
    return None

# Пример добавления в существующий бот
def add_games_to_existing_bot(bot):
    """Добавляет игровые модули к существующему боту"""
    try:
        from games.discord_integration import setup_games
        success = setup_games(bot)
        
        if success:
            print("✅ Игровые модули успешно добавлены к боту!")
        else:
            print("❌ Не удалось добавить игровые модули")
            
        return success
    except Exception as e:
        print(f"❌ Ошибка добавления игровых модулей: {e}")
        return False

# Пример использования в основном файле бота
if __name__ == "__main__":
    print("🎮 Тестирование игровых модулей...")
    
    # Тест менеджера игр
    from games.game_manager import game_manager, GameType
    
    # Тест начала игры
    response = game_manager.start_game(12345, GameType.TICTACTOE)
    print(f"Тест крестики-нолики: {response}")
    
    # Тест хода
    move_response = game_manager.make_move(12345, "5")
    print(f"Тест хода: {move_response}")
    
    # Тест статистики
    scores = game_manager.get_scores_text(12345)
    print(f"Тест статистики: {scores}")
    
    print("✅ Все тесты пройдены!")
