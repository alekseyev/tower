import asyncio

from beanie.operators import In
from litestar import get, post
from pydantic import BaseModel

from backend.babble.babble import get_sentences
from backend.babble.models import BabbleSentence
from backend.courses.courses import get_course_data
from backend.courses.models import Exercise, ExerciseResult, UserProgress
from backend.dictionary.models import DICTIONARIES


class WordsStats(BaseModel):
    total_count: int
    encountered: int
    new: int
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
            new_words = len(
                [word for word, w_data in lang_data.words.items() if word in c_data and w_data.seen_times < 5]
            )
            bad = len([word for word in lang_data.get_bad_words() if word in c_data])
            understanding_count = sum(c_data[word] for word in lang_data.words if word in c_data)
            total = sum(count for count in c_data.values())

            result[lang][course] = WordsStats(
                total_count=total_count,
                encountered=encountered,
                new=new_words,
                bad=bad,
                understanding_rate=int(understanding_count / total * 100),
                exercises=lang_data.total_exercises,
            )

    return result


@get("/user/{user_id:str}/exercises")
async def get_user_exercises(user_id: str, lang: str) -> list[Exercise]:
    user_progress = await UserProgress.get(user_id)
    sentences = await user_progress.get_sentences(lang)
    all_words = sum((sentence.lemmas[lang] for sentence in sentences), start=[])
    all_translations = await DICTIONARIES[lang].find({"_id": {"$in": all_words}}).to_list()
    full_dict = {translation.id: translation.translations["en"] for translation in all_translations}
    return [
        Exercise(
            type="word_bank",
            sentence=sentence,
            base_lang=lang,
            dictionary={word: full_dict[word] for word in set(sentence.lemmas[lang]) if word in full_dict},
        )
        for sentence in sentences
    ]


@get("/user/{user_id:str}/exercises/new_words")
async def get_user_exercises_new_words(
    user_id: str, lang: str, course: str, N: int = 4, exercises_per_word: int = 2
) -> list[Exercise]:
    user_progress = await UserProgress.get(user_id)
    new_words = user_progress.get_new_words(lang, course, N)

    sentences = {}
    for word in new_words:
        sentences[word] = await get_sentences(
            dictionary=list(user_progress.languages[lang].words.keys()),
            req_dictionary=[word],
            base_language=lang,
            exclude_ids=user_progress.languages[lang].last_exercises,
            N=exercises_per_word,
        )

    all_words = sum((sentence.lemmas[lang] for ss in sentences.values() for sentence in ss), start=[])
    full_dict = await DICTIONARIES[lang].get_translations(all_words)

    exercises = []

    for word, sentences in sentences.items():
        for i, sentence in enumerate(sentences):
            exercises.append(
                Exercise(
                    type="word_bank",
                    sentence=sentence,
                    base_lang=lang if not (i % 2) else "NATIVE",
                    dictionary={word: full_dict[word] for word in set(sentence.lemmas[lang]) if word in full_dict},
                    new_word=word,
                )
            )

    return exercises


@post("/exercise/result")
async def save_exercise_result(data: ExerciseResult) -> dict:
    sentences, user_progress = await asyncio.gather(
        BabbleSentence.find(In(BabbleSentence.id, list(data.results.keys()))).to_list(),
        UserProgress.get(data.user_id),
    )

    words_for_sentence = {sentence.id: sentence.lemmas[data.lang] for sentence in sentences}

    for exercise_id, correct in data.results.items():
        user_progress.languages[data.lang].add_exercise(
            id=exercise_id, words=words_for_sentence[exercise_id], correct=correct
        )
    await user_progress.save()
    return {"result": "ok"}


user_handlers = [get_user_stats, get_user_exercises, get_user_exercises_new_words, save_exercise_result]
