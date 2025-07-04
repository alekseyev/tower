from nicegui import ui

from backend.admin.common import render_navigation
from backend.babble.models import BabbleSentence
from backend.courses.models import UserProgress
from backend.settings import settings


def save_action_gen(sentence_id, editables):
    async def save_action(e):
        ui.notify(f"save action {sentence_id}")
        sentence = await BabbleSentence.get(sentence_id)
        for lang in editables:
            sentence.text[lang] = editables[lang].value.strip()
        sentence.update_lemmas()
        await sentence.save()
        ui.navigate.reload()
        # ui.notify(f"Saved: {sentence}")

    return save_action


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

    for i, id in enumerate(last_sent_ids[::-1]):
        if id in by_id:
            sentence = by_id[id]
            with ui.row().classes("w-full flex"):
                ui.label(i)
                editables = {}
                with ui.column().classes("grow"):
                    for j, lang in enumerate(langs):
                        with ui.row().classes("grow"):
                            ui.label(lang)
                            with ui.column().classes("grow"):
                                editables[lang] = (
                                    ui.input(value=sentence.text[lang]).props("bordered").classes("w-full")
                                )
                                ui.label(", ".join(sentence.lemmas[lang]))
                with ui.row():
                    save_button = ui.button(icon="save")
                    ui.button(icon="delete", on_click=del_action_gen(id))
                save_action = save_action_gen(id, editables)
                save_button.on("click", save_action)
                for lang in editables:
                    editables[lang].on("keydown.enter", save_action)
