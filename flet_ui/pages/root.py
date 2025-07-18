import flet as ft
from loguru import logger

from flet_ui.client import NotAuthenticated
from flet_ui.pages.const import COURSE, LANG


def perc(a, b):
    return f"{a} / {b} [{a / b * 100:.1f}%]"


class RootView(ft.Column):
    def __init__(self):
        super().__init__(expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.status = ft.Markdown("Loading...")
        self.button_practice = ft.FilledButton("Practice", on_click=self.go_exercise)
        self.button_new_words = ft.FilledButton("New words", on_click=self.go_new_words)
        self.button_logout = ft.FilledButton("Logout", on_click=self.logout)

        self.controls = [
            self.status,
            self.button_practice,
            self.button_new_words,
            ft.Container(expand=True, content=ft.Text(" ")),
            ft.Divider(),
            self.button_logout,
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
        user_stats = await self.page.client.stats(user_id)
        stats = user_stats[LANG][COURSE]
        self.status.value = (
            f"Words encountered from course {perc(stats['encountered'], stats['total_count'])}  \n"
            f"New words {perc(stats['new'], stats['encountered'])}  \n"
            f"Bad words {perc(stats['bad'], stats['encountered'])}  \n"
            f"Understanding rate {stats['understanding_rate']}%  \n"
            f"Total exercises: {stats['exercises']}  \n"
        )
        self.update()

    def logout(self, *args, **kwargs):
        self.page.client.set_access_token()
        self.page.go("/login")

    def go_exercise(self, *args, **kwargs):
        self.page.go("/practice")

    def go_new_words(self, *args, **kwargs):
        self.page.go("/new_words")


ROOT_VIEW_INSTANCE = RootView()
ROOT_VIEW = ft.View("/", [ft.AppBar(title=ft.Text("Welcome, learner!")), ROOT_VIEW_INSTANCE])
