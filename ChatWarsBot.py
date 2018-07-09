#!/usr/bin/python3
# coding=utf-8
import re
from collections import deque
from datetime import datetime

import _thread
import random

import pytz
from pytg.sender import Sender
from pytg.receiver import Receiver
from pytg.utils import coroutine
from time import sleep, time




# telegram-cli host and port
# run "telegram-cli --json -P 4458"
host = 'localhost'
port = 4458

# replace with your timezone if needed
tz = pytz.timezone('Europe/Moscow')

# username of bot
bot_username = 'ChatWarsBot'

# username for orders
order_username = 'cwDawnBot'

# user_id of bot, needed for configuration
bot_user_id = 'zebra1mrn'

# main pytg Sender
sender = Sender(host=host, port=port)

# storing last 30 messages for future getting them by telegram command
log_list = deque([], maxlen=30)

# list for future actions
action_list = deque([])

# list of all possible actions
orders = {
    'rassvet': '🌹',
    'mish_ebat': '🦇',
    'skala': '🖤',
    'ferma': '🍆',
    'oplot': '☘️',
    'tortuga': '🐢',
    'amber': '🍁',
    ######################
    'corovan': '/go',
    'hero': '🏅Герой',
    'quests': '🗺Квесты',
    'castle_menu': '🏰Замок',
    'cover': '🛡Защита',
    'attack': '⚔️️Атака'
}

quests_id = {
     0 : '🌲Лес',
     1 : '⛰️Долина',
     2 : '🍄Болото',
     3 : '🗡ГРАБИТЬ КОРОВАНЫ'
}

# delay for getting info will be random in future
get_info_diff = 360

# todo add description
lt_info = 0

# switches

bot_enabled = True
global quests_enabled
corovan_enabled = True

def log(text):
    message = '{0:%Y-%m-%d+ %H:%M:%S}'.format(datetime.now()) + ' ' + text
    print(message)
    log_list.append(message)



@coroutine
def work_with_message(receiver):
    global bot_user_id

    while True:
        msg = (yield)
        try:
            if msg['event'] == 'message' and 'text' in msg and msg['peer'] is not None:
                if bot_user_id == '' and msg['sender']['username'] == bot_username:
                    bot_user_id = msg['receiver']['peer_id']
                    log('user_id найден: {0}'.format(bot_user_id))
                # Checking for username for not getting Exception
                if 'username' in msg['sender']:
                    parse_text(msg['text'], msg['sender']['username'], msg['id'])
        except Exception as err:
            log('Ошибка coroutine: {0}'.format(err))


