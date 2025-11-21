const logger = require('../logger');
const { config } = require('../config');

/**
 * 1단계: 기안일자 필터 설정
 * - 붉은색 박스 (날짜 입력 필드) 클릭
 * - 20250101 ~ 20251231 입력
 * - 엔터
 */
async function setApplicationDate(page) {
  try {
    logger.info('📅 기안일자 필터 설정 중...');

    // 1) 날짜 input들 찾기
    await page.waitForSelector('input.OBTDatePickerRebuild_inputYMD__PtxMy', { timeout: 5000 });
    const dateInputs = page.locator('input.OBTDatePickerRebuild_inputYMD__PtxMy');
    const count = await dateInputs.count();
    logger.info(`🔍 날짜 input 개수: ${count}`);

    if (count === 0) {
      logger.error('❌ 날짜 input을 찾지 못했습니다. 셀렉터를 다시 확인하세요.');
      return false;
    }

    // 2) 시작일 / 종료일 나누기
    const startInput = dateInputs.nth(0);
    const endInput   = count > 1 ? dateInputs.nth(1) : null;

    // 시작일 입력
    logger.debug('시작일 input 클릭...');
    await startInput.click();
    await page.waitForTimeout(200);

    // 기존 값 전체 선택 후 덮어쓰기 (Ctrl+A)
    await startInput.press('Control+A').catch(() => {});
    await startInput.fill('20250101');
    logger.info('✅ 시작일 입력: 20250101');

    await page.waitForTimeout(200);

    if (endInput) {
      // 종료일이 별도 input인 경우
      logger.debug('종료일 input 클릭...');
      await endInput.click();
      await page.waitForTimeout(200);

      await endInput.press('Control+A').catch(() => {});
      await endInput.fill('20251231');
      logger.info('✅ 종료일 입력: 20251231');
    } else {
      // 종료일이 같은 input에 같이 들어가는 구조라면 이 분기 사용
      await startInput.press('Control+A').catch(() => {});
      await startInput.fill('20250101 ~ 20251231');
      logger.info('✅ 기간 입력: 20250101 ~ 20251231');
    }

    await page.waitForTimeout(300);

    // 엔터로 확정
    await page.keyboard.press('Enter');
    logger.info('✅ 엔터 입력');

    await page.waitForTimeout(1000);
    logger.info('✅ 기안일자 필터 설정 완료');
    return true;
  } catch (error) {
    logger.error('❌ setApplicationDate 실패:', error.message);
    logger.error('📍 상세 에러:', error);
    return false;
  }
}


/**
 * 2단계: 결재상태 필터 설정
 * - 결재상태 창 열림
 * - "전체" 체크박스 클릭 (모두 해제)
 * - "결재완료" 체크박스 선택
 * - 확인 버튼 클릭
 */
async function setApprovalStatus(page) {
  try {
    logger.info('✅ 결재상태 필터 설정 중...');

    await page.waitForTimeout(800);

    // "전체" 체크박스 찾기 및 클릭
    logger.debug('"전체" 체크박스 찾기...');
    const checkboxes = page.locator('input[type="checkbox"]');
    const checkboxCount = await checkboxes.count();
    
    let allCheckboxClicked = false;
    for (let i = 0; i < checkboxCount; i++) {
      const label = await checkboxes.nth(i).locator('..').textContent().catch(() => '');
      if (label.includes('전체')) {
        const isChecked = await checkboxes.nth(i).isChecked();
        if (isChecked) {
          await checkboxes.nth(i).click();
          logger.info('✅ "전체" 체크박스 클릭 (모두 해제)');
          allCheckboxClicked = true;
        }
        break;
      }
    }

    await page.waitForTimeout(300);

    // "결재완료" 체크박스 찾기 및 클릭
    logger.debug('"결재완료" 체크박스 찾기...');
    let completeCheckboxClicked = false;
    for (let i = 0; i < checkboxCount; i++) {
      const label = await checkboxes.nth(i).locator('..').textContent().catch(() => '');
      if (label.includes('결재완료')) {
        const isChecked = await checkboxes.nth(i).isChecked();
        if (!isChecked) {
          await checkboxes.nth(i).click();
          logger.info('✅ "결재완료" 체크박스 선택');
          completeCheckboxClicked = true;
        }
        break;
      }
    }

    await page.waitForTimeout(300);

    // 확인 버튼 클릭
    logger.debug('확인 버튼 클릭...');
    const confirmButton = page.locator('button:has-text("확인")').first();
    const confirmVisible = await confirmButton.isVisible().catch(() => false);
    
    if (confirmVisible) {
      await confirmButton.click();
      logger.info('✅ 확인 버튼 클릭');
    }

    await page.waitForTimeout(500);
    logger.info('✅ 결재상태 필터 설정 완료');
    return true;
  } catch (error) {
    logger.error('❌ ... 실패:', error.message);
    logger.error('📍 상세 에러:', error);  // ← 상세 에러 출력
    return false;  // ← false 반환해서 실제 실패 알리기
  }
}

