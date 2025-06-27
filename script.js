// Supabase 설정
const SUPABASE_URL = 'https://your-project-id.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key';

// Supabase 클라이언트 초기화 (실제 키가 설정되면 활성화)
let supabase = null;
try {
    // supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    console.log('Supabase 설정이 필요합니다.');
} catch (error) {
    console.log('Supabase 클라이언트 초기화 대기 중...');
}

// 전역 변수
let keywords = [];
let isSupabaseConnected = false;

// DOM 요소들
const keywordForm = document.getElementById('keywordForm');
const keywordsList = document.getElementById('keywordsList');
const filterSituation = document.getElementById('filterSituation');
const loading = document.getElementById('loading');
const toast = document.getElementById('toast');

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('영어 AI음성지원 프로그램이 시작되었습니다.');
    
    // 로컬 스토리지에서 데이터 로드
    loadKeywordsFromLocalStorage();
    
    // 이벤트 리스너 등록
    keywordForm.addEventListener('submit', handleSubmit);
    filterSituation.addEventListener('change', filterKeywords);
    
    // 초기 렌더링
    renderKeywords();
    
    // TTS 지원 확인
    checkTTSSupport();
});

// 폼 제출 처리
async function handleSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(keywordForm);
    const korean = formData.get('korean').trim();
    const english = formData.get('english').trim();
    const situation = formData.get('situation');
    
    if (!korean || !english || !situation) {
        showToast('모든 필드를 입력해주세요.', 'error');
        return;
    }
    
    const newKeyword = {
        id: Date.now().toString(),
        korean,
        english,
        situation,
        createdAt: new Date().toISOString()
    };
    
    showLoading(true);
    
    try {
        // Supabase에 저장 시도
        if (supabase && isSupabaseConnected) {
            await saveToSupabase(newKeyword);
        }
        
        // 로컬 배열에 추가
        keywords.unshift(newKeyword);
        
        // 로컬 스토리지에 저장
        saveKeywordsToLocalStorage();
        
        // GitHub에 백업 (실제로는 API를 통해 구현해야 함)
        await backupToGithub(newKeyword);
        
        // UI 업데이트
        renderKeywords();
        keywordForm.reset();
        
        showToast('키워드가 성공적으로 추가되었습니다!');
        
    } catch (error) {
        console.error('키워드 저장 중 오류:', error);
        showToast('키워드 저장 중 오류가 발생했습니다.', 'error');
    } finally {
        showLoading(false);
    }
}

// Supabase에 저장
async function saveToSupabase(keyword) {
    if (!supabase) {
        throw new Error('Supabase가 설정되지 않았습니다.');
    }
    
    const { data, error } = await supabase
        .from('keywords')
        .insert([
            {
                korean: keyword.korean,
                english: keyword.english,
                situation: keyword.situation,
                user_email: 'doyousee2@naver.com',
                created_at: keyword.createdAt
            }
        ]);
    
    if (error) {
        throw error;
    }
    
    return data;
}

// GitHub 백업 (시뮬레이션)
async function backupToGithub(keyword) {
    // 실제로는 GitHub API를 사용해야 합니다.
    // 여기서는 로컬 스토리지에 백업 로그를 남깁니다.
    
    const backupLog = JSON.parse(localStorage.getItem('githubBackupLog') || '[]');
    backupLog.push({
        ...keyword,
        backedUpAt: new Date().toISOString()
    });
    
    localStorage.setItem('githubBackupLog', JSON.stringify(backupLog));
    console.log('GitHub 백업 시뮬레이션 완료:', keyword);
}

// 로컬 스토리지에서 키워드 로드
function loadKeywordsFromLocalStorage() {
    const saved = localStorage.getItem('englishTutorKeywords');
    if (saved) {
        keywords = JSON.parse(saved);
    }
}

// 로컬 스토리지에 키워드 저장
function saveKeywordsToLocalStorage() {
    localStorage.setItem('englishTutorKeywords', JSON.stringify(keywords));
}

