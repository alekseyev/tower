import json
from pathlib import Path


def get_courses_list(lang: str) -> list[str]:
    p = Path(lang)
    return [f.name[:-5] for f in p.iterdir() if f.is_file() and f.name.endswith(".json") and f.name != "base.json"]


def get_base_words(lang: str):
    p = Path(lang) / "base.json"
    with p.open() as f:
        return json.load(f)


def get_course_data(lang: str, course: str) -> dict[str, int]:
    p = Path(lang) / f"{course}.json"
    with p.open() as f:
        return json.load(f)


def get_course_words(lang: str, course: str) -> list[str]:
    data = get_course_data(lang, course)

    return list(data.keys())


def get_new_words(lang: str, course: str, known_words: str, N: int = 5) -> list[str]:
    course_words = get_course_words(lang, course)
    new_words = []
    for word in course_words:
        if word not in known_words:
            new_words.append(word)
            if len(new_words) >= N:
                break

    return new_words
