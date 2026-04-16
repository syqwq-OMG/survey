import urllib.request
import urllib.error
import urllib.parse
import json

def post(url, data, headers={}):
    if isinstance(data, dict):
        data_encoded = json.dumps(data).encode()
    else:
        data_encoded = data.encode()
    req = urllib.request.Request(url, data=data_encoded, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)

# Login
login_data = urllib.parse.urlencode({"username": "syqwq", "password": "123456"})
status, text = post("http://localhost:8000/api/auth/login", login_data, {"Content-Type": "application/x-www-form-urlencoded"})

if status != 200:
    print("Login failed:", status, text)
else:
    token = json.loads(text).get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Get surveys
    req = urllib.request.Request("http://localhost:8000/api/surveys", headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            surveys = json.loads(response.read().decode())
            print(f"User has {len(surveys)} surveys.")
            for s in surveys:
                print(f"Survey ID: {s.get('id')}, Title: {s.get('title')}")
                for q in s.get('questions', []):
                    print(f"  Q: {q.get('title')} - Bank ID: {q.get('question_bank_id')}")
    except Exception as e:
        print("Error getting surveys:", e)

    # Get questions
    req = urllib.request.Request("http://localhost:8000/api/questions", headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            questions = json.loads(response.read().decode())
            print(f"\nUser has {len(questions)} questions in bank.")
    except Exception as e:
        print("Error getting questions:", e)

    # Try creating a new survey
    new_survey = {
      "title": "Agent Test Survey",
      "is_anonymous": True,
      "questions": [
        {
          "q_id": "q_agent1",
          "type": "text",
          "title": "Agent Test Q",
          "is_required": True,
          "is_shared": True,
          "jump_logic": [],
          "options": [],
          "constraints": {}
        }
      ]
    }
    status, text = post("http://localhost:8000/api/surveys", new_survey, headers)
    print("\nCreate New Survey:", status, text)
    
    # Check bank again
    req = urllib.request.Request("http://localhost:8000/api/questions", headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            questions = json.loads(response.read().decode())
            print(f"\nAfter creation, User has {len(questions)} questions in bank.")
            for q in questions:
                print(f"  Bank Q: {q.get('title')} - ID: {q.get('id')}")
    except Exception as e:
        pass
