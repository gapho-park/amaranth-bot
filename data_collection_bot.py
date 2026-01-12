"""
통장 자료수집 자동화 봇 (Bank Data Collection Bot)

자료수집및자동분개처리 메뉴에서 통장 데이터를 수집하는 자동화 스크립트

실행 흐름:
1. 로그인
2. 통합검색에서 "자료수집및자동분개처리" 검색 → 메뉴 클릭
3. 자료수집 탭 클릭
4. 증빙구분에서 "통장" 선택 → 10초 대기
5. 수집일 일괄적용 버튼 클릭 → 확인
6. 수집시작일/종료일 입력 → 적용
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
from config import Config, validate_config
from logger import logger
from bot.login import login
from bot.navigation import go_to_data_collection, switch_company
from bot.actions import (
    dismiss_notice_popup,  # 공지 팝업 처리
    click_data_collection_tab,
    select_bankbook_filter,
    click_batch_date_apply_button,
    fill_collection_dates,
    click_data_collection_and_auto_journalize  # 선택사항
)


async def run_bank_data_collection(
    page,
    start_date: str = None,
    end_date: str = None,
    execute_collection: bool = False
):
    """
    통장 자료수집 실행
    
    Args:
        page: Playwright page object
        start_date: 수집시작일 (YYYYMMDD 형식, 기본값: 오늘)
        end_date: 수집종료일 (YYYYMMDD 형식, 기본값: 오늘)
        execute_collection: 자료수집 및 자동분개 버튼까지 클릭할지 여부
    """
    # 날짜 기본값 설정 (오늘)
    today = datetime.now().strftime('%Y%m%d')
    start_date = start_date or today
    end_date = end_date or today
    
    logger.info(f'📅 Collection Date Range: {start_date} ~ {end_date}')
    
    # Step 1: 자료수집및자동분개처리 메뉴로 이동
    logger.info('\n========== Step 1: Navigate to 자료수집및자동분개처리 ==========')
    await go_to_data_collection(page)
    
    # Step 1.5: 공지 팝업 처리 (하루에 한번 뜨는 팝업)
    logger.info('\n========== Step 1.5: Dismiss Notice Popup ==========')
    await dismiss_notice_popup(page)
    
    # Step 2: 자료수집 탭 클릭
    logger.info('\n========== Step 2: Click 자료수집 Tab ==========')
    await click_data_collection_tab(page)
    
    # Step 3: 증빙구분에서 통장 선택
    logger.info('\n========== Step 3: Select 통장 Filter ==========')
    await select_bankbook_filter(page)
    
    # Step 4: 수집일 일괄적용 버튼 클릭
    logger.info('\n========== Step 4: Click 수집일 일괄적용 Button ==========')
    await click_batch_date_apply_button(page)
    
    # Step 5: 수집시작일/종료일 입력 후 적용
    logger.info('\n========== Step 5: Fill Collection Dates and Apply ==========')
    await fill_collection_dates(page, start_date, end_date)
    
    # Step 6 (선택사항): 자료수집 및 자동분개 실행
    if execute_collection:
        logger.info('\n========== Step 6: Execute Data Collection ==========')
        await click_data_collection_and_auto_journalize(page)
    
    logger.info('\n✅ Bank Data Collection Process Completed!')


async def main():
    """메인 실행 함수"""
    browser = None
    try:
        # 설정 검증
        logger.info('⚙️  Validating configuration...')
        validate_config()
        logger.info('✅ Configuration validated')

        # 필요한 디렉토리 생성
        if not os.path.exists(Config.DOWNLOAD_PATH):
            os.makedirs(Config.DOWNLOAD_PATH)
            logger.info(f'📁 Download directory created: {Config.DOWNLOAD_PATH}')

        if not os.path.exists('./screenshots'):
            os.makedirs('./screenshots')

        # 브라우저 시작
        logger.info('🌐 Starting Browser...')
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=Config.BOT_HEADLESS,  # 환경변수로 제어
                slow_mo=Config.BOT_SLOW_MO
            )
            logger.info('✅ Browser started')

            # 컨텍스트 생성
            context = await browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            logger.info('✅ Browser context created')

            # 페이지 생성
            page = await context.new_page()
            logger.info('✅ Page created')

            # 1️⃣ 로그인
            logger.info('\n========== Login ==========')
            if not await login(page):
                logger.error('❌ Login failed')
                return

            # 2️⃣ 통장 자료수집 실행
            # 환경변수 또는 기본값(오늘) 사용
            start_date = os.environ.get('COLLECTION_START_DATE') or None
            end_date = os.environ.get('COLLECTION_END_DATE') or None
            
            await run_bank_data_collection(
                page,
                start_date=start_date,  # YYYYMMDD 형식 또는 None(오늘)
                end_date=end_date,      # YYYYMMDD 형식 또는 None(오늘)
                execute_collection=True  # 실제 자료수집 실행
            )

            logger.info('\n🎉 All Tasks Completed Successfully!')

            # 개발 모드: 브라우저 유지
            if not Config.BOT_HEADLESS:
                logger.info('\n💡 Dev Mode - Browser staying open... (Press Ctrl+C to exit)')
                await asyncio.sleep(3600)

            await context.close()
            await browser.close()
            logger.info('🌐 Browser closed')

    except Exception as error:
        logger.error(f'❌ Error Occurred: {str(error)}')
        
        # 에러 시 브라우저 유지 (디버깅용)
        if browser and not Config.BOT_HEADLESS:
            logger.warning('⚠️ Error occurred. Keeping browser open for debugging... (Press Ctrl+C to exit)')
            await asyncio.sleep(3600)


if __name__ == '__main__':
    asyncio.run(main())
