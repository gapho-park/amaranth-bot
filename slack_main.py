import os
import asyncio
import logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from dotenv import load_dotenv

# 기존 봇 로직 임포트
# main.py의 main 함수를 run_bot이라는 이름으로 가져옵니다.
from main import main as run_bot

# 환경변수 로드
load_dotenv()

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Slack App 초기화
app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.command("/지출결의현황")
async def handle_amaranth_command(ack, body, client):
    """
    /지출결의현황 명령어 핸들러
    """
    # 1. 슬랙에게 명령어를 잘 받았다고 3초 내에 응답 (필수)
    await ack()

    user_id = body["user_id"]
    channel_id = body["channel_id"]
    
    logger.info(f"📢 Command received from {user_id} in {channel_id}")

    # 2. '시작' 메시지 전송
    initial_msg = await client.chat_postMessage(
        channel=channel_id,
        text=f"🚀 <@{user_id}>님, 아마란스 지출결의현황 업데이트를 시작합니다!"
    )
    
    # 스레드 ID (이 메시지의 타임스탬프)
    thread_ts = initial_msg['ts']

    try:
        # 3. 스레드에 진행 상황 알림
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="⏳ 봇이 작업을 수행 중입니다. (약 1~2분 소요 예상)"
        )

        # 4. 봇 로직 실행 (main.py의 main 함수)
        # main()은 비동기 함수이므로 await로 기다립니다.
        logger.info("🤖 Running main bot logic...")
        await run_bot()

        # 5. 완료 메시지 전송
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="✅ **작업 완료!** 구글 시트 업데이트가 끝났습니다."
        )
        
        # 원본 메시지에 완료 이모지 추가
        await client.reactions_add(
            channel=channel_id,
            name="white_check_mark",
            timestamp=thread_ts
        )
        logger.info("✅ Job completed successfully.")

    except Exception as e:
        error_msg = f"❌ 작업 중 오류가 발생했습니다:\n```{str(e)}```"
        logger.error(f"Error during bot execution: {e}")
        
        # 에러 알림
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=error_msg
        )
        
        # 실패 이모지
        await client.reactions_add(
            channel=channel_id,
            name="x",
            timestamp=thread_ts
        )

async def start_server():
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if not app_token:
        raise ValueError("❌ SLACK_APP_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
    handler = AsyncSocketModeHandler(app, app_token)
    await handler.start_async()

if __name__ == "__main__":
    print("⚡️ Slack Bolt app is running in Socket Mode!")
    asyncio.run(start_server())

