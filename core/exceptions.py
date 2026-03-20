class AutonomousLearningError(Exception):
    """Base exception for the system."""
    pass

class ConfigurationError(AutonomousLearningError):
    """Configuration related error."""
    pass

class DatabaseError(AutonomousLearningError):
    """Database operation error."""
    pass

class LLMError(AutonomousLearningError):
    """LLM invocation error."""
    pass

class VectorStoreError(AutonomousLearningError):
    """Vector store operation error."""
    pass
