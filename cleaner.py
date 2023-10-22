import datetime, pytz
from telegram import Update
from telegram.ext import JobQueue, ContextTypes
import logging


class Cleaner:
    def __init__(self, cfg, app):
    #
    # Cleaner constructor
    # This class queuing all messages except predefined topics and deletes
    # them once a day
    #
        logging.info("Launching Cleaner...")
        self.cfg = cfg
        self.clear_list = []

        # Load buffer
        try:
            buf_file = open(".clean_buffer", 'r')
            lines = buf_file.readlines()
            for line in lines:
                chat_id, message_id = line.split()
                self.clear_list.append((int(chat_id), int(message_id)))
            buf_file.close()
            logging.info("Cleaner buffer loaded")
        except:
            open('.clean_buffer', 'w').close()
            logging.info("New cleaner buffer file created")
        
        self.buf_file = open(".clean_buffer", 'a')

        self.time_on_delete = datetime.time(hour=cfg['time'], minute=0, second=0, tzinfo=pytz.timezone('Europe/Budapest'))

        logging.info("Daily cleanup set at {}".format(self.time_on_delete))

        app.job_queue.run_daily(self.delete_messages, self.time_on_delete, days=(0, 1, 2, 3, 4, 5, 6))

    async def append_message(self, update: Update) -> None:
    #
    # Method to check a thread_id and append message to removing queue
    #
        if str(update.message.message_thread_id) not in self.cfg['exclude_thread_id']:
            self.buf_file.write(str(update.message.chat_id) + ' ' + str(update.message.message_id) + '\n')
            self.clear_list.append((update.message.chat_id, update.message.message_id))

    async def delete_messages(self, context):
    #
    # Method to delete all queued messages
    #
        logging.info("Daily cleaning!")
        
        for chat_id, message_id in self.clear_list:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

        self.clear_list.clear()
        
        open('.clean_buffer', 'w').close()
    
    async def process_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #
    # Method to send cleaner status
    #   
        logging.debug("Got command: CLEANER_INFO")

        info_msg = '🧨 Очистка включена! 🧨\n'
        info_msg += ('Ожидаемое время очистки: ' + str(self.time_on_delete) + ' (UTC+2)\n\n')
        info_msg += ('id топиков с отключенной очисткой:\n')
        for i in self.cfg['exclude_thread_id']:
            info_msg += (i + '\n')
        info_msg += ('Количество сообщений, которое будет удалено: ' + str(len(self.clear_list)))
        await update.message.reply_text(info_msg)
        logging.debug("Cleaner status sent")
    
    def __del__(self):
        self.buf_file.close()