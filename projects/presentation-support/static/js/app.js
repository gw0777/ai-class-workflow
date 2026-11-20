// Global variables
let parsedData = null;
let analysisResults = null;

// DOM Elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileDetails = document.getElementById('fileDetails');
const settingsSection = document.getElementById('settingsSection');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const aiStatus = document.getElementById('aiStatus');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    checkAIStatus();
});

function initializeEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadBox.addEventListener('click', () => fileInput.click());
    uploadBox.addEventListener('dragover', handleDragOver);
    uploadBox.addEventListener('dragleave', handleDragLeave);
    uploadBox.addEventListener('drop', handleDrop);

    // Analyze button
    analyzeBtn.addEventListener('click', handleAnalyze);

    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Export buttons
    document.getElementById('exportBtn').addEventListener('click', exportResults);
    document.getElementById('printBtn').addEventListener('click', () => window.print());
}

// Check AI status
async function checkAIStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();

        if (data.ai_enabled) {
            aiStatus.textContent = '✅ AI 기능 활성화됨';
            aiStatus.style.color = '#48bb78';
        } else {
            aiStatus.textContent = '⚠️ AI 기능 비활성화 (룰 기반 생성 사용)';
            aiStatus.style.color = '#f6ad55';
        }
    } catch (error) {
        aiStatus.textContent = '❌ 서버 연결 실패';
        aiStatus.style.color = '#fc8181';
    }
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadBox.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadBox.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadBox.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelect({ target: { files: files } });
    }
}

// Handle file selection
async function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.ms-powerpoint',
                       'application/vnd.openxmlformats-officedocument.presentationml.presentation'];

    if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|ppt|pptx)$/i)) {
        alert('지원하지 않는 파일 형식입니다. PDF 또는 PPTX 파일만 업로드 가능합니다.');
        return;
    }

    // Upload file
    showLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            parsedData = result.parsed_data;
            displayFileInfo(result);
            settingsSection.style.display = 'block';
            showLoading(false);
        } else {
            alert(`파일 업로드 실패: ${result.error}`);
            showLoading(false);
        }
    } catch (error) {
        alert(`오류 발생: ${error.message}`);
        showLoading(false);
    }
}

// Display file information
function displayFileInfo(result) {
    const summary = result.summary;

    fileDetails.innerHTML = `
        <div class="file-detail-item">
            <span class="file-detail-label">파일명</span>
            <span class="file-detail-value">${result.filename}</span>
        </div>
        <div class="file-detail-item">
            <span class="file-detail-label">파일 형식</span>
            <span class="file-detail-value">${summary.file_type.toUpperCase()}</span>
        </div>
        <div class="file-detail-item">
            <span class="file-detail-label">총 슬라이드 수</span>
            <span class="file-detail-value">${summary.total_slides}개</span>
        </div>
        <div class="file-detail-item">
            <span class="file-detail-label">총 단어 수</span>
            <span class="file-detail-value">${summary.total_words.toLocaleString()}개</span>
        </div>
        <div class="file-detail-item">
            <span class="file-detail-label">슬라이드당 평균 단어</span>
            <span class="file-detail-value">${Math.round(summary.avg_words_per_slide)}개</span>
        </div>
        <div class="file-detail-item">
            <span class="file-detail-label">내용이 있는 슬라이드</span>
            <span class="file-detail-value">${summary.slides_with_content}개</span>
        </div>
    `;

    fileInfo.style.display = 'block';
}

// Handle analyze
async function handleAnalyze() {
    if (!parsedData) {
        alert('먼저 파일을 업로드해주세요.');
        return;
    }

    const totalTime = parseInt(document.getElementById('totalTime').value);
    const style = document.getElementById('presentationStyle').value;
    const qaCount = parseInt(document.getElementById('qaCount').value);

    showLoading(true);
    settingsSection.style.display = 'none';

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                parsed_data: parsedData,
                total_time: totalTime,
                style: style,
                qa_count: qaCount
            })
        });

        const result = await response.json();

        if (result.success) {
            analysisResults = result;
            displayResults(result);
            showLoading(false);
            resultsSection.style.display = 'block';
        } else {
            alert(`분석 실패: ${result.error}`);
            showLoading(false);
            settingsSection.style.display = 'block';
        }
    } catch (error) {
        alert(`오류 발생: ${error.message}`);
        showLoading(false);
        settingsSection.style.display = 'block';
    }
}

