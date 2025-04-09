import socketio
from aiohttp import web
import sqlite3
import os
import base64
from datetime import datetime

MEDIA_DIR = "../media/chat_images"
os.makedirs(MEDIA_DIR, exist_ok=True)

# # Подключение к базе данных сообщений
# conn_messages = sqlite3.connect("messages.db", check_same_thread=False)
# cursor_messages = conn_messages.cursor()
# cursor_messages.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT)")
# conn_messages.commit()

# Подключение к основной базе данных пользователей (db.sqlite3)
conn_messages = sqlite3.connect('../db.sqlite3', check_same_thread=False)
cursor_messages = conn_messages.cursor()

# Укажи правильное название таблицы, в которой хранятся пользователи
USER_TABLE = "auth_user"  # Измени на реальное название
USER_COLUMN = "username"

# Создаем объект сервера
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# Сопоставление sid и user_id
user_sessions = {}


async def static_handler(request):
    path = request.match_info.get('path', '')
    file_path = os.path.join(MEDIA_DIR, path)
    if os.path.exists(file_path):
        return web.FileResponse(file_path)
    return web.Response(status=404)

# Добавление маршрута для статичных файлов
app.router.add_get('/media/chat_images/{path:.*}', static_handler)
# Обработчик подключения нового клиента


@sio.event
async def connect(sid, environ):
    print(f'Клиент {sid} подключен')

    user_id = environ.get("HTTP_USER_ID")
    if not user_id:
        user_id = 0  # по умолчанию первый пользователь

    user_sessions[sid] = int(user_id)

    # Получаем имя пользователя из базы данных
    cursor_messages.execute("SELECT username FROM auth_user WHERE id = ?", (user_id,))
    user = cursor_messages.fetchone()
    username = user[0] if user else "Аноним"

    # Отправляем пользователю историю сообщений
    cursor_messages.execute("SELECT user_id, text, image FROM main_message")
    messages = cursor_messages.fetchall()
    for msg_user_id, text, image_path in messages:
        cursor_messages.execute("SELECT username FROM auth_user WHERE id = ?", (msg_user_id,))
        sender = cursor_messages.fetchone()
        sender_name = sender[0] if sender else "Аноним"

        # Если изображение сохранено — формируем URL (или None)
        image_url = image_path if image_path else None

        await sio.emit('message', {
            'user': sender_name,
            'message': text,
            'image': image_url
        }, room=sid)

    await sio.enter_room(sid, 'common_room')


@sio.event
async def message(sid, data):
    print(f'Получено сообщение от {sid}: {data}')

    message_text = data.get('message', '').strip()
    image = data.get('image')

    user_id = user_sessions.get(sid, 1)

    # Получаем имя пользователя
    cursor_messages.execute("SELECT username FROM auth_user WHERE id = ?", (user_id,))
    user = cursor_messages.fetchone()
    username = user[0] if user else "Аноним"

    if image:
        image_path = save_image(image)
    else:
        image_path = None

    # Сохраняем в базу
    cursor_messages.execute(
        "INSERT INTO main_message (user_id, text, image, timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
        (user_id, message_text, image_path)
    )
    conn_messages.commit()

    # Отправка другим пользователям
    await sio.emit('message', {
        'user': username,
        'message': message_text,
        'image': image_path,
    }, room='common_room', skip_sid=sid)


# Обработчик отключения клиента
@sio.event
async def disconnect(sid):
    print(f'Клиент {sid} отключен')
    user_sessions.pop(sid, None)
    await sio.leave_room(sid, 'common_room')


def save_image(image_base64):
    try:
        header, encoded = image_base64.split(",", 1)
        file_ext = header.split('/')[1].split(';')[0]
        image_data = base64.b64decode(encoded)
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{file_ext}"
        file_path = os.path.join(MEDIA_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(image_data)
        return f"/media/chat_images/{filename}"  # относительный путь для HTML
    except Exception as e:
        print(f"Ошибка сохранения изображения: {e}")
        return None


# Запуск сервера
if __name__ == '__main__':
    web.run_app(app, port=5000)
