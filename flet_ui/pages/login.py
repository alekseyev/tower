import flet as ft
from loguru import logger


class LoginForm(ft.Column):
    def __init__(self):
        super().__init__()
        self.edit_email = ft.TextField(label="Email")
        self.edit_password = ft.TextField(label="Password", password=True, can_reveal_password=True)
        self.button_login = ft.FilledButton("Login", on_click=self.login)
        self.status = ft.Text("", style=ft.TextStyle(color=ft.colors.RED))

        self._token = None

        self.controls = [
            self.edit_email,
            self.edit_password,
            self.button_login,
            self.status,
        ]

    def did_mount(self):
        self.status.value = ""
        self.update()

    async def set_token(self):
        self.page.local_data.client_token = self._token

    async def login(self, e):
        logger.info("clicked login")
        result = await self.page.client.login(self.edit_email.value, self.edit_password.value)
        if result:
            logger.info("successful login")
            self.status.value = "Success, logging in..."
            self.update()
            self._token = result
            self.page.run_task(self.set_token)
            self.page.go("/")
        else:
            logger.info("incorrect login")
            self.status.value = "Incorrect login"
            self.update()


LOGIN_VIEW = ft.View("/login", [ft.AppBar(title=ft.Text("Login to Tower")), LoginForm()])
