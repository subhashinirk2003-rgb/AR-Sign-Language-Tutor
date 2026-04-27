# main_v2.py
# ==========================================================
# AR SIGN LANGUAGE TUTOR - HYBRID ELITE VERSION
# FINAL UPGRADED VERSION (80+ TARGET)
# SIGNS: A / B / L
#
# RUN:
# python main_v2.py
#
# INSTALL:
# pip install pyqt5 opencv-python mediapipe numpy open3d
# ==========================================================

import sys
import os
import cv2
import csv
import time
import math
import random
import threading
import numpy as np
import mediapipe as mp
import open3d as o3d

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox,
    QFrame, QStackedLayout
)

# ==========================================================
# HELPERS
# ==========================================================
def normalize_landmarks(arr):
    pts = np.array(arr).reshape(-1, 3)
    pts = pts - pts[0]

    m = np.max(np.linalg.norm(pts, axis=1))
    if m > 0:
        pts = pts / m

    return pts.flatten()


def clamp(v, a, b):
    return max(a, min(v, b))


# ==========================================================
# OPEN3D THREAD
# ==========================================================
class ViewerThread(threading.Thread):

    def __init__(self):
        super().__init__()
        self.daemon = True
        self.path = None
        self.refresh = False

    def run(self):

        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(
            "3D Correct Pose",
            width=600,
            height=700
        )

        while True:

            if self.refresh and self.path:

                self.vis.clear_geometries()

                mesh = o3d.io.read_triangle_mesh(self.path)

                if mesh.has_triangles():
                    mesh.compute_vertex_normals()
                    self.vis.add_geometry(mesh)

                    ctr = self.vis.get_view_control()
                    ctr.set_zoom(0.75)

                self.refresh = False

            self.vis.poll_events()
            self.vis.update_renderer()

    def load(self, path):
        self.path = path
        self.refresh = True


