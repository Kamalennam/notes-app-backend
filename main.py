from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import datetime

app = Flask(__name__)
CORS(app)


client = MongoClient("mongodb://localhost:27017/")
db = client["notes_app"]
notes_collection = db["notes"]


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
    new_note = {
        "_id": note_id,
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "createdAt": datetime.datetime.now()
    }
    notes_collection.insert_one(new_note)
    return jsonify({"message": "Note added", "_id": note_id}), 201


@app.route('/api/notes', methods=['GET'])
def get_notes():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    skip = (page - 1) * limit

    notes = list(notes_collection.find().skip(skip).limit(limit))
    for note in notes:
        note["_id"] = str(note["_id"])  

    total_notes = notes_collection.count_documents({})
    total_pages = (total_notes + limit - 1) // limit  

    return jsonify({
        "notes": notes,
        "total_pages": total_pages,
        "current_page": page
    })


@app.route('/api/notes/<int:id>', methods=['GET'])
def get_note_by_id(id):
    note = notes_collection.find_one({"_id": id})
    if note:
        note["_id"] = str(note["_id"])
        return jsonify(note)
    else:
        return jsonify({"error": "Note not found"}), 404


@app.route('/api/notes/<int:id>', methods=['PUT'])
def update_note(id):
    data = request.json
    updated_note = {
        "title": data.get("title", ""),
        "content": data.get("content", "")
    }
    result = notes_collection.update_one({"_id": id}, {"$set": updated_note})
    if result.modified_count > 0:
        return jsonify({"message": "Note updated successfully"})
    else:
        return jsonify({"error": "Note not found"}), 404


@app.route('/api/notes/<int:id>', methods=['DELETE'])
def delete_note(id):
    result = notes_collection.delete_one({"_id": id})
    if result.deleted_count > 0:
        return jsonify({"message": "Note deleted successfully"})
    else:
        return jsonify({"error": "Note not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
