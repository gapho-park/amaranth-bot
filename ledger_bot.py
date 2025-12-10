import os
import time
import hmac
import hashlib
import base64
import random
import string
import json
import requests
import pandas as pd
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from logger import logger  # 기존 로거 사용

# === 설정값 (보안을 위해 .env 관리를 권장합니다) ===
CONFIG = {
    'groupSeq': 'gcmsAmaranth39483',
    'callerName': 'API_gcmsAmaranth39483',
    'accessToken': 'roifHrayJttms27ufGiqVa8grv6Sk0',
    'hashKey': '88761859188784596178355689527478836553536918',
    'proxyUrl': '/apiproxy/api11A30',
    'amaranthUrl': 'https://portal.rapportlabs.kr',
    'coCd': '1000',
    'sheetId': '1jcO4dHExbdwT6sZejj2Z22pycvZ6dRsyqPZ62zgUk-Y',
    'sheetTabName': '계정별원장_RAW'
}

# 판관비 계정과목 목록
SGA_ACCOUNTS = [
    '8000000', '8010000', '8020000', '8020001', '8030000', '8040000', '8050000',
    '8060000', '8070000', '8080000', '8090000', '8100000', '8110000', '8110001',
    '8110002', '8110003', '8110004', '8110005', '8110006', '8120000', '8130000',
    '8140000', '8150000', '8160000', '8170000', '8180000', '8190000', '8200000',
    '8210000', '8220000', '8230000', '8240000', '8250000', '8260000', '8270000',
    '8280000', '8290000', '8300000', '8300001', '8300002', '8310000', '8310001',
    '8310002', '8310003', '8310004', '8310005', '8310006', '8310007', '8310008',
    '8320000', '8330000', '8330001', '8340000', '8340001', '8340002', '8340003',
    '8340004', '8340005', '8340006', '8340007', '8340008', '8350000', '8360000',
    '8370000', '8380000', '8390000', '8400000', '8410000', '8420000', '8430000',
    '8440000', '8450000', '8460000', '8470000', '8480000', '8480001', '8480002',
    '8480003', '8490000', '8500000', '8510000'
]

