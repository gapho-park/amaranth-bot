const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const logger = require('./logger');
const { config, validateConfig } = require('./config');
const { login } = require('./bot/login');
const { goToAccounting } = require('./bot/navigation');
const {
  setApplicationDate,
  setApprovalStatus,
  clearFilters,
  setDocumentStatus,
  searchData
} = require('./bot/actions');

async function main() {
  let browser = null;

  try {
    // 설정값 검증
    logger.info('⚙️  설정 검증 중...');
    validateConfig();
    logger.info('✅ 설정 검증 완료');

    // 다운로드 디렉토리 생성
    if (!fs.existsSync(config.paths.downloads)) {
      fs.mkdirSync(config.paths.downloads, { recursive: true });
      logger.info(`📁 다운로드 디렉토리 생성: ${config.paths.downloads}`);
    }

    // 스크린샷 디렉토리 생성
    if (!fs.existsSync('./screenshots')) {
      fs.mkdirSync('./screenshots', { recursive: true });
    }

    // 브라우저 시작
    logger.info('🌐 브라우저 시작 중...');
    browser = await chromium.launch({
      headless: config.bot.headless,
      slowMo: config.bot.slowMo,
    });
    logger.info('✅ 브라우저 시작 완료');

    // Context 생성 (다운로드 활성화)
    const context = await browser.newContext({
      acceptDownloads: true,
    });
    logger.info('✅ 브라우저 컨텍스트 생성');

    // Page 생성
    const page = await context.newPage();
    logger.info('✅ 페이지 생성');

    // 1️⃣ 로그인
    logger.info('\n========== 단계 1: 로그인 ==========');
    await login(page);

    // 2️⃣ 지출결의현황 메뉴 이동 (통합검색 사용)
    logger.info('\n========== 단계 2: 지출결의현황 이동 ==========');
    await goToAccounting(page);

    logger.info('\n✅ 지출결의현황 페이지 도달 완료!');
    logger.info('다음 단계:');
    logger.info('  - 기안일자 필터 설정');
    logger.info('  - 기안부서, 기안자 필터 삭제');
    logger.info('  - 전표발행여부 설정');
    logger.info('  - 데이터 조회 및 다운로드');

     // 3️⃣ 기안일자 필터 설정
    logger.info('\n========== 단계 3: 기안일자 필터 설정 ==========');
    await setApplicationDate(page);

    // 4️⃣ 결재상태 필터 설정
    logger.info('\n========== 단계 4: 결재상태 필터 설정 ==========');
    await setApprovalStatus(page);

    // 5️⃣ 기안부서, 기안자 필터 삭제
    logger.info('\n========== 단계 5: 기안부서, 기안자 필터 삭제 ==========');
    await clearFilters(page);

    // 6️⃣ 전표발행여부 설정
    logger.info('\n========== 단계 6: 전표발행여부 설정 ==========');
    await setDocumentStatus(page);

    // 7️⃣ 데이터 조회
    logger.info('\n========== 단계 7: 데이터 조회 ==========');
    await searchData(page);

    logger.info('\n✨ 모든 필터 설정 및 데이터 조회 완료!');

    // 개발 중 브라우저 유지 (headless가 false일 때)
    if (!config.bot.headless) {
      logger.info('\n💡 개발 모드 - 브라우저 유지 중... (Ctrl+C로 종료)');
      await page.pause();
    }

    await context.close();
  } catch (error) {
    logger.error('❌ 오류 발생:', error);
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
      logger.info('🌐 브라우저 종료');
    }
  }
}

// 실행
if (require.main === module) {
  main();
}

module.exports = { main };