from playwright.async_api import Page
from typing import Optional
from logger import logger
from config import Config
import os
import datetime

async def set_application_date(page: Page) -> bool:
    """
    Step 1: Set Application Date Filter
    - Click date input field (Application Date)
    - Enter 20250101 ~ 20251231
    - Confirm with Enter
    """
    try:
        logger.info('📅 Setting Application Date Filter...')

        # Wait for date inputs
        await page.wait_for_selector('input.OBTDatePickerRebuild_inputYMD__PtxMy', timeout=5000)
        date_inputs = page.locator('input.OBTDatePickerRebuild_inputYMD__PtxMy')
        count = await date_inputs.count()
        logger.info(f'🔍 Date input count: {count}')

        if count == 0:
            logger.error('❌ Could not find date inputs. Check selector.')
            return False

        start_input = date_inputs.nth(0)
        end_input = date_inputs.nth(1) if count > 1 else None

        # Enter start date
        logger.debug('Clicking start date input...')
        await start_input.click()
        await page.wait_for_timeout(200)

        try:
            await start_input.press('Control+A')
        except Exception:
            pass
        await start_input.fill('20250101')
        logger.info('✅ Start date entered: 20250101')

        await page.wait_for_timeout(200)

        if end_input:
            # If end date is a separate input
            logger.debug('Clicking end date input...')
            await end_input.click()
            await page.wait_for_timeout(200)

            try:
                await end_input.press('Control+A')
            except Exception:
                pass
            await end_input.fill('20251231')
            logger.info('✅ End date entered: 20251231')
        else:
            # If range is in one input
            try:
                await start_input.press('Control+A')
            except Exception:
                pass
            await start_input.fill('20250101 ~ 20251231')
            logger.info('✅ Date range entered: 20250101 ~ 20251231')

        await page.wait_for_timeout(300)

        # Confirm with Enter
        await page.keyboard.press('Enter')
        logger.info('✅ Application Date Filter confirmed with Enter')

        await page.wait_for_timeout(1000)
        logger.info('✅ Application Date Filter set')
        return True
    except Exception as error:
        logger.error(f'❌ set_application_date failed: {str(error)}')
        return False

async def clear_filters(page: Page) -> bool:
    """
    Step 2: Process Filters Sequence & Trigger Search
    User Flow:
    - (After Date Set)
    - Enter (Pass Approval Status)
    - Enter (Pass Doc Class)
    - Enter (Pass Doc Title)
    - Enter (Pass Doc Number)
    - Delete -> Enter (Clear Department)
    - Delete -> Enter (Clear Drafter)
    - Enter (Pass Document Status -> Triggers Search)
    """
    try:
        logger.info('🎹 Processing Filter Sequence & Searching...')
        
        await page.wait_for_timeout(300)

        # 1. Approval Status -> Enter
        # 2. Document Class -> Enter
        # 3. Document Title -> Enter
        # 4. Document Number -> Enter
        logger.info('↩️  Passing 4 filters (Approval, Class, Title, Number)...')
        for _ in range(4):
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(150)

        # 5. Department -> Delete, Enter
        logger.info('🏢 Clearing Department (Delete → Enter)...')
        await page.keyboard.press('Delete')
        await page.wait_for_timeout(150)
        await page.keyboard.press('Enter')
        await page.wait_for_timeout(150)

        # 6. Drafter -> Delete, Enter
        logger.info('👤 Clearing Drafter (Delete → Enter)...')
        await page.keyboard.press('Delete')
        await page.wait_for_timeout(150)
        await page.keyboard.press('Enter')
        await page.wait_for_timeout(150)

        # 7. Document Status -> Enter (Triggers Search)
        logger.info('🔍 Triggering Search (Enter on Document Status)...')
        await page.keyboard.press('Enter')

        # Wait for data load (increased for schedule runs)
        logger.info('⏳ Waiting for data load...')
        await page.wait_for_timeout(3000)
        
        # Wait for network idle after search
        try:
            await page.wait_for_load_state('networkidle', timeout=15000)
            logger.info('  - Search: Network idle detected')
        except Exception:
            logger.warning('  - Search: Network idle timeout, continuing...')
        
        # Additional buffer
        await page.wait_for_timeout(2000)
        
        return True
    except Exception as error:
        logger.error(f'❌ clear_filters sequence failed: {str(error)}')
        return False