// Display results
function displayResults(results) {
    displayScript(results.script);
    displayTiming(results.script);
    displayQA(results.qa);
    displayTips(results.tips);
}

// Display script
function displayScript(scriptData) {
    const scriptContent = document.getElementById('scriptContent');
    const scripts = scriptData.scripts || [];

    let html = '';

    if (scriptData.generated_by === 'ai') {
        html += '<div class="ai-badge" style="background: #48bb78; color: white; padding: 8px 15px; border-radius: 20px; display: inline-block; margin-bottom: 20px;">✨ AI로 생성됨</div>';
    }

    scripts.forEach(script => {
        const keyPointsHtml = script.key_points && script.key_points.length > 0 ? `
            <div class="key-points">
                <h5>핵심 포인트</h5>
                <ul>
                    ${script.key_points.map(point => `<li>${point}</li>`).join('')}
                </ul>
            </div>
        ` : '';

        html += `
            <div class="script-item">
                <div class="script-header">
                    <span class="slide-number">슬라이드 ${script.slide_number}</span>
                    <span class="time-badge">⏱️ ${script.time_allocation}분</span>
                </div>
                <div class="script-text">${script.script}</div>
                ${keyPointsHtml}
            </div>
        `;
    });

    scriptContent.innerHTML = html;
}

// Display timing
function displayTiming(scriptData) {
    const timingContent = document.getElementById('timingContent');
    const scripts = scriptData.scripts || [];
    const totalTime = scriptData.total_time || 10;

    let html = '<div class="timing-chart">';

    scripts.forEach(script => {
        const percentage = (script.time_allocation / totalTime) * 100;

        html += `
            <div class="timing-item">
                <div class="timing-slide">슬라이드 ${script.slide_number}</div>
                <div class="timing-bar-container">
                    <div class="timing-bar" style="width: ${percentage}%">
                        ${Math.round(percentage)}%
                    </div>
                </div>
                <div class="timing-duration">${script.time_allocation}분</div>
            </div>
        `;
    });

    html += '</div>';

    // Summary
    const totalAllocated = scripts.reduce((sum, s) => sum + s.time_allocation, 0);
    html += `
        <div class="timing-summary" style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
            <h4 style="color: #667eea; margin-bottom: 15px;">⏱️ 시간 요약</h4>
            <div class="file-detail-item">
                <span class="file-detail-label">목표 발표 시간</span>
                <span class="file-detail-value">${totalTime}분</span>
            </div>
            <div class="file-detail-item">
                <span class="file-detail-label">할당된 시간</span>
                <span class="file-detail-value">${totalAllocated.toFixed(1)}분</span>
            </div>
            <div class="file-detail-item">
                <span class="file-detail-label">여유 시간</span>
                <span class="file-detail-value" style="color: ${totalTime - totalAllocated >= 0 ? '#48bb78' : '#fc8181'}">${(totalTime - totalAllocated).toFixed(1)}분</span>
            </div>
        </div>
    `;

    timingContent.innerHTML = html;
}

// Display Q&A
function displayQA(qaData) {
    const qaContent = document.getElementById('qaContent');
    const questions = qaData.questions || [];

    let html = '';

    if (qaData.generated_by === 'ai') {
        html += '<div class="ai-badge" style="background: #48bb78; color: white; padding: 8px 15px; border-radius: 20px; display: inline-block; margin-bottom: 20px;">✨ AI로 생성됨</div>';
    }

    questions.forEach((qa, index) => {
        const typeLabels = {
            'detail': '세부사항',
            'application': '실용적용',
            'critical': '비판적',
            'expansion': '확장성'
        };

        html += `
            <div class="qa-item">
                <div class="question">${qa.question}</div>
                <div class="answer">${qa.answer}</div>
                <div class="qa-meta">
                    <span class="qa-type-badge">${typeLabels[qa.type] || qa.type}</span>
                    ${qa.related_slide ? `<span class="qa-slide-ref">📊 슬라이드 ${qa.related_slide} 관련</span>` : ''}
                </div>
            </div>
        `;
    });

    qaContent.innerHTML = html;
}

