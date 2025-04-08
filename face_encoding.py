import os
import cv2
import face_recognition
import mysql.connector
import numpy as np
from config import DB_CONFIG

def store_face_encodings():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    known_faces_path = "known_faces"
    if not os.path.exists(known_faces_path):
        print(f"[ERROR] Folder '{known_faces_path}' not found!")
        return

    for filename in os.listdir(known_faces_path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join(known_faces_path, filename)
            print(f"[INFO] Processing: {filename}")

            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)

            if encodings:
                encoding_str = str(encodings[0].tolist())
                name = os.path.splitext(filename)[0]

                try:
                    cursor.execute("INSERT INTO students (name, encoding) VALUES (%s, %s)", (name, encoding_str))
                    print(f"[SUCCESS] Stored encoding for: {name}")
                except Exception as e:
                    print(f"[ERROR] Failed to insert {name}: {e}")
            else:
                print(f"[WARNING] No face found in: {filename}")

    conn.commit()
    cursor.close()
    conn.close()
    print("[DONE] Face encodings stored successfully.")

if __name__ == "__main__":
    store_face_encodings()
