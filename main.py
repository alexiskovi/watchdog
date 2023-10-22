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

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
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
        
        logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

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

        self.info = Info()
        self.cleaner = Cleaner(
            cfg = self.cfg['cleanup'],
            app = application
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

    async def process_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #
    # Callback which recalls methods to process all text messages
    #
        #print(update)

        if update.message.message_thread_id == self.cfg['chat']['thread_id']['wordle']:
            await self.wordle.process_attempt(update)

        # Add message to the cleaner queue
        await self.cleaner.append_message(update)

    def configure_handlers(self, app):
    #
    # Creating handlers for predefined events
    #
        # Handler for global status command
        app.add_handler(CommandHandler("info", self.info.process_status))
        # Handler for cleaner status command
        app.add_handler(CommandHandler("cleaner_info", self.cleaner.process_status))
        # Handler for all text messages except having urls
        app.add_handler(MessageHandler(~filters.Entity('url'), self.process_text_message))      


if __name__ == "__main__":
    main = Handler()