// 키워드 렌더링
function renderKeywords() {
    const filteredKeywords = getFilteredKeywords();
    
    if (filteredKeywords.length === 0) {
        keywordsList.innerHTML = '<p class="no-keywords">저장된 키워드가 없습니다.</p>';
        return;
    }
    
    const html = filteredKeywords.map(keyword => `
        <div class="keyword-item" data-id="${keyword.id}">
            <div class="keyword-content">
                <div class="keyword-text">
                    <div class="korean">${keyword.korean}</div>
                    <div class="english">${keyword.english}</div>
                    <span class="situation">${keyword.situation}</span>
                </div>
                <div class="keyword-actions">
                    <button class="listen-btn" onclick="speakText('${keyword.english}', '${keyword.korean}')">
                        🔊 듣기
                    </button>
                    <button class="delete-btn" onclick="deleteKeyword('${keyword.id}')">
                        🗑️ 삭제
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    keywordsList.innerHTML = html;
}

// 필터링된 키워드 가져오기
function getFilteredKeywords() {
    const selectedSituation = filterSituation.value;
    
    if (!selectedSituation) {
        return keywords;
    }
    
    return keywords.filter(keyword => keyword.situation === selectedSituation);
}

// 키워드 필터링
function filterKeywords() {
    renderKeywords();
}

// TTS 음성 재생
async function speakText(english, korean) {
    if (!('speechSynthesis' in window)) {
        showToast('음성 기능을 지원하지 않는 브라우저입니다.', 'error');
        return;
    }
    
    // 기존 음성 중지
    speechSynthesis.cancel();
    
    try {
        // 영어 먼저 재생
        await speak(english, 'en-US');
        
        // 잠깐 대기
        await sleep(500);
        
        // 한국어 재생
        await speak(korean, 'ko-KR');
        
    } catch (error) {
        console.error('음성 재생 오류:', error);
        showToast('음성 재생 중 오류가 발생했습니다.', 'error');
    }
}

// 음성 재생 함수
function speak(text, lang) {
    return new Promise((resolve, reject) => {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.rate = 0.8;
        utterance.pitch = 1;
        utterance.volume = 1;
        
        utterance.onend = resolve;
        utterance.onerror = reject;
        
        speechSynthesis.speak(utterance);
    });
}

// 슬립 함수
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 키워드 삭제
async function deleteKeyword(id) {
    if (!confirm('이 키워드를 삭제하시겠습니까?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        // Supabase에서 삭제
        if (supabase && isSupabaseConnected) {
            await deleteFromSupabase(id);
        }
        
        // 로컬 배열에서 제거
        keywords = keywords.filter(keyword => keyword.id !== id);
        
        // 로컬 스토리지 업데이트
        saveKeywordsToLocalStorage();
        
        // UI 업데이트
        renderKeywords();
        
        showToast('키워드가 삭제되었습니다.');
        
    } catch (error) {
        console.error('키워드 삭제 중 오류:', error);
        showToast('키워드 삭제 중 오류가 발생했습니다.', 'error');
    } finally {
        showLoading(false);
    }
}

// Supabase에서 삭제
async function deleteFromSupabase(id) {
    if (!supabase) {
        throw new Error('Supabase가 설정되지 않았습니다.');
    }
    
    const { error } = await supabase
        .from('keywords')
        .delete()
        .eq('id', id);
    
    if (error) {
        throw error;
    }
}

// TTS 지원 확인
function checkTTSSupport() {
    if (!('speechSynthesis' in window)) {
        showToast('이 브라우저는 음성 기능을 지원하지 않습니다.', 'error');
    } else {
        console.log('TTS 기능이 사용 가능합니다.');
    }
}

// 로딩 표시/숨김
function showLoading(show) {
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

// 토스트 메시지 표시
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// 개발자를 위한 유틸리티 함수들
window.englishTutorUtils = {
    // 데이터 내보내기
    exportData: function() {
        const data = {
            keywords,
            exportedAt: new Date().toISOString(),
            version: '1.0.0'
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `english-tutor-data-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },
    
    // 데이터 가져오기
    importData: function(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = JSON.parse(e.target.result);
                if (data.keywords && Array.isArray(data.keywords)) {
                    keywords = data.keywords;
                    saveKeywordsToLocalStorage();
                    renderKeywords();
                    showToast('데이터를 성공적으로 가져왔습니다.');
                } else {
                    throw new Error('올바르지 않은 데이터 형식입니다.');
                }
            } catch (error) {
                console.error('데이터 가져오기 오류:', error);
                showToast('데이터 가져오기에 실패했습니다.', 'error');
            }
        };
        reader.readAsText(file);
    },
    
    // 통계 보기
    showStats: function() {
        const stats = {
            총키워드수: keywords.length,
            상황별통계: keywords.reduce((acc, keyword) => {
                acc[keyword.situation] = (acc[keyword.situation] || 0) + 1;
                return acc;
            }, {}),
            최근추가: keywords.slice(0, 5).map(k => ({ korean: k.korean, english: k.english }))
        };
        
        console.table(stats);
        return stats;
    }
};

console.log('영어 AI음성지원 프로그램이 로드되었습니다.');
console.log('개발자 도구에서 englishTutorUtils 객체를 사용하여 데이터를 관리할 수 있습니다.');
