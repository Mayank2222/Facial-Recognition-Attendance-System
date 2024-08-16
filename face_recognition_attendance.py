import cv2
import numpy as np
import face_recognition
import sqlite3
from datetime import datetime
import csv

# Step 1: We will connect to SQLite Database
conn = sqlite3.connect('attendance.db')
c = conn.cursor()

# Step 2: Now we will create attendance table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS attendance
             (name TEXT, date TEXT, time TEXT)''')
conn.commit()


# Step 3:Here, we are going to Load and encode images of known faces
def load_and_encode_images(image_paths, names):
    encodings = []
    for img_path, name in zip(image_paths, names):
        img = face_recognition.load_image_file(img_path)
        img_encoding = face_recognition.face_encodings(img)[0]
        encodings.append((img_encoding, name))
    return encodings


# Here, I have added the names as well images of the people.
image_paths = ["person1.jpg", "person2.jpg", "person3.jpg"]
names = ["Donald Trump", "Narendra Modi", "Jack Ma"]

known_faces = load_and_encode_images(image_paths, names)

# Step 4: The following function is used to mark attendance in the database.
def mark_attendance(name):
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')

    # It will check if the person has already been marked for the day
    c.execute('SELECT * FROM attendance WHERE name=? AND date=?', (name, date))
    result = c.fetchall()
    if len(result) == 0:
        c.execute('INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)', (name, date, time))
        conn.commit()
        print(f"{name}'s attendance marked at {time} on {date}")


# Step 5: Program will capture video from webcam and recognize faces of the persons.
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = []

    try:
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    except Exception as e:
        print(f"Error in face encoding: {e}")

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces([enc[0] for enc in known_faces], face_encoding)
        face_distances = face_recognition.face_distance([enc[0] for enc in known_faces], face_encoding)
        best_match_index = np.argmin(face_distances)

        if matches[best_match_index]:
            name = known_faces[best_match_index][1]
            mark_attendance(name)

            for (top, right, bottom, left) in face_locations:
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Step 6: This will release webcam and close the window
cap.release()
cv2.destroyAllWindows()

# Step 7: This will show attendance records
def view_attendance():
    c.execute('SELECT * FROM attendance')
    rows = c.fetchall()
    for row in rows:
        print(row)


# Step 8: This block exports attendance records to a CSV file
def export_to_csv():
    c.execute('SELECT * FROM attendance')
    rows = c.fetchall()

    with open('attendance.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Date', 'Time'])  # Writing the header
        writer.writerows(rows)  # Writing the data

    print("Attendance records exported to 'attendance.csv'.")


# Step 9: They will call the functions to view and export attendance
view_attendance()
export_to_csv()

# Step 10: Now, finally it will close the database connection
conn.close()
