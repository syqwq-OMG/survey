import urllib.request
import urllib.error
import json

survey = {
  "title": "Test Survey",
  "is_anonymous": True,
  "questions": [
    {
      "q_id": "q_123",
      "type": "single",
      "title": "Q1",
      "is_required": True,
      "options": ["O1"],
      "constraints": {},
      "jump_logic": []
    }
  ]
}

def post(url, data, headers={}):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

_, txt = post("http://localhost:8000/api/auth/register", {"username": "testuser_sx2", "password": "password"})
print("Register:", txt)

from urllib.parse import urlencode
# login uses form data
req = urllib.request.Request("http://localhost:8000/api/auth/login", data=urlencode({"username": "testuser_sx2", "password": "password"}).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
with urllib.request.urlopen(req) as response:
    login_resp = json.loads(response.read().decode())
token = login_resp.get("access_token")

status, text = post("http://localhost:8000/api/surveys", survey, headers={"Authorization": f"Bearer {token}"})
print("Create Survey:", status, text)
