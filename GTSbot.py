#Keep your token secure and store it safely, it can be used by anyone to control your bot.
#For a description of the Bot API, see this page: https://core.telegram.org/bots/api

#!pip install pyTelegramBotAPI
#pip install python-telegram-bot[socks]

import sqlite3
import random
import telebot  # импортируем модуль pyTelegramBotAPI
import conf    # импортируем наш секретный токен

# подключаемся к базе данных
conn = sqlite3.connect('Artist_bot.db')
c = conn.cursor()
telebot.apihelper.proxy = conf.PROXY
bot = telebot.TeleBot(conf.TOKEN)  # создаем экземпляр бота

Score = []  # баллы игрока

# этот обработчик запускает функцию send_welcome,
# когда пользователь отправляет команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     '''Здравствуйте и добро пожаловать!
                     
Хотите сыграть?
                     
Правила простые: Вы выбираете артиста, а бот предлагает Вам отрывок из переведённого текста песни.
Ваша задача - угадать песню!
                     
Посмотрим, насколько вы преданный фанат :)
                     
Начнём?''')


def get_artists(): # список исполнителей, которые есть в БД
    c.execute('SELECT artist FROM all_tracks')
    artists_list = []
    for item in c.fetchall():
        if item[0] not in artists_list:
            artists_list.append(item[0])
    c.close()
    num = 0
    list_to_show = ''
    for artist in artists_list:
        num = num +1
        list_to_show = list_to_show + str(num) + ' - ' + artist + '\n'

    return list_to_show, artists_list


list_to_show, artists = get_artists()


# Handles all text messages that match the regular expression
@bot.message_handler(regexp='[Дд]а')
def begin(message):
    bot.send_message(message.chat.id,'''Отлично!

Напишите в ответ номер выбранного исполнителя:
''' + list_to_show)


ANSWER = []  # очень нужный список, в нём будет храниться верный ответ на каждый вопрос


@bot.message_handler(regexp="[0-9]{1,2}")  # выбор исполнителя
def game(message):
    choice = int(message.text)
    num = choice - 1
    chosen_one = artists[num]
    conn = sqlite3.connect('Artist_bot.db')  # обращения к БД не срабатывали иначе, приходится открывать/закрывать
    c = conn.cursor()
    c.execute('SELECT translated_text FROM all_tracks WHERE artist = ?', (chosen_one,))
    text = random.choice(c.fetchall())[0]
    c.close()
    conn = sqlite3.connect('Artist_bot.db')
    c = conn.cursor()
    c.execute('SELECT track_title FROM all_tracks WHERE translated_text = ?', (text,))
    title = c.fetchone()[0]
    ANSWER.append(title)
    c.close()
    t = text.split('\n')
    articles = []
    for i in range(1, len(t)):  # потому что некоторые переводы начинаются с названия
        articles.append('\n'.join(t[i:i + 3]))
    task_to_give = random.choice(articles)
    bot.send_message(message.chat.id, '''Что это за песня?\n\n'''
    + task_to_give + '\n\nВведите название на английском')


@bot.message_handler(regexp= "[A-Za-z]+")  # ответы пользователя
def win_or_lose(message):
    correct_answer = ANSWER[0]
    answer = message.text.lower()
    good = ['Супер гуд!','Верно!', 'Правильный ответ!', 'Молодчина!','В яблочко!', 'Так точно!', 'Зачёт!']
    bad = ['Ну нет...','Ошибочное предположение :(', 'Неправильно :(', 'Не-а :(','Только не расстраивайся, но нет :(']
    if answer == correct_answer:
        Score.append('1')
        bot.send_message(message.chat.id, random.choice(good) + '\n\nТекущий счёт: ' + len(Score) + '\n\nХотите продолжить?')
    if answer != correct_answer:
        bot.send_message(message.chat.id, random.choice(bad) + '\n\nПравильный ответ: '
        + correct_answer.title() + '\n\nТекущий счёт: ' + len(Score) + '\n\nХотите продолжить?')
    ANSWER.clear()


@bot.message_handler(regexp= '[Нн]ет?')  # если не хочется играть/продолжать
def end(message):
    bot.send_message(message.chat.id, 'Ну ладно... тогда пока! До встречи!\n Чтобы начать заново, напишите "Да"')
    Score.clear()

if __name__ == '__main__':
    bot.polling(none_stop=True)