async def set_document_status(page: Page) -> bool:
    """
    Step 3: Set Document Status Filter
    - Assume popup/window is open
    - Click "All" (Uncheck all)
    - Click "Document(Approved)" (Select)
    - Click "Confirm" button
    """
    try:
        logger.info('📄 Setting Document Status Filter...')

        # Wait a bit for popup
        await page.wait_for_timeout(800)

        # 1) Click "All" label (Uncheck all)
        logger.debug('Finding "전체" label...')
        all_label = page.locator('label', has_text='전체').first
        await all_label.wait_for(state='visible', timeout=5000)
        await all_label.click()
        logger.info('✅ "All" clicked (Unchecked)')

        await page.wait_for_timeout(300)

        # 2) Click "Document(Approved)" item
        logger.debug('Finding "전표(승인)" item...')
        approval_item = page.get_by_text('전표(승인)', exact=True).first
        await approval_item.wait_for(state='visible', timeout=5000)
        await approval_item.click()
        logger.info('✅ "Document(Approved)" selected')

        await page.wait_for_timeout(300)

        # 3) Click "Confirm" button
        logger.debug('Finding "Confirm" button...')
        # Try finding by text "확인" within the dropdown area or generally
        # The image shows "취소" and "확인" at the bottom.
        confirm_button = page.locator('button:has-text("확인")').last
        # Alternatively, if it's inside a specific container:
        # confirm_button = page.locator('.OBTMultiDropDownList_bottomButton__1xAmc').filter(has_text='확인')
        
        await confirm_button.wait_for(state='visible', timeout=5000)
        await confirm_button.click()
        logger.info('✅ "Confirm" button clicked')

        await page.wait_for_timeout(500)
        logger.info('✅ Document Status Filter set')
        return True
    except Exception as error:
        logger.error(f'❌ set_document_status failed: {str(error)}')
        return False

async def search_data(page: Page) -> bool:
    """
    Step 4: Search Data
    - Press F10 key
    """
    try:
        logger.info('🔍 Searching Data...')

        await page.wait_for_timeout(500)

        # Press F10
        await page.keyboard.press('F10')
        logger.info('✅ F10 key pressed')

        # Wait for data load
        logger.info('⏳ Waiting for data load...')
        await page.wait_for_timeout(2000)

        try:
            await page.wait_for_load_state('networkidle', timeout=5000)
        except Exception:
            logger.warning('⚠️ Network load timeout')

        logger.info('✅ Data search completed')
        return True
    except Exception as error:
        logger.error(f'❌ search_data failed: {str(error)}')
        return False

