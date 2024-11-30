import httpx

STATUS_LOGIN_OK = 201
STATUS_OK = 200


class NotAuthenticated(Exception):
    pass


class LearnClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.auth_headers = {}

    async def request(
        self, method: str, route: str, params: dict | None = None, raise_for_auth: bool = True
    ) -> tuple[int, dict]:
        if raise_for_auth and not self.auth_headers:
            raise NotAuthenticated()
        async with httpx.AsyncClient() as client:
            url = self.base_url + route
            kwargs = {}
            if method == "GET":
                kwargs["params"] = params or {}
            else:
                kwargs["json"] = params or {}
            if self.auth_headers:
                kwargs["headers"] = self.auth_headers
            response = await client.request(method, url, **kwargs)

            if raise_for_auth and response.status_code == 401:
                raise NotAuthenticated()

            return response.status_code, response.json()

    async def login(self, email: str, password: str) -> str | None:
        self.set_access_token()
        code, data = await self.request("POST", "/login", {"email": email, "password": password}, raise_for_auth=False)
        if code == STATUS_LOGIN_OK:
            token = data["token"]
            self.set_access_token(token)
            return token

    def set_access_token(self, token: str | None = None):
        if token:
            self.auth_headers = {"Authorization": f"Bearer {token}"}
        else:
            self.auth_headers = {}

    async def me(self) -> dict:
        code, data = await self.request("GET", "/me")
        return data

    async def stats(self, user_id: str) -> dict:
        code, data = await self.request("GET", f"/user/{user_id}/stats")
        return data

    async def get_exercises(self, user_id: str, lang: str) -> list:
        code, data = await self.request("GET", f"/user/{user_id}/exercises", params={"lang": lang})
        return data

    async def save_exercise_result(self, user_id: str, lang: str, results: dict[str, bool]):
        await self.request("POST", "/exercise/result", {"user_id": user_id, "lang": lang, "results": results})
