FROM python:3.11

# Мы устанавливаем зависимости с помощью pip
RUN pip install silero 

# В команде установки зависимостей мы используем apt-get для установки пакета sox и pip для установки Poetry.
RUN apt update && apt install portaudio19-dev ffmpeg && pip install poetry 

# Мы устанавливаем зависимости с помощью pip
RUN pip install sounddevice soundfile pydub tqdm nltk num2words transliterate numpy

# Копируем файлы проекта внутрь контейнера
WORKDIR /app
# Мы копируем все файлы проекта внутрь контейнера в рабочую директорию /app.
COPY . .

# Мы запускаем оболочку Bash при запуске контейнера.
CMD ["bash"]
