import flet as ft
from loguru import logger

from flet_ui.client import NotAuthenticated


class RootView(ft.Column):
    def __init__(self):
        super().__init__()

        self.status = ft.Text("Loading...", style=ft.TextStyle())
        self.button_logout = ft.FilledButton("Logout", on_click=self.logout)

        self.controls = [self.status, self.button_logout]

    def did_mount(self):
        logger.info("did mount")
        self.page.run_task(self.load_data)

    async def load_data(self):
        try:
            data = await self.page.client.me()
        except NotAuthenticated:
            self.page.go("/login")
            return
        self.status.value = f"Hello, user! {data=}"
        self.update()

    def logout(self, _):
        self.page.client.set_access_token()
        self.page.go("/login")


ROOT_VIEW = ft.View("/", [ft.AppBar(title=ft.Text("Welcome, learner!")), RootView()])
