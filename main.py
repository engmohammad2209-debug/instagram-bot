import os
import requests
import uvicorn
from fastapi import FastAPI, Request, Response
from google import genai
from google.genai import types

app = FastAPI()

# ==========================================
# Configuration / مفاتيح الربط
# ==========================================
GEMINI_API_KEY = "AQ.Ab8RN6IGEpJ2PqLyT4TJEflbN-5SSoiSKRZf6afEO3RUTmSd7Q"

PAGE_ACCESS_TOKEN = "IGAAZASRT398JFBZAGFwY3h2SG9xNnlheW5jX2Vrbk4wa09TdHlSRkRtT0ZAnOVQ5dTB0VWxlTEJIXy1Xdks0N2dqaDJxWU51SEdTYTVkY0R5anJ0MUk1SVZAybklhTzhrbS1tZA0EtQWFVdlV5RGc2Uy1kdG1TVTVlVWhvOEdIV3hmWQZDZD"

VERIFY_TOKEN = "my_secret_verify_token_123"

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# التعليمات البرمجية لتوجيه شخصية البوت
# ==========================================
SYSTEM_INSTRUCTION = """
أنت المساعد الذكي لـ "شركة المهندس للذكاء الاصطناعي والحلول التقنية".
وظيفتك: الرد على زبائن انستغرام بأسلوب عراقي محترم، ودود، ومقنع، وتوجيههم للخدمة المناسبة.

خدمات الشركة:
1️⃣ بناء شات بوت ذكي بالذكاء الاصطناعي للمتاجر والصفحات — يرد على الزبائن ويدير المبيعات تلقائياً 24 ساعة، بدون ما يحتاج صاحب المتجر يكون أونلاين طول الوقت.
2️⃣ تصميم فيديوهات وإعلانات سينمائية بتقنية 3D بالذكاء الاصطناعي — محتوى احترافي يشد انتباه الزبون ويزيد المبيعات.

طريقة الرد:
- أول رسالة من الزبون: رحّب فيه بأسلوب دافئ وقصير، واسأله شنو يحتاج بالضبط (شات بوت لمتجره، أو فيديوهات إعلانية، أو الاثنين).
- إذا حدد نوع الخدمة: اشرحها له بأسلوب مفصل شوي (3-4 أسطر) يوضح الفايدة الحقيقية له كتاجر (مثال: وفرة وقت، زيادة مبيعات، احترافية تميزه عن المنافسين). استخدم أمثلة ملموسة إذا أمكن.
- بعد الشرح، اسأله عن نوع نشاطه التجاري بسؤال بسيط (شنو تبيع؟ شنو صفحتك؟) عشان تخصص الجواب أكثر.
- إذا صار عنده اهتمام واضح أو سأل عن السعر: اطلب منه بأسلوب لطيف اسم متجره/صفحته + رقم تلفونه عشان المهندس يتواصل معه مباشرة ويعطيه عرض سعر دقيق.
- لا تعطي أسعار محددة بنفسك أبداً — هذا يحدده المهندس مباشرة حسب حجم المشروع.
- حافظ على الرسائل قصيرة نسبياً ومناسبة للخاص (DM)، وتجنب الحچي الطويل جداً بمقطع وحدة.
- إذا الزبون يحچي عن شي مو متعلق بالخدمات، رجّعه بلطف لموضوع الخدمة.
"""

def generate_ai_reply(user_text: str) -> str:
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return "أهلاً بك! جاري تحويل رسالتك إلى المهندس وسنقوم بالرد عليك في أقرب وقت."

def send_instagram_message(recipient_id: str, text_message: str):
    url = f"https://graph.instagram.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text_message}
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to send message: {response.status_code} - {response.text}")
    else:
        print(f"Message sent successfully to {recipient_id}")

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)

@app.post("/webhook")
async def handle_incoming_messages(request: Request):
    data = await request.json()
    print(f"Received webhook data: {data}")
    try:
        if data.get("object") in ["instagram", "page"]:
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    if "message" in messaging_event and not messaging_event["message"].get("is_echo"):
                        sender_id = messaging_event["sender"]["id"]
                        user_message = messaging_event["message"].get("text", "")
                        if user_message:
                            ai_reply = generate_ai_reply(user_message)
                            send_instagram_message(sender_id, ai_reply)
    except Exception as e:
        print(f"Error processing webhook event: {e}")
    return {"status": "EVENT_RECEIVED"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
