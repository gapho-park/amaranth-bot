const { config } = require('./config');

const LogLevel = {
  ERROR: 0,
  WARN: 1,
  INFO: 2,
  DEBUG: 3,
};

const levelMap = {
  error: LogLevel.ERROR,
  warn: LogLevel.WARN,
  info: LogLevel.INFO,
  debug: LogLevel.DEBUG,
};

const currentLevel = levelMap[config.logging.level] || LogLevel.INFO;

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m',
};

function getTimestamp() {
  const now = new Date();
  return now.toISOString();
}

function log(level, message, data = null) {
  if (levelMap[level] > currentLevel) return;

  const timestamp = getTimestamp();
  const levelColors = {
    error: colors.red,
    warn: colors.yellow,
    info: colors.cyan,
    debug: colors.gray,
  };

  const colorizedLevel = `${levelColors[level]}${level.toUpperCase()}${colors.reset}`;
  const output = `[${timestamp}] ${colorizedLevel} ${message}`;

  if (level === 'error') {
    console.error(output);
    if (data) console.error(data);
  } else {
    console.log(output);
    if (data) console.log(data);
  }
}

module.exports = {
  info: (msg, data) => log('info', msg, data),
  error: (msg, data) => log('error', msg, data),
  warn: (msg, data) => log('warn', msg, data),
  debug: (msg, data) => log('debug', msg, data),
};