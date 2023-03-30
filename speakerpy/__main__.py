import argparse
import pathlib

settings_selero = {
    "ru": {
        "sample_rate": 48000,
        "sp": dict(model_id="ru_v3", language="ru", speaker="aidar", device="cpu"),
    },
    "en": {
        "sample_rate": 48000,
        "sp": dict(model_id="v3_en", language="en", speaker="en_6", device="cpu"),
    },
}


def main(args):
    from .lib_speak import Speaker

    sample_rate = (
        args.sample_rate
        if args.sample_rate
        else settings_selero[args.language]["sample_rate"]
    )

    sp = Speaker(**settings_selero[args.language]["sp"])

    file = pathlib.Path(args.file)
    text = file.read_text()

    if args.type_out == "speak":
        sp.speak(text, sample_rate=sample_rate, speed=args.speed)
    elif args.type_out == "mp3":
        sp.to_mp3(
            text=text,
            name_text=args.name_text if args.name_text else file.name,
            sample_rate=sample_rate,
            audio_dir=args.audio_dir / "mp3",
            speed=args.speed,
        )
    else:
        raise KeyError("Не указано - Каким образом вывести сентезированный текст")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🎙️ SpeakerPy: CLI для синтеза речи с использованием SpeakerPy 🎙️",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Примеры использования:\n"
        "  python -m speakerpy -l ru -t speak -f ./books/example.txt;\n"
        "  python -m speakerpy -l ru -t mp3 -f ./books/example.txt;\n"
        "  python -m speakerpy -l en -t speak -f ./books/example.txt;\n"
        "  python -m speakerpy -l en -t mp3 -f ./books/example.txt;\n",
    )
    y = "\033[33m"
    r = "\033[0m"
    parser.add_argument(
        "-l",
        "--language",
        choices=["ru", "en"],
        required=True,
        help=f"{y}Язык синтеза (ru | en){r}",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help=f"{y}Путь к файлу с текстом для озвучивания{r}",
    )
    parser.add_argument(
        "-t",
        "--type_out",
        choices=["mp3", "speak"],
        required=True,
        help=f"{y}Каким образом вывести синтезированный текст (mp3 | speak){r}",
    )
    parser.add_argument(
        "-sr",
        "--sample_rate",
        type=int,
        default=48000,
        help=f"{y}Частота дискретизации (по умолчанию: 48000){r}",
    )
    parser.add_argument(
        "-s",
        "--speed",
        type=float,
        default=1.0,
        help=f"{y}Скорость чтения (по умолчанию: 1.0){r}",
    )
    parser.add_argument(
        "-n",
        "--name_text",
        type=str,
        default="",
        help=f"{y}Имя для текста, с таким именем сохранится итоговый mp3 файл (по умолчанию: имя файла с текстом){r}",
    )
    parser.add_argument(
        "-a",
        "--audio_dir",
        type=str,
        default=pathlib.Path(__file__).parent.parent,
        help=f"{y}Папка для сохранения готовых аудио файлов (по умолчанию: текущая папка){r}",
    )

    args = parser.parse_args()

    main(args)
