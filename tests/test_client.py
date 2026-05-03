from healthreport import client


class FakeResponse:
    def __init__(self, status_code, data=None, text="", headers=None):
        self.status_code = status_code
        self._data = data
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.gets = []

    def get(self, url, headers, params, timeout):
        self.gets.append(dict(params))
        return self.responses.pop(0)


def test_fetch_all_activities_paginates(monkeypatch):
    monkeypatch.setattr(client, "get_valid_token", lambda data_dir=None, session=None: "token")
    session = FakeSession(
        [
            FakeResponse(200, [{"id": 1}]),
            FakeResponse(200, [{"id": 2}]),
            FakeResponse(200, []),
        ]
    )

    activities = client.fetch_all_activities(session=session, sleep_func=lambda seconds: None)

    assert activities == [{"id": 1}, {"id": 2}]
    assert [request["page"] for request in session.gets] == [1, 2, 3]


def test_fetch_all_activities_retries_rate_limit(monkeypatch):
    monkeypatch.setattr(client, "get_valid_token", lambda data_dir=None, session=None: "token")
    sleeps = []
    session = FakeSession(
        [
            FakeResponse(429, headers={"Retry-After": "1"}),
            FakeResponse(200, []),
        ]
    )

    activities = client.fetch_all_activities(session=session, sleep_func=sleeps.append)

    assert activities == []
    assert sleeps == [1.0]
