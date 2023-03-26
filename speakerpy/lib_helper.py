from time import process_time


def timeit(func):
    """Декоратор для замера времени выполнения функции"""

    def wrapper(*args, **kwargs):
        start_time = process_time()
        result = func(*args, **kwargs)
        end_time = process_time()
        print(
            f"Время выполнения функции '{func.__name__}': {end_time - start_time} секунд"
        )
        return result

    return wrapper