async def download_excel(page: Page) -> Optional[str]:
    """
    Step 5: Right click grid → Convert to Excel → Download file
    Returns:
        str: Path to the downloaded file if successful
        None: If failed
    """
    try:
        logger.info('📥 Attempting Excel Download...')

        # 1) Find "Document Status" label to calculate coordinates
        # User requested clicking about 5cm (approx 150-200px) below the "Document Status" button/label
        logger.debug('Finding "전표발행여부" label for coordinate calculation...')
        
        # Try to find the label or the dropdown trigger
        target_anchor = page.locator('text="전표발행여부"').first
        
        if not await target_anchor.is_visible():
             # Fallback: try finding the dropdown we interacted with earlier, or just use a known location if possible
             # But let's try to find the label again
             target_anchor = page.locator('label:has-text("전표발행여부")').first
        
        if await target_anchor.is_visible():
            box = await target_anchor.bounding_box()
            if box:
                # Calculate target coordinates
                # x: center of the label
                # y: bottom of label + 150px (approx 4-5cm)
                target_x = box['x'] + (box['width'] / 2)
                target_y = box['y'] + box['height'] + 150
                
                logger.info(f'📍 Calculated click coordinates: ({target_x}, {target_y})')
                
                # Move mouse and right click
                await page.mouse.move(target_x, target_y)
                await page.wait_for_timeout(200)
                await page.mouse.click(target_x, target_y, button='right')
            else:
                raise Exception('Could not get bounding box for "전표발행여부"')
        else:
             # Fallback if label not found: try clicking in the middle of the screen (risky but better than failing)
             logger.warning('⚠️ Could not find "전표발행여부" label. Trying center screen click...')
             viewport = page.viewport_size
             if viewport:
                 await page.mouse.click(viewport['width'] / 2, viewport['height'] / 2, button='right')
             else:
                 raise Exception('Could not find anchor for right click')

        await page.wait_for_timeout(300)

        # 3) Click "Convert to Excel"
        logger.info('📄 Clicking "엑셀변환하기"...')
        await page.get_by_text('엑셀변환하기', exact=True).click()

        # 4) Wait for "Excel Conversion" popup and click Confirm
        logger.info('⏳ Waiting for Excel Conversion popup...')
        # The popup title is "엑셀변환하기" and has a "확인" button at the bottom
        
        # Wait for the popup to appear (optional, but good for stability)
        await page.wait_for_timeout(1000)
        
        logger.info('🖱️ Clicking "Confirm" in Excel popup...')
        
        # Start waiting for the download BEFORE clicking the final confirm button
        async with page.expect_download() as download_info:
            # Find the "확인" button in the popup. 
            # Using .last because there might be other "확인" buttons on the page (like the filter one), 
            # but the popup is usually on top.
            # A more specific selector would be better if we knew the popup class, but text is usually fine for popups.
            await page.locator('button:has-text("확인")').last.click()
        
        download = await download_info.value

        # 5) Save download file
        suggested_name = download.suggested_filename
        
        # Fix: If filename has no extension (e.g. GUID), append .xls
        if not os.path.splitext(suggested_name)[1]:
            suggested_name += '.xls'
            logger.info(f'⚠️ Filename missing extension. Renamed to: {suggested_name}')

        download_dir = Config.DOWNLOAD_PATH
        
        # Ensure download directory exists
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        save_path = os.path.join(download_dir, suggested_name)

        await download.save_as(save_path)
        logger.info(f'✅ Excel file downloaded: {save_path}')

        return save_path
    except Exception as error:
        logger.error(f'❌ download_excel failed: {str(error)}')
        return None

