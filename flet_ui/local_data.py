from typing import Any

from flet_core.client_storage import ClientStorage

CLIENT_TOKEN_ATTR = "client_token"


class LocalData:
    def __init__(self, storage: ClientStorage, prefix: str):
        self.prefix = prefix
        self.storage = storage

    def get_attr(self, attr: str) -> Any:
        return self.storage.get(f"{self.prefix}.{attr}")

    def set_attr(self, attr: str, val: Any):
        try:
            self.storage.set(f"{self.prefix}.{attr}", val)
        except TimeoutError:
            pass

    def clear_attr(self, attr: str):
        try:
            self.storage.remove(f"{self.prefix}.{attr}")
        except TimeoutError:
            pass

    @property
    def client_token(self):
        return self.get_attr(CLIENT_TOKEN_ATTR)

    @client_token.setter
    def client_token(self, value):
        self.set_attr(CLIENT_TOKEN_ATTR, value)

    @client_token.deleter
    def client_token(self):
        self.clear_attr(CLIENT_TOKEN_ATTR)
