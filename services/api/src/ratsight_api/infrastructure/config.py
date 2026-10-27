from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://ratsight:ratsight_dev_only@127.0.0.1:54329/ratsight"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:3002"
    log_level: str = "INFO"
    # Explicit endpoint identity for the single administrative reference layer.
    # Default is the documented Taipei dataset (Evidence ID
    # EVID-TPE-DISTRICT-BOUNDARIES-2026-10-15); override for another deployment.
    administrative_district_dataset_id: str = "121199"
    # Explicit endpoint identity for the single stormwater reference layer.
    # Default is the documented Candidate B dataset
    # (Evidence ID EVID-TPE-STORMWATER-NETWORK-2026-10-16).
    stormwater_dataset_id: str = "97b82d58-faba-4ee4-9488-dd5d04a79efd"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
