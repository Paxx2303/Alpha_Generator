from __future__ import annotations

from dataclasses import dataclass
import logging

import requests
from requests.auth import HTTPBasicAuth


LOGGER = logging.getLogger(__name__)


@dataclass
class WQSessionManager:
    username: str
    password: str
    base_url: str
    dry_run: bool = True

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self._authenticated = False

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    def login(self) -> bool:
        if self.dry_run:
            LOGGER.info("Dry-run mode enabled; skipping WorldQuant login.")
            self._authenticated = True
            return True

        if not self.username or not self.password:
            raise ValueError("Missing WorldQuant credentials.")

        login_url = f"{self.base_url.rstrip('/')}/authentication"
        response = self.session.post(
            login_url,
            auth=HTTPBasicAuth(self.username, self.password),
            timeout=30,
        )
        if response.ok:
            payload = response.json()
            if "inquiry" in payload:
                raise RuntimeError(
                    "WorldQuant requested biometric authentication. "
                    f"Complete it in the browser: {response.url}/persona?inquiry={payload['inquiry']}"
                )
            self._authenticated = True
            LOGGER.info("Authenticated with WorldQuant API.")
            return True

        LOGGER.error("WorldQuant login failed with status %s", response.status_code)
        response.raise_for_status()
        return False

    def ensure_session(self) -> requests.Session:
        if not self._authenticated:
            self.login()
        return self.session
