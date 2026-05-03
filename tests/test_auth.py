from healthreport.auth import get_valid_token
from healthreport.io_utils import atomic_write_json


class FakeResponse:
    status_code = 200
    text = ""

    def json(self):
        return {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_at": 9999999999,
        }


class FakeSession:
    def __init__(self):
        self.posts = []

    def post(self, url, data, timeout):
        self.posts.append((url, data, timeout))
        return FakeResponse()


def test_get_valid_token_refreshes_expired_token(tmp_path, monkeypatch):
    atomic_write_json(
        tmp_path / "tokens.json",
        {
            "access_token": "old-access",
            "refresh_token": "old-refresh",
            "expires_at": 1,
        },
    )
    monkeypatch.setenv("STRAVA_CLIENT_ID", "client-id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "client-secret")
    session = FakeSession()

    token = get_valid_token(data_dir=str(tmp_path), session=session, now=1000)

    assert token == "new-access"
    assert len(session.posts) == 1
    assert session.posts[0][1]["refresh_token"] == "old-refresh"
