from __future__ import annotations

from api_layer import WorldQuantClient
from pipeline.models import AlphaCandidate, SimulationMetrics


class Simulator:
    def __init__(self, client: WorldQuantClient) -> None:
        self.client = client

    def run(self, candidate: AlphaCandidate) -> SimulationMetrics:
        return self.client.simulate_expression(candidate)

