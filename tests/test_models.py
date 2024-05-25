from backend.courses.models import LanguageData, WordData


def test_suggested_words():
    l_data = LanguageData(
        words={
            "a": WordData(  # new word
                seen_times=1,
                last_seen_ts=1000,
                correctness_rate=100,
            ),
            "b": WordData(  # new word
                seen_times=2,
                last_seen_ts=1000,
                correctness_rate=100,
            ),
            "c": WordData(  # normal word
                seen_times=10,
                last_seen_ts=999,
                correctness_rate=90,
            ),
            "d": WordData(  # normal word
                seen_times=10,
                last_seen_ts=999,
                correctness_rate=90,
            ),
            "e": WordData(  # word needs practice (error rate)
                seen_times=10,
                last_seen_ts=999,
                correctness_rate=70,
            ),
            "f": WordData(  # word not encountered for too long
                seen_times=10,
                last_seen_ts=1,
                correctness_rate=90,
            ),
        }
    )

    assert l_data.suggest_words_to_practice(4) == {"a", "b", "e", "f"}
