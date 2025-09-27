import cv2
from deepface import DeepFace
import os
import pandas as pd
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox
import pygame

# ----- Setup -----
DATA_DIR = "data"
STUDENTS_FILE = "students.csv"
ATTENDANCE_FILE = "attendance.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# Ensure attendance file exists
if not os.path.exists(ATTENDANCE_FILE):
    pd.DataFrame(columns=["RollNo", "Name", "Class", "Date", "Time"]).to_csv(ATTENDANCE_FILE, index=False)

# ----- Sound -----
def play_sound(path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"[ERROR] Could not play sound: {e}")

# ----- Load attendance -----
def load_attendance():
    try:
        df = pd.read_csv(ATTENDANCE_FILE, dtype=str)
        df.columns = df.columns.str.strip()
        for col in ["RollNo", "Name", "Class", "Date", "Time"]:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception as e:
        print(f"[ERROR] Loading attendance failed: {e}")
        return pd.DataFrame(columns=["RollNo", "Name", "Class", "Date", "Time"])

# ----- Mark attendance -----
def mark_attendance(rollno, name, sclass, marked_today):
    df = load_attendance()
    today = datetime.now().strftime("%Y-%m-%d")

    if rollno in marked_today:
        return False

    # Prevent duplicate
    if ((df["RollNo"] == rollno) & (df["Date"] == today)).any():
        marked_today.add(rollno)
        return False

    now = datetime.now()
    new_row = {
        "RollNo": rollno,
        "Name": name,
        "Class": sclass,
        "Date": today,
        "Time": now.strftime("%H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(ATTENDANCE_FILE, index=False)
    marked_today.add(rollno)
    play_sound("sounds/success.mp3")
    messagebox.showinfo("Attendance Marked", f"Thank you {name}!")
    return True

# ----- Face Scanner -----
def start_scanner():
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    marked_today = set()
    students_df = pd.read_csv(STUDENTS_FILE, dtype=str)
    students_df.columns = students_df.columns.str.strip()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        for (x, y, w, h) in faces:
            face_img = frame[y:y+h, x:x+w]
            temp_path = "temp_face.jpg"
            cv2.imwrite(temp_path, face_img)

            try:
                result = DeepFace.find(img_path=temp_path, db_path=DATA_DIR, enforce_detection=False, silent=True)
                if len(result) > 0 and not result[0].empty:
                    match_path = result[0].iloc[0]["identity"]
                    folder_name = os.path.basename(os.path.dirname(match_path))
                    rollno, name = folder_name.split("_", 1)

                    # Get class
                    sclass_list = students_df[students_df["RollNo"] == str(rollno)]["Class"].values
                    sclass = sclass_list[0] if len(sclass_list) > 0 else "Unknown"

                    mark_attendance(str(rollno), name, sclass, marked_today)

                    # Draw rectangle & name
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                else:
                    cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
            except Exception as e:
                cv2.putText(frame, "Error", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
                print(f"[ERROR] {str(e)}")

        cv2.imshow("Attendance Scanner (Press 'q' to Quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# ----- Dashboard -----
def dashboard():
    root = Tk()
    root.title("Attendance Dashboard")
    root.geometry("800x500")

    cols = ("RollNo", "Name", "Class", "Date", "Time")
    tree = ttk.Treeview(root, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
    tree.pack(fill=BOTH, expand=True)

    def load_today():
        df = load_attendance()
        today = datetime.now().strftime("%Y-%m-%d")
        today_df = df[df["Date"] == today]
        for row in tree.get_children():
            tree.delete(row)
        for _, r in today_df.iterrows():
            tree.insert("", END, values=list(r))

    def export_excel():
        df = load_attendance()
        excel_file = "attendance.xlsx"
        df.to_excel(excel_file, index=False)
        messagebox.showinfo("Export", f"Attendance exported to {excel_file}")

    frame = Frame(root)
    frame.pack(fill=X, pady=5)
    Button(frame, text="Refresh", command=load_today).pack(side=LEFT, padx=10)
    Button(frame, text="Export to Excel", command=export_excel).pack(side=LEFT, padx=10)
    Button(frame, text="Start Scanner", command=start_scanner).pack(side=LEFT, padx=10)

    load_today()
    root.mainloop()

if __name__ == "__main__":
    dashboard()
