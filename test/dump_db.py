from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['survey_system']

questions = list(db.question_bank.find())
print(f"Total questions in DB: {len(questions)}")
for q in questions:
    print(f"ID: {q.get('_id')}, Creator: {q.get('creator_id')}, Shared: {q.get('is_shared')}, Title: {q.get('title')}")
