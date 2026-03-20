// API 基础 URL
const API_BASE = '/api/v1';

// 当前页面
let currentPage = 'home';
let currentGoalId = null;
let currentQuiz = [];
let currentQuizIndex = 0;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadHomeStats();
    loadGoals();
});

// 导航切换
function initNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            switchPage(page);
        });
    });
}

function switchPage(page) {
    // 更新导航按钮状态
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.page === page) {
            btn.classList.add('active');
        }
    });

    // 切换页面
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`page-${page}`).classList.add('active');

    currentPage = page;

    // 页面加载时刷新数据
    switch(page) {
        case 'home':
            loadHomeStats();
            break;
        case 'goals':
            loadGoals();
            break;
        case 'cards':
            loadGoalFilter();
            loadCards();
            break;
        case 'quiz':
            loadGoalFilter('quiz');
            break;
        case 'progress':
            loadGoalFilter('progress-goal');
            break;
    }
}

// API 请求封装
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast('请求失败: ' + error.message, 'error');
        throw error;
    }
}

function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ============ 首页 ============

async function loadHomeStats() {
    try {
        const goals = await apiRequest(`${API_BASE}/knowledge/goals`);
        const totalCards = goals.reduce((sum, g) => sum + g.total_units, 0);
        const masteredCards = goals.reduce((sum, g) => {
            const progress = getGoalProgress(g.id);
            return sum + progress.mastered;
        }, 0);

        document.getElementById('stat-goals').textContent = goals.length;
        document.getElementById('stat-cards').textContent = totalCards;
        document.getElementById('stat-mastered').textContent = masteredCards;
    } catch (error) {
        console.error('Load home stats error:', error);
    }
}

// ============ 学习目标 ============

async function loadGoals() {
    showLoading();
    try {
        const goals = await apiRequest(`${API_BASE}/knowledge/goals`);
        renderGoals(goals);
    } catch (error) {
        console.error('Load goals error:', error);
    } finally {
        hideLoading();
    }
}

