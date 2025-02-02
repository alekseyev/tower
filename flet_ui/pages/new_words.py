import flet as ft
from loguru import logger

from flet_ui.client import NotAuthenticated
from flet_ui.pages.const import COURSE, LANG
from flet_ui.pages.root import ROOT_VIEW_INSTANCE


class NewWordsView(ft.Column):
    def __init__(self):
        super().__init__(expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.message = ft.Markdown("Loading...")
        self.button_home = ft.FilledButton("Return home", on_click=self.go_home)

        self.controls = [
            self.message,
            ft.Container(expand=True, content=ft.Text(" ")),
            ft.Divider(),
            self.button_home,
        ]

    def init_controls(self):
        self.message.value = "Loading..."
        self.update()

    def did_mount(self):
        self.init_controls()
        self.page.run_task(self.load_data)

    async def load_data(self):
        try:
            data = await self.page.client.me()
        except NotAuthenticated:
            self.page.go("/login")
            return

        self.user_id = data["id"]
        logger.info("Loading new words...")
        self.new_words = await self.page.client.get_new_words(self.user_id, LANG, COURSE)
        logger.info(self.new_words)
        self.message.value = f"New words: {', '.join(self.new_words)}"
        self.update()

    def go_home(self, *args, **kwargs):
        self.page.go("/")
        self.page.run_task(ROOT_VIEW_INSTANCE.load_data)


NEW_WORDS_VIEW = ft.View("/new_words", [ft.AppBar(title=ft.Text("New words")), NewWordsView()])
