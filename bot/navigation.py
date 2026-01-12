from playwright.async_api import Page
from logger import logger
from config import Config
import datetime
import json
import re

async def go_to_accounting(page: Page) -> bool:
    try:
        logger.info('📍 Navigating to Expenditure Resolution Status...')
        
        # Log current page state
        current_url = page.url
        title = await page.title()
        logger.debug(f'Current URL: {current_url}')
        logger.debug(f'Page Title: {title}')

        # explicit wait for stability on real server
        # await page.wait_for_timeout(5000)

        search_input = None
        click_success = False

        # Method 1: Find by placeholder attribute (using locator with :visible to ignore hidden inputs)
        try:
            logger.debug('Method 1: locator("input[placeholder*=\'통합검색\']:visible") attempting...')
            
            # Use :visible pseudo-class to ignore hidden inputs
            # get_by_placeholder finds hidden elements too, so we use locator with CSS selector
            search_input_locator = page.locator('input[placeholder*="통합검색"]:visible, input[placeholder*="검색"]:visible')
            
            # Wait for at least one visible element
            await search_input_locator.first.wait_for(state='visible', timeout=15000)
            
            if await search_input_locator.first.is_visible():
                await search_input_locator.first.click()
                search_input = search_input_locator.first
                logger.info('✅ Integrated search bar clicked (Method 1: visible locator)')
                click_success = True
        except Exception as e:
            logger.warning(f'⚠️ Method 1 failed: {str(e)}')

        # Method 2: Find by class attribute
        if not click_success:
            try:
                logger.debug('Method 2: [class*="search"] attempting...')
                search_input_locator = page.locator('input[class*="search"]').first
                if await search_input_locator.is_visible():
                    await search_input_locator.click()
                    search_input = search_input_locator
                    logger.info('✅ Integrated search bar clicked (Method 2: class search)')
                    click_success = True
            except Exception as e:
                logger.warning(f'⚠️ Method 2 failed: {str(e)}')

        # Method 3: Iterate all input elements
        if not click_success:
            try:
                logger.debug('Method 3: Iterating all input elements...')
                inputs = await page.locator('input').all()
                logger.debug(f'📊 Found {len(inputs)} input elements')

                for i, el in enumerate(inputs):
                    placeholder = await el.get_attribute('placeholder') or ''
                    
                    if '통합' in placeholder or '검색' in placeholder:
                        if await el.is_visible():
                            await el.click()
                            search_input = el
                            logger.info(f'✅ Integrated search bar clicked (Method 3: input[{i}])')
                            click_success = True
                            break
            except Exception as e:
                logger.warning(f'⚠️ Method 3 failed: {str(e)}')

        if not click_success:
            # Save HTML dump for debugging
            try:
                html_content = await page.content()
                timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
                dump_path = f'./screenshots/error_dump_{timestamp}.html'
                with open(dump_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f'📄 Error HTML dump saved: {dump_path}')
            except Exception as dump_error:
                logger.warning(f'Failed to save HTML dump: {dump_error}')
                
            raise Exception('Could not find integrated search bar. Please check page structure.')

        # Step 2: Type '지출결의현황'
        logger.debug('Typing search term...')
        
        # Ensure focus
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

        # Method 2: Find "지출결의현황" under "회계관리" category in search results
        if not menu_click_success:
            try:
                logger.debug('Method 2: Finding "지출결의현황" under "회계관리" category...')
                
                # Look for search result items that contain both "회계관리" path and "지출결의현황"
                # The search result typically shows: 회계관리 > 지출결의현황
                search_result_items = page.locator('[class*="search"] li, [class*="result"] li, [class*="menu"] li')
                count = await search_result_items.count()
                logger.debug(f'📊 Found {count} search result items')
                
                for i in range(count):
                    try:
                        item = search_result_items.nth(i)
                        item_text = await item.inner_text()
                        
                        # Check if this item contains "회계관리" and "지출결의현황"
                        if '회계관리' in item_text and '지출결의현황' in item_text:
                            if await item.is_visible():
                                await item.click()
                                logger.info(f'✅ "지출결의현황" menu clicked (Method 2: 회계관리 category, item[{i}])')
                                menu_click_success = True
                                break
                    except Exception:
                        continue
                
                # Fallback: If no "회계관리" category found, try clicking any visible "지출결의현황"
                if not menu_click_success:
                    logger.debug('Fallback: Trying any visible "지출결의현황"...')
                    all_items = page.locator('text="지출결의현황"')
                    items_count = await all_items.count()
                    logger.debug(f'📊 Found {items_count} "지출결의현황" items')
                    
                    # Check in reverse order (right menu is usually later in DOM)
                    for i in range(items_count - 1, -1, -1):
                        try:
                            el = all_items.nth(i)
                            if await el.is_visible():
                                await el.click()
                                logger.info(f'✅ "지출결의현황" menu clicked (Method 2 fallback: item[{i}])')
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
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            screenshot_path = f'./screenshots/navigation_error_{timestamp}.png'
            await page.screenshot(path=screenshot_path)
            logger.info(f'📸 Error screenshot saved: {screenshot_path}')
        except Exception:
            logger.warning('Failed to save screenshot')

        raise error

