from os import getenv

import requests


class Finapp:
    def __init__(self):
        self.base_url = getenv("FINAPP_URL", "http://localhost:3000")
        self._email = getenv("FINAPP_EMAIL", "")
        self._password = getenv("FINAPP_PASSWORD", "")
        self.token: str | None = None

    def login(self) -> str:
        resp = requests.post(
            f"{self.base_url}/api/sign_in",
            json={"email": self._email, "password": self._password},
            timeout=30,
        )
        if not resp.ok:
            raise ValueError(resp.json())
        self.token = resp.json()["token"]
        return self.token
