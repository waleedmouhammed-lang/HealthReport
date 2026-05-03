from pathlib import Path


def test_launchd_schedules_sync_only_at_11am():
    script = Path("scripts/install_launchd.sh").read_text()

    assert "<integer>11</integer>" in script
    assert "scripts/sync_only.sh" in script
    assert "sync_then_dashboard.sh" not in script
    assert "run_dashboard.sh" not in script
