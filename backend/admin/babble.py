from nicegui import ui

from backend.admin.common import render_navigation


@ui.page("/babble")
def babble_page():
    render_navigation("Babble")
