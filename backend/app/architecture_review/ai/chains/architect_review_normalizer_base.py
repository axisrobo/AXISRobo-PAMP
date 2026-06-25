from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable


class ReviewResultNormalizer(ABC):
    @abstractmethod
    def normalize_result(
        self,
        raw_result: object,
        *,
        normalize_score: Callable[[object], float],
        build_normalized_result: Callable[[dict, dict | None, list[dict]], dict],
    ) -> dict:
        raise NotImplementedError