async def go_to_data_collection(page: Page) -> bool:
    """
    Navigate to 자료수집및자동분개처리 menu via integrated search.
    
    Flow:
    1. Click integrated search bar
    2. Type "자료수집및자동분개처리"
    3. Wait 2 seconds for dropdown results
    4. Click the menu hyperlink in dropdown
    """
    try:
        logger.info('📍 Navigating to 자료수집및자동분개처리...')
        
        current_url = page.url
        title = await page.title()
        logger.debug(f'Current URL: {current_url}')
        logger.debug(f'Page Title: {title}')

        search_input = None
        click_success = False

        # Method 1: Find by placeholder attribute (visible only)
        try:
            logger.debug('Method 1: locator("input[placeholder*=\'통합검색\']:visible") attempting...')
            search_input_locator = page.locator('input[placeholder*="통합검색"]:visible, input[placeholder*="검색"]:visible')
            await search_input_locator.first.wait_for(state='visible', timeout=15000)
            
            if await search_input_locator.first.is_visible():
                await search_input_locator.first.click()
                search_input = search_input_locator.first
                logger.info('✅ Integrated search bar clicked (Method 1)')
                click_success = True
        except Exception as e:
            logger.warning(f'⚠️ Method 1 failed: {str(e)}')

        # Method 2: Find by class attribute
        if not click_success:
            try:
                logger.debug('Method 2: [class*="search"] attempting...')
                search_input_locator = page.locator('input[class*="search"]').first
                if await search_input_locator.is_visible():
                    await search_input_locator.click()
                    search_input = search_input_locator
                    logger.info('✅ Integrated search bar clicked (Method 2)')
                    click_success = True
            except Exception as e:
                logger.warning(f'⚠️ Method 2 failed: {str(e)}')

        if not click_success:
            raise Exception('Could not find integrated search bar.')

        # Step 2: Type '자료수집및자동분개처리'
        logger.debug('Typing search term...')
        await search_input.focus()
        await page.wait_for_timeout(300)
        await search_input.evaluate('el => el.value = ""')
        await search_input.type('자료수집및자동분개처리', delay=30)
        logger.info('✅ "자료수집및자동분개처리" entered')

        # Step 3: Wait 2 seconds for dropdown results to appear
        logger.info('⏳ Waiting for dropdown search results (2 seconds)...')
        await page.wait_for_timeout(2000)

        # Step 4: Click the menu hyperlink in dropdown (NOT pressing Enter)
        logger.debug('Finding "자료수집및자동분개처리" in dropdown...')
        
        menu_click_success = False

        # Try to find in dropdown/autocomplete results
        try:
            # Look for the highlighted/matched text in search results
            # Usually in a dropdown container with hyperlink
            dropdown_selectors = [
                'text="자료수집및자동분개처리"',
                '[class*="search"] a:has-text("자료수집및자동분개처리")',
                '[class*="result"] a:has-text("자료수집및자동분개처리")',
                '[class*="dropdown"] :has-text("자료수집및자동분개처리")',
                '[class*="auto"] :has-text("자료수집및자동분개처리")',
            ]
            
            for selector in dropdown_selectors:
                try:
                    menu_item = page.locator(selector).last
                    if await menu_item.is_visible(timeout=1000):
                        await menu_item.click()
                        logger.info(f'✅ Menu clicked via selector: {selector}')
                        menu_click_success = True
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f'⚠️ Dropdown search failed: {str(e)}')

        # Fallback: Look for any visible "자료수집및자동분개처리" text
        if not menu_click_success:
            try:
                all_items = page.locator('text="자료수집및자동분개처리"')
                items_count = await all_items.count()
                logger.debug(f'📊 Found {items_count} "자료수집및자동분개처리" items')
                
                # Click the last visible one (usually the dropdown result)
                for i in range(items_count - 1, -1, -1):
                    try:
                        el = all_items.nth(i)
                        if await el.is_visible():
                            await el.click()
                            logger.info(f'✅ "자료수집및자동분개처리" menu clicked (fallback: item[{i}])')
                            menu_click_success = True
                            break
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f'⚠️ Fallback method failed: {str(e)}')

        if not menu_click_success:
            raise Exception('Could not find "자료수집및자동분개처리" menu in dropdown.')

        # Wait for page/menu load
        logger.info('⏳ Waiting for page load...')
        try:
            await page.wait_for_load_state('load', timeout=10000)
        except Exception:
            logger.warning('⚠️ Page load timeout (continuing)')

        await page.wait_for_timeout(2000)
        logger.info('✅ "자료수집및자동분개처리" page loaded')

        return True
        
    except Exception as error:
        logger.error(f'❌ Navigation to 자료수집및자동분개처리 Failed: {str(error)}')
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            screenshot_path = f'./screenshots/data_collection_nav_error_{timestamp}.png'
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
        await page.wait_for_timeout(1000)
        
        # 3. Select the target company
        logger.debug(f'Finding target company: {target_company_name}')
        
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
                # Check for the warning text
                warning_text = page.locator('text=열려 있는 탭이 모두 닫힙니다')
                if await warning_text.is_visible():
                    logger.info('⚠️ "Tabs will be closed" popup detected.')
                    
                    # Click the confirm button in this specific dialog
                    # Usually it's the last "확인" button or inside a specific container
                    confirm_btn = page.get_by_role("button", name="확인").last
                    if await confirm_btn.is_visible():
                        await confirm_btn.click()
                        logger.info('✅ Confirm button (2nd - warning popup) clicked')
                        
                        # Wait for page reload after company switch
                        logger.info('⏳ Waiting for page reload after company switch...')
                        await page.wait_for_load_state('networkidle', timeout=30000)
                        await page.wait_for_timeout(2000)  # Additional stability wait
                        logger.info('✅ Page reloaded after company switch')
            except Exception as e:
                logger.warning(f'⚠️ Error handling second popup: {str(e)}')
        else:
            logger.warning('⚠️ Could not find first Confirm button')

    except Exception as e:
        logger.error(f'❌ Failed to switch company: {str(e)}')
        raise e
