import pathlib

from .lib_speak import Speaker


def main(sp: Speaker):
    # sp.speak(text, sample_rate=48000, speed=1.0)

    _file = (
        pathlib.Path(__file__).parent.parent
        / "books"
        / "shot Приключения Шерлока Холмса.txt"
    )
    sp.to_mp3(
        text=_file.read_text(),
        name_text="shot Приключения Шерлока Холмса",
        sample_rate=48000,
        audio_dir=pathlib.Path(__file__).parent.parent / "mp3",
        speed=1.0,
    )


if __name__ == "__main__":
    """
    model_id: Доступные модели https://github.com/snakers4/silero-models/blob/master/models.yml
    """
    # Русски язык
    sp = Speaker(model_id="ru_v3", language="ru", speaker="aidar", device="cpu")
    # Английский язык
    # sp = Speaker(model_id="v3_en", language="en", speaker="en_6", device="cpu", DEBUG=True)
    main(sp)
