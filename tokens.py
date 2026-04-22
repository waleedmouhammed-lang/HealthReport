import requests, json

r = requests.post('https://www.strava.com/oauth/token', data={
    'client_id':     '227797',
    'client_secret': '9e663375d49d7218c17fc42a8c66305c9f22620b',
    'code':          'aba4dd10873359d2b48af1ba8e41a2e4baedc81b',
    'grant_type':    'authorization_code'
})

print(json.dumps(r.json(), indent=2))
