from parsers.moex_prices import MoexPriceTQBR
from dotenv import load_dotenv
import os
from time import sleep
import psycopg2

# Функция для ожидания доступности базы данных
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
            return conn
        except psycopg2.OperationalError as e:
            print('Database connection failed:', e)
            print('Waiting for the database...')
            sleep(5)

def main():
    load_dotenv()
    
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")  # Используйте DB_HOST, если нет специального ключа для docker
    port = os.getenv("DB_PORT")

    # проверяем, не включен ли TEST_MODE режим. Он используется для тестов на пайплайне
    TEST_MODE = int(os.getenv("TEST_APP_MODE"))
    print(f"TEST_MODE_STATUS: {TEST_MODE}")
    if  TEST_MODE == 1:
        host = "localhost" # переключаемся на localhost для тестов

    conn = wait_for_db(host, port, user, password, dbname)
    if conn is None:
        print("Failed to establish database connection after multiple retries.")
        exit(1)

    # Создаем экземпляр класса fetcher
    fetcher = MoexPriceTQBR(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
        logfile='log.txt'  # Указываем имя файла лога
    )
    
    # Интервал обновления — периодичность запуска в секундах.
    update_interval = int(os.getenv("TIME_SLEEP"))
    
    # Бесконечный цикл для периодического выполнения задач
    
    while TEST_MODE == 0:
        print('Fetching new prices and updating the database...')
        fetcher.get_prices()
        fetcher.update_db()
        fetcher.show_prices()
        fetcher.calculate_null_prices_percentage()
        print(f"Sleeping for {update_interval} seconds.")
        sleep(update_interval)  # Ожидаем заданный интервал перед следующим обновлением.
    else:
        # Тестовый режим - исполняем код один раз
        print("WARNING! TEST MODE ON")
        print('Running in test mode (one-time execution)...')
        fetcher.get_prices()
        fetcher.update_db()
        fetcher.show_prices()
        fetcher.calculate_null_prices_percentage()

if __name__ == "__main__":
    main()