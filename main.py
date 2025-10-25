import atexit
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)


# Use MONGO_URI from environment to avoid committing credentials
MONGO_URI = os.getenv('MONGO_URI') or "mongodb+srv://codingprodevtech_db_user:CumT0hxShdZaolY6@cluster0.38rpb04.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client[os.getenv('MONGO_DB', 'notes')]
notes_collection = db[os.getenv('MONGO_COLLECTION', 'notes')]

# import check_and_send_reminders for manual triggering and tests

def get_next_id():
    last_note = notes_collection.find_one(sort=[("_id", -1)])  
    if last_note:
        return last_note["_id"] + 1 
    else:
        return 1  


@app.route('/api/notes', methods=['POST'])
def add_note():
    data = request.json
    note_id = get_next_id()

    schedule_date = data.get("schedule_date")
    if schedule_date:
        try:
            # Accept ISO strings with trailing Z (UTC) by converting to +00:00
            if isinstance(schedule_date, str) and schedule_date.endswith('Z'):
                schedule_date = schedule_date.replace('Z', '+00:00')
            schedule_date = datetime.datetime.fromisoformat(schedule_date)
            # Ensure stored datetimes are timezone-aware (UTC) where possible
            if schedule_date.tzinfo is None:
                # Treat naive datetimes as local and convert to UTC
                schedule_date = schedule_date.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo).astimezone(datetime.timezone.utc)
            else:
                schedule_date = schedule_date.astimezone(datetime.timezone.utc)
        except Exception:
            return jsonify({"error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS or ending with Z for UTC)."}), 400


    new_note = {
        "_id": note_id,
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "schedule_date": schedule_date,
    "createdAt": datetime.datetime.now(datetime.timezone.utc)
    }
    try:
        notes_collection.insert_one(new_note)
    except Exception as e:
        return jsonify({"error": "Database unavailable", "details": str(e)}), 503
    return jsonify({"message": "Note added", "_id": note_id}), 201


@app.route('/api/notes', methods=['GET'])
def get_notes():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    skip = (page - 1) * limit

    try:
        notes = list(notes_collection.find().skip(skip).limit(limit))
    except Exception as e:
        return jsonify({"error": "Database unavailable", "details": str(e)}), 503
    for note in notes:
        note["_id"] = str(note["_id"])  

        if "createdAt" in note and isinstance(note["createdAt"], datetime.datetime):
            note["createdAt"] = note["createdAt"].isoformat()
        if "schedule_date" in note and isinstance(note["schedule_date"], datetime.datetime):
            note["schedule_date"] = note["schedule_date"].isoformat()

    total_notes = notes_collection.count_documents({})
    total_pages = (total_notes + limit - 1) // limit  

    return jsonify({
        "notes": notes,
        "total_pages": total_pages,
        "current_page": page
    })


@app.route('/api/notes/<int:id>', methods=['GET'])
def get_note_by_id(id):
    try:
        note = notes_collection.find_one({"_id": id})
    except Exception as e:
        return jsonify({"error": "Database unavailable", "details": str(e)}), 503

    if note:
        note["_id"] = str(note["_id"])
        if "createdAt" in note and isinstance(note["createdAt"], datetime.datetime):
            note["createdAt"] = note["createdAt"].isoformat()
        if "schedule_date" in note and isinstance(note["schedule_date"], datetime.datetime):
            note["schedule_date"] = note["schedule_date"].isoformat()
        return jsonify(note)
    else:
        return jsonify({"error": "Note not found"}), 404


@app.route('/api/notes/<int:id>', methods=['PUT'])
def update_note(id):
    data = request.json
    updated_fields = {
        "title": data.get("title", ""),
        "content": data.get("content", "")
    }
    if "schedule_date" in data:
        schedule_date = data.get("schedule_date")
        if schedule_date:
            try:
                if isinstance(schedule_date, str) and schedule_date.endswith('Z'):
                    schedule_date = schedule_date.replace('Z', '+00:00')
                dt = datetime.datetime.fromisoformat(schedule_date)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo).astimezone(datetime.timezone.utc)
                else:
                    dt = dt.astimezone(datetime.timezone.utc)
                updated_fields["schedule_date"] = dt
            except Exception:
                return jsonify({"error": "Invalid date format for schedule_date. Use ISO format."}), 400
        else:
            updated_fields["schedule_date"] = None

    try:
        result = notes_collection.update_one({"_id": id}, {"$set": updated_fields})
    except Exception as e:
        return jsonify({"error": "Database unavailable", "details": str(e)}), 503

    if result.modified_count > 0:
        return jsonify({"message": "Note updated successfully"})
    else:
        return jsonify({"error": "Note not found"}), 404


@app.route('/api/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    try:
        result = notes_collection.delete_one({"_id": id})
    except Exception as e:
        return jsonify({"error": "Database unavailable", "details": str(e)}), 503

    if result.deleted_count > 0:
        return jsonify({"message": "Note deleted successfully"})
    else:
        return jsonify({"error": "Note not found"}), 404



@app.route('/api/test-send', methods=['POST'])
def test_send():
    """Protected endpoint for one-off test sends.

    POST JSON: {"to": "email@example.com", "subject": "sub", "content": "body"}
    Must set TEST_SECRET in .env and include header X-TEST-SECRET with the same value.
    """
    secret = os.getenv('TEST_SECRET')
    header = request.headers.get('X-TEST-SECRET')
    if not secret or header != secret:
        return jsonify({"error": "Unauthorized or TEST_SECRET not set"}), 401

    data = request.json or {}
    to = data.get('to')
    subject = data.get('subject', 'Manual Test Reminder')
    content = data.get('content', 'This is a test reminder')

  


if __name__ == '__main__':
    # Start the scheduler only in the main process (prevents double-start with Flask reloader)

    app.run(debug=True)
