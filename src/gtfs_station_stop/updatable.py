"""Updatable"""

from abc import abstractmethod
from typing import Any


class Updatable:
    """Updatable Base class."""

    _last_updated: float | None = None
    id: Any

    @property
    def last_updated(self) -> float | None:
        """Time Last Updated."""
        return self._last_updated

    @abstractmethod
    def begin_update(self, timestamp: float | None = None) -> None:
        """Prepare for update by Feed Subject"""
        raise NotImplementedError