# ==========================================================
# MAIN APP
# ==========================================================
class Tutor(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AR Sign Language Tutor Elite")
        self.setGeometry(40, 20, 1750, 980)

        self.setStyleSheet("""
            QWidget{
                background:#05070c;
                color:white;
                font-family:Arial;
            }

            QPushButton{
                background:#0a1624;
                border:2px solid #00eaff;
                border-radius:14px;
                padding:12px;
                font-size:17px;
                color:#00eaff;
            }

            QPushButton:hover{
                background:#10243c;
            }

            QComboBox{
                background:#0a1624;
                border:2px solid #00eaff;
                border-radius:12px;
                padding:8px;
                min-height:42px;
                font-size:16px;
                color:white;
            }

            QFrame{
                background:#0c1018;
                border:1px solid #16304a;
                border-radius:16px;
            }
        """)

        # --------------------------------------------------
        # DATA
        # --------------------------------------------------
        self.signs = ["A", "B", "L"]
        self.reference = {}

        for f in os.listdir("reference_data"):
            if f.endswith(".npy"):
                s = f.replace(".npy", "")
                raw = np.load(
                    os.path.join("reference_data", f)
                )
                self.reference[s] = normalize_landmarks(raw)

        # --------------------------------------------------
        # STATE
        # --------------------------------------------------
        self.mode = "Practice"
        self.target = "A"

        self.quiz_round = 1
        self.quiz_total = 5
        self.quiz_time = 10
        self.quiz_score = 0

        self.level = "Beginner"

        self.thresholds = {
            "Beginner": 65,
            "Intermediate": 75,
            "Expert": 88
        }

        # analytics
        self.total_attempts = 0
        self.correct_attempts = 0
        self.best_scores = {
            "A": 0,
            "B": 0,
            "L": 0
        }

        self.streak = 0
        self.badges = 0

        self.last_pose = None
        self.stable_frames = 0

        self.last_log = time.time()

        # --------------------------------------------------
        # CSV
        # --------------------------------------------------
        self.csv_path = "session_log.csv"

        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                wr = csv.writer(f)
                wr.writerow([
                    "time",
                    "mode",
                    "target",
                    "detected",
                    "score",
                    "result"
                ])

        # --------------------------------------------------
        # CAMERA + MP
        # --------------------------------------------------
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        # --------------------------------------------------
        # VIEWER
        # --------------------------------------------------
        self.viewer = ViewerThread()
        self.viewer.start()

        # --------------------------------------------------
        # UI
        # --------------------------------------------------
        self.build_ui()
        self.load_pose("A")

        # --------------------------------------------------
        # TIMERS
        # --------------------------------------------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(15)

        self.quiz_timer = QTimer()
        self.quiz_timer.timeout.connect(self.tick_quiz)

    # ======================================================
    # UI
    # ======================================================
    def build_ui(self):

        root = QVBoxLayout()
        self.stack = QStackedLayout()

        # --------------------------------------------------
        # MENU
        # --------------------------------------------------
        menu = QWidget()
        ml = QVBoxLayout()

        t = QLabel("🖐 AR SIGN LANGUAGE TUTOR")
        t.setAlignment(Qt.AlignCenter)
        t.setFont(QFont("Arial", 30, QFont.Bold))
        t.setStyleSheet("color:#00eaff;")

        b1 = QPushButton("Practice")
        b2 = QPushButton("Quiz")
        b3 = QPushButton("Exit")

        b1.clicked.connect(self.start_practice)
        b2.clicked.connect(self.start_quiz)
        b3.clicked.connect(self.close)

        ml.addStretch()
        ml.addWidget(t)
        ml.addSpacing(30)
        ml.addWidget(b1)
        ml.addWidget(b2)
        ml.addWidget(b3)
        ml.addStretch()

        menu.setLayout(ml)

        # --------------------------------------------------
        # MAIN PAGE
        # --------------------------------------------------
        self.page = QWidget()
        pl = QVBoxLayout()

        top = QHBoxLayout()

        # left
        lf = QFrame()
        ll = QVBoxLayout()

        self.cam = QLabel()
        self.cam.setMinimumSize(980, 690)
        self.cam.setStyleSheet("background:black;")

        ll.addWidget(self.cam)
        lf.setLayout(ll)

        # right
        rf = QFrame()
        rl = QVBoxLayout()

        self.title_lab = QLabel("Practice Mode")
        self.title_lab.setAlignment(Qt.AlignCenter)
        self.title_lab.setFont(QFont("Arial", 22, QFont.Bold))
        self.title_lab.setStyleSheet("color:#00eaff;")

        self.combo = QComboBox()
        self.combo.addItems(self.signs)
        self.combo.currentTextChanged.connect(
            self.change_target
        )

        self.level_box = QComboBox()
        self.level_box.addItems(
            ["Beginner", "Intermediate", "Expert"]
        )
        self.level_box.currentTextChanged.connect(
            self.change_level
        )

        self.feedback = QLabel(
            "Match your hand to 3D pose"
        )
        self.feedback.setWordWrap(True)
        self.feedback.setAlignment(Qt.AlignCenter)
        self.feedback.setMinimumHeight(220)
        self.feedback.setStyleSheet("""
            background:#081018;
            border-radius:16px;
            font-size:23px;
            color:#00ffcc;
            padding:18px;
        """)

        back = QPushButton("⬅ Main Menu")
        back.clicked.connect(self.show_menu)

        rl.addWidget(self.title_lab)
        rl.addWidget(self.combo)
        rl.addWidget(self.level_box)
        rl.addWidget(self.feedback)
        rl.addWidget(back)

        rf.setLayout(rl)

        top.addWidget(lf, 2)
        top.addWidget(rf, 1)

        pl.addLayout(top)

        # stats
        bot = QHBoxLayout()

        self.box1 = self.stat("Target: A")
        self.box2 = self.stat("Detected: None")
        self.box3 = self.stat("Score: 0%")
        self.box4 = self.stat("Ready")

        bot.addWidget(self.box1)
        bot.addWidget(self.box2)
        bot.addWidget(self.box3)
        bot.addWidget(self.box4)

        pl.addLayout(bot)

        self.page.setLayout(pl)

        self.stack.addWidget(menu)
        self.stack.addWidget(self.page)

        root.addLayout(self.stack)
        self.setLayout(root)

    def stat(self, txt):

        x = QLabel(txt)
        x.setAlignment(Qt.AlignCenter)
        x.setMinimumHeight(95)

        x.setStyleSheet("""
            background:#081018;
            border-radius:16px;
            font-size:22px;
            color:#00eaff;
            font-weight:bold;
        """)

        return x

    # ======================================================
    # MENU
    # ======================================================
    def show_menu(self):
        self.quiz_timer.stop()
        self.stack.setCurrentIndex(0)

    def start_practice(self):
        self.mode = "Practice"
        self.title_lab.setText("Practice Mode")
        self.stack.setCurrentIndex(1)

    def start_quiz(self):
        self.mode = "Quiz"
        self.title_lab.setText("Quiz Mode")

        self.quiz_round = 1
        self.quiz_score = 0

        self.new_round()
        self.quiz_timer.start(1000)

        self.stack.setCurrentIndex(1)

    # ======================================================
    # QUIZ
    # ======================================================
    def tick_quiz(self):

        self.quiz_time -= 1
        self.box4.setText(f"⏱ {self.quiz_time}s")

        if self.quiz_time <= 0:

            self.quiz_round += 1

            if self.quiz_round > self.quiz_total:
                self.finish_quiz()
            else:
                self.new_round()

    def new_round(self):

        self.quiz_time = 10
        self.target = random.choice(self.signs)
        self.combo.setCurrentText(self.target)

        self.load_pose(self.target)

        self.box1.setText(
            f"Round {self.quiz_round}/5"
        )

    def finish_quiz(self):

        self.quiz_timer.stop()

        rank = "Beginner"

        if self.quiz_score > 350:
            rank = "Skilled"

        if self.quiz_score > 450:
            rank = "Expert"

        self.feedback.setText(
            f"🏆 QUIZ COMPLETE\n\n"
            f"Score: {self.quiz_score}\n"
            f"Rank: {rank}"
        )

    # ======================================================
    # SETTINGS
    # ======================================================
    def change_target(self, s):
        self.target = s
        self.load_pose(s)

    def change_level(self, x):
        self.level = x

    def load_pose(self, s):

        files = {
            "A": "printA.glb",
            "B": "printB.glb",
            "L": "printL.glb"
        }

        p = os.path.abspath(files[s])

        if os.path.exists(p):
            self.viewer.load(p)

    # ======================================================
    # LOGGING
    # ======================================================
    def write_log(self, detected, score, result):

        with open(self.csv_path, "a", newline="") as f:
            wr = csv.writer(f)

            wr.writerow([
                time.strftime("%H:%M:%S"),
                self.mode,
                self.target,
                detected,
                int(score),
                result
            ])

    # ======================================================
    # ADVANCED SCORE
    # ======================================================
    def calculate_score(self, ref, cur):

        d = np.linalg.norm(ref - cur)

        shape = max(0, 100 - d * 45)

        # stability bonus
        bonus = min(self.stable_frames * 2, 15)

        score = shape + bonus

        return clamp(score, 0, 100)

    # ======================================================
    # FEEDBACK ENGINE
    # ======================================================
    def smart_feedback(self, lm):

        if self.target == "A":
            if lm[8].y < lm[6].y:
                return "Fold fingers inward"

        elif self.target == "B":
            if lm[8].y > lm[6].y:
                return "Straighten fingers"

        elif self.target == "L":

            if lm[8].y > lm[6].y:
                return "Raise index finger"

            if lm[4].x > lm[3].x:
                return "Move thumb outward"

        return "Adjust hand slightly"

    # ======================================================
    # CAMERA LOOP
    # ======================================================
    def update_frame(self):

        ok, frame = self.cap.read()

        if not ok:
            return

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        res = self.hands.process(rgb)

        detected = "None"
        best = 0
        msg = "Show hand"

        if res.multi_hand_landmarks:

            for hand in res.multi_hand_landmarks:

                self.mp_draw.draw_landmarks(
                    frame,
                    hand,
                    self.mp_hands.HAND_CONNECTIONS
                )

                lm = hand.landmark
                h, w, _ = frame.shape

                cur = []
                pts = []

                for p in lm:
                    cur.extend([p.x, p.y, p.z])
                    pts.append(
                        (int(p.x*w), int(p.y*h))
                    )

                cur = normalize_landmarks(cur)

                # stability check
                if self.last_pose is not None:

                    diff = np.linalg.norm(
                        cur - self.last_pose
                    )

                    if diff < 0.15:
                        self.stable_frames += 1
                    else:
                        self.stable_frames = 0

                self.last_pose = cur.copy()

                # compare
                for s, ref in self.reference.items():

                    sc = self.calculate_score(ref, cur)

                    if sc > best:
                        best = sc
                        detected = s

                # smart arrows
                if self.target == "L":
                    cv2.arrowedLine(
                        frame,
                        pts[8],
                        (pts[8][0], pts[8][1]-40),
                        (0,255,255),
                        4
                    )

                msg = self.smart_feedback(lm)

        # --------------------------------------------------
        # DECISION
        # --------------------------------------------------
        need = self.thresholds[self.level]

        if detected == self.target and best >= need:

            result = "CORRECT"
            col = (0,255,0)

            msg = "✅ PERFECT"

            self.correct_attempts += 1
            self.streak += 1

            if self.streak % 3 == 0:
                self.badges += 1

            if self.mode == "Quiz":

                self.quiz_score += int(best)
                self.quiz_round += 1

                if self.quiz_round > 5:
                    self.finish_quiz()
                else:
                    self.new_round()

        elif best > need - 10:

            result = "CLOSE"
            col = (0,255,255)

            msg = "⚠ CLOSE"

            self.streak = 0

        else:

            result = "FAIL"
            col = (0,0,255)

            msg = "❌ TRY AGAIN"

            self.streak = 0

        self.total_attempts += 1

        if best > self.best_scores.get(
            self.target, 0
        ):
            self.best_scores[self.target] = int(best)

        # log every 1 sec
        if time.time() - self.last_log > 1:
            self.write_log(detected, best, result)
            self.last_log = time.time()

        # --------------------------------------------------
        # HUD
        # --------------------------------------------------
        acc = 0

        if self.total_attempts > 0:
            acc = int(
                self.correct_attempts /
                self.total_attempts * 100
            )

        cv2.putText(
            frame,
            f"Target: {self.target}",
            (20,40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            f"Detected: {detected}",
            (20,80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            col,
            2
        )

        cv2.putText(
            frame,
            f"Score: {int(best)}%",
            (20,120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            col,
            2
        )

        cv2.putText(
            frame,
            f"Acc: {acc}%  Badges:{self.badges}",
            (20,160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,255,255),
            2
        )

        # --------------------------------------------------
        # UI BOXES
        # --------------------------------------------------
        self.feedback.setText(msg)

        self.box1.setText(
            f"{self.level} | {self.target}"
        )

        self.box2.setText(
            f"Detected: {detected}"
        )

        self.box3.setText(
            f"Score: {int(best)}%"
        )

        self.box4.setText(
            f"Streak:{self.streak}  Acc:{acc}%"
        )

        # --------------------------------------------------
        # SHOW
        # --------------------------------------------------
        rgb2 = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        h, w, ch = rgb2.shape

        img = QImage(
            rgb2.data,
            w,
            h,
            ch*w,
            QImage.Format_RGB888
        )

        pix = QPixmap.fromImage(img)

        self.cam.setPixmap(
            pix.scaled(
                self.cam.width(),
                self.cam.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    # ======================================================
    # CLOSE
    # ======================================================
    def closeEvent(self, e):

        self.cap.release()
        e.accept()


# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":

    app = QApplication(sys.argv)

    win = Tutor()
    win.show()

    sys.exit(app.exec_())