// Display tips
function displayTips(tipsData) {
    const tipsContent = document.getElementById('tipsContent');

    let html = '';

    // Preparation tips
    if (tipsData.preparation) {
        html += `
            <div class="tips-section">
                <h4>📋 발표 전 준비사항</h4>
                <ul class="tips-list">
                    ${tipsData.preparation.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Delivery tips
    if (tipsData.delivery) {
        html += `
            <div class="tips-section">
                <h4>🎤 발표 중 유의사항</h4>
                <ul class="tips-list">
                    ${tipsData.delivery.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Time management
    if (tipsData.time_management) {
        html += `
            <div class="tips-section">
                <h4>⏰ 시간 관리</h4>
                <ul class="tips-list">
                    ${tipsData.time_management.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Common mistakes
    if (tipsData.common_mistakes) {
        html += `
            <div class="tips-section">
                <h4>⚠️ 흔한 실수 피하기</h4>
                <ul class="tips-list">
                    ${tipsData.common_mistakes.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Checklist
    if (tipsData.checklist) {
        html += `
            <div class="tips-section">
                <h4>✅ 발표 준비 체크리스트</h4>
                <ul class="checklist">
                    ${tipsData.checklist.map((item, index) => `
                        <li class="checklist-item">
                            <input type="checkbox" id="check${index}" ${item.checked ? 'checked' : ''}>
                            <label for="check${index}">${item.item}</label>
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }

    tipsContent.innerHTML = html;
}

// Switch tab
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    const tabMap = {
        'script': 'scriptTab',
        'timing': 'timingTab',
        'qa': 'qaTab',
        'tips': 'tipsTab'
    };

    document.getElementById(tabMap[tabName]).classList.add('active');
}

// Show/hide loading
function showLoading(show) {
    loadingSection.style.display = show ? 'block' : 'none';
}

// Export results to Markdown
function exportResults() {
    if (!analysisResults) {
        alert('분석 결과가 없습니다.');
        return;
    }

    let markdown = '# 발표 지원 자료\n\n';
    markdown += `생성일: ${new Date().toLocaleString('ko-KR')}\n\n`;
    markdown += '---\n\n';

    // Script
    markdown += '## 📝 발표 스크립트\n\n';
    analysisResults.script.scripts.forEach(script => {
        markdown += `### 슬라이드 ${script.slide_number} (${script.time_allocation}분)\n\n`;
        markdown += `${script.script}\n\n`;
        if (script.key_points && script.key_points.length > 0) {
            markdown += '**핵심 포인트:**\n';
            script.key_points.forEach(point => {
                markdown += `- ${point}\n`;
            });
            markdown += '\n';
        }
    });

    markdown += '---\n\n';

    // Q&A
    markdown += '## ❓ 예상 질문 및 답변\n\n';
    analysisResults.qa.questions.forEach((qa, index) => {
        markdown += `### Q${index + 1}: ${qa.question}\n\n`;
        markdown += `**A:** ${qa.answer}\n\n`;
    });

    markdown += '---\n\n';

    // Tips
    markdown += '## 💡 발표 팁\n\n';
    const tips = analysisResults.tips;

    if (tips.preparation) {
        markdown += '### 📋 발표 전 준비사항\n\n';
        tips.preparation.forEach(tip => {
            markdown += `- ${tip}\n`;
        });
        markdown += '\n';
    }

    if (tips.delivery) {
        markdown += '### 🎤 발표 중 유의사항\n\n';
        tips.delivery.forEach(tip => {
            markdown += `- ${tip}\n`;
        });
        markdown += '\n';
    }

    if (tips.checklist) {
        markdown += '### ✅ 체크리스트\n\n';
        tips.checklist.forEach(item => {
            markdown += `- [ ] ${item.item}\n`;
        });
        markdown += '\n';
    }

    // Download
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `presentation_support_${new Date().getTime()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
