from flask import (
    Flask,
    request,
    abort,
    jsonify,
    abort,
)

import os
from dotenv import load_dotenv

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

load_dotenv()
app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
# 檢查是否讀取成功
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("環境變數 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET 沒有正確讀取")

configuration = Configuration(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route('/webhook', methods=['POST'])
def webhook():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )


# 接收外部 URL 請求，並向 LINE 用戶發送通知
@app.route("/send_message", methods=['POST'])
def send_message():
    data = request.get_json()
    user_id = data.get('user_id')  # 從請求中取得用戶ID
    message = data.get('message')  # 從請求中取得要發送的訊息
    
    if user_id and message:
        try:
            configuration.push_message(user_id, TextSendMessage(text=message))
            return jsonify({'status': 'Message sent successfully.'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'user_id and message are required.'}), 400


# 發布桌面通知的路由
@app.route('/notify', methods=['POST'])
def notify():
    message = "來自 Flask 應用的通知"
    os.system(f'PowerShell -Command "New-BurntToastNotification -Text \\"通知標題\\", \\"{message}\\""')
    return jsonify({'status': 'Notification sent successfully!'}), 200


def register_routes(app):
    app.add_url_rule(
        "/notify/",
        "notify",
        notify,
        methods=["POST"],
    )
    app.add_url_rule(
        "/webhook",
        "webhook",
        webhook,
        methods=["POST"],
    )
    app.add_url_rule(
        "/send_message",
        "send_message",
        send_message,
        methods=["POST"],
    )
