from dataclasses import dataclass
from datetime import datetime


@dataclass(order=True)
class Alert:
    """Class for keeping arrival data."""

    active_period_start: datetime
    header_text: dict[str, str]  # key is language
    description_text: dict[str, str]  # key is language
