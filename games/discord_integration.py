"""
Интеграция игровых модулей с Discord ботом Геннадий 2.0
Поддержка всех версий: discord.py, nextcord, disnake, py-cord
"""

import asyncio
import sys
from typing import Any, Dict, Optional, Union, Callable
from .game_manager import game_manager, GameType

# Определяем тип Discord библиотеки
DISCORD_LIBRARY = None
discord = None

# Попытка импорта различных Discord библиотек
try:
    import discord
    DISCORD_LIBRARY = "discord.py"
except ImportError:
    try:
        import nextcord as discord
        DISCORD_LIBRARY = "nextcord"
    except ImportError:
        try:
            import disnake as discord
            DISCORD_LIBRARY = "disnake"
        except ImportError:
            try:
                import discord as discord
                DISCORD_LIBRARY = "py-cord"
            except ImportError:
                print("❌ Не найдена совместимая Discord библиотека")
                print("Установите одну из: pip install discord.py nextcord disnake py-cord")

# Импортируем кнопки (если доступно)
try:
    from .discord_buttons import (
        GameSelectionView, 
        TicTacToeView, 
        NumberGuessView, 
        RockPaperScissorsView
    )
    BUTTONS_AVAILABLE = True
    print("✅ Discord кнопки доступны")
except ImportError as e:
    BUTTONS_AVAILABLE = False
    print(f"⚠️ Кнопки недоступны: {e}")

