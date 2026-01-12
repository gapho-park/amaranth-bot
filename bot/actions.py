from playwright.async_api import Page
from typing import Optional
from logger import logger
from config import Config
import os
import datetime


# =====================================================
# 통장 자료수집 관련 함수들 (Data Collection Functions)
# =====================================================

async def dismiss_notice_popup(page: Page) -> bool:
    """
    공지 팝업창 닫기
    
    하루에 한번 뜨는 공지 팝업창을 처리:
    1. "오늘 하루 그만 보기" 체크박스 클릭
    2. "취소" 버튼 클릭
    """
    try:
        logger.info('📢 Checking for notice popup...')
        
        await page.wait_for_timeout(1000)
        
        # 공지 팝업 확인 (여러 방법으로 시도)
        popup_found = False
        
        # Method 1: "공지" 타이틀이 있는 팝업 확인
        try:
            notice_title = page.locator('text="공지"').first
            if await notice_title.is_visible(timeout=2000):
                popup_found = True
                logger.info('✅ Notice popup detected')
        except Exception:
            pass
        
        # Method 2: "오늘 하루 그만 보기" 텍스트로 팝업 확인
        if not popup_found:
            try:
                checkbox_text = page.locator('text="오늘 하루 그만 보기"').first
                if await checkbox_text.is_visible(timeout=1000):
                    popup_found = True
                    logger.info('✅ Notice popup detected (via checkbox text)')
            except Exception:
                pass
        
        if not popup_found:
            logger.info('ℹ️ No notice popup found, continuing...')
            return True
        
        # Step 1: "오늘 하루 그만 보기" 체크박스 클릭
        logger.info('☑️ Clicking "오늘 하루 그만 보기" checkbox...')
        
        checkbox_clicked = False
        
        try:
            # 체크박스 또는 레이블 클릭
            checkbox_selectors = [
                'input[type="checkbox"]',
                'text="오늘 하루 그만 보기"',
                'label:has-text("오늘 하루 그만 보기")',
                '[class*="checkbox"]:has-text("오늘 하루 그만 보기")',
            ]
            
            for selector in checkbox_selectors:
                try:
                    checkbox = page.locator(selector).last  # 팝업 내 체크박스는 보통 마지막
                    if await checkbox.is_visible(timeout=1000):
                        await checkbox.click()
                        logger.info(f'✅ Checkbox clicked ({selector})')
                        checkbox_clicked = True
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f'Checkbox click attempt failed: {str(e)}')
        
        if not checkbox_clicked:
            logger.warning('⚠️ Could not click checkbox, trying to close popup anyway...')
        
        await page.wait_for_timeout(300)
        
        # Step 2: "취소" 버튼 클릭
        logger.info('🖱️ Clicking "취소" button...')
        
        cancel_clicked = False
        
        try:
            cancel_selectors = [
                'button:has-text("취소")',
                'text="취소"',
                '[class*="button"]:has-text("취소")',
            ]
            
            for selector in cancel_selectors:
                try:
                    cancel_btn = page.locator(selector).last  # 팝업 내 버튼
                    if await cancel_btn.is_visible(timeout=1000):
                        await cancel_btn.click()
                        logger.info(f'✅ Cancel button clicked ({selector})')
                        cancel_clicked = True
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f'Cancel button click attempt failed: {str(e)}')
        
        # 취소 버튼 실패시 ESC 키로 닫기 시도
        if not cancel_clicked:
            try:
                await page.keyboard.press('Escape')
                logger.info('✅ Popup closed via ESC key')
                cancel_clicked = True
            except Exception:
                pass
        
        if not cancel_clicked:
            logger.warning('⚠️ Could not close notice popup')
            return False
        
        await page.wait_for_timeout(500)
        logger.info('✅ Notice popup dismissed')
        return True
        
    except Exception as error:
        logger.error(f'❌ dismiss_notice_popup failed: {str(error)}')
        return False