function renderGoals(goals) {
    const container = document.getElementById('goals-list');
    if (goals.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>还没有学习目标</p>
                <p>点击"创建目标"开始学习吧！</p>
            </div>
        `;
        return;
    }

    container.innerHTML = goals.map(goal => `
        <div class="goal-card">
            <div class="goal-header">
                <div class="goal-title">${goal.description}</div>
                <span class="goal-type">${getGoalTypeName(goal.goal_type)}</span>
            </div>
            <div class="goal-stats">
                <div class="goal-stat">
                    <div class="goal-stat-value">${goal.total_units}</div>
                    <div class="goal-stat-label">总单元</div>
                </div>
                <div class="goal-stat">
                    <div class="goal-stat-value">${goal.populated_count}</div>
                    <div class="goal-stat-label">已填充</div>
                </div>
                <div class="goal-stat">
                    <div class="goal-stat-value">${goal.populated ? '是' : '否'}</div>
                    <div class="goal-stat-label">已填充</div>
                </div>
            </div>
            <div class="goal-actions">
                <button class="btn btn-success" onclick="populateGoal(${goal.id})"
                        ${goal.populated ? 'disabled' : ''}>
                    ${goal.populated ? '已填充' : '填充卡片'}
                </button>
                <button class="btn btn-primary" onclick="viewCards(${goal.id})">
                    查看卡片
                </button>
                <button class="btn" onclick="viewProgress(${goal.id})">
                    查看进度
                </button>
                <button class="btn btn-danger" onclick="deleteGoal(${goal.id})">
                    删除
                </button>
            </div>
        </div>
    `).join('');
}

function getGoalTypeName(type) {
    const names = {
        'character': '汉字',
        'vocabulary': '词汇',
        'programming': '编程',
        'concept': '概念',
        'general': '通用'
    };
    return names[type] || type;
}

function showCreateGoalModal() {
    document.getElementById('modal-create-goal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

async function createGoal(event) {
    event.preventDefault();
    const description = document.getElementById('goal-description').value;

    showLoading();
    try {
        const result = await apiRequest(`${API_BASE}/knowledge/goals`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description })
        });

        showToast('创建成功！', 'success');
        closeModal('modal-create-goal');
        document.getElementById('goal-description').value = '';
        loadGoals();
    } catch (error) {
        console.error('Create goal error:', error);
        showToast('创建失败', 'error');
    } finally {
        hideLoading();
    }
}

async function populateGoal(goalId) {
    if (!confirm('确定要填充知识卡片吗？这可能需要1-2分钟。')) {
        return;
    }

    showLoading();
    try {
        const result = await apiRequest(`${API_BASE}/knowledge/goals/${goalId}/populate`, {
            method: 'POST'
        });

        showToast(`填充完成！生成 ${result.generated} 个卡片`, 'success');
        loadGoals();
    } catch (error) {
        console.error('Populate goal error:', error);
        showToast('填充失败', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteGoal(goalId) {
    if (!confirm('确定要删除这个学习目标吗？')) {
        return;
    }

    showLoading();
    try {
        await apiRequest(`${API_BASE}/knowledge/goals/${goalId}`, {
            method: 'DELETE'
        });

        showToast('删除成功', 'success');
        loadGoals();
    } catch (error) {
        console.error('Delete goal error:', error);
        showToast('删除失败', 'error');
    } finally {
        hideLoading();
    }
}

function viewCards(goalId) {
    currentGoalId = goalId;
    document.getElementById('goal-filter').value = goalId;
    switchPage('cards');
    loadCards();
}

function viewProgress(goalId) {
    currentGoalId = goalId;
    document.getElementById('progress-goal-filter').value = goalId;
    switchPage('progress');
    loadProgress();
}

// ============ 知识卡片 ============

async function loadGoalFilter(elementId = 'goal-filter') {
    try {
        const goals = await apiRequest(`${API_BASE}/knowledge/goals`);
        const select = document.getElementById(elementId);
        const currentValue = select.value;

        select.innerHTML = '<option value="">所有目标</option>' +
            goals.map(g => `<option value="${g.id}">${g.description}</option>`).join('');

        if (currentValue) {
            select.value = currentValue;
        }
    } catch (error) {
        console.error('Load goal filter error:', error);
    }
}

async function loadCards() {
    showLoading();
    try {
        const goalId = document.getElementById('goal-filter').value;
        let cards;

        if (goalId) {
            cards = await apiRequest(`${API_BASE}/knowledge/goals/${goalId}/cards`);
        } else {
            // 如果没有筛选，获取第一个目标的卡片
            const goals = await apiRequest(`${API_BASE}/knowledge/goals`);
            if (goals.length > 0) {
                cards = await apiRequest(`${API_BASE}/knowledge/goals/${goals[0].id}/cards`);
            } else {
                cards = [];
            }
        }

        renderCards(cards);
    } catch (error) {
        console.error('Load cards error:', error);
    } finally {
        hideLoading();
    }
}

function renderCards(cards) {
    const container = document.getElementById('cards-list');
    if (cards.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>还没有知识卡片</p>
                <p>先创建学习目标并填充知识卡片</p>
            </div>
        `;
        return;
    }

    container.innerHTML = cards.map(card => renderCard(card)).join('');
}

