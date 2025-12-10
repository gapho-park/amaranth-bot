const axios = require('axios');
const CryptoJS = require('crypto-js');
const { GoogleSpreadsheet } = require('google-spreadsheet');
const { JWT } = require('google-auth-library');
const fs = require('fs');
require('dotenv').config();

// === 설정 ===
const CONFIG = {
  groupSeq: 'gcmsAmaranth39483',
  callerName: 'API_gcmsAmaranth39483',
  accessToken: 'roifHrayJttms27ufGiqVa8grv6Sk0',
  hashKey: '88761859188784596178355689527478836553536918',
  proxyUrl: '/apiproxy/api11A30',
  amaranthUrl: 'https://portal.rapportlabs.kr',
  coCd: '1000',
  sheetId: '1jcO4dHExbdwT6sZejj2Z22pycvZ6dRsyqPZ62zgUk-Y',
  sheetTabName: '계정별원장_RAW'
};

// 수정된 계정 리스트 (입력불가 제외)
const SGA_ACCOUNTS = [
  '8000000', '8010000', '8020000', '8020001', '8030000', '8040000', '8050000',
  '8060000', '8070000', '8080000', '8090000', 
  '8110000', '8110001', '8110002', '8110003', '8110004', '8110005', '8110006',
  '8120000', '8130000', '8140000', '8150000', '8160000', '8170000', '8180000', 
  '8190000', '8200000', '8210000', '8220000', '8240000', '8250000', '8260000', 
  '8270000', '8280000', '8290000', '8300000', '8300001', '8300002',
  '8310001', '8310002', '8310003', '8310004', '8310005', '8310006', '8310007', '8310008',
  '8330000', '8330001', 
  '8340000', '8340001', '8340002', '8340003', '8340004', '8340005', '8340006', '8340007', '8340008',
  '8350000', '8360000', '8380000', '8390000', 
  '8410000', '8420000', '8430000', '8440000', '8450000', '8460000', '8470000',
  '8480000', '8480001', '8480002', '8480003', 
  '8490000', '8500000', '8510000'
];

// Axios 인스턴스 생성 (타임아웃 설정)
const apiClient = axios.create({
  baseURL: CONFIG.amaranthUrl,
  timeout: 30000, // 30초 타임아웃
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
  }
});

// 유틸리티 함수들
function generateTransactionId(length = 30) {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) result += chars.charAt(Math.floor(Math.random() * chars.length));
  return result;
}

function generateWehagoSign(hashKey, value) {
  const hmac = CryptoJS.HmacSHA256(value, hashKey);
  return CryptoJS.enc.Base64.stringify(hmac);
}

function getTodayString() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return year + month + day;
}

function formatDateStr(dt) {
  if (!dt || dt.length !== 8) return dt || '';
  return dt.substring(0, 4) + '-' + dt.substring(4, 6) + '-' + dt.substring(6, 8);
}

function convertDrcrFg(fg) {
  if (fg === '1') return '차변';
  if (fg === '2') return '대변';
  return fg;
}

