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
    user_input = event.message.text.strip()

    if user_input in ["help", "ช่วยเหลือ", "วิธีใช้", "สอบถาม"]:
        reply_text = (
            "🔹 วิธีใช้ระบบพยากรณ์ผล\n"
            "1️⃣ พิมพ์ 'Prediction' หรือ 'ทำนาย' เพื่อเริ่มต้น\n"
            "2️⃣ บอทจะถามค่าที่ต้องกรอกทีละข้อ\n"
            "3️⃣ ตอบค่าต่างๆ ตามที่ระบบขอ\n"
            "4️⃣ หลังจากกรอกครบ ระบบจะทำการพยากรณ์ผล\n"
            "🔸 หากต้องการเริ่มใหม่ ให้พิมพ์ 'ยกเลิก'"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_input in ["Prediction", "prediction", "พยากรณ์", "ทำนาย", "predict", "predictions"]:
        user_sessions[user_id] = {"step": 1, "data": {}}
        reply_text = "กรุณากรอกค่า Age (อายุ) เช่น 30"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_input == "ยกเลิก":
        user_sessions.pop(user_id, None)
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
                
                # เปลี่ยนเป็น Quick Reply สำหรับการเลือกเพศ
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="เพศ : ชาย", text="เพศ : ชาย")),
                    QuickReplyButton(action=MessageAction(label="เพศ : หญิง", text="เพศ : หญิง"))
                ])
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="กรุณาเลือกเพศ", quick_reply=quick_reply))
                session["step"] += 1
                return
            elif step == 4:
                if user_input not in ["เพศ : ชาย", "เพศ : หญิง"]:
                    raise ValueError("เลือกค่าที่ถูกต้อง")
                session["data"]["gender"] = 0 if user_input == "เพศ : ชาย" else 1

                # เปลี่ยนเป็น Quick Reply สำหรับสถานะสมรส
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="สถานะสมรส : โสด", text="สถานะสมรส : โสด")),
                    QuickReplyButton(action=MessageAction(label="สถานะสมรส : แต่งงานแล้ว", text="สถานะสมรส : แต่งงานแล้ว"))
                ])
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="กรุณาเลือกสถานะสมรส", quick_reply=quick_reply))
                session["step"] += 1
                return
            elif step == 5:
                if user_input not in ["สถานะสมรส : โสด", "สถานะสมรส : แต่งงานแล้ว"]:
                    raise ValueError("เลือกค่าที่ถูกต้อง")
                session["data"]["marital_status"] = 0 if user_input == "สถานะสมรส : โสด" else 1

                # แสดงข้อมูลที่กรอกทั้งหมดก่อนให้ยืนยัน
                summary_flex = create_summary_flex(session["data"])
                line_bot_api.reply_message(event.reply_token, summary_flex)
                return

            session["step"] += 1
        
        except ValueError as e:
            reply_text = f"⚠️ {str(e)} กรุณากรอกค่าที่ถูกต้อง"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return


def create_summary_flex(user_data):
    flex_message = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "ข้อมูลของคุณ", "weight": "bold", "size": "xl", "align": "center"},
                {"type": "text", "text": f"อายุ: {user_data['age']} ปี", "size": "md"},
                {"type": "text", "text": f"เพศ: {'ชาย' if user_data['gender'] == 0 else 'หญิง'}", "size": "md"},
                {"type": "text", "text": f"สถานะสมรส: {'โสด' if user_data['marital_status'] == 0 else 'แต่งงานแล้ว'}", "size": "md"}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "style": "primary", "action": {"type": "message", "label": "ยืนยันข้อมูล", "text": "ยืนยันข้อมูล"}},
                {"type": "button", "style": "secondary", "action": {"type": "message", "label": "ยกเลิก", "text": "ยกเลิก"}}
            ]
        }
    }
    return FlexSendMessage(alt_text="สรุปข้อมูลของคุณ", contents=flex_message)

