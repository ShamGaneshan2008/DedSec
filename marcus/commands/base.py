from abc import ABC, abstractmethod


class BaseCommand(ABC):
    """
    All Marcus commands inherit from this.
    Enforces a consistent interface so router.py
    can call any command the same way.
    """

    # Human-readable name shown in logs
    name: str = "unnamed_command"

    # Keywords that trigger this command (used by router)
    triggers: list[str] = []

    @abstractmethod
    def execute(self, command: str) -> str:
        """
        Run the command.

        Args:
            command: The raw user input string.

        Returns:
            A string response Marcus will speak aloud.
        """
        pass

    def matches(self, command: str) -> bool:
        """
        Check if any trigger keyword is in the command.
        Override this for more complex matching logic.
        """
        command = command.lower()
        return any(trigger in command for trigger in self.triggers)

    def __repr__(self):
        return f"<Command: {self.name} | triggers={self.triggers}>"