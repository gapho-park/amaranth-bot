# GitHub Actions 설정 가이드

## 1. GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

다음 Secrets를 추가하세요:

### 필수 Secrets

1. **AMARANTH_USER_ID**
   - 값: 아마란스 로그인 ID

2. **AMARANTH_PASSWORD**
   - 값: 아마란스 로그인 비밀번호

3. **GOOGLE_SHEET_URL**
   - 값: Google Sheets URL (예: `https://docs.google.com/spreadsheets/d/...`)

4. **GOOGLE_SERVICE_ACCOUNT_JSON**
   - 값: `service_account.json` 파일의 **전체 내용**을 복사해서 붙여넣기
   - 파일을 열어서 모든 JSON 내용을 복사 (예: `{"type": "service_account", ...}`)

## 2. 스케줄 설정

현재 설정: **매 시간 정각에 실행** (UTC 기준)

```yaml
schedule:
  - cron: '0 * * * *'  # 매 시간 정각
```

### 다른 스케줄 예시

```yaml
# 매 30분마다
- cron: '*/30 * * * *'

# 매일 오전 9시 (UTC 기준, 한국시간 18시)
- cron: '0 9 * * *'

# 평일 오전 9시~18시, 매 시간 (UTC 기준)
- cron: '0 9-18 * * 1-5'
```

## 3. 수동 실행

GitHub 저장소 → Actions → "Amaranth Bot Hourly Schedule" → Run workflow

## 4. 로그 확인

- Actions 탭에서 각 실행 결과 확인
- 실패 시 에러 로그와 스크린샷 다운로드 가능

## 5. 주의사항

⚠️ **GitHub Actions는 headless 환경이므로:**
- 로그인이 복잡하거나 CAPTCHA가 있으면 실패할 수 있음
- 브라우저 자동화가 감지될 수 있음
- 실패 시 클라우드 VM (AWS EC2, GCP 등) 사용 권장

## 6. 비용

- GitHub Actions: 월 2,000분 무료 (Public 저장소는 무료)
- Private 저장소: 월 2,000분 초과 시 분당 $0.008

## 7. 문제 해결

실행이 실패하면:
1. Actions 탭에서 로그 확인
2. 스크린샷 다운로드 (있는 경우)
3. Secrets가 올바르게 설정되었는지 확인
4. 로컬에서 `BOT_HEADLESS=true`로 테스트
