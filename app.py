from parsers.moex_prices import MoexPriceTQBR
from dotenv import load_dotenv
import os
from time import sleep
import psycopg2


def wait_for_db(host, port, user, password, dbname):
    
    # Функция для ожидания доступности базы данных
    # До начала работы приложения требуется проверить
    # Доступно ли подключение к БД, если нет - вернуть ошибку

    conn = None # устанавливаем флажок соединения на None
    while conn is None: 
        try:
            # попытка подключиться к БД
            print(f'Connecting to the database at host {host}...')
            # записываем результат в conn
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            print('Database connection established.')
            return conn # Возвращаем значение conn
        
        except psycopg2.OperationalError as e: # обработка исключений
            print('Database connection failed:', e) # Если соединение не удалось, вернуть в консоль исключение
            print('Waiting for the database...') # сообщение перед следующей попыткой подключиться
            sleep(5) 

def main():
    load_dotenv() # загружаем переменные среды
    
    # подключаемся в БД в основной части программы
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST") # этот хост подставляется если TEST_MODE=0
    port = os.getenv("DB_PORT")

    # проверяем, не включен ли TEST_MODE режим. Он используется для тестов на пайплайне
    TEST_MODE = int(os.getenv("TEST_APP_MODE")) # считываем значение
    print(f"TEST_MODE_STATUS: {TEST_MODE}") # выводим статус 
    if  TEST_MODE == 1: # если тест флаг активен, то
        host = "localhost" # переключаемся на БД по адресу localhost для тестов.

    # Возвращаем ответ соединения к БД в переменную conn
    conn = wait_for_db(host, port, user, password, dbname)
    if conn is None: # если None 
        print("Failed to establish database connection after multiple retries.")
        exit(1) # завершаемся с кодом 1

    # Создаем экземпляр класса fetcher для получения тикеров и цен TQBR
    # Таже передаем ему параметры подключения к БД для записи. 
    # Также передаем название лог файла для логирования действий
    fetcher = MoexPriceTQBR(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
        logfile='log.txt'
    )
    
    # Интервал обновления — периодичность запуска в секундах.
    # Устанавливаем необходимое время опроса. Это значение устанавливает 
    # В приложении sleep до следующей итерации
    update_interval = int(os.getenv("TIME_SLEEP"))
    
    # Бесконечный цикл для периодического выполнения задач    
    while TEST_MODE == 0: # если мы не в тестовом режиме
        print('Fetching new prices and updating the database...')
        fetcher.get_prices()
        fetcher.update_db()
        fetcher.show_prices()
        fetcher.calculate_null_prices_percentage()
        print(f"Sleeping for {update_interval} seconds.")
        sleep(update_interval)  # Ожидаем заданный интервал перед следующим обновлением.
    else:
        # Иначе если 1 или все что угодно, то тестовый режим - исполняем код один раз
        # Эта логика реализована для того чтобы приложение не зацикливалось на выполнении тестирования
        # Нам требуется один раз пройти итерацию, чтобы вернуть успешное выполнение и перейти к следующим 
        # шагам пайплайна.
        print("WARNING! TEST MODE ON")
        print('Running in test mode (one-time execution)...')
        fetcher.get_prices()
        fetcher.update_db()
        fetcher.show_prices()
        fetcher.calculate_null_prices_percentage()

# выполняем main
if __name__ == "__main__":
    main()