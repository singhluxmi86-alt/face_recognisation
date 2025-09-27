import cv2
import os
import csv
from tkinter import *
from tkinter import messagebox

# Paths
DATA_DIR = "data"
STUDENTS_FILE = "students.csv"
os.makedirs(DATA_DIR, exist_ok=True)

def register_student(rollno, name, sclass):
    # Create file with header if not exists
    if not os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["RollNo", "Name", "Class"])

    # Check for duplicate Roll No
    with open(STUDENTS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["RollNo"] == rollno:
                messagebox.showerror("Error", f"Roll No {rollno} already exists!")
                return  # stop registration

    # ---- FACE CAPTURE FIRST ----
    cap = cv2.VideoCapture(0)
    student_dir = os.path.join(DATA_DIR, f"{rollno}_{name}")
    os.makedirs(student_dir, exist_ok=True)

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Capture Faces (Press 'c' to Capture, 'q' to Quit)", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            count += 1
            img_path = os.path.join(student_dir, f"{count}.jpg")
            cv2.imwrite(img_path, frame)
            print(f"[INFO] Saved {img_path}")
            if count >= 1:  # require at least 1 images
                break
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # ---- CHECK CAPTURE COUNT ----
    if count < 1:
        messagebox.showwarning("Cancelled", f"Student {name} NOT registered (only {count} images captured).")
        # remove folder if incomplete
        if os.path.exists(student_dir):
            for f in os.listdir(student_dir):
                os.remove(os.path.join(student_dir, f))
            os.rmdir(student_dir)
        return  #DO NOT SAVE TO CSV

    # ---- SAVE TO CSV ONLY AFTER SUCCESSFUL CAPTURE ----
    with open(STUDENTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([rollno, name, sclass])

    messagebox.showinfo("Done", f"Student {name} Registered Successfully!")

def form_ui():
    root = Tk()
    root.title("📷 Student Registration")

    # Window size and center
    window_width = 500
    window_height = 350
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)

    # Header Label
    header = Label(root, text="Student Registration Form",
                   font=("Arial", 18, "bold"), bg="#2c3e50", fg="white", pady=10)
    header.pack(fill="x")

    # Form Frame
    form_frame = Frame(root, padx=20, pady=20)
    form_frame.pack(fill="both", expand=True)

    Label(form_frame, text="Roll No", font=("Arial", 12)).grid(row=0, column=0, pady=10, sticky="e")
    Label(form_frame, text="Name", font=("Arial", 12)).grid(row=1, column=0, pady=10, sticky="e")
    Label(form_frame, text="Class", font=("Arial", 12)).grid(row=2, column=0, pady=10, sticky="e")

    rollno = Entry(form_frame, font=("Arial", 12), width=25)
    name = Entry(form_frame, font=("Arial", 12), width=25)
    sclass = Entry(form_frame, font=("Arial", 12), width=25)

    rollno.grid(row=0, column=1, padx=10, pady=10)
    name.grid(row=1, column=1, padx=10, pady=10)
    sclass.grid(row=2, column=1, padx=10, pady=10)

    def submit():
        if rollno.get().strip() == "" or name.get().strip() == "" or sclass.get().strip() == "":
            messagebox.showerror("Error", "All fields are required!")
            return
        register_student(rollno.get().strip(), name.get().strip(), sclass.get().strip())

    Button(form_frame, text="Submit & Capture", font=("Arial", 12, "bold"),
           bg="#27ae60", fg="white", padx=10, pady=5, command=submit).grid(row=3, column=0, columnspan=2, pady=20)

    root.mainloop()

if __name__ == "__main__":
    form_ui()
