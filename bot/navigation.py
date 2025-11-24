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
        
        # Wait for page to be fully loaded (networkidle is safer for SPAs)
        try:
            await page.wait_for_load_state('networkidle', timeout=5000)
        except Exception:
            logger.warning('⚠️ Network idle timeout (continuing)')
            
        # explicit wait for stability on real server
        # await page.wait_for_timeout(5000)

        
        search_input = None
        click_success = False

        # Method 1: Find by placeholder attribute
        try:
            logger.debug('Method 1: input[placeholder*="통합검색"] attempting...')
            
            # Wait for element to be visible (up to 15s) - More robust than fixed sleep
            await page.wait_for_selector('input[placeholder*="통합검색"]', state='visible', timeout=15000)
            
            search_input = page.locator('input[placeholder*="통합검색"]').first
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
        
        # Type search term (faster typing with 30ms delay)
        await search_input.type('지출결의현황', delay=30)
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

async def switch_company(page: Page, target_company_name: str):
    """
    Switches the active company.
    """
    try:
        logger.info(f'🏢 Switching company to: {target_company_name}')

        # 1. Click the top profile/company button to open the menu/popup
        # The button usually contains the user name or current company name.
        # Based on screenshot: "박갑호" is visible.
        logger.debug('Finding company switch button...')
        
        # Try finding by User Name "박갑호" or generic profile icon
        # We use .first because it might appear in multiple places, but top right is usually first or last depending on DOM.
        # Let's try a generic approach: finding the header area.
        
        # Strategy 1: Text "박갑호"
        trigger = page.locator('text="박갑호"').first
        if not await trigger.is_visible():
             # Strategy 2: Text "Finance"
             trigger = page.locator('text="Finance"').first
        
        if await trigger.is_visible():
            await trigger.click()
            logger.info('✅ Company/Profile menu clicked')
        else:
            raise Exception('Could not find Company/Profile button (looked for "박갑호" or "Finance")')

        # 2. Wait for the popup/dropdown
        # User said: "Popup appears, select Rapport Studio at bottom"
        await page.wait_for_timeout(1000)
        
        # 3. Select the target company
        logger.debug(f'Finding target company: {target_company_name}')
        
        # User reported we need to click the radio button (circle) to the left of the company name.
        # The radio button is an SVG element with a circle inside.
        # Strategy: Find the row (tr) that contains the company name, then click the SVG in the first cell.
        
        # Try finding the row
        target_row = page.locator(f'tr:has-text("{target_company_name}")').first
        
        if await target_row.is_visible():
            logger.debug(f'Found row for {target_company_name}')
            
            # Strategy 1: Try to find and click the SVG element (the actual radio button)
            try:
                svg_radio = target_row.locator('svg').first
                await svg_radio.click()
                logger.info(f'✅ Target company radio button clicked (SVG) for "{target_company_name}"')
            except Exception as e1:
                logger.debug(f'SVG click failed: {str(e1)}')
                
                # Strategy 2: Click the first cell which contains the SVG
                try:
                    first_cell = target_row.locator('td').first
                    await first_cell.click()
                    logger.info(f'✅ Target company radio button clicked (first cell) for "{target_company_name}"')
                except Exception as e2:
                    logger.debug(f'First cell click failed: {str(e2)}')
                    
                    # Strategy 3: Try force clicking input[type="radio"] if it exists
                    try:
                        radio_input = target_row.locator('input[type="radio"]').first
                        await radio_input.click(force=True)
                        logger.info(f'✅ Target company radio button clicked (input force) for "{target_company_name}"')
                    except Exception as e3:
                        logger.warning(f'All radio click strategies failed. Last error: {str(e3)}')
                        raise Exception(f'Could not click radio button for "{target_company_name}"')
        else:
            raise Exception(f'Could not find row for target company "{target_company_name}"')
            
        await page.wait_for_timeout(500)

        # 4. Click Confirm "확인" (First one - company selection popup)
        logger.debug('Clicking Confirm (1st - company selection)...')
        first_confirm_btn = page.get_by_role("button", name="확인").last
        if await first_confirm_btn.is_visible():
            await first_confirm_btn.click()
            logger.info('✅ Confirm button (1st - company selection) clicked')

            # 5. Handle "Tabs will be closed" popup if it appears
            logger.debug('Waiting for potential second popup (Tabs closed warning)...')

            try:
                await page.wait_for_timeout(1500)
                await page.wait_for_selector('text=열려 있는 탭이 모두 닫힙니다', state='visible', timeout=3000)
                logger.info('⚠️ "Tabs will be closed" popup detected.')

                popup = page.get_by_role("dialog").filter(
                    has_text="열려 있는 탭이 모두 닫힙니다"
                ).first
                if not await popup.is_visible():
                    popup = page.locator('div:has-text("열려 있는 탭이 모두 닫힙니다")').first

                confirm_btn_in_popup = popup.get_by_role("button", name="확인").first
                await confirm_btn_in_popup.click()
                logger.info('✅ Second Confirm button clicked (inside popup dialog)')

            except Exception as e:
                logger.debug(f'ℹ️ No second popup appeared or failed to handle: {str(e)}')
        else:
            logger.warning('⚠️ First confirm button not found. Checking if switch happened automatically...')

        # 6. Wait for reload/switch
        logger.info('⏳ Waiting for company switch...')
        await page.wait_for_load_state('networkidle', timeout=10000)
        await page.wait_for_timeout(3000) # Extra wait for safety
        
        return True

    except Exception as e:
        logger.error(f'❌ Failed to switch company: {str(e)}')
        raise e