async def click_data_collection_tab(page: Page) -> bool:
    """
    자료수집 탭 클릭
    
    메뉴에 진입하면 3가지 탭이 있음:
    - 최근수집현황
    - 자료수집 (클릭 대상)
    - 오류현황
    """
    try:
        logger.info('📑 Clicking 자료수집 tab...')
        
        await page.wait_for_timeout(1000)
        
        # 자료수집 탭 찾기 (여러 방법 시도)
        tab_click_success = False
        
        # Method 1: 정확한 텍스트로 탭 찾기
        try:
            tab = page.get_by_text('자료수집', exact=True).first
            if await tab.is_visible(timeout=3000):
                await tab.click()
                logger.info('✅ 자료수집 tab clicked (Method 1: exact text)')
                tab_click_success = True
        except Exception as e:
            logger.debug(f'Method 1 failed: {str(e)}')
        
        # Method 2: 탭 컨테이너 내에서 찾기
        if not tab_click_success:
            try:
                # 탭 영역에서 자료수집 찾기
                tab_selectors = [
                    '[class*="tab"] :text-is("자료수집")',
                    '[role="tab"]:has-text("자료수집")',
                    'button:has-text("자료수집")',
                    'a:has-text("자료수집")',
                ]
                
                for selector in tab_selectors:
                    try:
                        tab = page.locator(selector).first
                        if await tab.is_visible(timeout=1000):
                            await tab.click()
                            logger.info(f'✅ 자료수집 tab clicked (Method 2: {selector})')
                            tab_click_success = True
                            break
                    except Exception:
                        continue
            except Exception as e:
                logger.debug(f'Method 2 failed: {str(e)}')
        
        # Method 3: 모든 자료수집 텍스트 중 클릭 가능한 것 찾기
        if not tab_click_success:
            try:
                all_tabs = page.locator('text="자료수집"')
                count = await all_tabs.count()
                logger.debug(f'Found {count} "자료수집" elements')
                
                for i in range(count):
                    try:
                        el = all_tabs.nth(i)
                        if await el.is_visible():
                            await el.click()
                            logger.info(f'✅ 자료수집 tab clicked (Method 3: index {i})')
                            tab_click_success = True
                            break
                    except Exception:
                        continue
            except Exception as e:
                logger.debug(f'Method 3 failed: {str(e)}')
        
        if not tab_click_success:
            raise Exception('Could not find 자료수집 tab')
        
        # 탭 전환 후 대기
        await page.wait_for_timeout(1000)
        logger.info('✅ 자료수집 tab activated')
        return True
        
    except Exception as error:
        logger.error(f'❌ click_data_collection_tab failed: {str(error)}')
        return False


async def select_bankbook_filter(page: Page) -> bool:
    """
    증빙구분 토글에서 '통장' 선택
    
    간단한 키보드 조작:
    1. 증빙구분 토글창 클릭 (열기)
    2. 방향키 아래 한 번 (통장 선택)
    3. 엔터 (확정)
    """
    try:
        logger.info('🏦 Selecting 통장 filter in 증빙구분...')
        
        await page.wait_for_timeout(500)
        
        # Step 1: 증빙구분 토글창 클릭 (열기)
        logger.info('🔽 Opening 증빙구분 dropdown...')
        
        label = page.locator('text="증빙구분"').first
        if await label.is_visible(timeout=3000):
            box = await label.bounding_box()
            if box:
                # 레이블 오른쪽 80px 지점 클릭 (드롭다운 위치)
                target_x = box['x'] + box['width'] + 80
                target_y = box['y'] + (box['height'] / 2)
                await page.mouse.click(target_x, target_y)
                logger.info(f'✅ 증빙구분 dropdown clicked at ({target_x:.0f}, {target_y:.0f})')
        else:
            raise Exception('Could not find 증빙구분 label')
        
        await page.wait_for_timeout(300)
        
        # Step 2: 방향키 아래로 한 번 (전체 → 통장)
        logger.info('⬇️ Arrow Down to select 통장...')
        await page.keyboard.press('ArrowDown')
        await page.wait_for_timeout(200)
        
        # Step 3: 엔터로 확정
        logger.info('↩️ Enter to confirm...')
        await page.keyboard.press('Enter')
        await page.wait_for_timeout(300)
        
        # Step 4: 추가 옵션 확인 엔터
        logger.info('↩️ Enter again for additional option...')
        await page.keyboard.press('Enter')
        logger.info('✅ 통장 selected')
        
        # Step 4: 로딩 대기 (10초)
        logger.info('⏳ Waiting for data load (10 seconds)...')
        await page.wait_for_timeout(10000)
        
        # 네트워크 안정화 대기
        try:
            await page.wait_for_load_state('networkidle', timeout=15000)
            logger.info('✅ Network idle detected')
        except Exception:
            logger.warning('⚠️ Network idle timeout, continuing...')
        
        logger.info('✅ 통장 filter selected and data loaded')
        return True
        
    except Exception as error:
        logger.error(f'❌ select_bankbook_filter failed: {str(error)}')
        return False


