from playwright.async_api import Page
from logger import logger
from config import Config
import datetime
import json

async def go_to_accounting(page: Page) -> bool:
    try:
        logger.info('📍 Navigating to Expenditure Resolution Status...')

        # Step 1: Find and Click Integrated Search Bar
        logger.debug('Finding integrated search bar...')
        
        search_input = None
        click_success = False

        # Method 1: Find by placeholder attribute
        try:
            logger.debug('Method 1: input[placeholder*="통합검색"] attempting...')
            search_input = page.locator('input[placeholder*="통합검색"]').first
            if await search_input.is_visible():
                await search_input.click()
                logger.info('✅ Integrated search bar clicked (Method 1: placeholder)')
                click_success = True
        except Exception as e:
            logger.warning(f'⚠️ Method 1 failed: {str(e)}')

        # Method 2: Find by class attribute
        if not click_success:
            try:
                logger.debug('Method 2: [class*="search"] attempting...')
                search_input = page.locator('input[class*="search"]').first
                if await search_input.is_visible():
                    await search_input.click()
                    logger.info('✅ Integrated search bar clicked (Method 2: class search)')
                    click_success = True
            except Exception as e:
                logger.warning(f'⚠️ Method 2 failed: {str(e)}')

        # Method 3: Iterate all input elements
        if not click_success:
            try:
                logger.debug('Method 3: Iterating all input elements...')
                inputs = page.locator('input')
                count = await inputs.count()
                logger.debug(f'📊 Found {count} input elements')

                for i in range(count):
                    el = inputs.nth(i)
                    placeholder = await el.get_attribute('placeholder') or ''
                    
                    # logger.debug(f'  [{i}] placeholder="{placeholder}"')

                    if placeholder and ('통합' in placeholder or '검색' in placeholder):
                        if await el.is_visible():
                            await el.click()
                            search_input = el
                            logger.info(f'✅ Integrated search bar clicked (Method 3: input[{i}])')
                            click_success = True
                            break
            except Exception as e:
                logger.warning(f'⚠️ Method 3 failed: {str(e)}')

        if not click_success:
            raise Exception('Could not find integrated search bar. Please check page structure.')

        # Step 2: Enter '지출결의현황'
        logger.debug('Entering search term...')
        
        # Check focus
        await search_input.focus()
        await page.wait_for_timeout(300)
        
        # Clear existing text
        await search_input.evaluate('el => el.value = ""')
        
        # Type search term
        await search_input.type('지출결의현황', delay=100)
        logger.info('✅ "지출결의현황" entered')

        # Wait for search results load
        await page.wait_for_timeout(500)

        # Step 3: Press Enter
        logger.debug('Pressing Enter...')
        await search_input.press('Enter')
        logger.info('✅ Enter key pressed')

        # Wait for search results load
        logger.info('⏳ Waiting for search results...')
        await page.wait_for_timeout(1500)

        # Step 4: Click '지출결의현황' in right menu
        logger.debug('Finding "지출결의현황" in right menu...')
        
        menu_click_success = False

        # Method 1: Find by text selector (last item)
        try:
            logger.debug('Method 1: text="지출결의현황" (last) attempting...')
            expense_menu = page.locator('text="지출결의현황"').last
            if await expense_menu.is_visible():
                await expense_menu.click()
                logger.info('✅ "지출결의현황" menu clicked (Method 1)')
                menu_click_success = True
        except Exception as e:
            logger.warning(f'⚠️ Method 1 failed: {str(e)}')

        # Method 2: Iterate all "지출결의현황" text elements
        if not menu_click_success:
            try:
                logger.debug('Method 2: Iterating all "지출결의현황" elements...')
                all_items = page.locator('text="지출결의현황"')
                count = await all_items.count()
                logger.debug(f'📊 Found {count} "지출결의현황" items')

                # Check in reverse order (right menu is usually later in DOM)
                for i in range(count - 1, -1, -1):
                    try:
                        el = all_items.nth(i)
                        if await el.is_visible():
                            await el.click()
                            logger.info(f'✅ "지출결의현황" menu clicked (Method 2: item[{i}])')
                            menu_click_success = True
                            break
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f'⚠️ Method 2 failed: {str(e)}')

        # Method 3: Find within right panel
        if not menu_click_success:
            try:
                logger.debug('Method 3: Searching within right panel...')
                right_panel = page.locator('[class*="right"], [class*="panel"], [class*="sidebar"]').first
                if await right_panel.is_visible():
                    menu = right_panel.locator('text="지출결의현황"')
                    menu_count = await menu.count()
                    logger.debug(f'📊 Found {menu_count} items in right panel')
                    
                    if menu_count > 0:
                        await menu.first.click()
                        logger.info('✅ "지출결의현황" menu clicked (Method 3: right panel)')
                        menu_click_success = True
            except Exception as e:
                logger.warning(f'⚠️ Method 3 failed: {str(e)}')

        if not menu_click_success:
            raise Exception('Could not find "지출결의현황" menu.')

        # Wait for page load
        logger.info('⏳ Waiting for page load...')
        try:
            await page.wait_for_load_state('load', timeout=10000)
        except Exception:
            logger.warning('⚠️ Page load timeout (continuing)')

        logger.info('✅ "지출결의현황" page loaded')

        # Check current status
        current_url = page.url
        title = await page.title()
        logger.debug(f'📍 Current URL: {current_url}')
        logger.debug(f'📄 Page Title: {title}')

        return True
    except Exception as error:
        logger.error(f'❌ Navigation Failed: {str(error)}')
        
        # Save screenshot on error
        try:
            timestamp = datetime.datetime.now().isoformat().replace(':', '-').replace('.', '-')
            screenshot_path = f'./screenshots/navigation_error_{timestamp}.png'
            await page.screenshot(path=screenshot_path)
            logger.info(f'📸 Error screenshot saved: {screenshot_path}')
        except Exception:
            logger.warning('Failed to save screenshot')

        raise error
