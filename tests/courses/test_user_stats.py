from unittest.mock import ANY

from litestar.status_codes import HTTP_200_OK

from backend.courses.models import LanguageData, UserProgress, WordData


async def test_get_user_stats(http_client, user, auth_headers):
    await UserProgress(
        id=user.id,
        languages={
            "es": LanguageData(
                courses=["casa.s01e01"],
                words={
                    "Saber": WordData(  # new word
                        seen_times=1,
                        last_seen_ts=1000,
                        correctness_rate=100,
                    ),
                    "Pensar": WordData(  # new word
                        seen_times=2,
                        last_seen_ts=1000,
                        correctness_rate=100,
                    ),
                    "El": WordData(  # normal word
                        last_seen_ts=999,
                        seen_times=10,
                        correctness_rate=90,
                    ),
                    "Que": WordData(  # normal word
                        seen_times=10,
                        last_seen_ts=999,
                        correctness_rate=90,
                    ),
                    "Ver": WordData(  # word needs practice (error rate)
                        seen_times=10,
                        last_seen_ts=999,
                        correctness_rate=70,
                    ),
                    "Decir": WordData(  # word not encountered for too long
                        seen_times=10,
                        last_seen_ts=1,
                        correctness_rate=90,
                    ),
                },
            )
        },
    ).save()

    response = await http_client.get(f"/user/{user.id}/stats", headers=auth_headers)

    assert response.status_code == HTTP_200_OK, response.json()

    assert response.json() == {
        "es": {
            "casa.s01e01": {
                "bad": 1,
                "encountered": 6,
                "exercises": 0,
                "practiced": 5,
                "total_count": ANY,
                "understanding_rate": ANY,
            }
        }
    }
