import os
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class UserConfig:
    pinecone_api_key: str = ""
    index_name: str = ""
    environment: str = ""
    namespace: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserConfig":
        return cls(
            pinecone_api_key=data.get("pinecone_api_key", ""),
            index_name=data.get("index_name", ""),
            environment=data.get("environment", ""),
            namespace=data.get("namespace"),
        )


class ConfigManager:
    def __init__(self, config: Optional[UserConfig] = None):
        self.config = config or UserConfig()

    @classmethod
    def from_env(cls) -> "ConfigManager":
        config = UserConfig(
            pinecone_api_key=os.environ.get("PINECONE_API_KEY", ""),
            index_name=os.environ.get("PINECONE_INDEX_NAME", ""),
            environment=os.environ.get("PINECONE_ENVIRONMENT", ""),
            namespace=os.environ.get("PINECONE_NAMESPACE") or None,
        )
        return cls(config)

    @classmethod
    def from_yaml(cls, path: str) -> "ConfigManager":
        if yaml is None:
            raise ImportError("PyYAML is required to load YAML config files")
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        return cls(UserConfig.from_dict(data))

    def to_dict(self) -> dict:
        return self.config.to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> "ConfigManager":
        return cls(UserConfig.from_dict(data))


def validate_config(config: UserConfig) -> list[str]:
    errors = []
    if not config.pinecone_api_key:
        errors.append("pinecone_api_key is required")
    elif not re.match(r"^[a-zA-Z0-9_-]+$", config.pinecone_api_key):
        errors.append("pinecone_api_key contains invalid characters")
    if not config.index_name:
        errors.append("index_name is required")
    if not config.environment:
        errors.append("environment is required")
    return errors
