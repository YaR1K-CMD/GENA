"""
Discord кнопки для игровых модулей Геннадий 2.0
Интерактивный интерфейс для игр
"""

import discord
from discord.ui import Button, View
from discord import Interaction
from typing import Optional, Dict, Any
import asyncio
from .game_manager import game_manager, GameType

class TicTacToeView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)  # 5 минут на ход
        self.user_id = user_id
        
    async def on_timeout(self):
        """Обработка таймаута"""
        for item in self.children:
            item.disabled = True
        if hasattr(self, 'message') and self.message:
            await self.message.edit(view=self)
    
    def create_board_buttons(self):
        """Создает кнопки для игрового поля"""
        for i in range(9):
            button = Button(
                label="⬜",
                style=discord.ButtonStyle.secondary,
                custom_id=f"tictactoe_{i}",
                row=i // 3
            )
            button.callback = self.make_move_callback(i)
            self.add_item(button)
    
    def make_move_callback(self, position: int):
        """Создает callback для кнопки"""
        async def callback(interaction: Interaction):
            # Проверяем, что это тот же пользователь
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    "❌ Это не твоя игра!", 
                    ephemeral=True
                )
                return
            
            # Проверяем, что кнопка не занята
            if interaction.message.components[0].children[position].label != "⬜":
                await interaction.response.send_message(
                    "❌ Эта клетка уже занята!", 
                    ephemeral=True
                )
                return
            
            # Делаем ход
            session = game_manager.sessions.get(self.user_id)
            if not session or session.game_type != GameType.TICTACTOE:
                await interaction.response.send_message(
                    "❌ У тебя нет активной игры в крестики-нолики!", 
                    ephemeral=True
                )
                return
            
            # Обновляем кнопку игрока локально
            interaction.message.components[0].children[position].label = "❌"
            interaction.message.components[0].children[position].style = discord.ButtonStyle.danger
            interaction.message.components[0].children[position].disabled = True

            # Показываем "ИИ ходит..." перед ответом
            thinking_embed = discord.Embed(
                title="🤖 ИИ ходит...",
                description="Я думаю над ходом.",
                color=discord.Color.blurple()
            )
            await interaction.response.edit_message(embed=thinking_embed, view=self)
            await asyncio.sleep(1.2)

            # Обрабатываем ход (ИИ делает ответ внутри GameManager)
            response = game_manager.make_move(self.user_id, str(position + 1))

            # Обновляем визуал доски по текущему состоянию
            board = session.game_data['board']
            for i, cell in enumerate(board):
                btn = interaction.message.components[0].children[i]
                if cell == 'X':
                    btn.label = "❌"
                    btn.style = discord.ButtonStyle.danger
                    btn.disabled = True
                elif cell == 'O':
                    btn.label = "⭕"
                    btn.style = discord.ButtonStyle.success
                    btn.disabled = True
            
            # Обновляем доску
            board_str = game_manager._format_tictactoe_board(session.game_data['board'])
            
            # Проверяем состояние игры
            if not session.game_data['game_active']:
                # Игра окончена - отключаем все кнопки
                for item in self.children:
                    item.disabled = True
                
                # Определяем результат
                winner = None
                if game_manager._check_tictactoe_winner(session.game_data['board'], 'X'):
                    winner = "player"
                    title = "🎉 Ты победил!"
                    color = discord.Color.green()
                elif game_manager._check_tictactoe_winner(session.game_data['board'], 'O'):
                    winner = "ai"
                    title = "🤖 ИИ победил!"
                    color = discord.Color.red()
                else:
                    winner = "draw"
                    title = "🤝 Ничья!"
                    color = discord.Color.gold()
                
                embed = discord.Embed(
                    title=title,
                    description=response,
                    color=color
                )
                embed.add_field(name="📋 Игровое поле", value=board_str, inline=False)
                
                await interaction.response.edit_message(embed=embed, view=self)
                game_manager.end_game(self.user_id)
            else:
                # Игра продолжается
                embed = discord.Embed(
                    title="🎮 Крестики-нолики",
                    description=response,
                    color=discord.Color.blue()
                )
                embed.add_field(name="📋 Игровое поле", value=board_str, inline=False)
                
                await interaction.response.edit_message(embed=embed, view=self)
        
        return callback

