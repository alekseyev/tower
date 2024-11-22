import flet as ft
from loguru import logger

from flet_ui.client import NotAuthenticated
from flet_ui.pages.const import LANG


class PracticeView(ft.Column):
    def __init__(self):
        super().__init__()
        self.status = ft.Markdown("Loading...")
        self.button_home = ft.FilledButton("Return home", on_click=self.go_home)

        self.controls = [
            self.status,
            ft.Container(expand=True, content=ft.Text(" ")),
            ft.Divider(),
            self.button_home,
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
        user_id = data["id"]
        self.page.state.user_id = user_id
        exercises = await self.page.client.get_exercises(user_id, LANG)
        self.status.value = f"Next exercise: {exercises[0]}"
        self.update()

    def go_home(self, *args, **kwargs):
        self.page.go("/")


PRACTICE_VIEW = ft.View("/practice", [ft.AppBar(title=ft.Text("Exercise")), PracticeView()])
