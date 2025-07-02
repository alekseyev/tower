from nicegui import ui

from backend.admin.common import render_navigation
from backend.dictionary.models import DICTIONARIES


def save_action_gen(lang, to_lang, word_id, editable):
    async def save_action(e):
        nonlocal word_id
        word = await DICTIONARIES[lang].get(word_id)
        word.translations[to_lang] = [val.strip() for val in editable.value.split("\n") if val.strip()]
        await word.save()
        ui.notify(f"Saved: {word}")

    return save_action


@ui.page("/words/{lang}")
async def words_page(lang: str, search: str = ""):
    def go_action(e):
        return ui.navigate.to(f"/words/{lang}?search={search_input.value}")

    render_navigation(f"Words {lang.upper()}")
    words_model = DICTIONARIES[lang]

    with ui.row():
        search_input = ui.input(label="Search", value=search, autocomplete=await words_model.get_all_words()).on(
            "keydown.enter", go_action
        )
        ui.button(icon="search", on_click=go_action)
        ui.button(icon="close", on_click=lambda e: ui.navigate.to(f"/words/{lang}"))

    if not search:
        query = words_model.find_all()
    else:
        query = words_model.find({"_id": search})

    with ui.grid(columns=1 + (len(DICTIONARIES) - 1)):
        ui.label(lang.upper())
        for to_lang in DICTIONARIES:
            if to_lang != lang:
                ui.label(to_lang.upper())
        for word in await query.limit(100).to_list():
            word_id = word.id
            ui.label(word.id).classes("font-bold")
            for to_lang in DICTIONARIES:
                if to_lang != lang:
                    with ui.row():
                        editable = ui.textarea(value="\n".join(word.translations.get(to_lang, []))).props("bordered")
                        save_action = save_action_gen(lang, to_lang, word_id, editable)
                        ui.button(icon="save", on_click=save_action)
                        editable.on("keydown.enter.ctrl", save_action)
                        editable.on("keydown.enter.meta", save_action)
                        editable.on("keydown.enter.alt", save_action)
