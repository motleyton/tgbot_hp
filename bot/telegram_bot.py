from datetime import datetime, timedelta

from apscheduler.executors.asyncio import AsyncIOExecutor
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, \
    filters, ContextTypes, CallbackContext, ConversationHandler, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database_helper import Database
from utils import error_handler
from openai_helper import localized_text, OpenAI
import asyncio

# Определение состояний
ENTER_NAME, ENTER_BIRTHDAY = range(2)

class BirthdayBot:
    """Telegram bot for managing birthdays."""
    # Конструктор и метод start остаются без изменений
    def __init__(self, config: dict, openai: OpenAI):
        self.config = config
        self.openai = openai 
        self.db = Database("users_data.db")

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Sends a welcome message and instructions."""
        await update.message.reply_text('Добро пожаловать! Используйте /add_friend чтобы добавить друзей')

    async def add_friend(self, update: Update, context: CallbackContext) -> int:
        """Starts the process of adding a new friend's birthday."""
        await update.message.reply_text('Введите имя друга')
        return ENTER_NAME

    async def enter_name(self, update: Update, context: CallbackContext) -> int:
        """Requests the friend's birthday after receiving the name."""
        context.user_data['friend_name'] = update.message.text
        await update.message.reply_text('Введите дату рождения в формате YYYY-MM-DD')
        return ENTER_BIRTHDAY

    async def enter_birthday(self, update: Update, context: CallbackContext) -> int:
        """Stores the friend's birthday in the database and concludes the process."""
        friend_name = context.user_data.get('friend_name')
        friend_birthday = update.message.text
        user_id = update.message.from_user.id
        self.db.add_friend(user_id, friend_name, friend_birthday)
        await update.message.reply_text(f'Дата рождения успешно добавлена')
        return ConversationHandler.END

    def setup_scheduler(self, bot):
        self.scheduler = AsyncIOScheduler(executors={'default': AsyncIOExecutor()})
        run_time = datetime.now() + timedelta(minutes=1)
        # Теперь можно напрямую добавлять асинхронные функции
        self.scheduler.add_job(self.check_birthdays, 'date', run_date=run_time, args=[bot])
        self.scheduler.start()

    async def check_birthdays(self, bot):
        birthdays_today = self.db.get_birthdays_today()
        for user_id, name, id in birthdays_today:
            # Создаем клавиатуру с кнопкой для генерации поздравления
            keyboard = [InlineKeyboardButton("Сгенерировать поздравление", callback_data=f'generate_birthday_{id}')]
            reply_markup = InlineKeyboardMarkup([keyboard])
            # Отправляем сообщение пользователю с user_id
            await bot.send_message(chat_id=user_id, text=f"Сегодня день рождения у {name}! Не забудьте поздравить!",
                                   reply_markup=reply_markup)

    async def generate_greeting(self, update: Update, context: CallbackContext):
        query = update.callback_query
        parts = query.data.split('_')
        if len(parts) < 3:
            await query.answer("Ошибка: неверный формат данных.", show_alert=True)
            return

        # Извлекаем id записи о дне рождения из callback_data
        id = int(parts[2])

        # Получаем информацию о дне рождения из базы данных по id
        birthday_info = self.db.get_birthday_info_by_id(id)
        if not birthday_info:
            await query.answer("День рождения не найден.", show_alert=True)
            return

        name = birthday_info['name']  # Имя именинника

        # Генерируем текст поздравления, используя имя именинника
        greeting_text = self.openai.generate_birthday_greeting(name)

        # Путь к изображению, которое вы хотите отправить
        image_path = '/home/bmf/Desktop/freelance/tgbot_HP/bot/Happy Birthday.png'

        # Отправляем изображение с поздравлением
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=open(image_path, 'rb'),
            caption=greeting_text
        )

        # Закрываем всплывающее уведомление о загрузке
        await query.answer()

    def run(self):
        """Runs the bot."""
        application = ApplicationBuilder() \
            .token(self.config['token']) \
            .build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('add_friend', self.add_friend)],
            states={
                ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_name)],
                ENTER_BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_birthday)],
            },
        )

        application.add_handler(conv_handler)
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(CallbackQueryHandler(self.generate_greeting))
        self.setup_scheduler(application.bot)
        application.run_polling()