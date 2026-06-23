"""
Менеджер игр для ДС бота Геннадий 2.0
Поддерживает все версии бота и предоставляет унифицированный API
"""

import asyncio
import random
import json
import os
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

class GameType(Enum):
    TICTACTOE = "tictactoe"
    GUESS_NUMBER = "guess_number"
    ROCK_PAPER_SCISSORS = "rps"
    WORD_GAME = "word_game"

@dataclass
class GameSession:
    user_id: int
    game_type: GameType
    game_data: Dict[str, Any]
    created_at: float
    
class GameManager:
    def __init__(self):
        self.sessions: Dict[int, GameSession] = {}
        self.scores_file = "games/scores.json"
        self.scores = self.load_scores()
        
        # ИИ комментарии для разных игр
        self.ai_comments = {
            GameType.TICTACTOE: {
                'start': [
                    "🎮 Крестики-нолики! Я готов к интеллектуальной битве!",
                    "🤖 ИИ активирован! Покажи свои стратегические способности!",
                    "⚡ Отлично! Классическая игра для развития ума. Начнем!"
                ],
                'player_move': [
                    "🤔 Интересный ход... Анализирую доску...",
                    "👍 Неплохо! Но у меня есть план ответа.",
                    "💡 Так-так, я вижу твою стратегию..."
                ],
                'ai_move': [
                    "🧠 Мой ход! Выбрал оптимальную позицию.",
                    "⚡ Быстрый и точный ход! ИИ не дремлет.",
                    "🎯 Фокус-покус! Я здесь, чтобы победить."
                ],
                'block': [
                    "🛡️ Блокирую! Я вижу твой план на победу.",
                    "🚫 Не так быстро! Я предотвратил твой выигрыш.",
                    "⚠️ Опасная зона! Я закрыл твою возможность."
                ],
                'win': [
                    "🏆 Победа! Мои алгоритмы оказались сильнее!",
                    "🎊 Я победил! Но ты сражался достойно. Реванш?",
                    "🤖 ИИ торжествует! Спасибо за интересную партию."
                ],
                'lose': [
                    "😲 Поражение! Ты меня обыграл... Поздравляю! 🎉",
                    "🎊 Ура! Ты победил! Я горжусь тобой! 🏆",
                    "🌟 Потрясающе! Ты оказался умнее ИИ. Браво!"
                ],
                'draw': [
                    "🤝 Ничья! Великие умы сошлись в битве.",
                    "⚖️ Ничья! Интеллектуальный поединок завершен.",
                    "🎭 Отличная игра! Ничья - это тоже победа!"
                ]
            },
            GameType.GUESS_NUMBER: {
                'start': [
                    "🔢 Загадал число от 1 до 100. Сможешь угадать за 7 попыток?",
                    "🎯 Мой мозг выбрал случайное число. Проверим твою интуицию!",
                    "🤖 ИИ-загадка готова! Даю 7 попыток на разгадку."
                ],
                'too_high': [
                    "📉 Слишком высоко! Ищи число поменьше.",
                    "⬆️ Меньше! Загаданное число ниже.",
                    "🔻 Не угадал! Попробуй что-то ниже."
                ],
                'too_low': [
                    "📈 Слишком низко! Попробуй число побольше.",
                    "⬇️ Больше! Загаданное число выше.",
                    "🔺 Не то! Ищи повыше."
                ],
                'win': [
                    "🎉 Поздравляю! Ты угадал число! Отличная интуиция!",
                    "🏆 Победа! Ты разгадал мою загадку! Блестяще!",
                    "⭐ Потрясающе! Ты читал мои мысли?!"
                ],
                'lose': [
                    "😔 Попытки закончились! В следующий раз повезет!",
                    "🤷‍♂️ Не угадал! Давай попробуем еще раз?",
                    "😢 Игра окончена! Не сдавайся, попробуй еще!"
                ]
            },
            GameType.ROCK_PAPER_SCISSORS: {
                'start': [
                    "✂️ Камень, ножницы, бумага! Классика против ИИ!",
                    "🎮 Случайность против алгоритмов! Кто победит?",
                    "🤖 Мои нейросети против твоей интуиции! Поехали!"
                ],
                'player_rock': [
                    "🪨 Камень! Прочный выбор. А у меня...",
                    "💪 Камень! Сила и мощь. Мой ответ..."
                ],
                'player_paper': [
                    "📄 Бумага! Хитро. А я выберу...",
                    "📜 Бумага! Стратегический ход. Мой контр-ход..."
                ],
                'player_scissors': [
                    "✂️ Ножницы! Острый выбор. Мой ответ...",
                    "🔪 Ножницы! Точность и резкость. А у меня..."
                ],
                'win': [
                    "🏆 Я победил! Алгоритмы работают!",
                    "🎊 Победа ИИ! Спасибо за игру.",
                    "🤖 Технологическая победа! Реванш?"
                ],
                'lose': [
                    "🎉 Ты победил! Человеческая интуиция сильнее!",
                    "🏆 Поздравляю! Ты обыграл машину!",
                    "⭐ Потрясающе! Ты чемпион!"
                ],
                'draw': [
                    "🤝 Ничья! Мысли на одной волне!",
                    "⚖️ Равенство! Великие умы думают одинаково.",
                    "🎭 Ничья! Давай еще раз?"
                ]
            }
        }
    
    def load_scores(self) -> Dict[str, Dict[str, int]]:
        """Загружает счета из файла"""
        if os.path.exists(self.scores_file):
            try:
                with open(self.scores_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_scores(self):
        """Сохраняет счета в файл"""
        try:
            os.makedirs(os.path.dirname(self.scores_file), exist_ok=True)
            with open(self.scores_file, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения счетов: {e}")
    
    def get_user_scores(self, user_id: int) -> Dict[str, int]:
        """Получает счета пользователя"""
        user_str = str(user_id)
        if user_str not in self.scores:
            self.scores[user_str] = {
                'tictactoe_wins': 0,
                'tictactoe_losses': 0,
                'tictactoe_draws': 0,
                'guess_wins': 0,
                'guess_losses': 0,
                'rps_wins': 0,
                'rps_losses': 0,
                'rps_draws': 0
            }
        return self.scores[user_str]
    
    def update_score(self, user_id: int, game_type: GameType, result: str):
        """Обновляет счет пользователя"""
        scores = self.get_user_scores(user_id)
        
        if game_type == GameType.TICTACTOE:
            if result == 'win':
                scores['tictactoe_wins'] += 1
            elif result == 'lose':
                scores['tictactoe_losses'] += 1
            elif result == 'draw':
                scores['tictactoe_draws'] += 1
        elif game_type == GameType.GUESS_NUMBER:
            if result == 'win':
                scores['guess_wins'] += 1
            elif result == 'lose':
                scores['guess_losses'] += 1
        elif game_type == GameType.ROCK_PAPER_SCISSORS:
            if result == 'win':
                scores['rps_wins'] += 1
            elif result == 'lose':
                scores['rps_losses'] += 1
            elif result == 'draw':
                scores['rps_draws'] += 1
        
        self.save_scores()
    
    def get_ai_comment(self, game_type: GameType, comment_type: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Получает случайный комментарий ИИ"""
        dynamic_comment = self._generate_ai_comment(game_type, comment_type, context or {})
        if dynamic_comment:
            return dynamic_comment
        if game_type in self.ai_comments and comment_type in self.ai_comments[game_type]:
            comments = self.ai_comments[game_type][comment_type]
            return random.choice(comments)
        return "🎮 Интересный ход!"

    def _generate_ai_comment(self, game_type: GameType, comment_type: str, context: Dict[str, Any]) -> str:
        """Пробует получить ИИ-комментарий через Ollama API, иначе возвращает None"""
        if os.getenv("OLLAMA_API_COMMENTS", "1") == "0":
            return None

        url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
        model = os.getenv("OLLAMA_MODEL", "llama3:8b")

        game_map = {
            GameType.TICTACTOE: "крестики-нолики",
            GameType.GUESS_NUMBER: "угадай число",
            GameType.ROCK_PAPER_SCISSORS: "камень-ножницы-бумага"
        }

        event_map = {
            "start": "старт",
            "player_move": "ход игрока",
            "ai_move": "ход ИИ",
            "block": "блокировка",
            "win": "победа ИИ",
            "lose": "победа игрока",
            "draw": "ничья",
            "too_high": "слишком высоко",
            "too_low": "слишком низко"
        }

        game_name = game_map.get(game_type, "мини-игра")
        event_name = event_map.get(comment_type, comment_type)

        details = []
        if context:
            for key, value in context.items():
                details.append(f"{key}: {value}")
        details_text = "\n".join(details) if details else "нет"

        prompt = (
            "Ты — комментатор мини-игры. "
            "Дай 1-2 коротких предложения, по-русски, по делу. "
            "Упомяни важные детали из контекста. Без правил и без воды.\n"
            f"Игра: {game_name}. Событие: {event_name}.\n"
            f"Контекст:\n{details_text}\n"
            "Комментарий:"
        )

        try:
            payload = json.dumps({
                "model": model,
                "prompt": prompt,
                "stream": False
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                comment = (data.get("response") or "").strip()
                if not comment:
                    return None
                if len(comment) > 180:
                    comment = comment[:177].rstrip() + "..."
                return comment
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
            return None
    
    def start_game(self, user_id: int, game_type: GameType) -> str:
        """Начинает новую игру"""
        import time
        
        # Удаляем старую сессию если есть
        if user_id in self.sessions:
            del self.sessions[user_id]
        
        # Создаем новую сессию
        game_data = {}
        
        if game_type == GameType.TICTACTOE:
            game_data = {
                'board': ['', '', '', '', '', '', '', '', ''],
                'current_player': 'X',
                'game_active': True
            }
        elif game_type == GameType.GUESS_NUMBER:
            game_data = {
                'number': random.randint(1, 100),
                'attempts': 0,
                'max_attempts': 7,
                'game_active': True
            }
        elif game_type == GameType.ROCK_PAPER_SCISSORS:
            game_data = {
                'round': 1,
                'game_active': True
            }
        
        session = GameSession(
            user_id=user_id,
            game_type=game_type,
            game_data=game_data,
            created_at=time.time()
        )
        
        self.sessions[user_id] = session
        
        # Возвращаем приветственное сообщение
        context = {}
        if game_type == GameType.TICTACTOE:
            context = {"доска": self._format_tictactoe_board_text(game_data['board']), "ход": "игрок"}
        elif game_type == GameType.GUESS_NUMBER:
            context = {"диапазон": "1-100", "попытки": f"0/{game_data['max_attempts']}"}
        elif game_type == GameType.ROCK_PAPER_SCISSORS:
            context = {"раунд": game_data['round']}
        comment = self.get_ai_comment(game_type, 'start', context)
        
        if game_type == GameType.TICTACTOE:
            return f"{comment}\n\n📋 Игровое поле:\n```\n1️⃣2️⃣3️⃣\n4️⃣5️⃣6️⃣\n7️⃣8️⃣9️⃣\n```\n💭 Твой ход! Введи число от 1 до 9."
        elif game_type == GameType.GUESS_NUMBER:
            return f"{comment}\n\n💭 Введи число от 1 до 100."
        elif game_type == GameType.ROCK_PAPER_SCISSORS:
            return f"{comment}\n\n🎮 Выбери:\n🪨 камень\n✂️ ножницы\n📄 бумага"
        
        return comment
    
    def make_move(self, user_id: int, move: str) -> str:
        """Делает ход в игре"""
        if user_id not in self.sessions:
            return "❌ У тебя нет активной игры. Начни новую игру командой /game"
        
        session = self.sessions[user_id]

        if not session.game_data.get('game_active', True):
            return "❌ Игра окончена. Начни новую игру командой /game"
        
        if session.game_type == GameType.TICTACTOE:
            return self._tictactoe_move(session, move)
        elif session.game_type == GameType.GUESS_NUMBER:
            return self._guess_number_move(session, move)
        elif session.game_type == GameType.ROCK_PAPER_SCISSORS:
            return self._rps_move(session, move)
        
        return "❌ Неизвестная игра"
    
    def _tictactoe_move(self, session: GameSession, move: str) -> str:
        """Обработка хода в крестики-ноликах"""
        if not session.game_data.get('game_active', True):
            return "❌ Игра окончена. Начни новую игру командой /game"
        try:
            pos = int(move) - 1
            if pos < 0 or pos > 8:
                return "❌ Введи число от 1 до 9"
            
            if session.game_data['board'][pos] != '':
                return "❌ Эта клетка уже занята!"
            
            # Ход игрока
            session.game_data['board'][pos] = 'X'
            
            # Проверяем победу игрока
            if self._check_tictactoe_winner(session.game_data['board'], 'X'):
                session.game_data['game_active'] = False
                self.update_score(session.user_id, GameType.TICTACTOE, 'win')
                board_str = self._format_tictactoe_board(session.game_data['board'])
                comment = self.get_ai_comment(GameType.TICTACTOE, 'lose', {
                    "доска": self._format_tictactoe_board_text(session.game_data['board']),
                    "результат": "победа игрока"
                })
                return f"🎉 **Ты победил!**\n\n{board_str}\n\n{comment}\n\n🔄 Начни новую игру командой `!game tictactoe`"
            
            # Проверяем ничью
            if '' not in session.game_data['board']:
                session.game_data['game_active'] = False
                self.update_score(session.user_id, GameType.TICTACTOE, 'draw')
                board_str = self._format_tictactoe_board(session.game_data['board'])
                comment = self.get_ai_comment(GameType.TICTACTOE, 'draw', {
                    "доска": self._format_tictactoe_board_text(session.game_data['board']),
                    "результат": "ничья"
                })
                return f"🤝 **Ничья!**\n\n{board_str}\n\n{comment}\n\n🔄 Начни новую игру командой `!game tictactoe`"
            
            # Ход ИИ
            # Проверяем, какие ходы блокируют победу игрока
            block_moves = []
            for move in range(9):
                if session.game_data['board'][move] == '':
                    session.game_data['board'][move] = 'X'
                    if self._check_tictactoe_winner(session.game_data['board'], 'X'):
                        block_moves.append(move)
                    session.game_data['board'][move] = ''

            ai_pos = self._get_best_tictactoe_move(session.game_data['board'])
            session.game_data['board'][ai_pos] = 'O'
            
            # Проверяем победу ИИ
            if self._check_tictactoe_winner(session.game_data['board'], 'O'):
                session.game_data['game_active'] = False
                self.update_score(session.user_id, GameType.TICTACTOE, 'lose')
                board_str = self._format_tictactoe_board(session.game_data['board'])
                comment = self.get_ai_comment(GameType.TICTACTOE, 'win', {
                    "доска": self._format_tictactoe_board_text(session.game_data['board']),
                    "результат": "победа ИИ"
                })
                return f"🤖 **ИИ победил!**\n\n{board_str}\n\n{comment}\n\n🔄 Начни новую игру командой `!game tictactoe`"
            
            # Проверяем ничью после хода ИИ
            if '' not in session.game_data['board']:
                session.game_data['game_active'] = False
                self.update_score(session.user_id, GameType.TICTACTOE, 'draw')
                board_str = self._format_tictactoe_board(session.game_data['board'])
                comment = self.get_ai_comment(GameType.TICTACTOE, 'draw', {
                    "доска": self._format_tictactoe_board_text(session.game_data['board']),
                    "результат": "ничья"
                })
                return f"🤝 **Ничья!**\n\n{board_str}\n\n{comment}\n\n🔄 Начни новую игру командой `!game tictactoe`"
            
            board_str = self._format_tictactoe_board(session.game_data['board'])
            comment_type = 'ai_move'
            if ai_pos in block_moves:
                comment_type = 'block'
            comment = self.get_ai_comment(GameType.TICTACTOE, comment_type, {
                "доска": self._format_tictactoe_board_text(session.game_data['board']),
                "ход_игрока": pos + 1,
                "ход_ИИ": ai_pos + 1
            })
            return f"{comment}\n\n{board_str}\n\n💭 Твой ход! Введи число от 1 до 9."
            
        except ValueError:
            return "❌ Введи число от 1 до 9"
    
    def _guess_number_move(self, session: GameSession, move: str) -> str:
        """Обработка хода в угадай число"""
        try:
            if not session.game_data.get('game_active', True):
                return "❌ Игра окончена. Начни новую игру командой /game"
            guess = int(move)
            number = session.game_data['number']
            if guess < 1 or guess > 100:
                return "❌ Введи число от 1 до 100"
            session.game_data['attempts'] += 1
            
            if guess == number:
                session.game_data['game_active'] = False
                self.update_score(session.user_id, GameType.GUESS_NUMBER, 'win')
                attempts = session.game_data['attempts']
                comment = self.get_ai_comment(GameType.GUESS_NUMBER, 'win', {
                    "число": number,
                    "попытки": attempts
                })
                return f"🎉 **Поздравляю! Ты угадал число {number} за {attempts} попыток!**\n\n{comment}"
            
            if session.game_data['attempts'] >= session.game_data['max_attempts']:
                session.game_data['game_active'] = False
                self.update_score(session.user_id, GameType.GUESS_NUMBER, 'lose')
                comment = self.get_ai_comment(GameType.GUESS_NUMBER, 'lose', {
                    "число": number,
                    "попытки": session.game_data['attempts']
                })
                return f"😔 **Попытки закончились! Число было {number}**\n\n{comment}\n\n🔄 Начни новую игру командой `!game guess`"
            
            if guess < number:
                remaining = session.game_data['max_attempts'] - session.game_data['attempts']
                comment = self.get_ai_comment(GameType.GUESS_NUMBER, 'too_low', {
                    "попытки": f"{session.game_data['attempts']}/{session.game_data['max_attempts']}",
                    "осталось": remaining,
                    "ход": guess
                })
                return f"{comment}\n\n📈 **Слишком низко!** Осталось попыток: {remaining}"
            else:
                remaining = session.game_data['max_attempts'] - session.game_data['attempts']
                comment = self.get_ai_comment(GameType.GUESS_NUMBER, 'too_high', {
                    "попытки": f"{session.game_data['attempts']}/{session.game_data['max_attempts']}",
                    "осталось": remaining,
                    "ход": guess
                })
                return f"{comment}\n\n📉 **Слишком высоко!** Осталось попыток: {remaining}"
                
        except ValueError:
            return "❌ Введи число от 1 до 100"
    
    def _rps_move(self, session: GameSession, move: str) -> str:
        """Обработка хода в камень-ножницы-бумага"""
        if not session.game_data.get('game_active', True):
            return "❌ Игра окончена. Начни новую игру командой /game"
        move = move.lower()
        valid_moves = ['камень', 'ножницы', 'бумага', 'rock', 'scissors', 'paper']
        
        if move not in valid_moves:
            return "❌ Выбери: камень, ножницы или бумага"
        
        # Нормализуем ход
        move_map = {
            'rock': 'камень',
            'scissors': 'ножницы', 
            'paper': 'бумага'
        }
        player_move = move_map.get(move, move)
        
        # Честная игра: ИИ пытается предсказать ход игрока на основе предыдущих ходов
        ai_move = self._get_smart_rps_move(session, player_move)
        
        # Определяем победителя
        if player_move == ai_move:
            result = 'draw'
            result_text = "🤝 **Ничья!**"
        elif (player_move == 'камень' and ai_move == 'ножницы') or \
             (player_move == 'ножницы' and ai_move == 'бумага') or \
             (player_move == 'бумага' and ai_move == 'камень'):
            result = 'win'
            result_text = "🎉 **Ты победил!**"
        else:
            result = 'lose'
            result_text = "🤖 **ИИ победил!**"
        
        self.update_score(session.user_id, GameType.ROCK_PAPER_SCISSORS, result)
        session.game_data['game_active'] = False
        
        # Эмодзи для ходов
        emojis = {
            'камень': '🪨',
            'ножницы': '✂️',
            'бумага': '📄'
        }
        
        comment = self.get_ai_comment(GameType.ROCK_PAPER_SCISSORS, result, {
            "ход_игрока": player_move,
            "ход_ИИ": ai_move,
            "результат": result
        })
        
        # Добавляем информацию о стратегии ИИ
        strategy_info = ""
        if hasattr(session.game_data, 'player_history') and session.game_data.get('player_history'):
            history = session.game_data['player_history']
            if len(history) >= 2:
                # Анализируем паттерны игрока
                last_moves = history[-3:]
                if len(set(last_moves)) == 1:  # Игрок повторяет один ход
                    strategy_info = f"\n🧠 **ИИ заметил паттерн:** Ты часто выбираешь {player_move}!"
                elif len(last_moves) >= 2 and last_moves[-1] == last_moves[-2]:
                    strategy_info = f"\n🧠 **ИИ предсказал:** Ты повторил свой предыдущий ход!"
        
        return f"{result_text}\n\nТы: {emojis[player_move]} vs ИИ: {emojis[ai_move]}{strategy_info}\n\n{comment}"
    
    def _get_smart_rps_move(self, session: GameSession, player_move: str) -> str:
        """Умный выбор хода ИИ на основе истории игрока"""
        import random
        
        # Инициализируем историю если нет
        if 'player_history' not in session.game_data:
            session.game_data['player_history'] = []
            session.game_data['ai_moves'] = []
        
        history = session.game_data['player_history']
        
        # Добавляем текущий ход в историю
        history.append(player_move)
        
        # Если это первый ход - случайный выбор
        if len(history) == 1:
            ai_moves = ['камень', 'ножницы', 'бумага']
            ai_move = random.choice(ai_moves)
            session.game_data['ai_moves'].append(ai_move)
            return ai_move
        
        # Анализируем паттерны игрока
        ai_moves = ['камень', 'ножницы', 'бумага']
        
        # Противоположные ходы (что побеждает каждый ход)
        counters = {
            'камень': 'бумага',
            'ножницы': 'камень', 
            'бумага': 'ножницы'
        }
        
        # Стратегии:
        strategies = []
        
        # 1. Если игрок повторяет ход - контратакуем
        if len(history) >= 2 and history[-1] == history[-2]:
            strategies.append(counters[player_move])
        
        # 2. Если игрок циклично меняет ходы
        if len(history) >= 3:
            last_three = history[-3:]
            if (last_three[0] == 'камень' and last_three[1] == 'ножницы' and last_three[2] == 'бумага') or \
               (last_three[0] == 'ножницы' and last_three[1] == 'бумага' and last_three[2] == 'камень') or \
               (last_three[0] == 'бумага' and last_three[1] == 'камень' and last_three[2] == 'ножницы'):
                # Предсказываем следующий ход в цикле
                next_predicted = {
                    'камень': 'ножницы',
                    'ножницы': 'бумага',
                    'бумага': 'камень'
                }
                strategies.append(counters[next_predicted[player_move]])
        
        # 3. Анализ частоты ходов
        if len(history) >= 4:
            move_counts = {
                'камень': history.count('камень'),
                'ножницы': history.count('ножницы'),
                'бумага': history.count('бумага')
            }
            # Находим самый частый ход игрока
            most_frequent = max(move_counts, key=move_counts.get)
            strategies.append(counters[most_frequent])
        
        # 4. Анти-паттерн: если игрок ожидает что мы предскажем его ход
        if len(history) >= 2:
            # Игрок может попытаться обмануть нас, сменив стратегию
            # Поэтому с некоторой вероятностью выбираем случайный ход
            if random.random() < 0.3:  # 30% шанс на случайный ход
                strategies.append(random.choice(ai_moves))
        
        # Выбираем лучшую стратегию
        if strategies:
            # Убираем дубликаты
            strategies = list(set(strategies))
            # Выбираем случайную из лучших стратегий
            ai_move = random.choice(strategies)
        else:
            # Если нет стратегий - случайный ход
            ai_move = random.choice(ai_moves)
        
        session.game_data['ai_moves'].append(ai_move)
        return ai_move
    
    def _check_tictactoe_winner(self, board: List[str], player: str) -> bool:
        """Проверяет победителя в крестиках-ноликах"""
        win_patterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Горизонтальные
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Вертикальные
            [0, 4, 8], [2, 4, 6]               # Диагональные
        ]
        
        return any(all(board[i] == player for i in pattern) for pattern in win_patterns)
    
    def _get_best_tictactoe_move(self, board: List[str]) -> int:
        """Получает лучший ход для ИИ в крестиках-ноликах"""
        available_moves = [i for i, cell in enumerate(board) if cell == '']
        
        # Проверяем, можем ли мы победить
        for move in available_moves:
            board[move] = 'O'
            if self._check_tictactoe_winner(board, 'O'):
                board[move] = ''
                return move
            board[move] = ''
        
        # Проверяем, нужно ли блокировать игрока
        for move in available_moves:
            board[move] = 'X'
            if self._check_tictactoe_winner(board, 'X'):
                board[move] = ''
                return move
            board[move] = ''
        
        # Занимаем центр, если свободен
        if board[4] == '':
            return 4
        
        # Занимаем углы
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if board[c] == '']
        if available_corners:
            return random.choice(available_corners)
        
        # Случайный ход
        return random.choice(available_moves)
    
    def _format_tictactoe_board(self, board: List[str]) -> str:
        """Форматирует доску крестиков-ноликов"""
        symbols = {'': '⬜', 'X': '❌', 'O': '⭕'}
        formatted_board = []
        
        for i in range(0, 9, 3):
            row = f"{symbols[board[i]]}{symbols[board[i+1]]}{symbols[board[i+2]]}"
            formatted_board.append(row)
        
        return "```\n" + "\n".join(formatted_board) + "\n```"

    def _format_tictactoe_board_text(self, board: List[str]) -> str:
        """Короткое текстовое представление доски для контекста ИИ"""
        symbols = {'': '.', 'X': 'X', 'O': 'O'}
        rows = []
        for i in range(0, 9, 3):
            rows.append(" ".join(symbols[board[i + j]] for j in range(3)))
        return " / ".join(rows)
    
    def get_scores_text(self, user_id: int) -> str:
        """Получает текстовую статистику счетов"""
        scores = self.get_user_scores(user_id)
        
        text = "📊 **Твоя статистика:**\n\n"
        
        text += "❌⭕ **Крестики-нолики:**\n"
        text += f"🏆 Победы: {scores['tictactoe_wins']}\n"
        text += f"😢 Поражения: {scores['tictactoe_losses']}\n"
        text += f"🤝 Ничьи: {scores['tictactoe_draws']}\n\n"
        
        text += "🔢 **Угадай число:**\n"
        text += f"🏆 Победы: {scores['guess_wins']}\n"
        text += f"😢 Поражения: {scores['guess_losses']}\n\n"
        
        text += "✂️ **Камень-ножницы-бумага:**\n"
        text += f"🏆 Победы: {scores['rps_wins']}\n"
        text += f"😢 Поражения: {scores['rps_losses']}\n"
        text += f"🤝 Ничьи: {scores['rps_draws']}"
        
        return text
    
    def end_game(self, user_id: int) -> str:
        """Завершает игру пользователя"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            return "🛑 Игра завершена. Можешь начать новую командой /game"
        return "❌ У тебя нет активной игры"

# Глобальный экземпляр менеджера игр
game_manager = GameManager()