async def download_excel_popup(page: Page) -> Optional[str]:
    """
    New Flow:
    1. Click "상하단 데이터 전체조회" button
    2. Wait 5 seconds
    3. In the popup, Right Click -> Convert to Excel
    4. Download
    """
    try:
        logger.info('📥 Starting Popup Excel Download Sequence...')

        # 1. Click "상하단 데이터 전체조회" button
        logger.info('🖱️ Clicking "상하단 데이터 전체조회"...')
        # Try to find the button by text
        popup_btn = page.locator('button', has_text='상하단 데이터 전체조회').first
        if not await popup_btn.is_visible():
            # Fallback: try finding by text directly if button tag is not wrapper
            popup_btn = page.locator('text="상하단 데이터 전체조회"').first
        
        await popup_btn.wait_for(state='visible', timeout=5000)
        await popup_btn.click()
        logger.info('✅ "상하단 데이터 전체조회" clicked')

        # 2. Wait for popup to fully load (increased timeout + loading check)
        logger.info('⏳ Waiting for popup data to fully load...')
        
        # Initial wait for popup to appear
        await page.wait_for_timeout(3000)
        
        # Wait for network idle first (most reliable)
        try:
            await page.wait_for_load_state('networkidle', timeout=45000)
            logger.info('  - Network idle detected')
        except Exception:
            logger.warning('  - Network idle timeout (45s)')
        
        # Extra buffer for rendering
        await page.wait_for_timeout(3000)
        logger.info('✅ Popup should be fully loaded')
        
        # Count actual rows in the grid for debugging
        try:
            # Try to count grid rows in popup
            grid_rows = page.locator('tr[data-index], .OBTDataGridBodyRow, [class*="GridRow"], [class*="grid-row"]')
            row_count = await grid_rows.count()
            logger.info(f'📊 Grid rows detected in popup: {row_count}')
        except Exception as e:
            logger.warning(f'  - Could not count grid rows: {e}')
        
        # Take screenshot for debugging (especially for headless mode)
        try:
            import os
            screenshot_dir = './screenshots'
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            screenshot_path = f'{screenshot_dir}/popup_before_download.png'
            await page.screenshot(path=screenshot_path, full_page=False)
            logger.info(f'📸 Screenshot saved: {screenshot_path}')
        except Exception as e:
            logger.warning(f'  - Could not take screenshot: {e}')

        # 2.5. Try to get row count for logging (helps debug missing data)
        try:
            # Look for row count indicator in popup (common patterns)
            count_patterns = [
                'text=/총\\s*\\d+\\s*건/',  # "총 123건"
                'text=/\\d+\\s*건/',         # "123건"
                '[class*="count"]',
                '[class*="total"]'
            ]
            for pattern in count_patterns:
                try:
                    count_elem = page.locator(pattern).last
                    if await count_elem.is_visible():
                        count_text = await count_elem.text_content()
                        logger.info(f'📊 Data count in popup: {count_text}')
                        break
                except Exception:
                    pass
        except Exception:
            pass

        # 3. Right Click in the popup
        # We need to find an element inside the popup to right-click.
        # Usually, the popup has a grid or some content.
        # Let's assume the popup is the focused active window or find a grid inside it.
        
        # Strategy: Find the last opened dialog/window or just click in the center of the screen 
        # if the popup is modal and centered.
        # Or better, look for a grid row in the popup.
        
        logger.info('📍 Attempting right click in popup...')
        
        # Try to find a grid row in the popup (assuming it has similar structure to main grid)
        # We'll try to click somewhat centrally in the latest opened dialog
        
        # Finding the latest dialog
        dialog = page.locator('.OBTDialog, .ui-dialog').last
        if await dialog.is_visible():
            box = await dialog.bounding_box()
            if box:
                # Click in the center of the dialog
                target_x = box['x'] + (box['width'] / 2)
                target_y = box['y'] + (box['height'] / 2)
                
                logger.info(f'📍 Popup found. Right clicking at ({target_x}, {target_y})')
                await page.mouse.click(target_x, target_y, button='right')
            else:
                 # Fallback
                 logger.warning('⚠️ Popup bounding box not found. Clicking center screen.')
                 vp = page.viewport_size
                 await page.mouse.click(vp['width']/2, vp['height']/2, button='right')
        else:
            logger.warning('⚠️ Popup selector not found. Trying generic right click in center.')
            vp = page.viewport_size
            await page.mouse.click(vp['width']/2, vp['height']/2, button='right')

        await page.wait_for_timeout(500)

        # 4. Click "엑셀변환하기" (Convert to Excel)
        logger.info('📄 Clicking "엑셀변환하기"...')
        # Need to be careful to click the one in the new context menu, 
        # essentially the last visible one
        convert_btn = page.locator('text="엑셀변환하기"').last
        await convert_btn.wait_for(state='visible', timeout=3000)
        await convert_btn.click()

        # 5. Confirm download popup
        logger.info('⏳ Waiting for Excel Conversion confirmation...')
        await page.wait_for_timeout(1000)
        
        async with page.expect_download() as download_info:
            # Click Confirm "확인"
            confirm_btn = page.locator('button:has-text("확인")').last
            await confirm_btn.click()
        
        download = await download_info.value
        suggested_name = download.suggested_filename
        if not os.path.splitext(suggested_name)[1]:
            suggested_name += '.xls'
            
        download_dir = Config.DOWNLOAD_PATH
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        save_path = os.path.join(download_dir, suggested_name)
        await download.save_as(save_path)
        
        logger.info(f'✅ Popup Excel file downloaded: {save_path}')

        # 6. Close the popup to return to main screen
        logger.info('❌ Closing popup (Pressing ESC)...')
        await page.keyboard.press('Escape')
        await page.wait_for_timeout(500)
        
        # Wait for dim layer to disappear (ensure popup is closed)
        try:
            # _dimClicker is usually the class for the modal background
            dim_layer = page.locator('._dimClicker').first
            if await dim_layer.is_visible():
                logger.info('  - Dim layer still visible, pressing ESC again...')
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)
        except Exception:
            pass

        return save_path

    except Exception as error:
        logger.error(f'❌ download_excel_popup failed: {str(error)}')
        return None
