from litestar import get
from pydantic import BaseModel

from backend.babble.models import BabbleSentence
from backend.courses.courses import get_course_data
from backend.courses.models import UserProgress


class WordsStats(BaseModel):
    total_count: int
    encountered: int
    practiced: int
    bad: int
    understanding_rate: int
    exercises: int


@get("/user/{user_id:str}/stats")
async def get_user_stats(user_id: str) -> dict[str, dict[str, WordsStats]]:
    user_progress = await UserProgress.get(user_id)

    result = {}

    for lang, lang_data in user_progress.languages.items():
        result[lang] = {}
        for course in lang_data.courses:
            c_data = get_course_data(lang, course)
            total_count = len(c_data)

            encountered = len([word for word in lang_data.words if word in c_data])
            practiced = len(
                [word for word, w_data in lang_data.words.items() if word in c_data and w_data.seen_times > 1]
            )
            bad = len([word for word in lang_data.get_bad_words() if word in c_data])
            understanding_count = sum(c_data[word] for word in lang_data.words if word in c_data)
            total = sum(count for count in c_data.values())

            result[lang][course] = WordsStats(
                total_count=total_count,
                encountered=encountered,
                practiced=practiced,
                bad=bad,
                understanding_rate=int(understanding_count / total * 100),
                exercises=lang_data.total_exercises,
            )

    return result


@get("/user/{user_id:str}/exercises")
async def get_user_exercises(user_id: str, lang: str) -> list[BabbleSentence]:
    user_progress = await UserProgress.get(user_id)
    return await user_progress.get_sentences(lang)


user_handlers = [get_user_stats, get_user_exercises]
