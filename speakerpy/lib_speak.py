import io
import os
import pathlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from hashlib import md5
from typing import Generator, Literal

import sounddevice
import soundfile
import torch
from pydub import AudioSegment
from silero import silero_tts
from tqdm import tqdm

from .lib_helper import timeit
from .lib_sl_text import SeleroText


class SpeakerBase:
    #: Для синхронизации потоков озвучки текста
    _th_lock_speak = threading.Lock()

    def __init__(
        self,
        model_id,
        language: Literal["ru", "en"],
        speaker: Literal["aidar", "baya", "kseniya", "xenia", "random"],
        device="cpu",
    ) -> None:
        self.language = language
        self.model_id = model_id
        # Модель
        self.model = self._init_models(
            model_id=model_id,
            language=language,
            device=device,
        )
        # Голос
        self.speaker = speaker

    @staticmethod
    def _init_models(
        model_id: str,
        language: Literal["ru"] = "ru",
        device: Literal[
            "cpu",
            "cuda",
            "ipu",
            "xpu",
            "mkldnn",
            "opengl",
            "opencl",
            "ideep",
            "hip",
            "ve",
            "fpga",
            "ort",
            "xla",
            "lazy",
            "vulkan",
            "mps",
        ] = "cpu",
    ):
        """
        Инициализация ИИ модели

        model_id: Доступные модели https://github.com/snakers4/silero-models/blob/master/models.yml
        """
        _device = torch.device(device)
        _model, *_any = silero_tts(language=language, speaker=model_id, device=_device)
        return _model

    ####################

    def _synthesize_text(
        self, text: str, sample_rate: int, put_accent: bool = True, put_yo: bool = True
    ) -> torch.Tensor:
        """Синтезировать текст"""
        audio: torch.Tensor = self.model.apply_tts(
            text=text,
            speaker=self.speaker,
            sample_rate=sample_rate,
            put_accent=put_accent,
            put_yo=put_yo,
        )
        return audio

    def _speak(
        self,
        th_name: int,
        text: str,
        audio: torch.Tensor,
        sample_rate: int,
        speed: float = 1.0,
    ):
        """Озвучить текст

        :param audio: Аудио
        :param sample_rate: Частота
        :param speed: Скорость воспроизведения [от 1.0 до 2.0]
        """
        _speed = sample_rate * speed
        # Блокировка потока. Может говорить только один поток
        with self._th_lock_speak:
            print(f"Th: {th_name}\t| {text}")
            sounddevice.play(audio, samplerate=_speed)
            time.sleep((len(audio) / _speed))
            sounddevice.stop()


