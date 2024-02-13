# Использование базового образа Python 3.10
FROM python:3.10

# Установка рабочей директории в контейнере
WORKDIR /app

# Копирование файла зависимостей в рабочую директорию
COPY requirements.txt .

# Установка зависимостей из файла
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всех файлов проекта в контейнер
COPY . .

# Команда запуска приложения
CMD ["python", "./app.py"]