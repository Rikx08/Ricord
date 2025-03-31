import socketio
from aiohttp import web
import sqlite3

# Подключение к базе данных сообщений
conn_messages = sqlite3.connect("messages.db", check_same_thread=False)
cursor_messages = conn_messages.cursor()
cursor_messages.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT)")
conn_messages.commit()

# Подключение к основной базе данных пользователей (db.sqlite3)
conn_users = sqlite3.connect("../db.sqlite3", check_same_thread=False)
cursor_users = conn_users.cursor()

# Укажи правильное название таблицы, в которой хранятся пользователи
USER_TABLE = "auth_user"  # Измени на реальное название
USER_COLUMN = "username"

# Создаем объект сервера
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# Сопоставление sid и user_id
user_sessions = {}

# Обработчик подключения нового клиента
@sio.event
async def connect(sid, environ):
    print(f'Клиент {sid} подключен')

    # Получаем user_id из параметров (нужно передавать user_id при подключении)
    user_id = environ.get("HTTP_USER_ID")
    if not user_id:
        user_id = 0  # По умолчанию первый пользователь

    user_sessions[sid] = int(user_id)

    # Получаем имя пользователя из `db.sqlite3`
    cursor_users.execute(f"SELECT {USER_COLUMN} FROM {USER_TABLE} WHERE id = ?", (user_id,))
    user = cursor_users.fetchone()
    username = user[0] if user else "Аноним"

    # Отправляем пользователю историю сообщений
    cursor_messages.execute("SELECT user_id, text FROM messages")
    messages = cursor_messages.fetchall()
    for msg_user_id, text in messages:
        cursor_users.execute(f"SELECT {USER_COLUMN} FROM {USER_TABLE} WHERE id = ?", (msg_user_id,))
        sender = cursor_users.fetchone()
        sender_name = sender[0] if sender else "Аноним"
        await sio.emit('message', f"{sender_name}: {text}", room=sid)

    await sio.enter_room(sid, 'common_room')

# Обработчик входящих сообщений
@sio.event
async def message(sid, data):
    print(f'Получено сообщение от {sid}: {data}')
    if not data.strip():  # Проверка на пустую строку
        print("Сообщение не отправлено: пустой текст")
        return None
    else:
        user_id = user_sessions.get(sid, 1)

        # Получаем имя пользователя
        cursor_users.execute(f"SELECT {USER_COLUMN} FROM {USER_TABLE} WHERE id = ?", (user_id,))
        user = cursor_users.fetchone()
        username = user[0] if user else "Аноним"

        # Сохраняем сообщение в `messages.db`
        cursor_messages.execute("INSERT INTO messages (user_id, text) VALUES (?, ?)", (user_id, data))
        conn_messages.commit()

        # Отправляем сообщение всем клиентам
        await sio.emit('message', f"{username}: {data}", room='common_room', skip_sid=sid)

# Обработчик отключения клиента
@sio.event
async def disconnect(sid):
    print(f'Клиент {sid} отключен')
    user_sessions.pop(sid, None)
    await sio.leave_room(sid, 'common_room')

# Запуск сервера
if __name__ == '__main__':
    web.run_app(app, port=5000)
