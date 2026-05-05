from pathlib import Path


def test_launchd_schedules_sync_only_at_11am():
    script = Path("scripts/install_launchd.sh").read_text()

    assert "<integer>11</integer>" in script
    assert "scripts/sync_only.sh" in script
    assert "sync_then_dashboard.sh" not in script
    assert "run_dashboard.sh" not in script


def test_dashboard_launcher_cleans_up_streamlit_process():
    script = Path("scripts/run_dashboard.sh").read_text()

    assert "trap cleanup EXIT INT TERM HUP TSTP" in script
    assert "--server.headless true" in script
    assert "browser_has_connection" in script
    assert "IDLE_SHUTDOWN_SECONDS" in script
    assert "kill \"$STREAMLIT_PID\"" in script
