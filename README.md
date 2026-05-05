# Sign Language Tutor

### A Real-Time 3D Interactive Learning System

## Overview

AR Sign Language Tutor is an interactive desktop application designed to support beginner sign language learning through real-time hand gesture recognition, three-dimensional pose guidance, and live feedback.

The system uses a webcam to capture the user’s hand gestures and compares them with stored reference templates for selected signs. A realistic 3D hand model is displayed to help users understand the correct pose.

This project focuses on the introductory signs:

* **A**
* **B**
* **L**

The aim of the project is to demonstrate how **3D Vision** and **Augmented Reality** technologies can improve accessibility, inclusive learning, and gesture-based education.

---

## Features

* Real-time webcam hand tracking
* MediaPipe 21-point hand landmark detection
* Gesture recognition for A, B, and L
* Live confidence score display
* Practice Mode for learning
* Quiz Mode for self-assessment
* Realistic 3D hand pose viewer using Open3D
* Interactive GUI using PyQt5
* Low-cost hardware implementation

---

## Technologies Used

* Python
* OpenCV
* MediaPipe
* NumPy
* PyQt5
* Open3D

---

## Project Structure

```text
AR-Sign-Language-Tutor/
│── main.py
│── requirements.txt
│── README.md
│── reference_data/
│   ├── A.npy
│   ├── B.npy
│   └── L.npy
│── printA.glb
│── printB.glb
│── printL.glb
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-link>
cd AR-Sign-Language-Tutor
```

### 2. Create Virtual Environment (Optional)

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run the Project

```bash
python main.py
```

---

## How to Use

1. Launch the application.
2. Choose **Practice Mode** or **Quiz Mode**.
3. Select target sign (A, B, or L).
4. Show your hand in front of the webcam.
5. Compare your gesture with the 3D hand model.
6. Improve your score using live feedback.

---

## Gesture Recognition Method

The system:

1. Detects the hand using MediaPipe
2. Extracts 21 landmarks
3. Normalizes landmark coordinates
4. Compares them with stored reference gestures
5. Returns best-matching sign with confidence score

---

## Educational Value

This project demonstrates practical applications of:

* 3D Vision
* Augmented Reality
* Human-centered computing
* Accessibility technology
* Real-time computer vision systems

---

## Future Improvements

* Full alphabet support
* Dynamic word recognition
* Mobile AR deployment
* Progress analytics
* Deep learning classification
* Two-hand gesture support

---

## Author

**Subhashini Reddy Kunduru**
MSc Robotics and Embedded AI
Maynooth University

---

## License

This project is for academic and educational purposes.
