const logger = require('../logger');
const { config } = require('../config');

async function goToAccounting(page) {
  try {
    logger.info('📍 지출결의현황으로 이동 중...');

    // 1단계: 통합검색창 찾기 및 클릭
    logger.debug('통합검색창 찾기 중...');
    
    let searchInput = null;
    let clickSuccess = false;

    // 방법 1: placeholder 속성으로 찾기
    try {
      logger.debug('방법 1: input[placeholder*="통합검색"] 시도 중...');
      searchInput = page.locator('input[placeholder*="통합검색"]').first();
      const isVisible = await searchInput.isVisible().catch(() => false);
      if (isVisible) {
        await searchInput.click();
        logger.info('✅ 통합검색창 클릭 (방법 1: placeholder)');
        clickSuccess = true;
      }
    } catch (e) {
      logger.warn('⚠️ 방법 1 실패: ' + e.message);
    }

    // 방법 2: class 속성으로 찾기
    if (!clickSuccess) {
      try {
        logger.debug('방법 2: [class*="search"] 시도 중...');
        searchInput = page.locator('input[class*="search"]').first();
        const isVisible = await searchInput.isVisible().catch(() => false);
        if (isVisible) {
          await searchInput.click();
          logger.info('✅ 통합검색창 클릭 (방법 2: class search)');
          clickSuccess = true;
        }
      } catch (e) {
        logger.warn('⚠️ 방법 2 실패: ' + e.message);
      }
    }

    // 방법 3: 모든 input 요소 순회
    if (!clickSuccess) {
      try {
        logger.debug('방법 3: 모든 input 요소 순회 중...');
        const inputs = page.locator('input');
        const count = await inputs.count();
        logger.debug(`📊 총 input 요소 ${count}개 발견`);

        for (let i = 0; i < count; i++) {
          const placeholder = await inputs.nth(i).getAttribute('placeholder').catch(() => '');
          const value = await inputs.nth(i).getAttribute('value').catch(() => '');
          const type = await inputs.nth(i).getAttribute('type').catch(() => '');
          
          logger.debug(`  [${i}] placeholder="${placeholder}", type="${type}"`);

          if (placeholder && (placeholder.includes('통합') || placeholder.includes('검색'))) {
            const isVisible = await inputs.nth(i).isVisible().catch(() => false);
            if (isVisible) {
              await inputs.nth(i).click();
              searchInput = inputs.nth(i);
              logger.info(`✅ 통합검색창 클릭 (방법 3: input[${i}])`);
              clickSuccess = true;
              break;
            }
          }
        }
      } catch (e) {
        logger.warn('⚠️ 방법 3 실패: ' + e.message);
      }
    }

    if (!clickSuccess) {
      throw new Error('통합검색창을 찾을 수 없습니다. 페이지 구조를 확인해주세요.');
    }

    // 2단계: '지출결의현황' 입력
    logger.debug('검색어 입력 중...');
    
    // 포커스 확인
    await searchInput.focus();
    await page.waitForTimeout(300);
    
    // 기존 텍스트 제거
    await searchInput.evaluate(el => el.value = '');
    
    // 검색어 입력
    await searchInput.type('지출결의현황', { delay: 100 });
    logger.info('✅ "지출결의현황" 입력 완료');

    // 검색 결과 로드 대기
    await page.waitForTimeout(500);

    // 3단계: 엔터키 누르기
    logger.debug('엔터키 입력...');
    await searchInput.press('Enter');
    logger.info('✅ 엔터키 입력');

    // 검색 결과 로드 대기
    logger.info('⏳ 검색 결과 로드 대기 중...');
    await page.waitForTimeout(1500);

    // 4단계: 우측 메뉴에서 '지출결의현황' 클릭
    logger.debug('우측 메뉴에서 지출결의현황 찾기 중...');
    
    let menuClickSuccess = false;

    // 방법 1: text 선택자로 마지막 항목 찾기
    try {
      logger.debug('방법 1: text="지출결의현황" (last) 시도 중...');
      const expenseMenu = page.locator('text="지출결의현황"').last();
      const isVisible = await expenseMenu.isVisible().catch(() => false);
      if (isVisible) {
        await expenseMenu.click();
        logger.info('✅ 지출결의현황 메뉴 클릭 (방법 1)');
        menuClickSuccess = true;
      }
    } catch (e) {
      logger.warn('⚠️ 방법 1 실패: ' + e.message);
    }

    // 방법 2: 모든 "지출결의현황" 텍스트 요소 순회
    if (!menuClickSuccess) {
      try {
        logger.debug('방법 2: 모든 지출결의현황 요소 순회 중...');
        const allItems = page.locator('text="지출결의현황"');
        const count = await allItems.count();
        logger.debug(`📊 "지출결의현황" 항목 ${count}개 발견`);

        // 역순으로 확인 (우측이 보통 뒤에 있음)
        for (let i = count - 1; i >= 0; i--) {
          try {
            const isVisible = await allItems.nth(i).isVisible().catch(() => false);
            if (isVisible) {
              const boundingBox = await allItems.nth(i).boundingBox().catch(() => null);
              logger.debug(`  [${i}] 위치: ${JSON.stringify(boundingBox)}`);
              
              await allItems.nth(i).click();
              logger.info(`✅ 지출결의현황 메뉴 클릭 (방법 2: 항목[${i}])`);
              menuClickSuccess = true;
              break;
            }
          } catch (innerError) {
            continue;
          }
        }
      } catch (e) {
        logger.warn('⚠️ 방법 2 실패: ' + e.message);
      }
    }

    // 방법 3: 우측 패널 내에서 찾기
    if (!menuClickSuccess) {
      try {
        logger.debug('방법 3: 우측 패널에서 검색 중...');
        const rightPanel = page.locator('[class*="right"], [class*="panel"], [class*="sidebar"]').first();
        const isVisible = await rightPanel.isVisible().catch(() => false);
        
        if (isVisible) {
          const menu = rightPanel.locator('text="지출결의현황"');
          const menuCount = await menu.count();
          logger.debug(`📊 우측 패널에서 ${menuCount}개 발견`);
          
          if (menuCount > 0) {
            await menu.first().click();
            logger.info('✅ 지출결의현황 메뉴 클릭 (방법 3: 우측 패널)');
            menuClickSuccess = true;
          }
        }
      } catch (e) {
        logger.warn('⚠️ 방법 3 실패: ' + e.message);
      }
    }

    if (!menuClickSuccess) {
      throw new Error('지출결의현황 메뉴를 찾을 수 없습니다.');
    }

    // 페이지 로드 대기
    logger.info('⏳ 페이지 로드 대기 중...');
    await page.waitForLoadState('load', { timeout: 10000 }).catch(() => {
      logger.warn('⚠️ 페이지 로드 타임아웃 (계속 진행)');
    });

    logger.info('✅ 지출결의현황 페이지 로드 완료');

    // 현재 상태 확인
    const currentUrl = page.url();
    const title = await page.title();
    logger.debug(`📍 현재 URL: ${currentUrl}`);
    logger.debug(`📄 페이지 타이틀: ${title}`);

    return true;
  } catch (error) {
    logger.error('❌ 메뉴 이동 실패:', error.message);
    
    // 에러 발생 시 스크린샷 저장
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const screenshotPath = `./screenshots/navigation_error_${timestamp}.png`;
      await page.screenshot({ path: screenshotPath });
      logger.info(`📸 에러 스크린샷 저장: ${screenshotPath}`);
    } catch (screenshotError) {
      logger.warn('스크린샷 저장 실패');
    }

    throw error;
  }
}

module.exports = { goToAccounting };