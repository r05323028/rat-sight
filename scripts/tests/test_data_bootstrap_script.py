from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "data_bootstrap.sh"
OVERLAY = REPO_ROOT / "infra" / "docker-compose.full-local.yml"
DISTRICTS_SHA256 = "77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9"
STORMWATER_SHA256 = "5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4"


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_unknown_profile_is_rejected() -> None:
    result = _run(env={"PROFILE": "shared", "PATH": "/usr/bin:/bin"})
    assert result.returncode == 2
    assert "unsupported profile: shared" in result.stderr


def test_unknown_argument_is_rejected() -> None:
    result = _run("--truncate", env={"PATH": "/usr/bin:/bin"})
    assert result.returncode == 2
    assert "unknown argument: --truncate" in result.stderr


def test_purge_requires_down() -> None:
    result = _run("--purge", env={"PATH": "/usr/bin:/bin"})
    assert result.returncode == 2
    assert "--purge is valid only with down" in result.stderr


def test_inspect_only_never_downloads_missing_sources(tmp_path: Path) -> None:
    result = _run(
        "--inspect-only",
        env={
            "PATH": "/usr/bin:/bin",
            "RATSIGHT_FULL_LOCAL_DATA_DIR": str(tmp_path / "absent"),
        },
    )
    assert result.returncode == 2
    assert "inspect-only mode never downloads" in result.stderr
    assert not (tmp_path / "absent").exists()


def test_profile_owns_its_project_and_volume() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    overlay = OVERLAY.read_text(encoding="utf-8")

    assert 'PROJECT="ratsight-full-local"' in script
    assert "ratsight-full-local-postgres-data:/var/lib/postgresql/data" in overlay
    # No implicit destructive teardown on the default path.
    assert "down -v" not in script.split("do_down()")[0]


def _shim(directory: Path, name: str, body: str) -> None:
    path = directory / name
    path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
    path.chmod(0o755)


def _post_first_write_env(tmp_path: Path) -> dict[str, str]:
    """Stub the tools around the imports so the run reaches the post-write branch.

    The real hash and Docker gates stop the run earlier and are covered elsewhere;
    here the interest is what the script says after the first importer committed.
    """
    shims = tmp_path / "shims"
    shims.mkdir()
    data = tmp_path / "data"
    data.mkdir()
    (data / "districts-121199-20220915.zip").write_bytes(b"stub")
    (data / "stormwater-5240223d-2026-02-23.xml").write_bytes(b"stub")

    _shim(
        shims,
        "sha256sum",
        f"""case "$1" in
  *districts-121199-20220915.zip) echo "{DISTRICTS_SHA256}  $1" ;;
  *) echo "{STORMWATER_SHA256}  $1" ;;
esac
""",
    )
    _shim(shims, "lsof", "exit 1\n")
    _shim(
        shims,
        "docker",
        """[[ "$1" == "info" ]] && exit 0
case "$*" in
  *"ps -q postgres"*) exit 0 ;;
  *"up -d --wait postgres"*) exit 0 ;;
  *"down"*) exit 0 ;;
  *administrative_districts*) echo 12 ;;
  *stormwater_pipelines*) echo 19747 ;;
  *) echo 0 ;;
esac
""",
    )
    _shim(
        shims,
        "uv",
        """case "$*" in
  *rodent_reports*) exit 0 ;;
  *stormwater_pipelines*--inspect-only*)
    echo '{"record_count": 19747, "z_handling": "dropped",' \
      '"provenance": {"target_crs": "EPSG:4326"}}' ;;
  *administrative_districts*--inspect-only*)
    echo '{"district_count": 12, "provenance": {"target_crs": "EPSG:4326"}}' ;;
  *alembic*) exit 0 ;;
  *stormwater_pipelines*)
    echo "error: stormwater network already imported" >&2; exit 3 ;;
  *administrative_districts*)
    echo '{"inserted": 12, "updated": 0, "unchanged": 0}' ;;
  *) exit 0 ;;
esac
""",
    )
    return {
        **os.environ,
        "PATH": f"{shims}:{os.environ['PATH']}",
        "PROFILE": "full-local",
        "RATSIGHT_FULL_LOCAL_DATA_DIR": str(data),
    }


def test_stormwater_conflict_after_district_import_is_explicit(tmp_path: Path) -> None:
    result = _run(env=_post_first_write_env(tmp_path))

    assert result.returncode == 3
    assert "administrative boundaries were imported before this point" in result.stderr
    # No false atomicity claim once the first importer has committed.
    assert "nothing was imported, replaced, or deleted" not in result.stderr
    assert '"inserted": 12' in result.stdout
