import flet as ft
from loguru import logger

from flet_ui.client import NotAuthenticated


class RootView(ft.Column):
    def __init__(self):
        super().__init__()

        self.status = ft.Text("Loading...", style=ft.TextStyle(color=ft.colors.RED))

        self.controls = [
            self.status,
        ]

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


ROOT_VIEW = ft.View("/", [ft.AppBar(title=ft.Text("Welcome, learner!")), RootView()])
