from playwright.async_api import Page
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
    Step 2: Clear Department and Drafter Filters
    - (From Application Date input state)
    - Enter 4 times (Tab move)
    - Delete 1 time + Enter 1 time (Clear Department)
    - Delete 1 time + Enter 1 time (Clear Drafter)
    """
    try:
        logger.info('🗑️  Starting Clear Filters Sequence...')

        await page.wait_for_timeout(300)

        # 1) Enter 4 times (Move to next filters)
        logger.info('↩️ Pressing Enter 4 times to move...')
        for _ in range(4):
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(150)
        
        await page.wait_for_timeout(300)

        # 2) Clear Department (Delete + Enter)
        logger.info('🏢 Clearing Department Filter (Delete → Enter)...')
        await page.keyboard.press('Delete')
        await page.wait_for_timeout(200)
        await page.keyboard.press('Enter')
        await page.wait_for_timeout(300)

        # 3) Clear Drafter (Delete + Enter)
        logger.info('👤 Clearing Drafter Filter (Delete → Enter)...')
        await page.keyboard.press('Delete')
        await page.wait_for_timeout(200)
        await page.keyboard.press('Enter')
        await page.wait_for_timeout(500)

        logger.info('✅ Department/Drafter Filters cleared')
        return True
    except Exception as error:
        logger.error(f'❌ clear_filters failed: {str(error)}')
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

async def download_excel(page: Page) -> bool:
    """
    Step 5: Right click grid → Convert to Excel → Download file
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

        return True
    except Exception as error:
        logger.error(f'❌ download_excel failed: {str(error)}')
        return False
