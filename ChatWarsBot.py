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

# username for reports
report_user = 'CWCastleBot'

# main pytg Sender
sender = Sender(host=host, port=port)

# storing last 30 messages for future getting them by telegram command
log_list = deque([], maxlen=30)

# list for future actions
action_list = deque([])

# switches
bot_enabled = True
corovan_enabled = True
quests_enabled = False
stock = False

forest_enabled = False
swamp_enabled = False
valley_enabled = True

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
    'attack': '⚔️️Атака',
    'craft': '⚒Мастерская',
    'report': '/report',
    'attack_corovan': '🗡ГРАБИТЬ КОРОВАНЫ'
}

quests_id = {
    'forest': '🌲Лес',
    'valley': '⛰️Долина',
    'swamp': '🍄Болото',
}


def quest_declaration(forest, swamp, valley):

    declared_quests = []

    if forest:
        declared_quests.append('forest')
    if swamp:
        declared_quests.append('swamp')
    if valley:
        declared_quests.append('valley')

    return declared_quests


# list of active quests
quests = quest_declaration(forest_enabled, swamp_enabled, valley_enabled)

# delay for getting info will be random in future
get_info_diff = 360

# todo add description
lt_info = 0


def log(text):
    message = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.now()) + ' ' + text
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
    global quests_enabled
    global corovan_enabled
    global bot_enabled
    global stock
    global forest_enabled
    global swamp_enabled
    global valley_enabled
    global quests

    if username == bot_username:
        log('Получили сообщение от бота. Проверяем условия')
        log(str(quests))

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
            if text.find('👝') != -1:
                pouch = int(re.search('👝(-?[0-9]+)', text).group(1))
            else:
                pouch = 0
            log('Уровень: {0}, золото: {1}, мешки: {2}, выносливость: {3} / {4}, Рюкзак: {5} / {6}, Состояние: {7}'
                .format(level, gold, pouch, endurance, endurance_max, inv.group(1), inv.group(2), state))
            if endurance > 0 and state == '🛌Отдых' and quests_enabled:
                sleep(random.randint(1, 4))
                action_list.append(orders['quests'])
                sleep(2)
                if level < 20:
                    action_list.append(quests_id['forest'])
                else:
                    if quests:
                        action_list.append(quests_id[random.choice(quests)])
            current_hour = datetime.now(tz).hour
            # attack corovans beetwen 3 and 6:59 AM
            if endurance >= 2 and 3 <= current_hour <= 6 and corovan_enabled:
                action_list.append(orders['quests'])
                action_list.append(orders['attack_corovan'])  # 3 - corovans

            if (current_hour == 7 or current_hour == 15 or current_hour == 23) and stock:
                if gold >= 120:
                    action_list.append(orders['castle_menu'])
                    action_list.append(orders['craft'])
                    send_msg('@', bot_username, '/craft_100')
                    log('Крафтим мешочек')
                elif gold >= 6:
                    pelt_to_buy = gold // 6
                    send_msg('@', bot_username, '/t pelt')
                    sleep(6)
                    send_msg('@', bot_username, '/wtb_03_' + str(pelt_to_buy))
                    log('Пытаемся купить {0} пелтов'.format(pelt_to_buy))

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

        elif text.find('Твои результаты в бою:') != -1:
            fwd('@', report_user, message_id)

        elif text.find('Изготовлено: Pouch of gold') != -1:
            log('Скрафтили мешок')

        sender.mark_read('@' + bot_username)

    if username == order_username:
        msg = sender.message_get(message_id)

        if 'reply_id' in msg:  # check if we have pin from order bot
            # reply_msg = sender.message_get(msg.reply_id)
            # log(str(reply_msg))
            # log(str(msg))
            fwd('@', bot_user_id, msg.reply_id)  # forward this shit to us

    if username == report_user:
        if text.find('Изменения в вашем стоке:') != -1:
            action_list.append(orders['report'])

    if username == bot_user_id:

        if text.find('⚔️🌹') != -1:
            action_list.append(orders['cover'])
        elif text.find('⚔️🖤') != -1:
            action_list.append(orders['skala'])
        elif text.find('⚔️☘️') != -1:
            action_list.append(orders['oplot'])
        elif text.find('⚔️🍁') != -1:
            action_list.append(orders['amber'])
        elif text.find('⚔️🍆') != -1:
            action_list.append(orders['ferma'])
        elif text.find('⚔️🦇') != -1:
            action_list.append(orders['mish_ebat'])
        elif text.find('⚔️🐢') != -1:
            action_list.append(orders['tortuga'])

        elif text == 'help':
            send_msg('@', bot_user_id, '\n'.join([
                'quest_on/off',
                'corovan_on/off',
                'bot_on/off',
                'stock_on/off'
            ]))
        elif text == 'quest_off':
            quests_enabled = False
            send_msg('@', bot_user_id, 'Походы по квестам выключены')
        elif text == 'corovan_off':
            corovan_enabled = False
            send_msg('@', bot_user_id, 'Ты оставил корованы в покое')
        elif text == 'bot_off':
            bot_enabled = False
            send_msg('@', bot_user_id, 'Бот выключен')
        elif text == 'quest_on':
            quests_enabled = True
            send_msg('@', bot_user_id, 'Походы по квестам включены')
        elif text == 'corovan_on':
            corovan_enabled = True
            send_msg('@', bot_user_id, 'Корованы в беде. Ты отправишься за ними с 3 до 7 утра')
        elif text == 'bot_on':
            bot_enabled = True
            send_msg('@', bot_user_id, 'Бот включен')
        elif text == 'stock_on':
            stock = True
            send_msg('@', bot_user_id, 'Биржа включена')
        elif text == 'stock_off':
            stock = False
            send_msg('@', bot_user_id, 'Биржа выключена')
        elif text == 'les_on':
            forest_enabled = True
            quest_switch_on('forest')
        elif text == 'swamp_on':
            swamp_enabled = True
            quest_switch_on('swamp')
        elif text == 'valley_on':
            valley_enabled = True
            quest_switch_on('valley')
        elif text == 'valley_off':
            valley_enabled = False
            quest_switch_off('valley')
        elif text == 'forest_off':
            forest_enabled = False
            quest_switch_off('forest')
        elif text == 'swamp_off':
            swamp_enabled = False
            quest_switch_off('swamp')
        else:
            del_msg(message_id)


