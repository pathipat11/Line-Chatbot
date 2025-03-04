import re
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import ( MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage, ImageSendMessage )
import requests

LINE_CHANNEL_ACCESS_TOKEN = "Ea4Fo1WAIUnKbPl18U7ZG9UM5P98DSt0F74h4yAxjid9GclP1rl1rAnZ7Hh+Nbq2zPifb+HOKhscyVo4YVYUKr3D09ycpcq16UUxvAp+4E0Twwj+JTBUNe8dE8kEjDYy6J1bS5Z9JW64xQyQvkMrCAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "38ef76e8fd8dc498b03c3e1484e8eefe"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PREDICTION_API_URL = "https://bot-restful-api.onrender.com/predict"

user_sessions = {}

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Line Chatbot for Employee Status Prediction is Running."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip().lower()

    if user_input in ["help", "ช่วยเหลือ", "วิธีใช้", "สอบถาม"]:
        reply_text = (
            "🔹 วิธีใช้ระบบพยากรณ์ผล\n"
            "1️⃣ พิมพ์ 'Prediction' เพื่อเริ่มต้น\n"
            "2️⃣ บอทจะถามค่าที่ต้องกรอกทีละข้อ\n"
            "3️⃣ ตอบค่าต่างๆ ตามที่ระบบขอ\n"
            "4️⃣ หลังจากกรอกครบ ระบบจะทำการพยากรณ์ผล\n"
            "🔸 หากต้องการเริ่มใหม่ ให้พิมพ์ 'ยกเลิก'"
        )
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_input in ["prediction", "พยากรณ์", "ทำนาย", "predict", "predictions"]:
        user_sessions[user_id] = {"step": 1, "data": {}}
        reply_text = "กรุณากรอกค่า Age (อายุ) เช่น 30"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_input == "ยกเลิก":
        del user_sessions[user_id]
        reply_text = "ข้อมูลถูกยกเลิก กรุณาเริ่มใหม่"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_id in user_sessions:
        session = user_sessions[user_id]
        step = session["step"]

        try:
            if step == 1:
                session["data"]["age"] = int(user_input)
                reply_text = "กรุณากรอกค่า Length of Service (ระยะเวลาทำงาน) เช่น 5"
            elif step == 2:
                session["data"]["length_of_service"] = int(user_input)
                reply_text = "กรุณากรอกค่า Salary (เงินเดือน) เช่น 30000"
            elif step == 3:
                session["data"]["salary"] = float(user_input)
                reply_text = "กรุณากรอกค่า Gender (เพศ) เช่น 0 (ชาย) หรือ 1 (หญิง)"
            elif step == 4:
                try:
                    gender = int(user_input.strip())
                    if gender not in [0, 1]:
                        raise ValueError
                    session["data"]["gender"] = gender
                    reply_text = "กรุณากรอกค่า Marital Status (สถานะสมรส) เช่น 0 (โสด) หรือ 1 (แต่งงานแล้ว)"
                except ValueError:
                    reply_text = "กรุณากรอกค่าเพศเป็นตัวเลข 0 (ชาย) หรือ 1 (หญิง) เท่านั้น"
            elif step == 5:
                try:
                    marital_status = int(user_input.strip())
                    if marital_status not in [0, 1]:
                        raise ValueError
                    session["data"]["marital_status"] = marital_status
                except ValueError:
                    reply_text = "กรุณากรอกค่าสถานะสมรสเป็นตัวเลข 0 (โสด) หรือ 1 (แต่งงานแล้ว) เท่านั้น"


                # ส่งข้อมูลไปยัง API สำหรับทำนายผล
                response = requests.post(PREDICTION_API_URL, json=session["data"])
                result = response.json()

                if "prediction" in result:
                    reply_text = f"ผลลัพธ์: {result['prediction']}"
                else:
                    reply_text = f"Error: {result.get('error', 'ไม่สามารถพยากรณ์ได้')}"
                
                # ลบเซสชั่นหลังจากส่งผลลัพธ์แล้ว
                del user_sessions[user_id]

            session["step"] += 1
        
        except ValueError:
            reply_text = "กรุณากรอกค่าตัวเลขที่ถูกต้อง"
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
