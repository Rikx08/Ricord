import socketio
from aiohttp import web

sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="aiohttp")  # Разрешаем кросс-доменные запросы
app = web.Application()

sio.attach(app)


# Обработчик подключения нового клиента к общей комнате
@sio.event
async def connect(sid, environ):
    print(f'Клиент {sid} подключен к общей комнате')

    # Присоединяем клиента к общей комнате
    await sio.enter_room(sid, 'common_room')


# Обработчик отключения клиента от общей комнаты
@sio.event
async def disconnect(sid):
    print(f'Клиент {sid} отключен от общей комнаты')

    # Покидаем общую комнату при отключении
    await sio.leave_room(sid, 'common_room')


# Обработчик нового сообщения от клиента
@sio.event
async def message(sid, data):
    print(f'Получено сообщение от {sid}: {data}')

    # Отправляем сообщение всем клиентам в общей комнате, кроме отправителя
    await sio.emit('message', data, room='common_room', skip_sid=sid)


# Запуск сервера
if __name__ == '__main__':
    web.run_app(app, port=5000)