# Использование базового образа Python 3.10
FROM python:3.10

# Установим не-root пользователя для безопасности
RUN groupadd -r usr02-moex-docker && useradd -m -g usr02-moex-docker usr02-moex-docker

# Создаем виртуальное окружение Python внутри контейнера и активируем его
ENV VIRTUAL_ENV=/home/usr02-moex-docker/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Установка рабочей директории в контейнере
WORKDIR /home/usr02-moex-docker/app

# Копирование файла зависимостей в рабочую директорию
COPY requirements.txt .

# Установка зависимостей из файла в виртуальное окружение
RUN pip install --no-cache-dir -r requirements.txt

# Смена владельца директории
COPY --chown=usr02-moex-docker:usr02-moex-docker . .

# Смена пользователя
USER usr02-moex-docker

# Команда запуска приложения
CMD ["python", "./app.py"]