def parse_text(text, username, message_id):



    if username == bot_username:
        log('Получили сообщение от бота. Проверяем условия')

        # if someone tries to get "corovan"
        if text.find(' /go') != -1:
            action_list.append(orders['corovan'])

        # reading main info about hero
        elif text.find('Битва семи замков через') != -1:
            endurance = int(re.search('Выносливость: (\d+)', text).group(1))
            endurance_max = int(re.search('Выносливость: (\d+)/(\d+)', text).group(2))
            gold = int(re.search('💰(-?[0-9]+)', text).group(1))
            inv = re.search('🎒Рюкзак: ([0-9]+)/([0-9]+)', text)
            level = int(re.search('🏅Уровень: (\d+)', text).group(1))
            state = re.search('Состояние:\n(.*)', text).group(1)
            log('Уровень: {0}, золото: {1}, выносливость: {2} / {3}, Рюкзак: {4} / {5}, Состояние: {6}'
                .format(level, gold, endurance, endurance_max, inv.group(1), inv.group(2), state))
            if endurance > 0 and state == '🛌Отдых' and False:
                sleep(random.randint(1,4))
                action_list.append(orders['quests'])
                sleep(2)
                if level < 20:
                    action_list.append(quests_id[0])
                else:
                    action_list.append(quests_id[random.randint(0,2)]) # random choose: 0 -  forest, 1 - valley, 2 - swamp
            current_hour = datetime.now(tz).hour
            # attack corovans beetwen 3 and 6:59 AM
            if endurance >= 2 and 3 <= current_hour <= 6:
                action_list.append(orders['quests'])
                action_list.append(quests_id[3]) # 3 - corovans

            if gold >=4 and current_hour == 7:
                sticks_to_buy = gold // 4
                send_msg('@', bot_username, '/t stick')
                sleep(6)
                send_msg('@', bot_username, '/wtb_02_' + str(sticks_to_buy))

            elif state != '🛌Отдых':
                log('Чем-то занят')
            elif endurance == 0:
                log('Выносливость на нуле. Ждём')

        elif 'Горы полны опасностей. Ты решил исследовать, что там происходит.' in text:
            log('Ушёл гулять в долину')

        elif 'Ты отправился искать приключения в лес.' in text:
            log('Ушёл в лес')

        elif 'Приключения зовут. Но ты отправился в болото.' in text:
            log('Бродишь по болоту')

        elif '/pledge' in text:
            send_msg('@', bot_username, '/pledge')





    if username == order_username:
        msg = sender.message_get(message_id)
        if 'reply_id' in msg: # check if we have pin from order bot
            msg = sender.message_get(msg.reply_id) # go to the top message
            if msg.text.find('⚔️🌹') != -1:
                action_list.append(orders['cover'])
            elif msg.text.find('⚔️🖤') != -1:
                action_list.append(orders['skala'])
            elif msg.text.find('⚔️☘️') != -1:
                action_list.append(orders['oplot'])
            elif msg.text.find('⚔️🍁') != -1:
                action_list.append(orders['amber'])
            elif msg.text.find('⚔️🍆') != -1:
                action_list.append(orders['ferma'])
            elif msg.text.find('⚔️🦇') != -1:
                action_list.append(orders['mish_ebat'])
            elif msg.text.find('⚔️🐢') != -1:
                action_list.append(orders['tortuga'])





    if username == bot_user_id:

        if text == 'help':
            send_msg('@', bot_user_id, '\n'.join([
                'quest_off',
                'corovan_off',
                'bot_off',
                'bot_on',
                'quest_on',
                'corovan_on'
            ]))
        elif text == 'quest_off':
            quests_enabled = False
            send_msg('@', bot_user_id, 'Походы по квестам выключены')
        elif text == 'corovan_off':
            corovan_enabled = False
            send_msg('@', bot_user_id, 'Ты оставил корованы в покое')
        elif text == 'bot_off':
            bot_enabled = False
            send_msg('@', bot_user_id,'Бот выключен')
        elif text == 'quest_on':
            quests_enabled = True
            send_msg('@', bot_user_id,'Походы по квестам выключены')
        elif text == 'corovan_on':
            corovan_enabled = True
            send_msg('@', bot_user_id,'Ты оставил корованы в покое')
        elif text == 'bot_on':
            bot_enabled = True
            send_msg('@', bot_user_id,'Бот выключен')

def get_message_replied_to(msg, sender):
    if 'reply_id' in msg:
        next_msg = sender.message_get(msg.reply_id)
        return get_message_replied_to(next_msg, sender)
    return msg




def send_msg(pref, to, message):
    sender.send_msg(pref + to, message)

def send_msg(pref, to, message):
    sender.send_msg(pref + to, message)

def fwd(pref, to, message_id):
    sender.fwd(pref + to, message_id)


def queue_worker():
    global get_info_diff
    global lt_info
    global tz

    sleep(3)
    while True:
        try:
            if time() - lt_info > get_info_diff:

                lt_info = time()
                current_hour = datetime.now(tz).hour
                if 9 <= current_hour <= 23:
                    get_info_diff = random.randint(420, 900)
                else:
                    get_info_diff = random.randint(600, 900)
                if bot_enabled and 3 <= current_hour <= 7:
                    send_msg('@', bot_username, orders['hero'])
                continue
            # if fight_path != '' and castle_name is not None:
            #     os.chdir(fight_path)
            #     for file_name in glob.glob(castle_name + "*"):
            #         if file_name[-4:] != port:
            #             f = open(file_name, 'r')
            #             action_list.append(f.readline())
            #             f.close
            #             os.remove(file_name)
            if len(action_list):
                log('Отправляем ' + action_list[0])
                send_msg('@', bot_username, action_list.popleft())
            sleep_time = random.randint(2, 5)
            sleep(sleep_time)
        except Exception as err:
            log('Ошибка очереди: {0}'.format(err))


# main function supposed to be in the end
if __name__ == '__main__':
    receiver = Receiver(host=host, port=port)
    receiver.start()  # start the Connector.
    _thread.start_new_thread(queue_worker, ())
    receiver.message(work_with_message(receiver))
    receiver.stop()
