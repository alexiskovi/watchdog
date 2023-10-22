from datetime import datetime
import logging
from telegram import Update
from telegram.ext import ContextTypes

class Info:
    def __init__(self):
    #
    # Info constructor
    # This class is aimed to process base commands which
    # requires just text-based easy answer
    #
        logging.info("Launching Info")
        self.start_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logging.info("Start time: {}".format(self.start_time))

    async def process_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #
    # Method which assemble an answer for "info" request
    #
        logging.debug("Got command: INFO")

        info_msg = '🐶 Бот активен 🐶\n'
        info_msg += ('Время последнего рестарта: ' + self.start_time + ' (UTC+2)\n\n')
        info_msg += self.version_description()
        await update.message.reply_text(info_msg)
        logging.debug("Status sent")

    def version_description(self):
    #
    # Open history.txt file and find last version
    #
        with open('history.txt', 'r') as file:
            file.readline()
            line = file.readline()
            info_msg = ""
            if len(line.split()) == 2:
                info_msg += 'Текущая версия - '
                info_msg += line.split()[1] + '\n\n'
                info_msg += 'Что изменилось?\n'
                line = file.readline()
                while not '---' in line:
                    info_msg += line
                    line = file.readline()
        file.close()

        return info_msg