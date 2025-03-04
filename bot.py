import re
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import ( MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, FlexSendMessage, ImageSendMessage )
import requests

LINE_CHANNEL_ACCESS_TOKEN = "Ea4Fo1WAIUnKbPl18U7ZG9UM5P98DSt0F74h4yAxjid9GclP1rl1rAnZ7Hh+Nbq2zPifb+HOKhscyVo4YVYUKr3D09ycpcq16UUxvAp+4E0Twwj+JTBUNe8dE8kEjDYy6J1bS5Z9JW64xQyQvkMrCAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "38ef76e8fd8dc498b03c3e1484e8eefe"

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

    if user_input == "ยืนยันข้อมูล":
        if user_id not in user_sessions or "data" not in user_sessions[user_id]:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบข้อมูล กรุณาเริ่มใหม่"))
            return

        user_data = user_sessions[user_id]["data"]

        response = requests.post(PREDICTION_API_URL, json=user_data)
        result = response.json()

        if "prediction" in result:
            reply_text = f"ผลลัพธ์: {result['prediction']}"
        else:
            reply_text = f"Error: {result.get('error', 'ไม่สามารถพยากรณ์ได้')}"

        del user_sessions[user_id]  
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
                gender = int(user_input)
                if gender not in [0, 1]:
                    raise ValueError
                session["data"]["gender"] = gender
                reply_text = "กรุณากรอกค่า Marital Status (สถานะสมรส) เช่น 0 (โสด) หรือ 1 (แต่งงานแล้ว)"
            elif step == 5:
                marital_status = int(user_input)
                if marital_status not in [0, 1]:
                    raise ValueError
                session["data"]["marital_status"] = marital_status

                # แสดงข้อมูลที่กรอกทั้งหมดก่อนให้ยืนยัน
                summary_flex = create_summary_flex(session["data"])
                line_bot_api.reply_message(event.reply_token, summary_flex)
                return

            session["step"] += 1
        
        except ValueError:
            reply_text = "กรุณากรอกค่าตัวเลขที่ถูกต้อง"
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

def create_summary_flex(user_data):
    flex_message = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#E3F2FD", 
            "cornerRadius": "md",
            "paddingAll": "lg",
            "contents": [
                {
                    "type": "text",
                    "text": "ข้อมูลของคุณ",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#1976D2",  
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "sm",
                    "color": "#B0BEC5"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "sm",
                    "spacing": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"อายุ: {user_data['age']} ปี",
                            "size": "md",
                            "color": "#37474F"
                        },
                        {
                            "type": "text",
                            "text": f"ระยะเวลาทำงาน: {user_data['length_of_service']} ปี",
                            "size": "md",
                            "color": "#37474F"
                        },
                        {
                            "type": "text",
                            "text": f"เงินเดือน: {user_data['salary']} บาท",
                            "size": "md",
                            "color": "#37474F"
                        },
                        {
                            "type": "text",
                            "text": f"เพศ: {'ชาย' if user_data['gender'] == 0 else 'หญิง'}",
                            "size": "md",
                            "color": "#37474F"
                        },
                        {
                            "type": "text",
                            "text": f"สถานะสมรส: {'โสด' if user_data['marital_status'] == 0 else 'แต่งงานแล้ว'}",
                            "size": "md",
                            "color": "#37474F"
                        }
                    ]
                },
                {
                    "type": "separator",
                    "margin": "sm",
                    "color": "#B0BEC5"
                },
                {
                    "type": "text",
                    "text": "ข้อมูลของคุณถูกต้องหรือไม่?",
                    "margin": "sm",
                    "size": "md",
                    "color": "#1976D2",
                    "align": "center",
                    "weight": "bold"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "message",
                        "label": "ยืนยันข้อมูล",
                        "text": "ยืนยันข้อมูล"
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "message",
                        "label": "ยกเลิก",
                        "text": "ยกเลิก"
                    }
                }
            ]
        }
    }
    return FlexSendMessage(alt_text="สรุปข้อมูลของคุณ", contents=flex_message)
