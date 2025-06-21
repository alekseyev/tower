from nicegui import ui


def render_navigation(header: str):
    from backend.admin.babble import babble_page
    from backend.admin.words import words_page

    with ui.header(elevated=True):
        ui.label(header)

    with ui.left_drawer():
        ui.link("Words", words_page)
        ui.link("Babble", babble_page)
