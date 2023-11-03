######################################
#
# This bot is aimed to organize a
# local supergroup with a lot of
# links in different topics
#
######################################

# Global imports

import time
import yaml
import logging

# Telegram-related imports

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, Update, Bot, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Local modules

from cleaner import Cleaner
from info import Info
from wordle import Wordle

class Handler:

    def __init__(self):
        # Disable INFO level for network loggers
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("telegram").setLevel(logging.WARNING)
        
        logging.basicConfig(
            encoding='utf-8',
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.DEBUG,
            datefmt='%Y-%m-%d %H:%M:%S')

        logging.info("Launching watchdog bot...")

        # Load configs
        logging.info("Parsing credentials...")
        with open('credentials.yaml', 'r') as file:
            token = yaml.safe_load(file)['credentials']['token']
        file.close()

        logging.info("Parsing config...")
        with open('conf.yaml', 'r') as file:
            self.cfg = yaml.safe_load(file)
        file.close()

        # Create application with token
        logging.info("Creating application...")
        application = Application.builder().token(token).build()

        logging.info("Load chats list...")
        self.chat_list = {}
        try:
            buf_file = open("tmp/.chat_list", 'r')
            lines = buf_file.readlines()
            for line in lines:
                thread_id, thread_name, thread_clean_status = line.split()
                if thread_clean_status == 'True':
                    self.chat_list[thread_id] = [thread_name, True]
                else:
                    self.chat_list[thread_id] = [thread_name, False]
            buf_file.close()
            logging.info("Chat list loaded successfully")
        except:
            open('tmp/.chat_list', 'w').close()
            logging.info("New chat list buffer file created")

        self.info = Info()
        self.cleaner = Cleaner(
            cfg = self.cfg['cleanup'],
            app = application,
            chat_list = self.chat_list,
        )

        self.configure_handlers(
            app = application,
        )

        self.wordle = Wordle(
            cfg = self.cfg,
            app = application,
        )

        logging.info("Start polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    def save_chat_list(self):
        file = open('tmp/.chat_list', 'w')
        for i in self.chat_list:
            file.write('{} {} {}\n'.format(i, self.chat_list[i][0], self.chat_list[i][1]))
        file.close()
        logging.info("Chat list changed saved")

    async def process_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #
    # Callback which recalls methods to process all text messages
    #
        #print(update)
        
        if not str(update.message.message_thread_id) in self.chat_list:
            logging.info("New thread with ID {} added to list".format(update.message.message_thread_id))
            self.chat_list[str(update.message.message_thread_id)] = ['#', False]
            self.save_chat_list()

        if update.message.message_thread_id == self.cfg['chat']['thread_id']['wordle']:
            await self.wordle.process_attempt(update)

        # Add message to the cleaner queue
        await self.cleaner.append_message(update)

    async def print_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = ''
        text += self.wordle.get_leaderboard()
        await update.message.reply_text(text)
    
    async def change_cleaner_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(self.chat_list)
        keyboard = []
        for i in self.chat_list:
            text = ''
            if self.chat_list[i][0] == '#':
                text = str(i)
                if self.chat_list[i][1]:
                    text += ' 🔇'
                else:
                    text += ' 🔊'
            else:
                text = self.chat_list[i][0]
                if self.chat_list[i][1]:
                    text += ' 🔇'
                else:
                    text += ' 🔊'
            keyboard.append([InlineKeyboardButton(text, callback_data=str(i))])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Нажмите на топик чтобы инвертировать текущую настройку:", reply_markup=reply_markup)
    
    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=f"Selected option: {query.data}")
        self.chat_list[query.data][1] = not self.chat_list[query.data][1]
        self.save_chat_list()

    async def set_chat_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        pass

    def configure_handlers(self, app):
    #
    # Creating handlers for predefined events
    #
        # Handler for global status command
        app.add_handler(CommandHandler("info", self.info.process_status))
        # Handler for cleaner status command
        app.add_handler(CommandHandler("cleaner_info", self.cleaner.process_status))
        # Handler for leaderboard command
        app.add_handler(CommandHandler("game_leaderboard", self.print_leaderboard))
        # Handler for chat cleaning status change
        app.add_handler(CommandHandler("cleaner_change_status", self.change_cleaner_status))
        app.add_handler(CallbackQueryHandler(self.button))
        # Handler for chat cleaning status change
        app.add_handler(CommandHandler("set_chat_name", self.set_chat_name))
        # Handler for all text messages except having urls
        app.add_handler(MessageHandler(~filters.Entity('url'), self.process_text_message))


if __name__ == "__main__":
    main = Handler()