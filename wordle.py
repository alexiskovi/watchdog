import logging
import random
import datetime, pytz


class Wordle:
    def __init__(self, cfg, app):
        self.words_total = 51301
        self.is_opened = False
        self.cfg = cfg
        self.current_word = ''

        self.load_leaderboard()

        for hour in self.cfg['wordle']['time']:
            new_word_time = datetime.time(hour=hour, minute=0, second=0, tzinfo=pytz.timezone('Europe/Budapest'))
            logging.info("Wordle update set at {}".format(new_word_time))
            app.job_queue.run_daily(self.update_word, new_word_time, days=(0, 1, 2, 3, 4, 5, 6))
    
    def save_leaderboard(self):
        file = open('.wordle_leaderboard', 'w')
        for i in self.leaderboard:
            file.write('{} {}\n'.format(i, self.leaderboard[i]))
        file.close()
    
    def load_leaderboard(self):
        self.leaderboard = {}
        try:
            buf_file = open(".wordle_leaderboard", 'r')
            lines = buf_file.readlines()
            for line in lines:
                username, score = line.split()
                self.leaderboard[username] = int(score)
            buf_file.close()
            logging.info("Wordle leaderboard buffer loaded")
        except:
            open('.wordle_leaderboard', 'w').close()
            logging.info("New wordle leaderboard buffer file created")
    
    def get_leaderboard(self):
        res = ''
        sorted_leaderboard = sorted(self.leaderboard.items(), key=lambda x:x[1], reverse=True)
        k = 1
        for i in sorted_leaderboard:
            res += '{}. {}: {}\n'.format(k, i[0], i[1])
            k += 1
        return res
    
    async def update_word(self, context):
        self.is_opened = False

        self.current_word = ''
        while len(self.current_word) < 4 or len(self.current_word) > 8: 
            chosen_word = random.randint(1, 51303)
            with open('russian.txt', 'r') as file:
                for i in range(chosen_word):
                    file.readline()
                line = file.readline().split(':')
                self.current_word = line[0]
                self.definition = ''
                for i in range(1, len(line)):
                    self.definition += line[i]
                file.close()

        self.current_flags = [False for _ in range(len(self.current_word))]
        
        word = 'Слово обновлено!\n'
        for _ in range(len(self.current_word)):
            word += '🟥'
        
        logging.info("Wordle word updated. New one is {}".format(self.current_word))

        await context.bot.send_message(chat_id=self.cfg['chat']['chat_id'], message_thread_id=self.cfg['chat']['thread_id']['wordle'], text=word)

    async def process_attempt(self, update):

        if self.current_word == '':
            text = "На данный момент нет загаданного слова! Новые будут в:\n"
            for i in self.cfg['wordle']['time']:
                text += ('- ' + str(datetime.time(hour=i, minute=0, second=0, tzinfo=pytz.timezone('Europe/Budapest'))) + ' (UTC+02:00)\n')
            await update.message.reply_text(text)
            return

        text = update.message.text.lower()

        if len(text) != len(self.current_word):
            await update.message.reply_text("Неверная длина слова")
            return
        
        real_word = False
        with open('russian.txt', 'r') as file:
            for i in range(self.words_total):
                line = file.readline()
                if text == line.split(':')[0]:
                    real_word = True
                    break
            file.close()
        
        if not real_word:
            await update.message.reply_text("Такого слова нет в моем словаре!")
            return

        game_over = True
        wcopy = self.current_word[:]
        current_username = update.message.from_user.username

        if current_username not in self.leaderboard:
            self.leaderboard[current_username] = 0

        # Mark in-place letters
        for i in range(len(text)):
            if wcopy[i] == text[i]:
                text = text[:i] + '🟩' + text[i + 1:]
                wcopy = wcopy[:i] + '*' + wcopy[i + 1:]
                if not self.current_flags[i]:
                    self.current_flags[i] = True
                    self.leaderboard[current_username] += 1
        # Find all wrong placed
        for i in range(len(text)):
            if text[i] in wcopy:
                wcopy = wcopy.replace(text[i], "*", 1)
                text = text[:i] + '🟨' + text[i + 1:]
                game_over = False
        for i in range(len(text)):
            if text[i] != '🟨' and text[i] != '🟩':
                text = text[:i] + '🟥' + text[i + 1:]
                game_over = False

        await update.message.reply_text(text)

        if game_over:

            text = 'Слово угадано!\n ✅ ' + self.current_word + '\n' + '❓ ' + self.definition
            self.leaderboard[current_username] += 1
            self.is_opened = True
            self.current_word = ''

            self.save_leaderboard()

            await update.message.reply_text(text)