/**
 * 3단계: 기안부서, 기안자 필터 삭제
 * - 엔터 3번
 * - Delete 1번
 * - 엔터 1번
 * - Delete 1번
 * - 엔터 1번
 */
async function clearFilters(page) {
  try {
    logger.info('🗑️  기안부서, 기안자 필터 삭제 중...');

    await page.waitForTimeout(300);

    // 엔터 3번
    await page.keyboard.press('Enter');
    await page.keyboard.press('Enter');
    await page.keyboard.press('Enter');
    logger.info('✅ 엔터 3번 입력');

    await page.waitForTimeout(300);

    // Delete 1번
    await page.keyboard.press('Delete');
    logger.info('✅ Delete 1번 입력');

    await page.waitForTimeout(300);

    // 엔터 1번
    await page.keyboard.press('Enter');
    logger.info('✅ 엔터 1번 입력');

    await page.waitForTimeout(300);

    // Delete 1번
    await page.keyboard.press('Delete');
    logger.info('✅ Delete 1번 입력');

    await page.waitForTimeout(300);

    // 엔터 1번
    await page.keyboard.press('Enter');
    logger.info('✅ 엔터 1번 입력');

    await page.waitForTimeout(500);
    logger.info('✅ 필터 삭제 완료');
    return true;
  } catch (error) {
    logger.error('❌ ... 실패:', error.message);
    logger.error('📍 상세 에러:', error);  // ← 상세 에러 출력
    return false;  // ← false 반환해서 실제 실패 알리기
  }
}

/**
 * 4단계: 전표발행여부 필터 설정
 * - 전표발행여부 창 열림
 * - "전체" 체크박스 클릭 (모두 해제)
 * - "전표(승인)" 체크박스 선택
 * - 확인 버튼 클릭
 */
async function setDocumentStatus(page) {
  try {
    logger.info('📄 전표발행여부 필터 설정 중...');

    await page.waitForTimeout(800);

    // "전체" 체크박스 찾기 및 클릭
    logger.debug('"전체" 체크박스 찾기...');
    const checkboxes = page.locator('input[type="checkbox"]');
    const checkboxCount = await checkboxes.count();
    
    let allCheckboxClicked = false;
    for (let i = 0; i < checkboxCount; i++) {
      const label = await checkboxes.nth(i).locator('..').textContent().catch(() => '');
      if (label.includes('전체')) {
        const isChecked = await checkboxes.nth(i).isChecked();
        if (isChecked) {
          await checkboxes.nth(i).click();
          logger.info('✅ "전체" 체크박스 클릭 (모두 해제)');
          allCheckboxClicked = true;
        }
        break;
      }
    }

    await page.waitForTimeout(300);

    // "전표(승인)" 체크박스 찾기 및 클릭
    logger.debug('"전표(승인)" 체크박스 찾기...');
    let approvalCheckboxClicked = false;
    for (let i = 0; i < checkboxCount; i++) {
      const label = await checkboxes.nth(i).locator('..').textContent().catch(() => '');
      if (label.includes('전표') || label.includes('승인')) {
        const isChecked = await checkboxes.nth(i).isChecked();
        if (!isChecked) {
          await checkboxes.nth(i).click();
          logger.info('✅ "전표(승인)" 체크박스 선택');
          approvalCheckboxClicked = true;
        }
        break;
      }
    }

    await page.waitForTimeout(300);

    // 확인 버튼 클릭
    logger.debug('확인 버튼 클릭...');
    const confirmButton = page.locator('button:has-text("확인")').first();
    const confirmVisible = await confirmButton.isVisible().catch(() => false);
    
    if (confirmVisible) {
      await confirmButton.click();
      logger.info('✅ 확인 버튼 클릭');
    }

    await page.waitForTimeout(500);
    logger.info('✅ 전표발행여부 필터 설정 완료');
    return true;
  } catch (error) {
    logger.error('❌ ... 실패:', error.message);
    logger.error('📍 상세 에러:', error);  // ← 상세 에러 출력
    return false;  // ← false 반환해서 실제 실패 알리기
  }
}

/**
 * 5단계: 데이터 조회
 * - F10 키 누르기
 */
async function searchData(page) {
  try {
    logger.info('🔍 데이터 조회 중...');

    await page.waitForTimeout(500);

    // F10 키 누르기
    await page.keyboard.press('F10');
    logger.info('✅ F10 키 입력');

    // 데이터 로드 대기
    logger.info('⏳ 데이터 조회 중...');
    await page.waitForTimeout(2000);

    try {
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {
        logger.warn('⚠️ 네트워크 로드 타임아웃');
      });
    } catch (e) {
      logger.warn('⚠️ 데이터 조회 중 타임아웃');
    }

    logger.info('✅ 데이터 조회 완료');
    return true;
  } catch (error) {
    logger.error('❌ ... 실패:', error.message);
    logger.error('📍 상세 에러:', error);  // ← 상세 에러 출력
    return false;  // ← false 반환해서 실제 실패 알리기
  }
}

module.exports = {
  setApplicationDate,
  setApprovalStatus,
  clearFilters,
  setDocumentStatus,
  searchData,
};