// 날짜 기간 분할 (1개월 단위)
function getMonthlyRanges(startStr, endStr) {
  const ranges = [];
  const parseDate = (str) => new Date(str.substring(0, 4), str.substring(4, 6) - 1, str.substring(6, 8));
  const stringifyDate = (date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}${m}${d}`;
  };

  let current = parseDate(startStr);
  const end = parseDate(endStr);

  while (current <= end) {
    const rangeStart = new Date(current);
    const nextMonth = new Date(current);
    nextMonth.setMonth(current.getMonth() + 1);
    nextMonth.setDate(1);
    
    let rangeEnd = new Date(nextMonth);
    rangeEnd.setDate(rangeEnd.getDate() - 1);
    
    if (rangeEnd > end) rangeEnd = new Date(end);

    ranges.push({ from: stringifyDate(rangeStart), to: stringifyDate(rangeEnd) });
    current = new Date(nextMonth);
  }
  return ranges;
}

// API 호출
async function callAccountLedgerApi(params) {
  const transactionId = generateTransactionId();
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const url = CONFIG.proxyUrl;
  
  const wehagoSign = generateWehagoSign(
    CONFIG.hashKey,
    CONFIG.accessToken + transactionId + timestamp + url
  );
  
  const requestBody = {
    header: { groupSeq: CONFIG.groupSeq, empSeq: 1, tId: '', pId: '' },
    coCd: params.coCd,
    divCds: params.divCds,
    fillDtFrom: params.fillDtFrom,
    fillDtTo: params.fillDtTo,
    prtFg: params.prtFg,
    acctCd: params.acctCd,
    zeroDisp: params.zeroDisp,
    viewPage: params.viewPage,
    viewCount: params.viewCount
  };
  
  try {
    const response = await apiClient.post(CONFIG.proxyUrl, requestBody, {
      headers: {
        'callerName': CONFIG.callerName,
        'Authorization': 'Bearer ' + CONFIG.accessToken,
        'transaction-id': transactionId,
        'timestamp': timestamp,
        'groupSeq': CONFIG.groupSeq,
        'wehago-sign': wehagoSign,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    if (error.code === 'ECONNABORTED') {
      console.error(`❌ [Timeout] ${params.acctCd}: 요청 시간 초과`);
    } else {
      console.error(`❌ [Error] ${params.acctCd}: ${error.message}`);
    }
    return { resultCode: -1, resultMsg: error.message };
  }
}

// 페이지 순회 (수정된 로직)
async function fetchAllPagesForAccount(params) {
  const allData = [];
  let currentPage = 1;
  
  while (true) {
    params.viewPage = currentPage;
    
    const result = await callAccountLedgerApi(params);
    
    if (result.resultCode !== 0) break; // 에러 시 중단
    
    const resultData = result.resultData;
    if (!resultData || !resultData.datas || resultData.datas.length === 0) {
      break; // 데이터 없음
    }
    
    allData.push(...resultData.datas);
    
    // 총 페이지 수 도달 시 종료
    if (currentPage >= (resultData.totalPage || 1)) {
      break;
    }
    
    currentPage++;
    await new Promise(resolve => setTimeout(resolve, 100)); // 0.1초 대기
  }
  
  return allData;
}

// 구글 시트 업로드
async function uploadToGoogleSheet(data) {
  if (data.length === 0) {
    console.log('⚠️ 업로드할 데이터가 없습니다.');
    return;
  }

  console.log('📊 구글 시트 연결 중...');
  try {
    const serviceAccountAuth = new JWT({
      email: require('./service_account.json').client_email,
      key: require('./service_account.json').private_key,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const doc = new GoogleSpreadsheet(CONFIG.sheetId, serviceAccountAuth);
    await doc.loadInfo();
    
    let sheet = doc.sheetsByTitle[CONFIG.sheetTabName];
    if (!sheet) {
      sheet = await doc.addSheet({ title: CONFIG.sheetTabName, headerValues: [] });
    }
    
    await sheet.clear();
    
    const headers = [
      '회사코드', '사업장코드', '계정과목', '차대구분', '승인일', '승인번호',
      '적요', '거래처코드', '거래처명', '사업자번호', '차변', '대변', '잔액',
      '작성일', '작성순번', '화면순번', '라인순번',
      '사용부서코드', '사용부서명', '프로젝트코드', '프로젝트명', '사용사원코드', '사용사원명'
    ];
    
    await sheet.setHeaderRow(headers);
    
    const rows = data.map(item => ({
      '회사코드': item.coCd || '', '사업장코드': item.divCd || '', '계정과목': item.acctCd || '',
      '차대구분': convertDrcrFg(item.drcrFg), '승인일': formatDateStr(item.fillDt), '승인번호': item.fillNb || 0,
      '적요': item.rmkDc || '', '거래처코드': item.trCd || '', '거래처명': item.trNm || '', '사업자번호': item.regNb || '',
      '차변': item.drAm || 0, '대변': item.crAm || 0, '잔액': item.restAm || 0,
      '작성일': formatDateStr(item.isuDt), '작성순번': item.isuSq || 0, '화면순번': item.dispSq || 0, '라인순번': item.lnSq || 0,
      '사용부서코드': item.ctDeptCd || '', '사용부서명': item.ctDeptNm || '',
      '프로젝트코드': item.pjtCd || '', '프로젝트명': item.pjtNm || '',
      '사용사원코드': item.ctEmpCd || '', '사용사원명': item.ctEmpNm || ''
    }));
    
    rows.sort((a, b) => (a['승인일'] !== b['승인일'] ? (a['승인일'] < b['승인일'] ? -1 : 1) : a['승인번호'] - b['승인번호']));

    const CHUNK_SIZE = 2000;
    for (let i = 0; i < rows.length; i += CHUNK_SIZE) {
      const chunk = rows.slice(i, i + CHUNK_SIZE);
      await sheet.addRows(chunk);
      console.log(`  - ${Math.min(i + CHUNK_SIZE, rows.length)} / ${rows.length} 건 업로드 완료`);
    }
    
    await sheet.loadCells('Y1:Y2');
    const headerCell = sheet.getCell(0, 24);
    const valueCell = sheet.getCell(1, 24);
    headerCell.value = '업데이트'; headerCell.textFormat = { bold: true };
    const now = new Date();
    valueCell.value = now.toISOString().replace('T', ' ').substring(0, 19);
    await sheet.saveUpdatedCells();
    
    console.log('✅ 구글 시트 업로드 완료!');
  } catch (error) {
    console.error('❌ 구글 시트 업로드 오류:', error);
  }
}

// 메인 실행
async function main() {
  const startDate = '20250101';
  const endDate = getTodayString();
  const dateRanges = getMonthlyRanges(startDate, endDate);
  
  console.log(`=== 판관비 계정별원장 조회 시작 (${startDate} ~ ${endDate}) ===`);
  console.log(`📅 총 ${dateRanges.length}개 구간 (월 단위)`);

  const baseParams = {
    coCd: CONFIG.coCd,
    divCds: '1000|',
    prtFg: '2',
    zeroDisp: '0',
    viewCount: 50
  };
  
  const allData = [];
  
  for (let i = 0; i < SGA_ACCOUNTS.length; i++) {
    const acctCd = SGA_ACCOUNTS[i];
    let accountTotal = 0;
    
    for (const range of dateRanges) {
      try {
        const params = { ...baseParams, acctCd: acctCd, fillDtFrom: range.from, fillDtTo: range.to };
        const periodData = await fetchAllPagesForAccount(params);
        if (periodData.length > 0) {
          allData.push(...periodData);
          accountTotal += periodData.length;
        }
      } catch (error) {
        console.error(`❌ ${acctCd} (${range.from}): ${error.message}`);
      }
    }
    
    if (accountTotal > 0) {
      console.log(`[${i+1}/${SGA_ACCOUNTS.length}] ${acctCd}: ✅ ${accountTotal}건`);
    } else {
      console.log(`[${i+1}/${SGA_ACCOUNTS.length}] ${acctCd}: 데이터 없음`);
    }
    
    await new Promise(resolve => setTimeout(resolve, 50)); 
  }
  
  console.log(`\n=== 조회 완료 (총 ${allData.length}건) ===`);
  await uploadToGoogleSheet(allData);
}

main();
