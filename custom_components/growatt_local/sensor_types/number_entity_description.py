from dataclasses import dataclass
from homeassistant.components.number import NumberEntityDescription

@dataclass
class GrowattNumberRequiredKeysMixin:
    key: str
    register: int
    scale: float
    writeable: bool

@dataclass
class GrowattNumberEntityDescription(
    NumberEntityDescription, GrowattNumberRequiredKeysMixin
):
    """Custom NumberEntityDescription for Growatt."""
