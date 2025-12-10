import os
import asyncio
import logging
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from dotenv import load_dotenv

# 기존 봇 로직 임포트
from main import main as run_bot

# 환경변수 로드
load_dotenv()

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Slack App 초기화 (AMARANTH_ prefix로 다른 봇과 구분)
app = AsyncApp(token=os.environ.get("AMARANTH_SLACK_BOT_TOKEN"))


@app.shortcut("run_ledger_bot")
async def handle_amaranth_shortcut(ack, shortcut, client):
    """
    Global Shortcut 핸들러: 지출결의현황 업데이트
    슬랙 앱 설정에서 Callback ID를 'run_ledger_bot'으로 설정해야 합니다.
    결과는 SLACK_CHANNEL_ID 환경변수로 지정된 채널에 스레드로 전송됩니다.
    """
    # 1. 슬랙에게 shortcut을 잘 받았다고 3초 내에 응답 (필수)
    await ack()

    user_id = shortcut["user"]["id"]
    
    logger.info(f"📢 Shortcut triggered by {user_id}")

    # 2. 결과를 보낼 채널 ID (환경변수에서 가져옴)
    channel_id = os.environ.get("AMARANTH_SLACK_CHANNEL_ID")
    if not channel_id:
        logger.error("❌ AMARANTH_SLACK_CHANNEL_ID가 설정되지 않았습니다.")
        # DM으로 에러 알림
        dm_response = await client.conversations_open(users=user_id)
        await client.chat_postMessage(
            channel=dm_response["channel"]["id"],
            text="❌ AMARANTH_SLACK_CHANNEL_ID 환경변수가 설정되지 않았습니다. .env 파일을 확인해주세요."
        )
        return

    # 3. '시작' 메시지 전송 (지정된 채널에)
    initial_msg = await client.chat_postMessage(
        channel=channel_id,
        text=f"🚀 <@{user_id}>님이 아마란스 지출결의현황 업데이트를 시작했습니다!"
    )
    
    # 스레드 ID (이 메시지의 타임스탬프)
    thread_ts = initial_msg['ts']

    try:
        # 4. 스레드에 진행 상황 알림
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="⏳ 봇이 작업을 수행 중입니다. (약 1~2분 소요 예상)"
        )

        # 5. 봇 로직 실행 (main.py의 main 함수)
        logger.info("🤖 Running main bot logic...")
        await run_bot()

        # 6. 완료 메시지 전송
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="✅ *작업 완료!* 구글 시트 업데이트가 끝났습니다."
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
    app_token = os.environ.get("AMARANTH_SLACK_APP_TOKEN")
    if not app_token:
        raise ValueError("❌ AMARANTH_SLACK_APP_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
    handler = AsyncSocketModeHandler(app, app_token)
    await handler.start_async()

if __name__ == "__main__":
    print("⚡️ Slack Bolt app is running in Socket Mode!")
    asyncio.run(start_server())