class GameSelectionView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)  # 1 минута на выбор
        self.user_id = user_id
    
    async def on_timeout(self):
        """Обработка таймаута"""
        for item in self.children:
            item.disabled = True
        if hasattr(self, 'message') and self.message:
            await self.message.edit(view=self)
    
    @discord.ui.button(
        label="❌⭕ Крестики-нолики",
        style=discord.ButtonStyle.primary,
        custom_id="game_tictactoe",
        row=0
    )
    async def tictactoe_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Это не твое меню!", 
                ephemeral=True
            )
            return
        
        # Начинаем игру
        response = game_manager.start_game(self.user_id, GameType.TICTACTOE)
        
        # Создаем игровое поле с кнопками
        view = TicTacToeView(self.user_id)
        view.create_board_buttons()
        
        embed = discord.Embed(
            title="🎮 Крестики-нолики",
            description=response,
            color=discord.Color.blue()
        )
        
        board_str = game_manager._format_tictactoe_board(
            game_manager.sessions[self.user_id].game_data['board']
        )
        embed.add_field(name="📋 Игровое поле", value=board_str, inline=False)
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(
        label="🔢 Угадай число",
        style=discord.ButtonStyle.success,
        custom_id="game_guess",
        row=1
    )
    async def guess_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Это не твое меню!", 
                ephemeral=True
            )
            return
        
        # Начинаем игру
        response = game_manager.start_game(self.user_id, GameType.GUESS_NUMBER)
        
        # Создаем кнопки для быстрого выбора чисел
        view = NumberGuessView(self.user_id)
        
        embed = discord.Embed(
            title="🔢 Угадай число",
            description=response,
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(
        label="✂️ Камень-ножницы-бумага",
        style=discord.ButtonStyle.danger,
        custom_id="game_rps",
        row=2
    )
    async def rps_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Это не твое меню!", 
                ephemeral=True
            )
            return
        
        # Начинаем игру
        response = game_manager.start_game(self.user_id, GameType.ROCK_PAPER_SCISSORS)
        
        # Создаем кнопки для выбора
        view = RockPaperScissorsView(self.user_id)
        
        embed = discord.Embed(
            title="✂️ Камень-ножницы-бумага",
            description=response,
            color=discord.Color.red()
        )
        
        await interaction.response.edit_message(embed=embed, view=view)

class NumberGuessView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)  # 3 минуты на игру
        self.user_id = user_id
        self.create_number_buttons()
    
    async def on_timeout(self):
        """Обработка таймаута"""
        for item in self.children:
            item.disabled = True
        if hasattr(self, 'message') and self.message:
            await self.message.edit(view=self)
    
    def create_number_buttons(self):
        """Создает кнопки с числами"""
        # Создаем кнопки для популярных чисел
        popular_numbers = [1, 5, 10, 25, 50, 75, 90, 100]
        for i, num in enumerate(popular_numbers):
            button = Button(
                label=str(num),
                style=discord.ButtonStyle.secondary,
                custom_id=f"guess_{num}",
                row=i // 4
            )
            button.callback = self.make_number_callback(num)
            self.add_item(button)
    
    def make_number_callback(self, number: int):
        """Создает callback для кнопки с числом"""
        async def callback(interaction: Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    "❌ Это не твоя игра!", 
                    ephemeral=True
                )
                return
            
            await self.handle_exact_guess(interaction, str(number))
        
        return callback
    
    @discord.ui.button(
        label="🎯 Точное число",
        style=discord.ButtonStyle.primary,
        custom_id="guess_exact",
        row=2
    )
    async def guess_exact(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Это не твоя игра!", 
                ephemeral=True
            )
            return
        
        # Создаем модальное окно для ввода точного числа
        modal = NumberModal(self.user_id)
        await interaction.response.send_modal(modal)
    
    async def handle_exact_guess(self, interaction: Interaction, guess: str):
        """Обрабатывает точное число"""
        try:
            # Делаем ход
            response = game_manager.make_move(self.user_id, guess)
            
            session = game_manager.sessions.get(self.user_id)
            
            embed = discord.Embed(
                title="🔢 Угадай число",
                description=f"🎯 Твой выбор: {guess}\n\n{response}",
                color=discord.Color.green()
            )
            
            if session and not session.game_data['game_active']:
                # Игра окончена - скрываем кнопки
                await interaction.response.edit_message(embed=embed, view=None)
                game_manager.end_game(self.user_id)
            else:
                # Игра продолжается
                await interaction.response.edit_message(embed=embed, view=self)
                
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Ошибка: {str(e)}", 
                ephemeral=True
            )

