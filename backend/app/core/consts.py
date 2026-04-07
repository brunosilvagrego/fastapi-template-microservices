from enum import StrEnum

ENTITY_CREATION_ERROR = "Error while creating %s with schema: %s. Exception: %s"


class Environment(StrEnum):
    """Enum for supported environments."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
