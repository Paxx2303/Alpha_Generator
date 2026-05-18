from __future__ import annotations

from api_layer import WorldQuantClient


class WQScraper:
    def __init__(self, client: WorldQuantClient) -> None:
        self.client = client

    def leaderboard_snapshot(self) -> list[dict]:
        return self.client.list_leaderboard()