async def click_batch_date_apply_button(page: Page) -> bool:
    """
    수집일 일괄적용 버튼 클릭
    
    우측상단에 있는 "수집일 일괄적용" 버튼을 클릭
    확인 팝업이 뜨면 확인 누르기
    """
    try:
        logger.info('📅 Clicking 수집일 일괄적용 button...')
        
        await page.wait_for_timeout(500)
        
        # Step 1: 수집일 일괄적용 버튼 찾아서 클릭
        button_click_success = False
        
        try:
            button_selectors = [
                'button:has-text("수집일 일괄적용")',
                'text="수집일 일괄적용"',
                '[class*="button"]:has-text("수집일 일괄적용")',
            ]
            
            for selector in button_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=3000):
                        await button.click()
                        logger.info(f'✅ 수집일 일괄적용 button clicked ({selector})')
                        button_click_success = True
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f'Button click failed: {str(e)}')
        
        if not button_click_success:
            raise Exception('Could not find 수집일 일괄적용 button')
        
        # Step 2: 확인 팝업 대기 및 클릭
        logger.info('⏳ Waiting for confirmation popup...')
        await page.wait_for_timeout(1000)
        
        # 확인 버튼 찾아서 클릭
        try:
            confirm_btn = page.locator('button:has-text("확인")').last
            if await confirm_btn.is_visible(timeout=3000):
                await confirm_btn.click()
                logger.info('✅ Confirmation popup - 확인 clicked')
            else:
                logger.info('ℹ️ No confirmation popup appeared, continuing...')
        except Exception as e:
            logger.debug(f'Confirmation popup handling: {str(e)}')
        
        await page.wait_for_timeout(500)
        logger.info('✅ 수집일 일괄적용 button process completed')
        return True
        
    except Exception as error:
        logger.error(f'❌ click_batch_date_apply_button failed: {str(error)}')
        return False


