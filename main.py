import telebot
import sqlite3
import config

bot = telebot.TeleBot(config.token)

conn = sqlite3.connect('files.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS files
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT,
                   file BLOB)''')


admins = [1677887525, ]


# выводит список файлов в бд
@bot.message_handler(commands=['list'])
def list_files_command(message):
    cursor.execute("SELECT name FROM files")
    files = cursor.fetchall()
    if files:
        markup = telebot.types.InlineKeyboardMarkup()
        for file_name in files:
            button = telebot.types.InlineKeyboardButton(text=file_name[0], callback_data=file_name[0])
            markup.add(button)
        bot.send_message(message.chat.id, 'Выберите файл:', reply_markup=markup)
    else:
        bot.reply_to(message, "В базе данных нет файлов.")


# отправляет файл
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        cursor.execute("SELECT name, file FROM files WHERE name= ?", (call.data, ))
        file = cursor.fetchall()
        # если файл имеет тип png/jpg, то отправляем его картинкой
        if str(file[0][0])[-4:] == ".png" or str(file[0][0])[-4:] == ".jpg":
            # отправляем фото
            bot.send_photo(call.message.chat.id, photo=file[0])
        else:
            # отправляем документ
            bot.send_document(call.message.chat.id, file[0])
    except Exception as e:
        bot.send_message(call.message.chat.id, f'Ошибка при отправке файла: {e}')


# удаляет документ из бд
@bot.message_handler(commands=['delete'])
def delete_document(message):
    name = str(message.text)[8:]
    if message.from_user.id in admins:
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
    if message.from_user.id in admins:
        try:
            cursor.execute('DELETE FROM files')
            conn.commit()
            bot.reply_to(message, f'Все файлы успешно удалены')
        except:
            bot.reply_to(message, f'Ошибка')
    else:
        bot.reply_to(message, f'У вас нет прав для данного действия')


# получаем pk user'a
@bot.message_handler(commands=['pk'])
def user_pk(message):
    bot.send_message(message.chat.id, f'Ваш pk = { message.from_user.id }')


# сохраняем файл
# если файл отправляется без сжатия, то нужно указать имя файла без расширения
# если файл отправляется с сжатием, то нужно указать имя файла + желаемое расширение
# (если этого не сделать, то будет выбрано имя, отправленного файла)
@bot.message_handler(content_types=['document', 'photo'])
def handle_files(message):
    if message.from_user.id in admins:
        try:
            if message.caption:
                file_name = message.caption
            else:
                if message.document:
                    file_name = message.document.file_name
                else:
                    # если пользователь не указал имя для изображения,
                    # то выбрасываем исключение
                    raise Exception('Вы не указалии имя для файла')

            # если нужно сохранить в бд документ
            if message.document:
                # Получаем информацию о документе
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                # Сохраняем документ в бд
                cursor.execute("INSERT INTO files (name, file) VALUES (?, ?)", (file_name, downloaded_file))
                conn.commit()

                bot.reply_to(message, f'Документ "{file_name}" успешно сохранен.')
            # если нужно сохранить фото в бд
            elif message.photo:
                # Получаем информацию о фото
                file_info = bot.get_file(message.photo[-1].file_id)

                # Сохраняем фото в бд
                downloaded_file = bot.download_file(file_info.file_path)
                cursor.execute("INSERT INTO files (name, file) VALUES (?, ?)", (file_name + '.png', downloaded_file))
                conn.commit()

                bot.reply_to(message, f'Фото "{ file_name + ".png" }" успешно сохранено.')
        except Exception as e:
            bot.reply_to(message, f'Ошибка при сохранении файла: {e}')
    else:
        bot.reply_to(message, 'У вас нет прав для этого действия')


bot.polling()
