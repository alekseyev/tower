import flet as ft

from flet_ui.client import LearnClient
from flet_ui.local_data import LocalData
from flet_ui.pages.login import LOGIN_VIEW
from flet_ui.pages.root import ROOT_VIEW
from flet_ui.settings import settings

page_global = None

ROUTES = {
    "/login": LOGIN_VIEW,
    "/": ROOT_VIEW,
}

def main(page: ft.Page):
    global page_global
    page_global = page
    page.title = "Learn App"
    page.local_data = LocalData(page.client_storage, settings.LOCAL_STORAGE_PREFIX)
    page.client = LearnClient(settings.BACKEND_URL)

    if token := page.local_data.client_token:
        page.client.set_access_token(token)

    def route_change(route):
        page.views.clear()
        if not page.local_data.client_token or page.route == "/login":
            page.views.append(LOGIN_VIEW)
        else:
            page.views.append(
                ROOT_VIEW
            )

            if page.route != "/":
                page.views.append(
                    ROUTES[page.route]
                )
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


ft.app(main)
