import telebot
import sqlite3
from telebot import types
import config

bot = telebot.TeleBot(config.token)

conn = sqlite3.connect('files.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS files
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT,
                   file BLOB)''')


# выводит список файлов в бд
@bot.message_handler(commands=['list'])
def list_files_command(message):
    cursor.execute("SELECT name FROM files")
    files = cursor.fetchall()
    if files:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for file in files:
            markup.add(types.KeyboardButton(file[0]))
        file_names = [file[0] for file in files]
        bot.reply_to(message, f"Список файлов:\n\n{', '.join(file_names)}", reply_markup=markup)
        bot.set_state(message.chat.id, 'list')
        bot.register_next_step_handler(message, get_file)
    else:
        bot.reply_to(message, "В базе данных нет файлов.")


# выводит кнопочки
def get_file(message):
    try:
        file_name = message.text
        cursor.execute("SELECT * FROM files WHERE name= ?", (file_name, ))
        file_content = cursor.fetchone()[2]
        bot.send_document(message.chat.id, file_content)
    except:
        pass


# берёт файл с переданным названием
@bot.message_handler(commands=['get'])
def get_file_command(message):
    file_name = message.text.split(' ')[1]
    cursor.execute("SELECT file FROM files WHERE name=?", (file_name,))
    file_data = cursor.fetchone()
    if file_data:
        file_bytes = file_data[0]
        bot.send_document(message.chat.id, file_bytes)
    else:
        bot.reply_to(message, "Файл с указанным названием не найден.")


# добавляет документ с переданным названием
@bot.message_handler(content_types=['document', 'string'])
def add_document(message):
    if message.from_user.id == 1677887525:
        try:
            if message.document:
                # Получаем информацию о документе
                file_id = message.document.file_id
                file_info = bot.get_file(file_id)
                file_path = file_info.file_path

                # Скачиваем документ
                downloaded_file = bot.download_file(file_path)

                # проверяем есть ли файл с таким названием в бд
                cursor.execute('SELECT * FROM files WHERE name=?', (message.caption, ))
                ft = cursor.fetchall()
                if ft:
                    # файл существует
                    bot.reply_to(message, 'Файл с таким названием уже существует')
                else:
                    # Сохраняем документ в базе данных
                    cursor.execute("INSERT INTO files (name, file) VALUES (?, ?)", (message.caption, downloaded_file))
                    conn.commit()

                    bot.reply_to(message, 'Файл сохранен в базе данных!')
            else:
                bot.reply_to(message, 'Вы не прикрепили файл')
        except:
            bot.send_message(message.chat.id, 'Произошла неизвестная ошибка!')
    else:
        bot.reply_to(message, 'У вас нет прав для данного действия!')


# удаляет из бд документ с переданным названием
@bot.message_handler(commands=['delete'])
def delete_document(message):
    name = str(message.text)[8:]
    print(name)
    if message.from_user.id == 1677887525:
        try:
            cursor.execute('DELETE FROM files WHERE name=?', (name, ))
            conn.commit()
            bot.reply_to(message, f'Файл { name } успешно удалён!')
        except:
            bot.reply_to(message, 'Ошибка')
    else:
        bot.reply_to(message, 'У вас нет прав для данного действия')


# очищает бд
@bot.message_handler(commands=['clear'])
def clear_documents(message):
    print('База данных очищена')
    if message.from_user.id == 1677887525:
        try:
            cursor.execute('DELETE FROM files')
            conn.commit()
            bot.reply_to(message, f'Все файлы успешно удалены')
        except:
            bot.reply_to(message, f'Ошибка')
    else:
        bot.reply_to(message, f'У вас нет прав для данного действия')


@bot.message_handler(commands=['pk'])
def user_pk(message):
    bot.send_message(message.chat.id, f'Ваш pk = { message.from_user.id }')


bot.polling()
