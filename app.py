from flask import Flask, render_template, Response, redirect, url_for, jsonify
import cv2
import numpy as np
import face_recognition
import csv
import os
from datetime import datetime, timedelta
import mysql.connector
import ast
import time
from config import DB_CONFIG

app = Flask(__name__)

# Connect to database
def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

# Load known faces from DB
known_face_encodings = []
known_face_ids = []
known_face_names = []

def load_known_faces():
    global known_face_encodings, known_face_ids, known_face_names
    known_face_encodings.clear()
    known_face_ids.clear()
    known_face_names.clear()

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, encoding FROM students")
    for student_id, name, encoding_str in cursor.fetchall():
        try:
            encoding = np.array(ast.literal_eval(encoding_str))
            known_face_encodings.append(encoding)
            known_face_ids.append(student_id)
            known_face_names.append(name)
        except Exception as e:
            print(f"[ERROR] Failed to load encoding for {name}: {e}")
    conn.close()

load_known_faces()

recent_attendance = {}
redirect_flag = {"matched": False}
matched_student_id = None


def mark_attendance(student_id):
    now = datetime.now()
    last_marked = recent_attendance.get(student_id)

    if not last_marked or (now - last_marked) > timedelta(seconds=30):
        conn = connect_db()
        cursor = conn.cursor()

        # Fetch student name
        cursor.execute("SELECT name FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        student_name = student[0] if student else "Unknown"

        # Insert into database
        cursor.execute("INSERT INTO attendance (student_id, timestamp) VALUES (%s, %s)", (student_id, now))
        conn.commit()
        conn.close()

        # Save to CSV
        csv_filename = "attendance.csv"
        file_exists = os.path.isfile(csv_filename)

        with open(csv_filename, mode='a', newline='') as csvfile:
            fieldnames = ['ID', 'Name', 'Date', 'Time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'ID': student_id,
                'Name': student_name,
                'Date': now.strftime("%Y-%m-%d"),
                'Time': now.strftime("%H:%M:%S")
            })

        recent_attendance[student_id] = now
        return True

    return False

def gen_frames():
    global matched_student_id
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("[ERROR] Camera not available.")
        return

    while True:
        success, frame = camera.read()
        if not success:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small)
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches and matches[best_match_index]:
                student_id = known_face_ids[best_match_index]
                student_name = known_face_names[best_match_index]

                if mark_attendance(student_id):
                    print(f"[INFO] Attendance marked for {student_name}")
                    redirect_flag["matched"] = True
                    matched_student_id = student_id

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    camera.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/dashboard/<int:student_id>')
def dashboard(student_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()

    cursor.execute("SELECT timestamp FROM attendance WHERE student_id = %s ORDER BY timestamp DESC LIMIT 1", (student_id,))
    last_attendance = cursor.fetchone()

    conn.close()

    return render_template('dashboard.html',
                           student_id=student_id,
                           name=student[0] if student else "Unknown",
                           last_attendance=last_attendance[0] if last_attendance else "No records")

@app.route('/check_redirect')
def check_redirect():
    if redirect_flag["matched"]:
        student_id = matched_student_id
        # Reset flag for next detection
        redirect_flag["matched"] = False
        return jsonify({"redirect": True, "url": url_for('dashboard', student_id=student_id)})
    return jsonify({"redirect": False})

if __name__ == '__main__':
    app.run(debug=True)
