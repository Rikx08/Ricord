from django.core.management.base import BaseCommand
import subprocess

class Command(BaseCommand):
    help = 'Запускает сервер чата'

    def handle(self, *args, **kwargs):

        chat_script_path = 'Ricord/main/chat.py'

        # Запуск chat.py через subprocess
        try:
            subprocess.run(['python', chat_script_path], check=True)
            self.stdout.write(self.style.SUCCESS('Сервер чата успешно запущен'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при запуске сервера чата: {e}'))
