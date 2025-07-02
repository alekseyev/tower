from nicegui import ui

from backend.admin.common import render_navigation
from backend.babble.models import BabbleSentence
from backend.courses.models import UserProgress
from backend.settings import settings


def del_action_gen(sentence_id):
    async def del_action(e):
        nonlocal sentence_id
        await BabbleSentence.find_one(BabbleSentence.id == sentence_id).delete()
        ui.navigate.reload()

    return del_action


@ui.page("/babble")
async def babble_page():
    render_navigation("Babble")

    # TODO: get last sentences from analytical log, get last/most complained about sentences
    user = await UserProgress.get("ff2caa0f-2426-4ad4-b9fe-b1e01f0f0e2a")
    last_sent_ids = user.languages["es"].last_exercises
    data = await BabbleSentence.find({"_id": {"$in": last_sent_ids}}).to_list()
    by_id = {sentence.id: sentence for sentence in data}
    langs = list(settings.LANGUAGES.keys())

    with ui.grid(columns=4):
        for i, id in enumerate(last_sent_ids[::-1]):
            if id in by_id:
                sentence = by_id[id]
                lang = langs[0]
                ui.label(i)
                ui.label(sentence.text[lang])
                ui.label(", ".join(sentence.lemmas[lang]))
                with ui.row():
                    ui.button(icon="delete", on_click=del_action_gen(id))
                for lang in langs[1:]:
                    ui.label()
                    ui.label(sentence.text[lang])
                    ui.label(", ".join(sentence.lemmas[lang]))
                    ui.label()