async def fill_collection_dates(page: Page, start_date: str, end_date: str) -> bool:
    """
    수집시작일/종료일 입력 후 적용 버튼 클릭
    
    Args:
        start_date: 수집시작일 (형식: YYYYMMDD, 예: 20260112)
        end_date: 수집종료일 (형식: YYYYMMDD, 예: 20260112)
    """
    try:
        logger.info(f'📅 Filling collection dates: {start_date} ~ {end_date}...')
        
        await page.wait_for_timeout(1000)
        
        # Step 1: 수집시작일 입력
        logger.info('📝 Entering 수집시작일...')
        
        start_date_success = False
        
        # Method 1: 수집시작일 레이블 근처의 입력 필드 찾기
        try:
            # 수집시작일 입력 필드 찾기 (여러 방법)
            start_input_selectors = [
                'text="수집시작일" >> .. >> input',
                '[class*="DatePicker"] input',
                'input[class*="date"]',
                'input[type="text"]',
            ]
            
            # 먼저 수집시작일 레이블 찾기
            start_label = page.locator('text="수집시작일"').first
            if await start_label.is_visible(timeout=3000):
                # 레이블의 부모/형제 요소에서 input 찾기
                parent = start_label.locator('xpath=ancestor::*[1]/following-sibling::*[1]//input').first
                if not await parent.is_visible(timeout=1000):
                    parent = start_label.locator('xpath=../following-sibling::*//input').first
                if not await parent.is_visible(timeout=1000):
                    parent = start_label.locator('xpath=../..//input').first
                
                if await parent.is_visible(timeout=1000):
                    await parent.click()
                    await page.wait_for_timeout(200)
                    await parent.press('Control+A')
                    await parent.fill(start_date)
                    logger.info(f'✅ 수집시작일 entered: {start_date}')
                    start_date_success = True
        except Exception as e:
            logger.debug(f'Method 1 for start date failed: {str(e)}')
        
        # Method 2: 팝업 내 첫 번째 날짜 입력 필드
        if not start_date_success:
            try:
                # 팝업/다이얼로그 내 날짜 입력 필드 찾기
                date_inputs = page.locator('[class*="Dialog"] input, [class*="Popup"] input, [class*="Modal"] input, [role="dialog"] input')
                count = await date_inputs.count()
                logger.debug(f'Found {count} date input fields in popup')
                
                if count >= 1:
                    first_input = date_inputs.nth(0)
                    await first_input.click()
                    await page.wait_for_timeout(200)
                    await first_input.press('Control+A')
                    await first_input.fill(start_date)
                    logger.info(f'✅ 수집시작일 entered (Method 2): {start_date}')
                    start_date_success = True
            except Exception as e:
                logger.debug(f'Method 2 for start date failed: {str(e)}')
        
        # Method 3: 날짜 형식 input 필드 찾기
        if not start_date_success:
            try:
                date_inputs = page.locator('input[class*="YMD"], input[class*="date"], input[placeholder*="날짜"]')
                count = await date_inputs.count()
                logger.debug(f'Found {count} date-like input fields')
                
                if count >= 1:
                    first_input = date_inputs.nth(0)
                    await first_input.click()
                    await page.wait_for_timeout(200)
                    await first_input.press('Control+A')
                    await first_input.fill(start_date)
                    logger.info(f'✅ 수집시작일 entered (Method 3): {start_date}')
                    start_date_success = True
            except Exception as e:
                logger.debug(f'Method 3 for start date failed: {str(e)}')
        
        if not start_date_success:
            raise Exception('Could not find 수집시작일 input field')
        
        await page.wait_for_timeout(300)
        
        # Step 2: 수집종료일 입력
        logger.info('📝 Entering 수집종료일...')
        
        end_date_success = False
        
        # Method 1: 수집종료일 레이블 근처의 입력 필드 찾기
        try:
            end_label = page.locator('text="수집종료일"').first
            if await end_label.is_visible(timeout=3000):
                parent = end_label.locator('xpath=ancestor::*[1]/following-sibling::*[1]//input').first
                if not await parent.is_visible(timeout=1000):
                    parent = end_label.locator('xpath=../following-sibling::*//input').first
                if not await parent.is_visible(timeout=1000):
                    parent = end_label.locator('xpath=../..//input').first
                
                if await parent.is_visible(timeout=1000):
                    await parent.click()
                    await page.wait_for_timeout(200)
                    await parent.press('Control+A')
                    await parent.fill(end_date)
                    logger.info(f'✅ 수집종료일 entered: {end_date}')
                    end_date_success = True
        except Exception as e:
            logger.debug(f'Method 1 for end date failed: {str(e)}')
        
        # Method 2: 팝업 내 두 번째 날짜 입력 필드
        if not end_date_success:
            try:
                date_inputs = page.locator('[class*="Dialog"] input, [class*="Popup"] input, [class*="Modal"] input, [role="dialog"] input')
                count = await date_inputs.count()
                
                if count >= 2:
                    second_input = date_inputs.nth(1)
                    await second_input.click()
                    await page.wait_for_timeout(200)
                    await second_input.press('Control+A')
                    await second_input.fill(end_date)
                    logger.info(f'✅ 수집종료일 entered (Method 2): {end_date}')
                    end_date_success = True
            except Exception as e:
                logger.debug(f'Method 2 for end date failed: {str(e)}')
        
        # Method 3: 날짜 형식 input 필드 두 번째 것
        if not end_date_success:
            try:
                date_inputs = page.locator('input[class*="YMD"], input[class*="date"], input[placeholder*="날짜"]')
                count = await date_inputs.count()
                
                if count >= 2:
                    second_input = date_inputs.nth(1)
                    await second_input.click()
                    await page.wait_for_timeout(200)
                    await second_input.press('Control+A')
                    await second_input.fill(end_date)
                    logger.info(f'✅ 수집종료일 entered (Method 3): {end_date}')
                    end_date_success = True
            except Exception as e:
                logger.debug(f'Method 3 for end date failed: {str(e)}')
        
        if not end_date_success:
            raise Exception('Could not find 수집종료일 input field')
        
        await page.wait_for_timeout(300)
        
        # Step 3: 적용 버튼 클릭
        logger.info('🖱️ Clicking 적용 button...')
        
        apply_success = False
        
        try:
            apply_selectors = [
                'button:has-text("적용")',
                'text="적용"',
                '[class*="button"]:has-text("적용")',
            ]
            
            for selector in apply_selectors:
                try:
                    apply_btn = page.locator(selector).last
                    if await apply_btn.is_visible(timeout=2000):
                        await apply_btn.click()
                        logger.info(f'✅ 적용 button clicked ({selector})')
                        apply_success = True
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f'Apply button click failed: {str(e)}')
        
        if not apply_success:
            raise Exception('Could not find 적용 button')
        
        # 적용 후 처리 대기
        await page.wait_for_timeout(2000)
        
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except Exception:
            logger.warning('⚠️ Network idle timeout after apply')
        
        logger.info('✅ Collection dates filled and applied successfully')
        return True
        
    except Exception as error:
        logger.error(f'❌ fill_collection_dates failed: {str(error)}')
        return False


