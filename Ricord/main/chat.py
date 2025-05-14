import socketio
from aiohttp import web
import sqlite3
import os
import base64
from datetime import datetime
from threading import Lock
# Подключение к основной базе данных пользователей (db.sqlite3)
conn_messages = sqlite3.connect('../db.sqlite3', check_same_thread=False)
cursor_messages = conn_messages.cursor()


# Укажи правильное название таблицы, в которой хранятся пользователи
USER_TABLE = "auth_user"  # Измени на реальное название
USER_COLUMN = "username"

# Создаем объект сервера
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application(client_max_size=100*1024**2)  # 100MB
sio.attach(app)

# Сопоставление sid и user_id
user_sessions = {}
user_rooms = {}


# Глобальная блокировка для доступа к базе данных
db_lock = Lock()


def safe_db_execute(query, params=()):
    with db_lock:
        cursor = conn_messages.cursor()
        cursor.execute(query, params)
        conn_messages.commit()
        return cursor.fetchall()


@sio.event
async def join(sid, room_name):
    prev_room = user_rooms.get(sid)
    if prev_room:
        await sio.leave_room(sid, prev_room)

    await sio.enter_room(sid, room_name)
    user_rooms[sid] = room_name
    print(f"User {sid} joined room: {room_name}")

    # Отправка истории сообщений из этой комнаты
    cursor_messages.execute("SELECT user_id, text, image, image_type FROM main_message WHERE room = ?", (room_name,))
    messages = cursor_messages.fetchall()

    for msg_user_id, text, image_data, image_type in messages:
        cursor_messages.execute("SELECT username FROM auth_user WHERE id = ?", (msg_user_id,))
        sender = cursor_messages.fetchone()
        sender_name = sender[0] if sender else "Аноним"

        # Если есть изображение - создаем data URL
        image_url = None
        if image_data and image_type:
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            image_url = f"data:{image_type};base64,{image_base64}"

        await sio.emit('message', {
            'user': sender_name,
            'message': text,
            'image': image_url
        }, room=sid)


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
    cursor_messages.execute("SELECT user_id, text, image, image_type FROM main_message")
    messages = cursor_messages.fetchall()
    for msg_user_id, text, image_path, image_type in messages:
        cursor_messages.execute("SELECT username FROM auth_user WHERE id = ?", (msg_user_id,))
        sender = cursor_messages.fetchone()
        sender_name = sender[0] if sender else "Аноним"

        image_url = None
        if image_path and image_type:
            image_base64 = base64.b64encode(image_path).decode('utf-8')
            image_url = f"data:{image_type};base64,{image_base64}"
        print(f"Image type: {image_type}")
        await sio.emit('message', {
            'user': sender_name,
            'message': text,
            'image': image_url
        }, room=sid)


@sio.event
async def message(sid, data):
    print(f'Получено сообщение от {sid}: {data}')

    message_text = data.get('message', '').strip()
    image_data_url = data.get('image')

    user_id = user_sessions.get(sid, 1)
    room_name = user_rooms.get(sid, 'common_room')

    cursor_messages.execute("SELECT username FROM auth_user WHERE id = ?", (user_id,))
    user = cursor_messages.fetchone()
    username = user[0] if user else "Аноним"

    # Обработка изображения
    image_binary = None
    image_type = None

    if image_data_url:
        try:
            # Разделяем data URL на части
            if isinstance(image_data_url, str) and image_data_url.startswith('data:image'):
                header, encoded = image_data_url.split(",", 1)
                image_type = header.split(':')[1].split(';')[0]

                # Декодируем base64 в бинарные данные
                image_binary = base64.b64decode(encoded)
            else:
                # Если пришло что-то неожиданное
                print(f"Unexpected image format: {type(image_data_url)}")
                image_binary = None
        except Exception as e:
            print(f"Ошибка обработки изображения: {e}")
            image_binary = None

    # Сохраняем сообщение в базу данных
    try:
        if image_binary is not None:
            cursor_messages.execute(
                "INSERT INTO main_message (user_id, text, image, image_type, room, timestamp) "
                "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (user_id, message_text, image_binary, image_type, room_name)
            )
        else:
            cursor_messages.execute(
                "INSERT INTO main_message (user_id, text, room, timestamp) "
                "VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (user_id, message_text, room_name)
            )
        conn_messages.commit()
    except Exception as e:
        print(f"Ошибка сохранения сообщения: {e}")
        conn_messages.rollback()

    # Отправляем сообщение всем в комнате (кроме отправителя)
    await sio.emit('message', {
        'user': username,
        'message': message_text,
        'image': image_data_url  # Отправляем оригинальный data URL
    }, room=room_name, skip_sid=sid)


@sio.event
async def disconnect(sid):
    print(f'Клиент {sid} отключен')
    user_sessions.pop(sid, None)
    user_rooms.pop(sid, None)
    await sio.leave_room(sid, 'common_room')


@sio.event
async def join_voice_room(sid, room_name):
    await sio.enter_room(sid, room_name)
    for other_sid in sio.manager.rooms['/'].get(room_name, set()):
        if other_sid != sid:
            await sio.emit('user_joined', {'userId': sid}, room=other_sid)

@sio.event
async def offer(sid, data):
    await sio.emit('offer', {'from': sid, 'offer': data['offer']}, room=data['to'])

@sio.event
async def answer(sid, data):
    await sio.emit('answer', {'from': sid, 'answer': data['answer']}, room=data['to'])

@sio.event
async def ice_candidate(sid, data):
    await sio.emit('ice_candidate', {'from': sid, 'candidate': data['candidate']}, room=data['to'])

# Запуск сервера
if __name__ == '__main__':
    web.run_app(app, port=5000)