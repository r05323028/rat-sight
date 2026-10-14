from ratsight_api.infrastructure.database.connection import postgis_status


def system_status() -> dict[str, object]:
    available, version = postgis_status()
    return {
        "status": "ok",
        "service": "ratsight-api",
        "version": "0.1.0",
        "database": {
            "status": "available" if available else "unavailable",
            "postgis_version": version,
        },
    }