async def click_data_collection_and_auto_journalize(page: Page) -> bool:
    """
    자료수집 및 자동분개 버튼 클릭 (선택사항)
    
    수집일 적용 후 실제 자료수집을 실행하려면 이 버튼을 클릭
    """
    try:
        logger.info('📊 Clicking 자료수집 및 자동분개 button...')
        
        await page.wait_for_timeout(500)
        
        button_click_success = False
        
        try:
            button_selectors = [
                'button:has-text("자료수집 및 자동분개")',
                'text="자료수집 및 자동분개"',
                '[class*="button"]:has-text("자료수집 및 자동분개")',
            ]
            
            for selector in button_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=3000):
                        await button.click()
                        logger.info(f'✅ 자료수집 및 자동분개 button clicked ({selector})')
                        button_click_success = True
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f'Button click failed: {str(e)}')
        
        if not button_click_success:
            raise Exception('Could not find 자료수집 및 자동분개 button')
        
        # 팝업창 확인 버튼 클릭
        logger.info('⏳ Waiting for confirmation popup...')
        await page.wait_for_timeout(1000)
        
        try:
            confirm_btn = page.locator('button:has-text("확인")').last
            if await confirm_btn.is_visible(timeout=3000):
                await confirm_btn.click()
                logger.info('✅ Confirmation popup - 확인 clicked')
        except Exception as e:
            logger.debug(f'Confirmation popup handling: {str(e)}')
        
        # 처리 완료 대기 (자료수집은 시간이 걸릴 수 있음)
        logger.info('⏳ Waiting for data collection process...')
        await page.wait_for_timeout(5000)
        
        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
        except Exception:
            logger.warning('⚠️ Network idle timeout during data collection')
        
        logger.info('✅ 자료수집 및 자동분개 process completed')
        return True
        
    except Exception as error:
        logger.error(f'❌ click_data_collection_and_auto_journalize failed: {str(error)}')
        return False


# =====================================================
# 지출결의현황 관련 함수들 (Expenditure Resolution Functions)
# =====================================================

