from nicegui import ui

from backend.settings import settings


def render_navigation(header: str):
    from backend.admin.babble import babble_page
    from backend.admin.words import words_page  # noqa

    with ui.header(elevated=True):
        ui.label(header)

    with ui.left_drawer():
        for lang in settings.LANGUAGES:
            ui.link(f"Words {lang.upper()}", f"/words/{lang}")
        ui.link("Babble", babble_page)
