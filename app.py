from parsers.moex_prices import MoexPriceTQBR
from dotenv import load_dotenv
import os
import psycopg2
from time import sleep


def wait_for_db(host, port, user, password, dbname):
    conn = None
    while conn is None:
        try:
            print(f'Connecting to the database at host {host}...')
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            print('Database connection established.')
            return conn  # Возвращаем объект подключения для дальнейшего использования.
        except psycopg2.OperationalError as e:
            print('Database connection failed:', e)
            print('Waiting for the database...')
            sleep(5)

# В основной функции теперь есть логика для прерывания попыток после TEST_MODE.
def main():
    load_dotenv()
    
    # Базовая конфигурация подключения к БД.
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_DOCKER_HOST")
    port = os.getenv("DB_DOCKER_PORT")

    # Если установлена переменная TEST_MODE, используем localhost.
    if os.getenv("TEST_MODE") == "true":
        host = "localhost"
    
    # Ожидание готовности базы данных и подключение к ней.
    conn = wait_for_db(host, port, user, password, dbname)
    if conn is None:
        print("Failed to establish database connection after multiple retries.")
        exit(1)  # Завершение приложения с ошибкой, если не удалось подключиться.

    # Выполнение операций с MOEX и базой данных.
    fetcher = MoexPriceTQBR(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )

    print('Fetching new prices and updating the database...')
    fetcher.get_prices()
    fetcher.update_db()
    fetcher.show_prices()
    fetcher.calculate_null_prices_percentage()

    # Если TEST_MODE активен, завершаем после одной итерации.
    if os.getenv("TEST_MODE") == "true":
        return

    # В противном случае продолжаем выполнение в бесконечном цикле.
    while True:
        sleep(int(os.getenv("TIME_SLEEP", "300")))  # Пауза перед следующим обновлением.


if __name__ == "__main__":
    main()