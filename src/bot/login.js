const logger = require('../logger');
const { config } = require('../config');

async function login(page) {
  try {
    logger.info('🚀 아마란스10 로그인 시작...');

    // 1. 로그인 페이지 접속
    logger.info(`📍 접속 중: ${config.amaranth.url}`);
    await page.goto(config.amaranth.url, {
      waitUntil: 'networkidle',
      timeout: config.bot.timeout,
    });
    logger.info('✅ 로그인 페이지 로드 완료');

    // ========== 1단계: 사용자ID 입력 ==========
    logger.info('📍 1단계: 사용자ID 입력...');
    
    // 첫 번째 input은 회사코드(disabled)이므로 스킵
    // 두 번째 input - 사용자ID 입력
    logger.debug('사용자ID 입력 필드 찾기 중...');
    const userIdInput = page.locator('input').nth(1);
    
    await userIdInput.waitFor({ state: 'visible', timeout: config.bot.timeout });
    await userIdInput.fill(config.amaranth.userId);
    logger.info(`✅ 사용자ID 입력 완료: ${config.amaranth.userId}`);

    // "다음" 버튼 클릭 (첫 번째만)
    logger.debug('"다음" 버튼 찾기 중...');
    const nextButton = page.locator('button:has-text("다음")').first();
    
    await nextButton.waitFor({ state: 'visible', timeout: config.bot.timeout });
    await nextButton.click();
    logger.info('✅ "다음" 버튼 클릭');

    // 2단계 페이지 로드 대기
    logger.info('⏳ 2단계 페이지 로드 대기 중...');
    await page.waitForLoadState('load', { timeout: 10000 }).catch(() => {
      logger.warn('⚠️ 페이지 로드 타임아웃 (계속 진행)');
    });

    // ========== 2단계: 비밀번호 입력 ==========
    logger.info('📍 2단계: 비밀번호 입력...');
    
    // 비밀번호 입력 필드 찾기
    logger.debug('비밀번호 입력 필드 찾기 중...');
    const passwordInput = page.locator('input[type="password"]');
    
    await passwordInput.waitFor({ state: 'visible', timeout: config.bot.timeout });
    await passwordInput.fill(config.amaranth.password);
    logger.info('✅ 비밀번호 입력 완료');

    // "로그인" 버튼 클릭
    logger.debug('"로그인" 버튼 찾기 중...');
    const loginButton = page.locator('button:has-text("로그인")').first();
    
    await loginButton.waitFor({ state: 'visible', timeout: config.bot.timeout });
    await loginButton.click();
    logger.info('✅ "로그인" 버튼 클릭');

    // 페이지 로드 대기
    logger.info('⏳ 로그인 완료 대기 중...');
    await page.waitForLoadState('domcontentloaded', { timeout: 5000 }).catch(() => {
      logger.warn('⚠️ 페이지 로드 타임아웃 (계속 진행)');
    });

    await page.waitForTimeout(1000);

    logger.info('✅ 로그인 성공!');
    // 현재 상태 확인
    const currentUrl = page.url();
    const title = await page.title();
    logger.debug(`📍 현재 URL: ${currentUrl}`);
    logger.debug(`📄 페이지 타이틀: ${title}`);

    return true;
  } catch (error) {
    logger.error('❌ 로그인 실패:', error.message);
    
    // 에러 발생 시 스크린샷 저장
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const screenshotPath = `./screenshots/login_error_${timestamp}.png`;
      await page.screenshot({ path: screenshotPath });
      logger.info(`📸 에러 스크린샷 저장: ${screenshotPath}`);
    } catch (screenshotError) {
      logger.warn('스크린샷 저장 실패');
    }

    throw error;
  }
}

module.exports = { login };