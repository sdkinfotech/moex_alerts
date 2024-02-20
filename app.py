from parsers.moex_prices import MoexPriceTQBR
from dotenv import load_dotenv
import os
import psycopg2
from time import sleep


def wait_for_db(host, port, user, password, dbname):
    conn = None
    while conn is None:
        try:
            print('Connecting to the database...')
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            print('Database connection established.')
        except psycopg2.OperationalError as e:
            print('Database connection failed:', e)
            print('Waiting for the database...')
            sleep(5)
        finally:
            if conn is not None:
                conn.close()

def main():
    
    load_dotenv()
    
    # Получение значений переменных окружения
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_DOCKER_HOST")
    port = os.getenv("DB_DOCKER_PORT")
    
    # Ожидание готовности базы данных
    wait_for_db(host, port, user, password, dbname)

    # Создание экземпляра класса для соединения с MOEX и получения данных TQBR
    fetcher = MoexPriceTQBR(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )

    # Выполнение операций с MOEX и базой данных
    print('Fetching new prices and updating the database...')
    fetcher.get_prices()  # Запрос к MOEX и сохранение в формате JSON
    fetcher.update_db()   # Обновление базы данных из JSON
    fetcher.show_prices() # Отображение данных в консоли из JSON
    fetcher.calculate_null_prices_percentage() # Расчет процента отсутствующих цен

    test_mode = os.getenv("TEST_MODE")

    if not test_mode:
        # Бесконечный цикл работы приложения
        while True:
            # Ожидание готовности базы данных
            wait_for_db(host, port, user, password, dbname)

            # Выполнение операций с MOEX и базой данных
            print('Fetching new prices and updating the database...')
            fetcher.get_prices()  # Запрос к MOEX и сохранение в формате JSON
            fetcher.update_db()   # Обновление базы данных из JSON
            fetcher.show_prices() # Отображение данных в консоли из JSON
            fetcher.calculate_null_prices_percentage() # Расчет процента отсутствующих цен
            
            delay = int(os.getenv("TIME_SLEEP", "300"))
            print(f'Waiting for {delay} seconds before the next update...')
            sleep(delay)  # По умолчанию 300 секунд = 5 минут

if __name__ == "__main__":
    main()