def quest_switch_on(quest_name):
    global quests
    global quests_enabled

    if quest_name not in quests:
        quests.append(quest_name)
        send_msg('@', bot_user_id, quest_name + ' добавлен в список')
        if not quests_enabled:
            send_msg('@', bot_user_id, 'Квесты выключены. Нужно их включить, чтобы бот начал бегать по списку')

    else:
        send_msg('@', bot_user_id, quest_name + ' уже есть в списке')

    send_msg('@', bot_user_id, 'Состояние списка: ' + str(quests))


def quest_switch_off(quest_name):
    global quests
    global quests_enabled

    if quest_name in quests:
        quests.remove(quest_name)
        send_msg('@', bot_user_id, quest_name + ' удалён из списка')
        if not quests:
            send_msg('@', bot_user_id, 'list is empty')
            quests_enabled = False

    else:
        send_msg('@', bot_user_id, quest_name + ' отсутствует в списке')

    send_msg('@', bot_user_id, 'Состояние списка: ' + str(quests))


def del_msg(msg):
    sender.raw('delete_msg ' + msg)  # raw telegram-cli command


def send_msg(pref, to, message):
    sender.send_msg(pref + to, message)


def fwd(pref, to, message_id):
    sender.fwd(pref + to, message_id)


def queue_worker():
    global get_info_diff
    global lt_info
    global tz
    global bot_enabled

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
                if bot_enabled:
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
