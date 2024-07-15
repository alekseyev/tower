import flet as ft


class LoginForm(ft.Column):
    def __init__(self):
        super().__init__()
        self.edit_email = ft.TextField(label="Email")
        self.edit_password = ft.TextField(label="Password", password=True, can_reveal_password=True)
        self.button_login = ft.FilledButton("Login", on_click=self.login)
        self.status = ft.Text("", style=ft.TextStyle(color=ft.colors.RED))

        self.controls = [
            self.edit_email,
            self.edit_password,
            self.button_login,
            self.status,
        ]

    async def login(self, e):
        result = await self.page.client.login(self.edit_email.value, self.edit_password.value)
        if result:
            self.page.local_data.client_token = result
            self.page.go("/")
        else:
            self.status.value = "Incorrect login"
            self.update()


LOGIN_VIEW = ft.View("/login", [ft.AppBar(title=ft.Text("Login to Tower")), LoginForm()])
