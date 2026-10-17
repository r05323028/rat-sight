from __future__ import annotations

from scripts import seed_rodent_report_smoke


def test_smoke_empty_allows_freshly_empty_database(monkeypatch) -> None:
    monkeypatch.setenv("SMOKE_EMPTY", "1")
    monkeypatch.setattr(seed_rodent_report_smoke, "fixture_row_count", lambda: 0)
    assert seed_rodent_report_smoke.main() == 0


def test_smoke_empty_rejects_non_empty_database(monkeypatch, capsys) -> None:
    monkeypatch.setenv("SMOKE_EMPTY", "1")
    monkeypatch.setattr(seed_rodent_report_smoke, "fixture_row_count", lambda: 5)
    assert seed_rodent_report_smoke.main() == seed_rodent_report_smoke.EXIT_NOT_EMPTY
    assert "freshly recreated disposable database" in capsys.readouterr().err
