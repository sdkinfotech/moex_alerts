# Использование базового образа Python 3.10
FROM python:3.10

# Установим не-root пользователя для безопасности
RUN useradd -m myuser
USER myuser

# Создаем виртуальное окружение Python внутри контейнера и активируем его
ENV VIRTUAL_ENV=/home/myuser/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Установка рабочей директории в контейнере
WORKDIR /home/myuser/app

# Копирование файла зависимостей в рабочую директорию
COPY requirements.txt .

# Установка зависимостей из файла в виртуальное окружение
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всех файлов проекта в контейнер
COPY . .

# Команда запуска приложения
CMD ["python", "./app.py"]