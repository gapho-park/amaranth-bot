import asyncio
import os
from playwright.async_api import async_playwright
from config import Config, validate_config
from logger import logger
from bot.login import login
from bot.navigation import go_to_accounting
from bot.actions import (
    set_application_date,
    clear_filters,
    set_document_status,
    search_data,
    download_excel
)
from bot.sheets import upload_excel_to_sheet
import glob

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

            # Create Context (Enable Downloads)
            context = await browser.new_context(accept_downloads=True)
            logger.info('✅ Browser context created')

            # Create Page
            page = await context.new_page()
            logger.info('✅ Page created')

            # 1️⃣ Login
            logger.info('\n========== Step 1: Login ==========')
            await login(page)

            # 2️⃣ Go to Accounting Menu
            logger.info('\n========== Step 2: Navigate to Accounting ==========')
            await go_to_accounting(page)

            logger.info('\n✅ Reached Expenditure Resolution Status Page!')
            logger.info('Next Steps:')
            logger.info('  - Set Application Date Filter')
            logger.info('  - Clear Department/Drafter Filters')
            logger.info('  - Set Document Status')
            logger.info('  - Search and Download Excel')

            # 3️⃣ Set Application Date
            logger.info('\n========== Step 3: Set Application Date ==========')
            await set_application_date(page)

            # 4️⃣ Document Status (Skip if default, but we implement it as per JS logic)
            # JS logic said "Step 4: Approval Status is default so skip", but then called setDocumentStatus in Step 6.
            # We will follow the JS execution flow:
            # JS Flow:
            # 1. Login
            # 2. Navigation
            # 3. Set Application Date
            # 4. (Log says skip approval status)
            # 5. Clear Filters
            # 6. Set Document Status
            # 7. Search
            # 8. Download

            # 5️⃣ Clear Filters
            logger.info('\n========== Step 5: Clear Filters ==========')
            await clear_filters(page)

            # 6️⃣ Set Document Status
            logger.info('\n========== Step 6: Set Document Status ==========')
            await set_document_status(page)

            # 7️⃣ Search Data (Skipped as per user request)
            logger.info('\n========== Step 7: Search Data (Skipped) ==========')
            # await search_data(page)

            logger.info('\n✨ Filters set and Search completed! Proceeding to Download...')

            # 8️⃣ Download Excel
            logger.info('\n========== Step 8: Download Excel ==========')
            if await download_excel(page):
                # Find the latest file in download directory
                list_of_files = glob.glob(os.path.join(Config.DOWNLOAD_PATH, '*'))
                if list_of_files:
                    latest_file = max(list_of_files, key=os.path.getctime)
                    logger.info(f'📂 Latest file found: {latest_file}')
                    
                    # 9️⃣ Upload to Google Sheets
                    logger.info('\n========== Step 9: Upload to Google Sheets ==========')
                    upload_excel_to_sheet(latest_file)
                else:
                    logger.warning('⚠️ No files found in download directory.')

            logger.info('\n🎉 All Processes Completed!')

            # Keep browser open in dev mode
            if not Config.BOT_HEADLESS:
                logger.info('\n💡 Dev Mode - Browser staying open... (Press Ctrl+C to exit)')
                # In Python async, we can just wait indefinitely or for a long time
                # await page.pause() is also an option if using inspector, but simple wait is fine
                await asyncio.sleep(3600) 

            await context.close()
            await browser.close()
            logger.info('🌐 Browser closed')

    except Exception as error:
        logger.error(f'❌ Error Occurred: {str(error)}')
        # In a real script we might want to exit with code 1, but here we just log
        # sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
