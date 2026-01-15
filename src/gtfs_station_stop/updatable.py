"""Updatable"""

from abc import abstractmethod


class Updatable:
    """Updatable Base class."""

    _last_updated: float | None = None

    @property
    def last_updated(self) -> None:
        """Time Last Updated."""
        return self._last_updated

    @abstractmethod
    def begin_update(self, timestamp: float | None = None) -> None:
        """Prepare for update by Feed Subject"""
        raise NotImplementedError
