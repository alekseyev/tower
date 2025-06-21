from nicegui import ui

from backend.admin.common import render_navigation
from backend.dictionary.models import SpanishDictionary


def save_action_gen(word_id, editable):
    async def save_action(e):
        nonlocal word_id
        word = await SpanishDictionary.get(word_id)
        word.translations["en"] = [val for val in editable.value.split("\n") if val]
        await word.save()
        ui.notify(f"Saved: {word}")

    return save_action


@ui.page("/words")
async def words_page(search: str = ""):
    def go_action(e):
        return ui.navigate.to(f"/words?search={search_input.value}")

    render_navigation("Words")

    with ui.row():
        search_input = ui.input(label="Search", value=search).on("keydown.enter", go_action)
        ui.button(icon="search", on_click=go_action)
        ui.button(icon="close", on_click=lambda e: ui.navigate.to("/words"))

    if not search:
        query = SpanishDictionary.all()
    else:
        query = SpanishDictionary.find({"_id": search})

    for word in await query.limit(100).to_list():
        word_id = word.id
        with ui.row():
            ui.label(word.id).classes("font-bold")
            editable = ui.textarea(value="\n".join(word.translations["en"])).props("bordered")
            ui.button(icon="save", on_click=save_action_gen(word_id, editable))
