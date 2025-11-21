require('dotenv').config();

const config = {
  // 아마란스10 설정
  amaranth: {
    userId: process.env.AMARANTH_USER_ID || 'gapho',
    password: process.env.AMARANTH_PASSWORD,
    url: process.env.AMARANTH_URL || 'https://portal.rapportlabs.kr/#/login',
  },

  // 봇 설정
  bot: {
    headless: process.env.BOT_HEADLESS === 'true' || false,
    slowMo: parseInt(process.env.BOT_SLOW_MO || '500', 10),
    timeout: 30000, // 30초
  },

  // 경로 설정
  paths: {
    downloads: process.env.DOWNLOAD_PATH || './downloads',
  },

  // 로그 설정
  logging: {
    level: process.env.LOG_LEVEL || 'info',
  },
};

// 필수 설정값 검증
function validateConfig() {
  if (!config.amaranth.password) {
    throw new Error('❌ AMARANTH_PASSWORD 환경변수가 설정되지 않았습니다.');
  }
  return true;
}

module.exports = {
  config,
  validateConfig,
};