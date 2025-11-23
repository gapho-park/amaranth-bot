const logger = require('../logger');
const { config } = require('../config');

/**
 * 1단계: 기안일자 필터 설정
 * - 날짜 입력 필드(기안일자) 클릭
 * - 20250101 ~ 20251231 입력
 * - 엔터로 확정
 */
async function setApplicationDate(page) {
  try {
    logger.info('📅 기안일자 필터 설정 중...');

    // 날짜 input들 기다렸다가 가져오기
    await page.waitForSelector('input.OBTDatePickerRebuild_inputYMD__PtxMy', { timeout: 5000 });
    const dateInputs = page.locator('input.OBTDatePickerRebuild_inputYMD__PtxMy');
    const count = await dateInputs.count();
    logger.info(`🔍 날짜 input 개수: ${count}`);

    if (count === 0) {
      logger.error('❌ 날짜 input을 찾지 못했습니다. 셀렉터를 다시 확인하세요.');
      return false;
    }

    const startInput = dateInputs.nth(0);
    const endInput   = count > 1 ? dateInputs.nth(1) : null;

    // 시작일 입력
    logger.debug('시작일 input 클릭...');
    await startInput.click();
    await page.waitForTimeout(200);

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
      // 하나의 input에 범위를 넣는 구조라면 이 분기 사용
      await startInput.press('Control+A').catch(() => {});
      await startInput.fill('20250101 ~ 20251231');
      logger.info('✅ 기간 입력: 20250101 ~ 20251231');
    }

    await page.waitForTimeout(300);

    // 날짜 필터 확정용 엔터
    await page.keyboard.press('Enter');
    logger.info('✅ 기안일자 필터 엔터로 확정');

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
 * 2단계: 기안부서, 기안자 필터 삭제
 * - (기안일자 입력 후 상태에서)
 * - 엔터 4번 (탭 이동)
 * - Delete 1번 + Enter 1번 (기안부서 삭제)
 * - Delete 1번 + Enter 1번 (기안자 삭제)
 */
async function clearFilters(page) {
  try {
    logger.info('🗑️  기안부서, 기안자 필터 삭제 시퀀스 시작...');

    await page.waitForTimeout(300);

    // 1) 엔터 4번 (다음 필터들 순차 이동)
    logger.info('↩️ 엔터 4번 입력으로 필터 칸 이동...');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(150);

    await page.keyboard.press('Enter');
    await page.waitForTimeout(150);

    await page.keyboard.press('Enter');
    await page.waitForTimeout(150);

    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);

    // 2) 기안부서에 도달했다고 가정하고 Del + Enter
    logger.info('🏢 기안부서 필터 삭제 (Delete → Enter)...');
    await page.keyboard.press('Delete');
    await page.waitForTimeout(200);

    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);

    // 3) 기안자에 도달했다고 가정하고 Del + Enter
    logger.info('👤 기안자 필터 삭제 (Delete → Enter)...');
    await page.keyboard.press('Delete');
    await page.waitForTimeout(200);

    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);

    logger.info('✅ 기안부서/기안자 필터 삭제 완료');
    return true;
  } catch (error) {
    logger.error('❌ clearFilters 실패:', error.message);
    logger.error('📍 상세 에러:', error);
    return false;
  }
}

/**
 * 3단계: 전표발행여부 필터 설정
 * - 전표발행여부 팝업/창이 떠 있다고 가정
 * - "전체" 클릭 (모두 해제)
 * - "전표(승인)" 클릭 (선택)
 * - "확인" 버튼 클릭
 */
async function setDocumentStatus(page) {
  try {
    logger.info('📄 전표발행여부 필터 설정 중...');

    // 팝업이 뜰 시간 약간 대기
    await page.waitForTimeout(800);

    // 1) "전체" 라벨 클릭 (모두 해제)
    logger.debug('"전체" 라벨 찾는 중...');
    const allLabel = page.locator('label', { hasText: '전체' }).first();
    await allLabel.waitFor({ state: 'visible', timeout: 5000 });
    await allLabel.click();
    logger.info('✅ "전체" 클릭 (체크 해제)');

    await page.waitForTimeout(300);

    // 2) "전표(승인)" 항목 클릭
    logger.debug('"전표(승인)" 항목 찾는 중...');
    const approvalItem = page.getByText('전표(승인)', { exact: true }).first();
    await approvalItem.waitFor({ state: 'visible', timeout: 5000 });
    await approvalItem.click();
    logger.info('✅ "전표(승인)" 선택');

    await page.waitForTimeout(300);

    // 3) "확인" 버튼 클릭
    logger.debug('"확인" 버튼 찾는 중...');
    const confirmButton = page.locator('button.OBTMultiDropDownList_bottomButton__1xAmc').first();
    await confirmButton.waitFor({ state: 'visible', timeout: 5000 });
    await confirmButton.click();
    logger.info('✅ "확인" 버튼 클릭');

    await page.waitForTimeout(500);
    logger.info('✅ 전표발행여부 필터 설정 완료');
    return true;
  } catch (error) {
    logger.error('❌ setDocumentStatus 실패:', error.message);
    logger.error('📍 상세 에러:', error);
    return false;
  }
}


/**
 * 4단계: 데이터 조회
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
    logger.error('❌ searchData 실패:', error.message);
    logger.error('📍 상세 에러:', error);
    return false;
  }
}

/**
 * 5단계: 그리드 우클릭 → 엑셀변환하기 → 파일 다운로드
 */
async function downloadExcel(page) {
  try {
    logger.info('📥 엑셀 다운로드 시도 중...');

    // 1) 그리드 안의 아무 셀 하나 잡기
    // 예시로, 첫 번째 행의 "회계단위" 텍스트 기준으로 셀을 잡아봄
    // (너네 화면 텍스트에 맞게 아래 텍스트는 필요하면 바꿔도 됨)
    const gridCell = page.getByText('라포랩스', { exact: false }).first();

    await gridCell.waitFor({ state: 'visible', timeout: 5000 });

    // 2) 해당 셀에서 우클릭 (컨텍스트 메뉴 열기)
    logger.info('🖱️ 그리드 셀 우클릭 (컨텍스트 메뉴 열기)...');
    await gridCell.click({ button: 'right' });
    await page.waitForTimeout(300);

    // 3) 엑셀변환하기 클릭 + 다운로드 이벤트 기다리기
    logger.info('📄 "엑셀변환하기" 메뉴 클릭...');

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByText('엑셀변환하기', { exact: true }).click()
    ]);

    // 4) 다운로드 파일 저장 위치 설정 (원하면 config로 빼도 됨)
    const suggestedName = download.suggestedFilename();
    const downloadDir = config.downloadDir || path.join(__dirname, '..', 'downloads');
    const savePath = path.join(downloadDir, suggestedName);

    await download.saveAs(savePath);
    logger.info(`✅ 엑셀 파일 다운로드 완료: ${savePath}`);

    return true;
  } catch (error) {
    logger.error('❌ downloadExcel 실패:', error.message);
    logger.error('📍 상세 에러:', error);
    return false;
  }
}



module.exports = {
  setApplicationDate,
  clearFilters,
  setDocumentStatus,
  searchData,
  downloadExcel,
};