class Speaker(SpeakerBase):
    @timeit
    def speak(
        self,
        text: str,
        sample_rate: int,
        speed=1.0,
        *,
        put_accent: bool = True,
        put_yo: bool = True,
    ):
        """Синтезировать и воспроизвести звук

        text         : Текст который нужно озвучить
        sample_rate  : Частота дискретизации(качество), у каждой модели свои доступные значения
        speed        : Скорость воспроизведения звука [от 1.0 до 2.0]
        put_accent   : Флаг автоматической простановки ударения;
        put_yo       : Флаг автоматической простановки буквы ё;
        """
        sl_text = SeleroText(text, to_language=self.language)

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Синтезируем и озвучиваем текст по кускам
            for i, _chunk_text in enumerate(sl_text.chunk()):
                audio: torch.Tensor = self._synthesize_text(
                    _chunk_text,
                    sample_rate=sample_rate,
                    put_accent=put_accent,
                    put_yo=put_yo,
                )
                executor.submit(self._speak, i, _chunk_text, audio, sample_rate, speed)

    @timeit
    def to_mp3(
        self,
        text: str,
        name_text: str,
        sample_rate: int,
        audio_dir: pathlib.Path | str,
        speed: float = 1.0,
    ) -> pathlib.Path:
        """Синтезировать и сохранить звук в mp3 файл

        text         : Текст который нужно озвучить
        name_text    : Имя текста(файла)
        sample_rate  : Частота дискретизации(качество), у каждой модели свои доступные значения
        audio_path   : Папка куда сохранить файл
        speed        : Скорость воспроизведения звука [от 1.0 до 2.0]

        return: Путь к сохраненному файлу
        """
        name_text = name_text.replace(" ", "_")
        # Текст для синтезации
        sl_text = SeleroText(text, to_language=self.language)
        # Скорость речи
        _speed: int = int(sample_rate * speed)
        ###
        #
        # Перебираем и синтезируем куски в файлы
        #
        # Список путей кусков
        list_path_to_audio: list[pathlib.Path] = list(
            self._chunks_synthes(sl_text, audio_dir, _speed, sample_rate)
        )
        ###
        #
        # Объединить куски файлов в единый файл mp3
        #
        output_file: pathlib.Path = pathlib.Path(audio_dir) / (
            "out_"
            + name_text
            + md5(
                f"{text}{_speed}{self.model_id}{self.language}{self.speaker}".encode(
                    "utf-8"
                )
            ).hexdigest()
            + ".mp3"
        )
        self._join_mp3(
            list_path_to_audio,
            output_file=output_file,
        )

        return list_path_to_audio

    ###################################################
    #
    #
    #

    @staticmethod
    def _join_mp3(filenames: list[pathlib.Path], output_file: pathlib.Path):
        """Объединить куски mp3 в единое mp3 файл

        filenames   : Список кусков файлов с MP3
        output_file : Путь куда сохранить единый MP3
        """
        if not output_file.exists():
            combined = AudioSegment.empty()

            # Объединяем все аудио файлы в список
            for filename in filenames:
                sound = AudioSegment.from_mp3(filename)
                combined += sound

            # Экспортируем объединенный файл в MP3
            combined.export(output_file, format="mp3")
            print("Build___Mp3: 0 \t| ", output_file)
        else:
            print("Cache___Mp3: 0 \t| ", output_file)

    def _chunks_synthes(
        self,
        sl_text: SeleroText,
        audio_dir: pathlib.Path,
        speed: float,
        sample_rate: int,
    ) -> Generator[pathlib.Path, None, None]:
        """Синтезировать куски текста и возвращать путь к синтезированным файлам

        sl_text: SeleroText, объект текста, разбитого на куски
        audio_dir: pathlib.Path, путь до папки для сохранения аудио
        speed: float, скорость синтеза (пример: 0.5 - в два раза медленнее, 2 - в два раза быстрее)
        sample_rate: int, частота дискретизации

        return: Путь до синтезированного аудио файла
        """
        for i, chunk_text in enumerate(tqdm(sl_text.chunk())):
            path_to_audio = (
                pathlib.Path(audio_dir)
                / "cache"
                / (
                    md5(
                        f"{chunk_text}{speed}{self.model_id}{self.language}{self.speaker}".encode(
                            "utf-8"
                        )
                    ).hexdigest()
                    + ".mp3"
                )
            )
            os.makedirs(path_to_audio.parent, exist_ok=True)
            if not path_to_audio.exists():
                audio = self._synthesize_text(
                    chunk_text,
                    sample_rate=sample_rate,
                    put_accent=True,
                    put_yo=True,
                )
                # Сохраняем в MP3
                with io.BytesIO() as buffer:
                    soundfile.write(buffer, audio, sample_rate, format="WAV")
                    # Конвертируем данные из буфера WAV в файл MP3
                    buffer.seek(0)
                    sound = AudioSegment.from_wav(buffer)
                    # сохранить в mp3 файл
                    sound.export(path_to_audio, format="mp3")
                tqdm.write(f"Build_Chunk: {i} \t| {path_to_audio}")
            else:
                tqdm.write(f"Cache_Chunk: {i} \t| {path_to_audio}")

            yield path_to_audio