class DiscordGameIntegration:
    def __init__(self):
        self.library = DISCORD_LIBRARY
        self.game_manager = game_manager
        
    def get_commands(self) -> Dict[str, Callable]:
        """Возвращает словарь команд для бота"""
        return {
            'game': self.cmd_game,
            'игра': self.cmd_game,
            'move': self.cmd_move,
            'ход': self.cmd_move,
            'scores': self.cmd_scores,
            'статистика': self.cmd_scores,
            'endgame': self.cmd_endgame,
            'конецигры': self.cmd_endgame
        }
    
    def get_slash_commands(self):
        """Возвращает слэш-команды для современных Discord библиотек"""
        if self.library in ["discord.py", "py-cord"] and hasattr(discord, 'app_commands'):
            return self._get_discord_py_slash_commands()
        elif self.library == "nextcord":
            return self._get_nextcord_slash_commands()
        elif self.library == "disnake":
            return self._get_disnake_slash_commands()
        return []
    
    def _get_discord_py_slash_commands(self):
        """Слэш-команды для discord.py v2.0+"""
        import discord.app_commands
        
        # Команда игры
        @discord.app_commands.command(
            name="game",
            description="Начать игру с ИИ"
        )
        @discord.app_commands.describe(
            game_type="Выберите тип игры"
        )
        @discord.app_commands.choices(
            game_type=[
                discord.app_commands.Choice(name="Крестики-нолики", value="tictactoe"),
                discord.app_commands.Choice(name="Угадай число", value="guess_number"),
                discord.app_commands.Choice(name="Камень-ножницы-бумага", value="rps")
            ]
        )
        async def game_slash(interaction: discord.Interaction, game_type: str):
            await interaction.response.defer()
            
            game_type_map = {
                'tictactoe': GameType.TICTACTOE,
                'guess_number': GameType.GUESS_NUMBER,
                'rps': GameType.ROCK_PAPER_SCISSORS
            }
            
            selected_type = game_type_map.get(game_type, GameType.TICTACTOE)
            response = self.game_manager.start_game(interaction.user.id, selected_type)
            
            embed = discord.Embed(
                title="🎮 Игра начата!",
                description=response,
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
        
        # Команда хода
        @discord.app_commands.command(
            name="move",
            description="Сделать ход в игре"
        )
        @discord.app_commands.describe(
            move="Ваш ход (число для крестиков-ноликов, число для угадайки, выбор для КНБ)"
        )
        async def move_slash(interaction: discord.Interaction, move: str):
            await interaction.response.defer()
            
            response = self.game_manager.make_move(interaction.user.id, move)
            
            embed = discord.Embed(
                title="🎯 Ход сделан!",
                description=response,
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
        
        # Команда статистики
        @discord.app_commands.command(
            name="scores",
            description="Показать статистику игр"
        )
        async def scores_slash(interaction: discord.Interaction):
            await interaction.response.defer()
            
            response = self.game_manager.get_scores_text(interaction.user.id)
            
            embed = discord.Embed(
                title="📊 Статистика игр",
                description=response,
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
        
        return [game_slash, move_slash, scores_slash]
    
    def _get_nextcord_slash_commands(self):
        """Слэш-команды для Nextcord"""
        import nextcord
        
        class GameSlashCommands(nextcord.Client):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        
        # Здесь можно добавить команды для Nextcord
        return []
    
    def _get_disnake_slash_commands(self):
        """Слэш-команды для Disnake"""
        import disnake
        
        # Здесь можно добавить команды для Disnake
        return []
    
    async def cmd_game(self, message, args: list = None) -> Optional[str]:
        """Обработчик команды /game"""
        user_id = message.author.id
        
        if not args:
            # Показываем доступные игры с кнопками
            if BUTTONS_AVAILABLE and self.library in ["discord.py", "py-cord"]:
                print(f"🎮 Используем кнопки для пользователя {user_id}")
                # Используем кнопки
                view = GameSelectionView(user_id)
                
                embed = discord.Embed(
                    title="🎮 Игры с ИИ",
                    description="Выбери игру, в которую хочешь сыграть:",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="❌⭕ Крестики-нолики",
                    value="Классическая стратегическая игра с умным ИИ",
                    inline=False
                )
                embed.add_field(
                    name="🔢 Угадай число", 
                    value="Угадай число от 1 до 100 за 7 попыток",
                    inline=False
                )
                embed.add_field(
                    name="✂️ Камень-ножницы-бумага",
                    value="Классическая игра на удачу против ИИ",
                    inline=False
                )
                
                await message.reply(embed=embed, view=view)
                return None
            else:
                print(f"📝 Используем текстовый режим для пользователя {user_id}")
                print(f"BUTTONS_AVAILABLE: {BUTTONS_AVAILABLE}, library: {self.library}")
                # Текстовый режим
                games_text = """
🎮 **Доступные игры:**

1. **Крестики-нолики** - `!game tictactoe`
   Классическая стратегическая игра

2. **Угадай число** - `!game guess` 
   Угадай число от 1 до 100 за 7 попыток

3. **Камень-ножницы-бумага** - `!game rps`
   Классическая игра на удачу

💭 Используй: `!game [название игры]`
                """
                
                if self.library in ["discord.py", "py-cord"]:
                    embed = discord.Embed(
                        title="🎮 Игры с ИИ",
                        description=games_text,
                        color=discord.Color.blue()
                    )
                    await message.reply(embed=embed)
                    return None
                else:
                    return games_text
        
        # Определяем тип игры
        game_name = args[0].lower()
        game_type = None
        
        if game_name in ['tictactoe', 'крестики', 'нолики', 'кн']:
            game_type = GameType.TICTACTOE
        elif game_name in ['guess', 'угадай', 'число', 'угадайка']:
            game_type = GameType.GUESS_NUMBER
        elif game_name in ['rps', 'камень', 'ножницы', 'бумага', 'кнб']:
            game_type = GameType.ROCK_PAPER_SCISSORS
        
        if not game_type:
            response = "❌ Неизвестная игра. Используй: `!game` для списка доступных игр"
        else:
            # Начинаем игру с кнопками если возможно
            if BUTTONS_AVAILABLE and self.library in ["discord.py", "py-cord"]:
                if game_type == GameType.TICTACTOE:
                    response = game_manager.start_game(user_id, game_type)
                    view = TicTacToeView(user_id)
                    view.create_board_buttons()
                    
                    embed = discord.Embed(
                        title="🎮 Крестики-нолики",
                        description=response,
                        color=discord.Color.blue()
                    )
                    
                    board_str = game_manager._format_tictactoe_board(
                        game_manager.sessions[user_id].game_data['board']
                    )
                    embed.add_field(name="📋 Игровое поле", value=board_str, inline=False)
                    
                    await message.reply(embed=embed, view=view)
                    return None
                    
                elif game_type == GameType.GUESS_NUMBER:
                    response = game_manager.start_game(user_id, game_type)
                    view = NumberGuessView(user_id)
                    
                    embed = discord.Embed(
                        title="🔢 Угадай число",
                        description=response,
                        color=discord.Color.green()
                    )
                    
                    await message.reply(embed=embed, view=view)
                    return None
                    
                elif game_type == GameType.ROCK_PAPER_SCISSORS:
                    response = game_manager.start_game(user_id, game_type)
                    view = RockPaperScissorsView(user_id)
                    
                    embed = discord.Embed(
                        title="✂️ Камень-ножницы-бумага",
                        description=response,
                        color=discord.Color.red()
                    )
                    
                    await message.reply(embed=embed, view=view)
                    return None
            else:
                # Текстовый режим
                response = game_manager.start_game(user_id, game_type)
        
        if self.library in ["discord.py", "py-cord"]:
            embed = discord.Embed(
                title="🎮 Игра начата!",
                description=response,
                color=discord.Color.green()
            )
            await message.reply(embed=embed)
            return None
        else:
            return response
    
    async def cmd_move(self, message, args: list = None) -> Optional[str]:
        """Обработчик команды /move"""
        user_id = message.author.id
        
        if not args:
            response = "❌ Укажи твой ход. Например: `!move 5` для крестиков-ноликов"
        else:
            move = ' '.join(args)
            # Если активны крестики-нолики — показываем ожидание хода ИИ
            session = self.game_manager.sessions.get(user_id)
            temp_msg = None
            if session and session.game_type == GameType.TICTACTOE and session.game_data.get('game_active', True):
                try:
                    temp_msg = await message.reply("🤖 ИИ ходит...")
                except Exception:
                    temp_msg = None
            response = self.game_manager.make_move(user_id, move)
            if temp_msg:
                try:
                    await temp_msg.delete()
                except Exception:
                    pass
            session = self.game_manager.sessions.get(user_id)
            if session and not session.game_data.get('game_active', True):
                self.game_manager.end_game(user_id)
        
        if self.library in ["discord.py", "py-cord"]:
            color = discord.Color.green() if "❌" not in response else discord.Color.red()
            embed = discord.Embed(
                title="🎯 Ход сделан!",
                description=response,
                color=color
            )
            await message.reply(embed=embed)
            return None
        else:
            return response
    
    async def cmd_scores(self, message, args: list = None) -> Optional[str]:
        """Обработчик команды /scores"""
        user_id = message.author.id
        response = self.game_manager.get_scores_text(user_id)
        
        if self.library in ["discord.py", "py-cord"]:
            embed = discord.Embed(
                title="📊 Твоя статистика",
                description=response,
                color=discord.Color.gold()
            )
            await message.reply(embed=embed)
            return None
        else:
            return response
    
    async def cmd_endgame(self, message, args: list = None) -> Optional[str]:
        """Обработчик команды /endgame"""
        user_id = message.author.id
        response = self.game_manager.end_game(user_id)
        
        if self.library in ["discord.py", "py-cord"]:
            embed = discord.Embed(
                title="🛑 Игра завершена",
                description=response,
                color=discord.Color.orange()
            )
            await message.reply(embed=embed)
            return None
        else:
            return response
    
    def setup_bot_commands(self, bot):
        """Настраивает команды для бота"""
        # НЕ переопределяем on_message - просто возвращаем True для успешной инициализации
        print("🎮 Игровые команды интегрированы в существующий on_message")
        return True

# Глобальный экземпляр интеграции
discord_integration = DiscordGameIntegration()

# Функция для удобного подключения к боту
def setup_games(bot):
    """Подключает игровые модули к Discord боту"""
    if not DISCORD_LIBRARY:
        print("❌ Discord библиотека не найдена")
        return False
    
    print(f"🎮 Подключаю игровые модули для {DISCORD_LIBRARY}...")
    discord_integration.setup_bot_commands(bot)
    print("✅ Игровые модули успешно подключены!")
    
    return True

# Экспортируем для использования в основных файлах бота
__all__ = ['setup_games', 'discord_integration', 'game_manager']
