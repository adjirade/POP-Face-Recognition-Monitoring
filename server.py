import pandas as pd
import cv2
import urllib.request
import numpy as np
import os
from datetime import datetime
import face_recognition
import paho.mqtt.client as mqtt
import ssl
import requests  # ✅ Tambahan untuk Telegram

# ====================== MQTT SETUP ==========================
MQTT_BROKER = "0b67bb8ef1e14bc69fc0ae5f559dd11e.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "RECOG"
MQTT_PASSWORD = "Michael1"
MQTT_TOPIC = "valid"

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
    print("🔗 MQTT Connected!")
except Exception as e:
    print("❌ MQTT Connection Failed:", e)

# ====================== TELEGRAM SETUP ==========================
BOT_TOKEN = "7908929521:AAGyKTRFIT5emF7uvM7OZeUOQ48y4NGvogo"
CHAT_ID = "1467028737"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_telegram_message(message):
    """Fungsi untuk mengirim pesan ke Telegram"""
    try:
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'  # Agar bisa pakai formatting HTML
        }
        response = requests.post(TELEGRAM_API_URL, data=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Telegram Sent: {message}")
            return True
        else:
            print(f"❌ Telegram Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

# ============================================================

path = "/home/adjira/Downloads/ATTENDANCE/ATTENDANCE/image_folder"
url = 'http://10.109.141.212/cam-hi.jpg'
attendance_folder = "/home/adjira/Downloads/ATTENDANCE/ATTENDANCE"

if 'Attendance.csv' in os.listdir(attendance_folder):
    print("there iss..")
    os.remove(os.path.join(attendance_folder, "Attendance.csv"))
else:
    df = pd.DataFrame(list())
    df.to_csv(os.path.join(attendance_folder, "Attendance.csv"))

images = []
classNames = []
myList = os.listdir(path)
print(myList)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])
print(classNames)

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodes = face_recognition.face_encodings(img)
        if len(encodes) == 0:
            print("❌ Tidak ada wajah terdeteksi pada gambar, dilewati.")
            continue
        encodeList.append(encodes[0])
    return encodeList

def markAttendance(name):
    with open("Attendance.csv", 'r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
        
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')
            return True  # ✅ Return True jika attendance baru dicatat
        return False  # ✅ Return False jika sudah tercatat sebelumnya

encodeListKnown = findEncodings(images)
print('Encoding Complete')

# ✅ Dictionary untuk tracking apakah sudah kirim telegram
telegram_sent = {}

while True:
    img_resp = urllib.request.urlopen(url)
    imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
    img = cv2.imdecode(imgnp, -1)
    
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
    
    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)
        
        if matches[matchIndex]:
            name = classNames[matchIndex].upper()
            
            # ===================== MQTT SEND ==========================
            try:
                mqtt_client.publish(MQTT_TOPIC, f"VALID")
                print(f"📡 MQTT Sent → VALID: {name}")
            except Exception as e:
                print("❌ MQTT publish error:", e)
            
            # ===================== TELEGRAM SEND ==========================
            # ✅ Kirim telegram hanya sekali per nama
            if name not in telegram_sent:
                telegram_message = f"✅ <b>VALID</b>: {name}\n⏰ {datetime.now().strftime('%H:%M:%S')}"
                if send_telegram_message(telegram_message):
                    telegram_sent[name] = True  # Tandai sudah terkirim
            # ==========================================================
            
            # ===================== MARK ATTENDANCE ====================
            is_new_attendance = markAttendance(name)
            if is_new_attendance:
                print(f"📝 Attendance marked for {name}")
            # ==========================================================
            
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, name, (x1 + 6, y2 - 6),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
    
    cv2.imshow('Webcam', img)
    key = cv2.waitKey(5)
    if key == ord('q'):
        break

cv2.destroyAllWindows()
mqtt_client.loop_stop()
mqtt_client.disconnect()