import os
import pathlib
import re
from string import punctuation, whitespace
from typing import Generator, Literal

import nltk
from num2words import num2words
from transliterate import translit

nltk.download("punkt")


def nltk_remove_other_model_but_russian(directory: str | pathlib.Path):
    """Удалить все языки кроме русского

    directory: Путь к директорию в которой искать файлы
    """

    extension = ".pickle"  # замените на нужное расширение

    # обходим все файлы в указанной директории
    for root, dirs, files in os.walk(directory):
        for file in files:
            # если файл имеет нужное расширение, выводим его путь
            if file.endswith(extension) and not file.startswith("russian"):
                abs_path = os.path.join(root, file)
                os.remove(abs_path)


class SeleroText:
    """
    Класс для хранения, и удобного использования текста,
    который вы хотите синтезировать в голос
    """

    #: Флаг который используется для чтения модели nltk единожды
    IF_INIT = False
    #: Путь для хранения моделей nltk
    download_dir = pathlib.Path(__file__).parent.parent / "models/nltk_store"
    ###
    #
    #: Максимальное количество сиголов в куске текста. Если больше, то это уже новый кусок
    _max_chunk_symbols = 1000
    #: Символы которые нужно исключать
    exclude_characters = whitespace + punctuation

    def __init__(self, text: str, to_language: Literal["ru"]) -> None:
        """Преобразовать текст в подходящий формат."""
        self.text = text
        self.to_language = to_language
        ###
        #
        # Инициализация моделей nltk
        #
        if not self.IF_INIT:
            os.makedirs(self.download_dir, exist_ok=True)
            # nltk.download(
            #     "punkt",
            #     download_dir=self.download_dir,
            # )
            if self.to_language in ("ru"):
                # Удалить все модели языки кроме русского языка
                nltk_remove_other_model_but_russian(self.download_dir)
            self.IF_INIT = True
        #
        self._normal()

    def chunk(self) -> Generator[str, None, None]:
        """Поделить текст на куски"""

        # 3. Разделения по предложениям
        for t in self._punkt(self.text):
            if t:
                # 4. Разделения длинных предложений
                for t2 in self._split_long_string(t, self._max_chunk_symbols):
                    # В тексте должны быть буквы
                    if re.search(r"\w", t2):
                        yield t2

    ##########################
    #
    #
    def _normal(self) -> str:
        """Преобразовать текст в подходящий формат для синтезаци

        to_language: В какой язык сделать тралит
        """
        # 1. Транскрипция иностранного языка
        if self.to_language in ("ru"):
            self.text = translit(self.text, self.to_language)
        # 2. Текстовое описание цифр
        self.text = self._nums_to_text()

    def _transcription(self) -> str:
        """Транскрипция иностранного языка (Типо hello->хелоо)"""
        self.text = translit(self.text, self.to_language)

    def _nums_to_text(self) -> str:
        """Преобразует числа в буквы: 1 -> один, 23 -> двадцать три"""
        return re.sub(
            r"(\d+)",
            lambda x: num2words(int(x.group(0)), lang=self.to_language),
            self.text,
        )

    @staticmethod
    def _punkt(text: str) -> Generator[str, None, None]:
        """Разделения по предложениям"""
        for t in nltk.sent_tokenize(text, language="russian"):
            # Оставляем в строке только буквы, цифры и знаки пунктуации.
            yield re.sub(r"[^a-zA-Zа-яА-Я0-9.,!?;:\-\–\'\"\s]", "", t)

    @staticmethod
    def _split_long_string(text: str, slice_length: int) -> Generator[str, None, None]:
        """Поделить текст на части.

        :param text: Текст
        :param slice_length: Через сколько символов делить строку
        """
        words = text.split()
        current_slice = []
        current_length = 0
        for word in words:
            # Добавляем текущее слово к текущей "кусочной" строке,
            # если она еще не началась или длина слова и пробела не превышает slice_length.
            if not current_slice or current_length + len(word) + 1 <= slice_length:
                current_slice.append(word)
                current_length += len(word) + 1
            else:
                # Иначе, если текущая "кусочная" строка уже достаточно длинная,
                # то добавляем ее в результат и начинаем новую "кусочную" строку с текущего слова.
                yield " ".join(current_slice)
                current_slice = [word]
                current_length = len(word)
        # Добавляем последнюю "кусочную" строку в результат.
        yield " ".join(current_slice)