async def set_application_date(page: Page) -> bool:
    """
    Step 1: Set Application Date Filter
    - Click date input field (Application Date)
    - Enter 20250101 ~ 20261231
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
            await end_input.fill('20261231')
            logger.info('✅ End date entered: 20261231')
        else:
            # If range is in one input
            try:
                await start_input.press('Control+A')
            except Exception:
                pass
            await start_input.fill('20250101 ~ 20261231')
            logger.info('✅ Date range entered: 20250101 ~ 20261231')

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
        
        # ===== Load ALL data in virtual grid using Ctrl+End =====
        # Amaranth popup uses lazy loading - Ctrl+End jumps to last row and forces all data to load
        logger.info('📜 Loading all data in popup grid (Ctrl+End)...')
        
        try:
            # Click inside the popup to give it focus, then press Ctrl+End
            # Find popup title and click below it (inside grid area)
            popup_title = page.locator('text="상하단 데이터 전체조회"').last
            if await popup_title.is_visible():
                box = await popup_title.bounding_box()
                if box:
                    # Click inside the grid area (below the title)
                    target_x = box['x'] + 300
                    target_y = box['y'] + 150
                    await page.mouse.click(target_x, target_y)
                    logger.info(f'  - Clicked inside popup grid at ({target_x:.0f}, {target_y:.0f})')
            
            await page.wait_for_timeout(300)
            
            # Ctrl+End: Jump to last row (triggers full data load)
            await page.keyboard.press('Control+End')
            logger.info('  - Ctrl+End pressed (jump to last row)')
            
            # Wait for data to load
            await page.wait_for_timeout(2000)
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
                logger.info('  - Network idle after Ctrl+End')
            except Exception:
                pass
            
            logger.info('✅ All data loaded')
            
        except Exception as scroll_error:
            logger.warning(f'⚠️ Data loading had issues: {scroll_error}')
        
        # Count actual rows in the grid for debugging
        try:
            # Try multiple selectors for grid rows (Amaranth uses various patterns)
            row_selectors = [
                'tr[data-index]',
                '.OBTDataGridBodyRow',
                '[class*="GridRow"]',
                '[class*="grid-row"]',
                '.dx-data-row',
                'tr.dx-row',
                '[class*="DataRow"]',
                'tbody tr',  # Generic table rows
            ]
            
            total_rows = 0
            matched_selector = None
            for selector in row_selectors:
                try:
                    grid_rows = page.locator(selector)
                    count = await grid_rows.count()
                    if count > total_rows:
                        total_rows = count
                        matched_selector = selector
                except Exception:
                    continue
            
            if total_rows > 0:
                logger.info(f'📊 Grid rows detected in popup: {total_rows} (via {matched_selector})')
            else:
                logger.warning(f'📊 Grid rows detected in popup: 0 (no matching selector)')
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
        logger.info('📍 Attempting right click in popup...')
        
        # Try multiple dialog/popup selectors (Amaranth 10 uses various patterns)
        popup_selectors = [
            '.OBTDialog',
            '.ui-dialog', 
            '[role="dialog"]',
            '.modal-content',
            '.popup',
            '.OBTPopup',
            'div[class*="Dialog"]',
            'div[class*="Popup"]',
            'div[class*="Modal"]',
            '.AllGridPopup',
            'div[class*="AllGrid"]',
        ]
        
        popup_found = False
        for selector in popup_selectors:
            try:
                dialog = page.locator(selector).last
                if await dialog.is_visible(timeout=500):
                    box = await dialog.bounding_box()
                    if box and box['width'] > 100 and box['height'] > 100:
                        target_x = box['x'] + (box['width'] / 2)
                        target_y = box['y'] + (box['height'] / 2)
                        logger.info(f'📍 Popup found with selector "{selector}". Right clicking at ({target_x:.0f}, {target_y:.0f})')
                        await page.mouse.click(target_x, target_y, button='right')
                        popup_found = True
                        break
            except Exception:
                continue
        
        if not popup_found:
            # Fallback: Look for the popup title "상하단 데이터 전체조회"
            try:
                popup_title = page.locator('text="상하단 데이터 전체조회"').last
                if await popup_title.is_visible():
                    box = await popup_title.bounding_box()
                    if box:
                        target_x = box['x'] + 200
                        target_y = box['y'] + 200
                        logger.info(f'📍 Found popup by title. Right clicking at ({target_x:.0f}, {target_y:.0f})')
                        await page.mouse.click(target_x, target_y, button='right')
                        popup_found = True
            except Exception:
                pass
        
        if not popup_found:
            logger.warning('⚠️ No popup selector matched. Falling back to center-right of screen.')
            vp = page.viewport_size
            await page.mouse.click(vp['width'] * 0.6, vp['height'] * 0.5, button='right')

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
