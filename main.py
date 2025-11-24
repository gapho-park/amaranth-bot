import asyncio
import os
import glob
from playwright.async_api import async_playwright
from config import Config, validate_config
from logger import logger
from bot.login import login
from bot.navigation import go_to_accounting, switch_company
from bot.actions import (
    set_application_date,
    clear_filters,
    set_document_status,
    search_data,
    download_excel
)
from bot.sheets import upload_excel_to_sheet

async def main():
    browser = None
    try:
        # Validate Config
        logger.info('⚙️  Validating configuration...')
        validate_config()
        logger.info('✅ Configuration validated')

        # Create Download Directory
        if not os.path.exists(Config.DOWNLOAD_PATH):
            os.makedirs(Config.DOWNLOAD_PATH)
            logger.info(f'📁 Download directory created: {Config.DOWNLOAD_PATH}')

        # Create Screenshots Directory
        if not os.path.exists('./screenshots'):
            os.makedirs('./screenshots')

        # Start Browser
        logger.info('🌐 Starting Browser...')
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=Config.BOT_HEADLESS,
                slow_mo=Config.BOT_SLOW_MO
            )
            logger.info('✅ Browser started')

            # Create Context (Enable Downloads, Set Viewport)
            context = await browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            logger.info('✅ Browser context created')

            # Create Page
            page = await context.new_page()
            logger.info('✅ Page created')

            # 1️⃣ Login
            logger.info('\n========== Step 1: Login ==========')
            if not await login(page):
                return

            # Define tasks for multi-company support
            tasks = [
                {
                    'company_name': '주식회사 라포랩스', 
                    'target_tab': Config.GOOGLE_SHEET_TAB, 
                    'needs_switch': False # Assumes default login is Rapport Labs
                },
                {
                    'company_name': '주식회사 라포스튜디오', 
                    'target_tab': 'A10 지출결의_RPST', 
                    'needs_switch': True
                }
            ]

            for i, task in enumerate(tasks):
                logger.info(f'\n🚀 Starting Task {i+1}: {task["company_name"]}')
                
                # Switch Company if needed
                if task['needs_switch']:
                    logger.info(f'\n========== Switching Company: {task["company_name"]} ==========')
                    await switch_company(page, task['company_name'])

                # 2️⃣ Navigation
                logger.info(f'\n========== Step {i+1}-2: Navigate to Expenditure Resolution ==========')
                await go_to_accounting(page)

                logger.info(f'\n✅ Reached Expenditure Resolution Status Page ({task["company_name"]})!')

                # 3️⃣ Set Application Date
                logger.info(f'\n========== Step {i+1}-3: Set Application Date ==========')
                await set_application_date(page)

                # 4️⃣ Clear Filters
                logger.info(f'\n========== Step {i+1}-4: Clear Filters ==========')
                await clear_filters(page)

                # 5️⃣ Set Document Status
                logger.info(f'\n========== Step {i+1}-5: Set Document Status ==========')
                await set_document_status(page)

                logger.info('\n✨ Filters set! Proceeding to Download...')

                # 6️⃣ Download Excel
                logger.info(f'\n========== Step {i+1}-6: Download Excel ==========')
                if await download_excel(page):
                    # Find the latest file in download directory
                    # Wait slightly for file system
                    await asyncio.sleep(2)
                    
                    list_of_files = glob.glob(os.path.join(Config.DOWNLOAD_PATH, '*'))
                    if list_of_files:
                        latest_file = max(list_of_files, key=os.path.getctime)
                        logger.info(f'📂 Latest file found: {latest_file}')
                        
                        # 7️⃣ Upload to Google Sheets
                        logger.info(f'\n========== Step {i+1}-7: Upload to Google Sheets ({task["target_tab"]}) ==========')
                        upload_excel_to_sheet(latest_file, task['target_tab'])
                    else:
                        logger.warning('⚠️ No files found in download directory.')
                
                logger.info(f'✅ Task {i+1} Completed for {task["company_name"]}')

            logger.info('\n🎉 All Tasks Completed Successfully!')

            # Keep browser open in dev mode
            if not Config.BOT_HEADLESS:
                logger.info('\n💡 Dev Mode - Browser staying open... (Press Ctrl+C to exit)')
                await asyncio.sleep(3600) 

            await context.close()
            await browser.close()
            logger.info('🌐 Browser closed')

    except Exception as error:
        logger.error(f'❌ Error Occurred: {str(error)}')
        
        # Keep browser open on error for debugging
        if browser and not Config.BOT_HEADLESS:
            logger.warning('⚠️ Error occurred. Keeping browser open for debugging... (Press Ctrl+C to exit)')
            await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
