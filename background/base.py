from abc import ABC, abstractmethod
from core.utils import get_logger


class BaseTask(ABC):
    """Abstract base class for all background tasks."""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique task name."""
        ...

    @property
    @abstractmethod
    def interval_seconds(self) -> int:
        """How often to run (seconds)."""
        ...

    @abstractmethod
    def run(self) -> None:
        """Synchronous entry point called by APScheduler."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} interval={self.interval_seconds}s>"
