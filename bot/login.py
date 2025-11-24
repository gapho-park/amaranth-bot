from playwright.async_api import Page
from logger import logger
from config import Config
import asyncio
import datetime

async def login(page: Page) -> bool:
    try:
        logger.info('🚀 Starting Amaranth 10 Login...')

        # 1. Go to Login Page
        logger.info(f'📍 Connecting to: {Config.AMARANTH_URL}')
        await page.goto(Config.AMARANTH_URL, wait_until='networkidle', timeout=Config.BOT_TIMEOUT)
        logger.info('✅ Login page loaded')

        # ========== Step 1: Enter User ID ==========
        logger.info('📍 Step 1: Enter User ID...')
        
        # The first input is company code (disabled), so skip it.
        # Second input - User ID
        logger.debug('Finding User ID input field...')
        user_id_input = page.locator('input').nth(1)
        
        await user_id_input.wait_for(state='visible', timeout=Config.BOT_TIMEOUT)
        await user_id_input.fill(Config.AMARANTH_USER_ID)
        logger.info(f'✅ User ID entered: {Config.AMARANTH_USER_ID}')

        # Click "Next" button (first one)
        logger.debug('Finding "Next" button...')
        next_button = page.locator('button:has-text("다음")').first
        
        await next_button.wait_for(state='visible', timeout=Config.BOT_TIMEOUT)
        await next_button.click()
        logger.info('✅ "Next" button clicked')

        # Wait for Step 2 page load
        logger.info('⏳ Waiting for Step 2 page load...')
        try:
            await page.wait_for_load_state('load', timeout=10000)
        except Exception:
            logger.warning('⚠️ Page load timeout (continuing)')

        # ========== Step 2: Enter Password ==========
        logger.info('📍 Step 2: Enter Password...')
        
        # Find password input field
        logger.debug('Finding password input field...')
        password_input = page.locator('input[type="password"]')
        
        await password_input.wait_for(state='visible', timeout=Config.BOT_TIMEOUT)
        await password_input.fill(Config.AMARANTH_PASSWORD)
        logger.info('✅ Password entered')

        # Click "Login" button
        logger.debug('Finding "Login" button...')
        login_button = page.locator('button:has-text("로그인")').first
        
        await login_button.wait_for(state='visible', timeout=Config.BOT_TIMEOUT)
        await login_button.click()
        logger.info('✅ "Login" button clicked')

        # Wait for login completion
        logger.info('⏳ Waiting for login completion...')
        try:
            await page.wait_for_load_state('domcontentloaded', timeout=5000)
        except Exception:
            logger.warning('⚠️ Page load timeout (continuing)')

        await page.wait_for_timeout(1000)

        logger.info('✅ Login Successful!')
        # Check current status
        current_url = page.url
        title = await page.title()
        logger.debug(f'📍 Current URL: {current_url}')
        logger.debug(f'📄 Page Title: {title}')

        return True
    except Exception as error:
        logger.error(f'❌ Login Failed: {str(error)}')
        
        # Save screenshot on error
        try:
            timestamp = datetime.datetime.now().isoformat().replace(':', '-').replace('.', '-')
            screenshot_path = f'./screenshots/login_error_{timestamp}.png'
            await page.screenshot(path=screenshot_path)
            logger.info(f'📸 Error screenshot saved: {screenshot_path}')
        except Exception:
            logger.warning('Failed to save screenshot')

        raise error