class RockPaperScissorsView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)  # 1 минута на ход
        self.user_id = user_id
    
    async def on_timeout(self):
        """Обработка таймаута"""
        for item in self.children:
            item.disabled = True
        if hasattr(self, 'message') and self.message:
            await self.message.edit(view=self)
    
    @discord.ui.button(
        label="🪨",
        style=discord.ButtonStyle.primary,
        custom_id="rps_rock",
        row=0
    )
    async def rock_button(self, interaction: Interaction, button: Button):
        await self.handle_rps_move(interaction, "камень")
    
    @discord.ui.button(
        label="📄",
        style=discord.ButtonStyle.success,
        custom_id="rps_paper",
        row=0
    )
    async def paper_button(self, interaction: Interaction, button: Button):
        await self.handle_rps_move(interaction, "бумага")
    
    @discord.ui.button(
        label="✂️",
        style=discord.ButtonStyle.danger,
        custom_id="rps_scissors",
        row=0
    )
    async def scissors_button(self, interaction: Interaction, button: Button):
        await self.handle_rps_move(interaction, "ножницы")
    
    async def handle_rps_move(self, interaction: Interaction, move: str):
        """Обрабатывает ход в камень-ножницы-бумагу"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Это не твоя игра!", 
                ephemeral=True
            )
            return
        
        # Делаем ход
        response = game_manager.make_move(self.user_id, move)
        
        embed = discord.Embed(
            title="✂️ Камень-ножницы-бумага",
            description=response,
            color=discord.Color.red()
        )
        session = game_manager.sessions.get(self.user_id)
        if session and not session.game_data['game_active']:
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            game_manager.end_game(self.user_id)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

class NumberModal(discord.ui.Modal):
    def __init__(self, user_id: int):
        super().__init__(title="Угадай число")
        self.user_id = user_id
        
        self.number_input = discord.ui.TextInput(
            label="Введите число от 1 до 100",
            placeholder="50",
            required=True,
            max_length=3,
            style=discord.TextStyle.short
        )
        self.add_item(self.number_input)
    
    async def on_submit(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Это не твоя игра!", 
                ephemeral=True
            )
            return
        
        try:
            guess = self.number_input.value.strip()
            # Проверяем, что это число
            num = int(guess)
            if not 1 <= num <= 100:
                await interaction.response.send_message(
                    "❌ Введите число от 1 до 100!", 
                    ephemeral=True
                )
                return
            
            # Делаем ход
            response = game_manager.make_move(self.user_id, guess)
            
            session = game_manager.sessions.get(self.user_id)
            
            embed = discord.Embed(
                title="🔢 Угадай число",
                description=f"🎯 Твой выбор: {guess}\n\n{response}",
                color=discord.Color.green()
            )
            
            if session and not session.game_data['game_active']:
                # Игра окончена - скрываем кнопки
                await interaction.response.edit_message(embed=embed, view=None)
                game_manager.end_game(self.user_id)
            else:
                # Игра продолжается
                view = NumberGuessView(self.user_id)
                await interaction.response.edit_message(embed=embed, view=view)
                
        except ValueError:
            await interaction.response.send_message(
                "❌ Введите корректное число!", 
                ephemeral=True
            )

# Импортируем random для NumberGuessView
import random
