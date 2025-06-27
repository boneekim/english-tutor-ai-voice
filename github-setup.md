# GitHub 연동 설정 가이드

이 가이드는 영어 AI음성지원 프로그램을 GitHub와 연동하는 방법을 설명합니다.

## 1. GitHub 리포지토리 생성

### 웹 브라우저에서 설정:

1. [GitHub](https://github.com)에 boneekim 계정으로 로그인
2. "New repository" 버튼 클릭
3. 리포지토리 설정:
   - Repository name: `english-tutor-ai-voice`
   - Description: `영어 AI음성지원 프로그램 - 한국어와 영어 키워드를 저장하고 AI 음성으로 학습할 수 있는 웹 애플리케이션`
   - Visibility: Public (또는 Private)
   - README 파일 추가하지 않음 (이미 로컬에 있음)

## 2. 로컬 Git 설정

### Git 사용자 정보 설정:
```bash
git config --global user.name "boneekim"
git config --global user.email "doyousee2@naver.com"
```

### 원격 저장소 연결:
```bash
# GitHub 리포지토리와 연결
git remote add origin https://github.com/boneekim/english-tutor-ai-voice.git

# 메인 브랜치 설정
git branch -M main

# 첫 번째 푸시
git push -u origin main
```

## 3. GitHub Pages 설정 (선택사항)

GitHub Pages를 사용하여 무료로 웹사이트를 호스팅할 수 있습니다:

1. GitHub 리포지토리 페이지에서 "Settings" 탭으로 이동
2. 왼쪽 메뉴에서 "Pages" 클릭
3. Source 섹션에서:
   - Source: "Deploy from a branch" 선택
   - Branch: "main" 선택
   - Folder: "/ (root)" 선택
4. "Save" 버튼 클릭

설정 완료 후 `https://boneekim.github.io/english-tutor-ai-voice/`에서 접속 가능합니다.

## 4. 자동 백업 기능

현재 프로그램은 키워드 추가 시 GitHub에 백업하는 시뮬레이션을 포함하고 있습니다. 실제 GitHub API 연동을 위해서는:

### GitHub Personal Access Token 생성:

1. GitHub 설정 > Developer settings > Personal access tokens > Tokens (classic)
2. "Generate new token" 클릭
3. 권한 설정:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
4. 토큰을 안전한 곳에 저장

### script.js에서 실제 GitHub API 사용:

```javascript
// GitHub API 설정
const GITHUB_TOKEN = 'your-personal-access-token';
const GITHUB_REPO = 'boneekim/english-tutor-ai-voice';

// 실제 GitHub 백업 함수
async function backupToGithub(keyword) {
    try {
        const response = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/contents/data/keywords.json`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: `Add keyword: ${keyword.korean} - ${keyword.english}`,
                content: btoa(JSON.stringify(keywords, null, 2)),
                sha: await getFileSha('data/keywords.json') // 기존 파일의 SHA 필요
            })
        });
        
        if (response.ok) {
            console.log('GitHub 백업 성공');
        } else {
            throw new Error('GitHub 백업 실패');
        }
    } catch (error) {
        console.error('GitHub 백업 오류:', error);
    }
}
```

## 5. 워크플로우 설정

`.github/workflows/deploy.yml` 파일을 생성하여 자동 배포 설정:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Pages
      uses: actions/configure-pages@v3
      
    - name: Upload artifact
      uses: actions/upload-pages-artifact@v2
      with:
        path: '.'
        
    - name: Deploy to GitHub Pages
      id: deployment
      uses: actions/deploy-pages@v2
```

## 6. 브랜치 전략

### 기본 브랜치 구조:
- `main`: 안정적인 프로덕션 코드
- `develop`: 개발 중인 기능들
- `feature/*`: 새로운 기능 개발

### 워크플로우:
```bash
# 새 기능 개발
git checkout -b feature/new-feature
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin feature/new-feature

# Pull Request 생성 후 main에 병합
git checkout main
git pull origin main
```

## 7. 이슈 템플릿

`.github/ISSUE_TEMPLATE/bug_report.md`:
```markdown
---
name: Bug report
about: 버그 리포트
title: '[BUG] '
labels: bug
assignees: boneekim

---

**버그 설명**
발생한 버그에 대한 명확하고 간결한 설명

**재현 방법**
1. 이동할 페이지
2. 클릭할 요소
3. 스크롤 또는 기타 작업
4. 발생하는 오류

**예상 동작**
정상적으로 작동해야 하는 방식

**스크린샷**
가능하다면 스크린샷 첨부

**환경:**
- OS: [예: iOS]
- 브라우저: [예: chrome, safari]
- 버전: [예: 22]
```

## 8. 보안 고려사항

### 환경 변수 관리:
- API 키는 절대 소스 코드에 직접 포함하지 않음
- GitHub Secrets를 사용하여 민감한 정보 관리
- `.env` 파일은 `.gitignore`에 포함

### Repository Settings:
- Branch protection rules 설정
- Required status checks 활성화
- Require branches to be up to date before merging

---

설정 완료 후 프로젝트가 GitHub에서 안전하게 관리되며, 자동 배포와 백업이 가능합니다.