function renderCard(card) {
    const content = card.content || {};
    const mastery = card.mastery || {};

    return `
        <div class="card-item">
            <div class="card-header">${card.unit}</div>
            <div class="card-content">
                ${renderCardContent(card.goal_type, content)}
                <div class="card-mastery">
                    <div>
                        <strong>掌握度:</strong>
                        ${(mastery.score * 100).toFixed(0)}%
                    </div>
                    <div class="mastery-bar">
                        <div class="mastery-progress" style="width: ${mastery.score * 100}%"></div>
                    </div>
                    <div>
                        <strong>状态:</strong>
                        ${getMasteryStatusName(mastery.status)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderCardContent(goalType, content) {
    switch(goalType) {
        case 'character':
            return `
                <div class="card-field">
                    <div class="card-field-label">拼音</div>
                    <div>${content.reading || 'N/A'}</div>
                </div>
                <div class="card-field">
                    <div class="card-field-label">笔画</div>
                    <div>${content.strokes || 'N/A'}</div>
                </div>
                <div class="card-field">
                    <div class="card-field-label">部首</div>
                    <div>${content.radical || 'N/A'}</div>
                </div>
                <div class="card-field">
                    <div class="card-field-label">含义</div>
                    <div>${(content.meanings || []).join('；')}</div>
                </div>
                <div class="card-field">
                    <div class="card-field-label">组词</div>
                    <div>${(content.compounds || []).join('、')}</div>
                </div>
            `;
        case 'vocabulary':
            return `
                <div class="card-field">
                    <div class="card-field-label">发音</div>
                    <div>${content.pronunciation || 'N/A'}</div>
                </div>
                <div class="card-field">
                    <div class="card-field-label">定义</div>
                    <div>${(content.definitions || []).join('；')}</div>
                </div>
                <div class="card-field">
                    <div class="card-field-label">例句</div>
                    <div>${(content.examples || []).join('；')}</div>
                </div>
            `;
        default:
            return `
                <div class="card-field">
                    <div class="card-field-label">摘要</div>
                    <div>${content.summary || 'N/A'}</div>
                </div>
                <div class="card-field">
                    <div class="card-field-label">要点</div>
                    <div>${(content.key_points || []).join('、')}</div>
                </div>
            `;
    }
}

function getMasteryStatusName(status) {
    const names = {
        'unseen': '未接触',
        'learning': '学习中',
        'familiar': '已熟悉',
        'mastered': '已掌握'
    };
    return names[status] || status;
}

// ============ 测试练习 ============

async function generateQuiz() {
    const goalId = document.getElementById('goal-filter').value || currentGoalId;

    if (!goalId) {
        showToast('请先选择学习目标', 'error');
        return;
    }

    showLoading();
    try {
        const result = await apiRequest(`${API_BASE}/knowledge/goals/${goalId}/quiz?count=3&mode=mixed`, {
            method: 'POST'
        });

        if (!result.quizzes || result.quizzes.length === 0) {
            showToast('没有可用的测试题，请先填充知识卡片', 'error');
            return;
        }

        currentQuiz = result.quizzes;
        currentQuizIndex = 0;
        renderQuizQuestion();
        showToast('生成测试题成功！', 'success');
    } catch (error) {
        console.error('Generate quiz error:', error);
        showToast('生成测试题失败', 'error');
    } finally {
        hideLoading();
    }
}

function renderQuizQuestion() {
    if (currentQuizIndex >= currentQuiz.length) {
        showQuizComplete();
        return;
    }

    const quiz = currentQuiz[currentQuizIndex];
    const container = document.getElementById('quiz-area');

    container.innerHTML = `
        <div class="quiz-card">
            <div style="text-align: right; margin-bottom: 1rem; color: #666;">
                ${currentQuizIndex + 1} / ${currentQuiz.length}
            </div>
            <div class="quiz-question">${quiz.question}</div>
            ${quiz.hint ? `
                <div class="quiz-hint">
                    <strong>提示:</strong> ${quiz.hint}
                </div>
            ` : ''}
            <input type="text" class="quiz-answer"
                   id="quiz-answer-input"
                   placeholder="输入你的答案"
                   onkeypress="if(event.key === 'Enter') submitAnswer()">
            <div class="quiz-actions">
                <button class="btn btn-primary" onclick="submitAnswer()">提交答案</button>
                <button class="btn" onclick="showAnswer()">查看答案</button>
                <button class="btn" onclick="skipQuestion()">跳过</button>
            </div>
        </div>
    `;

    // 自动聚焦到答案输入框
    setTimeout(() => {
        document.getElementById('quiz-answer-input')?.focus();
    }, 100);
}

async function submitAnswer() {
    const answer = document.getElementById('quiz-answer-input').value.trim();
    const quiz = currentQuiz[currentQuizIndex];

    if (!answer) {
        showToast('请输入答案', 'error');
        return;
    }

    // 简化处理：不管对错都继续下一题
    // 实际应用中应该调用 API 更新掌握度
    showToast('答案已提交', 'info');
    currentQuizIndex++;
    renderQuizQuestion();
}

function showAnswer() {
    const quiz = currentQuiz[currentQuizIndex];
    showToast(`答案: ${quiz.answer}`, 'info');
}

function skipQuestion() {
    currentQuizIndex++;
    renderQuizQuestion();
}

function showQuizComplete() {
    const container = document.getElementById('quiz-area');
    container.innerHTML = `
        <div class="quiz-card" style="text-align: center;">
            <h2 style="color: var(--primary-color); margin-bottom: 1rem;">
                🎉 测试完成！
            </h2>
            <p style="font-size: 1.2rem; margin-bottom: 2rem;">
                您已完成 ${currentQuiz.length} 道测试题
            </p>
            <button class="btn btn-primary" onclick="generateQuiz()">再来一次</button>
            <button class="btn" onclick="viewCards()">查看知识卡片</button>
        </div>
    `;
}

// ============ 学习进度 ============

async function loadProgress() {
    showLoading();
    try {
        const goalId = document.getElementById('progress-goal-filter').value || currentGoalId;

        if (!goalId) {
            showToast('请先选择学习目标', 'error');
            hideLoading();
            return;
        }

        const progress = await apiRequest(`${API_BASE}/knowledge/goals/${goalId}/progress`);
        renderProgress(progress);
    } catch (error) {
        console.error('Load progress error:', error);
    } finally {
        hideLoading();
    }
}

function renderProgress(progress) {
    const container = document.getElementById('progress-area');

    const completionRate = (progress.completion_rate * 100).toFixed(1);
    const masteryRate = (progress.mastery_rate * 100).toFixed(1);

    container.innerHTML = `
        <div class="quiz-card">
            <h3 style="margin-bottom: 1.5rem; color: var(--primary-color);">
                学习进度统计
            </h3>

            <div style="margin-bottom: 2rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>完成度</strong>
                    <strong>${completionRate}%</strong>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${completionRate}%"></div>
                </div>
            </div>

            <div style="margin-bottom: 2rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>掌握度</strong>
                    <strong>${masteryRate}%</strong>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${masteryRate}%"></div>
                </div>
            </div>

            <div class="progress-stats">
                <div class="progress-stat">
                    <div class="progress-stat-value">${progress.total_units}</div>
                    <div class="progress-stat-label">总单元</div>
                </div>
                <div class="progress-stat">
                    <div class="progress-stat-value">${progress.learned}</div>
                    <div class="progress-stat-label">已学习</div>
                </div>
                <div class="progress-stat">
                    <div class="progress-stat-value">${progress.unseen}</div>
                    <div class="progress-stat-label">未接触</div>
                </div>
                <div class="progress-stat">
                    <div class="progress-stat-value">${progress.learning}</div>
                    <div class="progress-stat-label">学习中</div>
                </div>
                <div class="progress-stat">
                    <div class="progress-stat-value">${progress.familiar}</div>
                    <div class="progress-stat-label">已熟悉</div>
                </div>
                <div class="progress-stat">
                    <div class="progress-stat-value" style="color: var(--secondary-color);">
                        ${progress.mastered}
                    </div>
                    <div class="progress-stat-label">已掌握</div>
                </div>
            </div>
        </div>
    `;
}

// 辅助函数：获取目标进度（本地计算）
function getGoalProgress(goalId) {
    // 这个函数需要实际调用 API 获取进度
    // 这里返回默认值
    return { mastered: 0, learned: 0 };
}