def generate_transaction_id(length=30):
    """30자리 랜덤 문자열 생성"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_wehago_sign(hash_key, value):
    """Wehago 서명 생성 (HMAC-SHA256 -> Base64)"""
    # Python의 hmac은 bytes 타입을 요구합니다.
    key_bytes = hash_key.encode('utf-8')
    value_bytes = value.encode('utf-8')
    
    signature = hmac.new(key_bytes, value_bytes, hashlib.sha256).digest()
    return base64.b64encode(signature).decode('utf-8')

def get_today_string():
    """오늘 날짜 yyyymmdd"""
    return datetime.now().strftime('%Y%m%d')

def format_date_str(dt_str):
    """yyyymmdd -> yyyy-mm-dd 변환"""
    if not dt_str or len(str(dt_str)) != 8:
        return dt_str
    s = str(dt_str)
    return f"{s[:4]}-{s[4:6]}-{s[6:]}"

def convert_drcr_fg(fg):
    """차대구분 코드 변환"""
    if fg == '1': return '차변'
    if fg == '2': return '대변'
    return fg

def call_account_ledger_api(params):
    """API 호출 함수"""
    transaction_id = generate_transaction_id()
    timestamp = str(int(time.time()))
    url_path = CONFIG['proxyUrl']
    
    # 서명 생성 값: accessToken + transactionId + timestamp + url
    sign_value = CONFIG['accessToken'] + transaction_id + timestamp + url_path
    wehago_sign = generate_wehago_sign(CONFIG['hashKey'], sign_value)
    
    api_url = CONFIG['amaranthUrl'] + url_path
    
    request_body = {
        "header": {
            "groupSeq": CONFIG['groupSeq'],
            "empSeq": 1,
            "tId": "",
            "pId": ""
        },
        "coCd": params.get('coCd'),
        "divCds": params.get('divCds'),
        "fillDtFrom": params.get('fillDtFrom'),
        "fillDtTo": params.get('fillDtTo'),
        "prtFg": params.get('prtFg'),
        "acctCd": params.get('acctCd'),
        "zeroDisp": params.get('zeroDisp'),
        "viewPage": params.get('viewPage'),
        "viewCount": params.get('viewCount')
    }
    
    headers = {
        'callerName': CONFIG['callerName'],
        'Authorization': 'Bearer ' + CONFIG['accessToken'],
        'transaction-id': transaction_id,
        'timestamp': timestamp,
        'groupSeq': CONFIG['groupSeq'],
        'wehago-sign': wehago_sign,
        'Content-Type': 'application/json'
    }
    
    try:
        # timeout=30 추가 (30초 대기)
        response = requests.post(api_url, headers=headers, json=request_body, verify=True, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"API Request Timeout (30s)")
        return {"resultCode": -1, "resultMsg": "Timeout"}
    except requests.exceptions.RequestException as e:
        logger.error(f"API Request Failed: {e}")
        return {"resultCode": -1, "resultMsg": str(e)}

def fetch_all_pages_for_account(base_params):
    """특정 계정의 전체 페이지 데이터 수집"""
    all_data = []
    current_page = 1
    total_page = 1
    
    while current_page <= total_page:
        base_params['viewPage'] = current_page
        result = call_account_ledger_api(base_params)
        
        if result.get('resultCode') != 0:
            logger.error(f"API Error for {base_params['acctCd']}: {result.get('resultMsg')}")
            return []
            
        result_data = result.get('resultData', {})
        if not result_data:
            return all_data
            
        total_page = result_data.get('totalPage', 1)
        datas = result_data.get('datas', [])
        
        if datas:
            all_data.extend(datas)
            
        current_page += 1
        # API 과부하 방지를 위해 짧은 대기
        if current_page <= total_page:
            time.sleep(0.1)
            
    return all_data

def upload_to_google_sheet(data_list):
    """데이터프레임을 구글 시트에 업로드"""
    if not data_list:
        logger.warning("업로드할 데이터가 없습니다.")
        return

    try:
        logger.info("📊 구글 시트 연결 중...")
        
        # 서비스 계정 인증
        # service_account.json 파일이 같은 경로에 있어야 합니다.
        gc = gspread.service_account(filename='service_account.json')
        sh = gc.open_by_key(CONFIG['sheetId'])
        
        try:
            worksheet = sh.worksheet(CONFIG['sheetTabName'])
            worksheet.clear()
        except gspread.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=CONFIG['sheetTabName'], rows=1000, cols=26)
            
        # Pandas로 데이터 가공
        df = pd.DataFrame(data_list)
        
        # 필요한 컬럼 매핑 및 순서 정렬
        # GAS 코드의 headers 순서와 맞춤
        columns_map = {
            'coCd': '회사코드', 'divCd': '사업장코드', 'acctCd': '계정과목', 'drcrFg': '차대구분',
            'fillDt': '승인일', 'fillNb': '승인번호', 'rmkDc': '적요', 'trCd': '거래처코드',
            'trNm': '거래처명', 'regNb': '사업자번호', 'drAm': '차변', 'crAm': '대변',
            'restAm': '잔액', 'isuDt': '작성일', 'isuSq': '작성순번', 'dispSq': '화면순번',
            'lnSq': '라인순번', 'ctDeptCd': '사용부서코드', 'ctDeptNm': '사용부서명',
            'pjtCd': '프로젝트코드', 'pjtNm': '프로젝트명', 'ctEmpCd': '사용사원코드',
            'ctEmpNm': '사용사원명'
        }
        
        # 존재하는 컬럼만 선택하여 이름 변경
        target_cols = [col for col in columns_map.keys() if col in df.columns]
        df = df[target_cols].rename(columns=columns_map)
        
        # 데이터 포맷팅
        if '차대구분' in df.columns:
            df['차대구분'] = df['차대구분'].apply(convert_drcr_fg)
        if '승인일' in df.columns:
            df['승인일'] = df['승인일'].apply(format_date_str)
        if '작성일' in df.columns:
            df['작성일'] = df['작성일'].apply(format_date_str)
            
        # 숫자형 변환 (NaN -> 0)
        numeric_cols = ['승인번호', '차변', '대변', '잔액', '작성순번', '화면순번', '라인순번']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 정렬 (승인일, 승인번호)
        if '승인일' in df.columns and '승인번호' in df.columns:
            df = df.sort_values(by=['승인일', '승인번호'])

        # 업데이트 시간 컬럼 추가 (마지막 컬럼 뒤에)
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 헤더 + 데이터 준비
        headers = df.columns.tolist()
        values = df.astype(str).values.tolist() # gspread 호환을 위해 string 변환
        
        # 시트 업데이트
        worksheet.update(range_name='A1', values=[headers] + values)
        
        # 업데이트 시간 별도 표기 (헤더 옆)
        worksheet.update_cell(1, len(headers) + 2, "업데이트")
        worksheet.update_cell(2, len(headers) + 2, update_time)
        
        logger.info(f"✅ 시트 업로드 완료: {len(values)}건")
        
    except Exception as e:
        logger.error(f"❌ 시트 업로드 실패: {e}")

def run_ledger_bot():
    """메인 실행 함수"""
    
    base_params = {
        'coCd': CONFIG['coCd'],
        'divCds': '1000|',
        'fillDtFrom': '20250101',
        'fillDtTo': get_today_string(),
        'prtFg': '2',
        'zeroDisp': '0',
        'viewPage': 1,
        'viewCount': 100
    }
    
    logger.info(f"=== 판관비 계정별원장 조회 시작 ({base_params['fillDtFrom']} ~ {base_params['fillDtTo']}) ===")
    
    all_data = []
    success_count = 0
    empty_count = 0
    
    for i, acct_cd in enumerate(SGA_ACCOUNTS):
        try:
            logger.info(f"[{i+1}/{len(SGA_ACCOUNTS)}] {acct_cd} 조회 시작...") # 진행 상황 로그 추가
            params = base_params.copy()
            params['acctCd'] = acct_cd
            
            account_data = fetch_all_pages_for_account(params)
            
            if account_data:
                all_data.extend(account_data)
                logger.info(f"[{i+1}/{len(SGA_ACCOUNTS)}] {acct_cd}: ✅ {len(account_data)}건")
                success_count += 1
            else:
                # logger.debug(f"[{i+1}/{len(SGA_ACCOUNTS)}] {acct_cd}: 데이터 없음")
                logger.info(f"[{i+1}/{len(SGA_ACCOUNTS)}] {acct_cd}: 데이터 없음") # 빈 것도 로그 출력
                empty_count += 1
                
            time.sleep(0.1) # 루프 간 짧은 대기
            
        except Exception as e:
            logger.error(f"[{i+1}/{len(SGA_ACCOUNTS)}] {acct_cd}: ❌ {e}")

    logger.info(f"\n=== 조회 완료 ===")
    logger.info(f"총 데이터: {len(all_data)}건 (유효 계정: {success_count}개)")
    
    if all_data:
        upload_to_google_sheet(all_data)
    else:
        logger.warning("⚠️ 조회된 데이터가 없어 시트를 업데이트하지 않았습니다.")

if __name__ == "__main__":
    run_ledger_bot()

