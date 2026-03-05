from flask import Flask, render_template, jsonify, request
import sqlite3
import random
import json

app = Flask(__name__)
DB_PATH = "selftest.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def load_specialties():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code, name FROM specialty ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [{"code": r[0], "name": r[1]} for r in rows]

def load_questions(specialty_code, limit=25):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, html, answers FROM question WHERE speciality_id = ? ORDER BY RANDOM() LIMIT ?",
        (specialty_code, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    questions = []
    for r in rows:
        try:
            answers = json.loads(r[2]) if r[2] else []
        except:
            answers = []
        questions.append({
            "id": r[0],
            "html": r[1],
            "answers": answers
        })
    return questions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/specialties')
def api_specialties():
    return jsonify(load_specialties())

@app.route('/api/questions')
def api_questions():
    specialty = request.args.get('specialty', '31.08.63')
    limit = int(request.args.get('limit', 25))
    return jsonify(load_questions(specialty, limit))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8501)
