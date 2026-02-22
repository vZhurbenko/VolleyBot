const API_URL = window.location.origin;

// ==================== Auth Functions ====================

async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
            credentials: 'include'
        });

        console.log('admin.js checkAuth status:', response.status);

        if (response.ok) {
            const user = await response.json();
            console.log('admin.js: пользователь авторизован, показываем панель');
            showAdminPanel(user);
        } else {
            // Не авторизован - перенаправляем на страницу входа
            console.log('admin.js: не авторизован, редирект на /');
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Ошибка проверки авторизации:', error);
        window.location.href = '/';
    }
}

async function onTelegramAuth(user) {
    showMessage('login-message', 'Авторизация...', 'success');

    try {
        const response = await fetch(`${API_URL}/api/auth/telegram`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(user),
            credentials: 'include'
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showAdminPanel(result.user);
        } else {
            showMessage('login-message', result.detail || 'Ошибка авторизации', 'error');
            if (response.status === 403) {
                document.getElementById('telegram-login').classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showMessage('login-message', 'Ошибка соединения с сервером', 'error');
    }
}

async function logout() {
    try {
        const response = await fetch(`${API_URL}/api/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        console.log('Logout response:', response.status);
        // После выхода перенаправляем на страницу входа
        window.location.href = '/';
    } catch (error) {
        console.error('Ошибка выхода:', error);
        window.location.href = '/';
    }
}

// ==================== View Functions ====================

function showAdminPanel(user) {
    console.log('showAdminPanel: показываем админ-панель');
    const adminView = document.getElementById('admin-view');
    if (adminView) {
        adminView.classList.remove('hidden');
    }

    const userPhoto = document.getElementById('user-photo');
    if (userPhoto) {
        userPhoto.src = user.photo_url || 'https://via.placeholder.com/40';
    }
    
    const userName = document.getElementById('user-name');
    if (userName) {
        userName.textContent = `${user.first_name} ${user.last_name || ''}`.trim();
    }

    loadTemplate();
    loadSchedules();
    loadActivePolls();
    loadAdmins();
}

function showMessage(elementId, text, type) {
    const el = document.getElementById(elementId);
    el.textContent = text;
    el.className = `message ${type}`;
    el.classList.remove('hidden');

    if (type === 'success') {
        setTimeout(() => el.classList.add('hidden'), 3000);
    }
}

// ==================== Load Functions ====================

async function loadTemplate() {
    try {
        const response = await fetch(`${API_URL}/api/admin/settings/template`, {
            credentials: 'include'
        });
        if (response.ok) {
            const template = await response.json();
            renderTemplate(template);
        }
    } catch (error) {
        console.error('Ошибка загрузки шаблона:', error);
    }
}

function renderTemplate(template) {
    const html = `
        <div class="form-group">
            <label>Название</label>
            <input type="text" id="template-name" value="${template.name || ''}">
        </div>
        <div class="form-group">
            <label>Описание</label>
            <textarea id="template-description" rows="2">${template.description || ''}</textarea>
        </div>
        <div class="form-group">
            <label>День тренировки</label>
            <input type="text" id="template-training-day" value="${template.training_day || ''}">
        </div>
        <div class="form-group">
            <label>День опроса</label>
            <input type="text" id="template-poll-day" value="${template.poll_day || ''}">
        </div>
        <div class="form-group">
            <label>Время</label>
            <input type="text" id="template-training-time" value="${template.training_time || ''}">
        </div>
        <button class="btn" onclick="saveTemplate()">Сохранить</button>
    `;
    document.getElementById('template-content').innerHTML = html;
}

async function saveTemplate() {
    const template = {
        name: document.getElementById('template-name').value,
        description: document.getElementById('template-description').value,
        training_day: document.getElementById('template-training-day').value,
        poll_day: document.getElementById('template-poll-day').value,
        training_time: document.getElementById('template-training-time').value,
        options: ['Буду', '50/50', 'Не буду'],
        enabled: true
    };

    try {
        const response = await fetch(`${API_URL}/api/admin/settings/template`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(template)
        });

        if (response.ok) {
            alert('Шаблон сохранён!');
        } else {
            alert('Ошибка сохранения');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка сохранения');
    }
}

async function loadSchedules() {
    try {
        const response = await fetch(`${API_URL}/api/admin/settings/schedules`, {
            credentials: 'include'
        });
        if (response.ok) {
            const schedules = await response.json();
            renderSchedules(schedules);
        }
    } catch (error) {
        console.error('Ошибка загрузки расписаний:', error);
    }
}

function renderSchedules(schedules) {
    if (!schedules || schedules.length === 0) {
        document.getElementById('schedules-content').innerHTML = `
            <p>Нет расписаний</p>
            <button class="btn" onclick="showAddScheduleForm()" style="margin-top: 1rem;">Добавить расписание</button>
        `;
        return;
    }

    let html = `
        <button class="btn" onclick="showAddScheduleForm()" style="margin-bottom: 1rem;">Добавить расписание</button>
    `;

    html += schedules.map(s => `
        <div class="list-item" style="align-items: flex-start;">
            <div>
                <strong>${s.name}</strong><br>
                <small>${s.training_day} → ${s.poll_day} в ${s.training_time}</small><br>
                <small>Chat: ${s.chat_id}${s.message_thread_id ? ' (топик ' + s.message_thread_id + ')' : ''}</small>
            </div>
            <div class="list-item-actions">
                <span class="tag ${s.enabled ? 'tag-enabled' : 'tag-disabled'}">
                    ${s.enabled ? 'Активно' : 'Отключено'}
                </span>
                <button class="btn btn-small" onclick="editSchedule('${s.id}')">✎</button>
                <button class="btn btn-danger btn-small" onclick="deleteSchedule('${s.id}')">✕</button>
            </div>
        </div>
    `).join('');

    document.getElementById('schedules-content').innerHTML = html;
}

async function showAddScheduleForm() {
    let defaultTemplate = {
        name: '',
        training_day: 'sunday',
        poll_day: 'friday',
        training_time: '18:00 - 20:00',
        default_chat_id: '',
        default_topic_id: null
    };

    try {
        const response = await fetch(`${API_URL}/api/admin/settings/template`, {
            credentials: 'include'
        });
        if (response.ok) {
            const template = await response.json();
            if (template) {
                defaultTemplate = {
                    name: template.name || defaultTemplate.name,
                    training_day: template.training_day || defaultTemplate.training_day,
                    poll_day: template.poll_day || defaultTemplate.poll_day,
                    training_time: template.training_time || defaultTemplate.training_time,
                    default_chat_id: template.default_chat_id || defaultTemplate.default_chat_id,
                    default_topic_id: 'default_topic_id' in template ? template.default_topic_id : defaultTemplate.default_topic_id
                };
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки шаблона:', error);
    }

    const html = `
        <div class="form-group">
            <label>Название</label>
            <input type="text" id="schedule-name" value="${defaultTemplate.name}" placeholder="Например: Воскресенье">
        </div>
        <div class="form-group">
            <label>Chat ID</label>
            <input type="text" id="schedule-chat-id" value="${defaultTemplate.default_chat_id}" placeholder="-1002588984009">
        </div>
        <div class="form-group">
            <label>Topic ID (опционально)</label>
            <input type="number" id="schedule-topic-id" value="${defaultTemplate.default_topic_id !== null && defaultTemplate.default_topic_id !== undefined ? defaultTemplate.default_topic_id : ''}" placeholder="Оставьте пустым если не используется">
        </div>
        <div class="form-group">
            <label>День тренировки</label>
            <select id="schedule-training-day">
                <option value="monday" ${defaultTemplate.training_day === 'monday' ? 'selected' : ''}>Понедельник</option>
                <option value="tuesday" ${defaultTemplate.training_day === 'tuesday' ? 'selected' : ''}>Вторник</option>
                <option value="wednesday" ${defaultTemplate.training_day === 'wednesday' ? 'selected' : ''}>Среда</option>
                <option value="thursday" ${defaultTemplate.training_day === 'thursday' ? 'selected' : ''}>Четверг</option>
                <option value="friday" ${defaultTemplate.training_day === 'friday' ? 'selected' : ''}>Пятница</option>
                <option value="saturday" ${defaultTemplate.training_day === 'saturday' ? 'selected' : ''}>Суббота</option>
                <option value="sunday" ${defaultTemplate.training_day === 'sunday' ? 'selected' : ''}>Воскресенье</option>
            </select>
        </div>
        <div class="form-group">
            <label>День создания опроса</label>
            <select id="schedule-poll-day">
                <option value="monday" ${defaultTemplate.poll_day === 'monday' ? 'selected' : ''}>Понедельник</option>
                <option value="tuesday" ${defaultTemplate.poll_day === 'tuesday' ? 'selected' : ''}>Вторник</option>
                <option value="wednesday" ${defaultTemplate.poll_day === 'wednesday' ? 'selected' : ''}>Среда</option>
                <option value="thursday" ${defaultTemplate.poll_day === 'thursday' ? 'selected' : ''}>Четверг</option>
                <option value="friday" ${defaultTemplate.poll_day === 'friday' ? 'selected' : ''}>Пятница</option>
                <option value="saturday" ${defaultTemplate.poll_day === 'saturday' ? 'selected' : ''}>Суббота</option>
                <option value="sunday" ${defaultTemplate.poll_day === 'sunday' ? 'selected' : ''}>Воскресенье</option>
            </select>
        </div>
        <div class="form-group">
            <label>Время тренировки</label>
            <input type="text" id="schedule-training-time" value="${defaultTemplate.training_time}" placeholder="18:00 - 20:00">
        </div>
        <div class="form-group">
            <label>Включено</label>
            <input type="checkbox" id="schedule-enabled" checked style="width: auto;">
        </div>
        <div class="form-actions">
            <button class="btn" onclick="addSchedule()">Сохранить</button>
            <button class="btn btn-secondary" onclick="loadSchedules()">Отмена</button>
        </div>
    `;
    document.getElementById('schedules-content').innerHTML = html;
}

async function addSchedule() {
    const schedule = {
        name: document.getElementById('schedule-name').value,
        chat_id: document.getElementById('schedule-chat-id').value,
        message_thread_id: document.getElementById('schedule-topic-id').value ? parseInt(document.getElementById('schedule-topic-id').value) : null,
        training_day: document.getElementById('schedule-training-day').value,
        poll_day: document.getElementById('schedule-poll-day').value,
        training_time: document.getElementById('schedule-training-time').value,
        enabled: document.getElementById('schedule-enabled').checked
    };

    if (!schedule.name || !schedule.chat_id) {
        alert('Заполните название и Chat ID');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/admin/settings/schedules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(schedule)
        });

        if (response.ok) {
            loadSchedules();
        } else {
            const error = await response.json();
            alert(error.detail || 'Ошибка добавления');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка добавления расписания');
    }
}

async function editSchedule(scheduleId) {
    try {
        const response = await fetch(`${API_URL}/api/admin/settings/schedules`, {
            credentials: 'include'
        });
        if (response.ok) {
            const schedules = await response.json();
            const schedule = schedules.find(s => s.id === scheduleId);
            if (schedule) {
                showEditScheduleForm(schedule);
            }
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка загрузки расписания');
    }
}

function showEditScheduleForm(schedule) {
    const html = `
        <div class="form-group">
            <label>Название</label>
            <input type="text" id="schedule-name" value="${schedule.name || ''}">
        </div>
        <div class="form-group">
            <label>Chat ID</label>
            <input type="text" id="schedule-chat-id" value="${schedule.chat_id || ''}">
        </div>
        <div class="form-group">
            <label>Topic ID (опционально)</label>
            <input type="number" id="schedule-topic-id" value="${schedule.message_thread_id || ''}" placeholder="Оставьте пустым если не используется">
        </div>
        <div class="form-group">
            <label>День тренировки</label>
            <select id="schedule-training-day">
                <option value="monday" ${schedule.training_day === 'monday' ? 'selected' : ''}>Понедельник</option>
                <option value="tuesday" ${schedule.training_day === 'tuesday' ? 'selected' : ''}>Вторник</option>
                <option value="wednesday" ${schedule.training_day === 'wednesday' ? 'selected' : ''}>Среда</option>
                <option value="thursday" ${schedule.training_day === 'thursday' ? 'selected' : ''}>Четверг</option>
                <option value="friday" ${schedule.training_day === 'friday' ? 'selected' : ''}>Пятница</option>
                <option value="saturday" ${schedule.training_day === 'saturday' ? 'selected' : ''}>Суббота</option>
                <option value="sunday" ${schedule.training_day === 'sunday' ? 'selected' : ''}>Воскресенье</option>
            </select>
        </div>
        <div class="form-group">
            <label>День создания опроса</label>
            <select id="schedule-poll-day">
                <option value="monday" ${schedule.poll_day === 'monday' ? 'selected' : ''}>Понедельник</option>
                <option value="tuesday" ${schedule.poll_day === 'tuesday' ? 'selected' : ''}>Вторник</option>
                <option value="wednesday" ${schedule.poll_day === 'wednesday' ? 'selected' : ''}>Среда</option>
                <option value="thursday" ${schedule.poll_day === 'thursday' ? 'selected' : ''}>Четверг</option>
                <option value="friday" ${schedule.poll_day === 'friday' ? 'selected' : ''}>Пятница</option>
                <option value="saturday" ${schedule.poll_day === 'saturday' ? 'selected' : ''}>Суббота</option>
                <option value="sunday" ${schedule.poll_day === 'sunday' ? 'selected' : ''}>Воскресенье</option>
            </select>
        </div>
        <div class="form-group">
            <label>Время тренировки</label>
            <input type="text" id="schedule-training-time" value="${schedule.training_time || ''}">
        </div>
        <div class="form-group">
            <label>Включено</label>
            <input type="checkbox" id="schedule-enabled" ${schedule.enabled ? 'checked' : ''} style="width: auto;">
        </div>
        <div class="form-actions">
            <button class="btn" onclick="updateSchedule('${schedule.id}')">Сохранить</button>
            <button class="btn btn-secondary" onclick="loadSchedules()">Отмена</button>
        </div>
    `;
    document.getElementById('schedules-content').innerHTML = html;
}

async function updateSchedule(scheduleId) {
    const updates = {
        name: document.getElementById('schedule-name').value,
        chat_id: document.getElementById('schedule-chat-id').value,
        message_thread_id: document.getElementById('schedule-topic-id').value ? parseInt(document.getElementById('schedule-topic-id').value) : null,
        training_day: document.getElementById('schedule-training-day').value,
        poll_day: document.getElementById('schedule-poll-day').value,
        training_time: document.getElementById('schedule-training-time').value,
        enabled: document.getElementById('schedule-enabled').checked
    };

    try {
        const response = await fetch(`${API_URL}/api/admin/settings/schedules/${scheduleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(updates)
        });

        if (response.ok) {
            loadSchedules();
        } else {
            const error = await response.json();
            alert(error.detail || 'Ошибка обновления');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка обновления расписания');
    }
}

async function deleteSchedule(scheduleId) {
    if (!confirm('Удалить это расписание?')) return;

    try {
        const response = await fetch(`${API_URL}/api/admin/settings/schedules/${scheduleId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            loadSchedules();
        } else {
            alert('Ошибка удаления');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка удаления расписания');
    }
}

async function loadActivePolls() {
    try {
        const response = await fetch(`${API_URL}/api/admin/settings/active_polls`, {
            credentials: 'include'
        });
        if (response.ok) {
            const polls = await response.json();
            renderActivePolls(polls);
        }
    } catch (error) {
        console.error('Ошибка загрузки опросов:', error);
    }
}

function renderActivePolls(polls) {
    if (!polls || polls.length === 0) {
        document.getElementById('active-polls-content').innerHTML = '<p>Нет активных опросов</p>';
        return;
    }

    const html = polls.map(p => `
        <div class="list-item">
            <div>
                <strong>Опрос #${p.id.substr(0, 8)}</strong><br>
                <small>Chat: ${p.chat_id}</small>
            </div>
        </div>
    `).join('');

    document.getElementById('active-polls-content').innerHTML = html;
}

async function loadAdmins() {
    try {
        const response = await fetch(`${API_URL}/api/admin/settings/admin_ids`, {
            credentials: 'include'
        });
        if (response.ok) {
            const data = await response.json();
            renderAdmins(data.admin_ids);
        }
    } catch (error) {
        console.error('Ошибка загрузки админов:', error);
    }
}

function renderAdmins(adminIds) {
    if (!adminIds || adminIds.length === 0) {
        document.getElementById('admins-content').innerHTML = `
            <p>Нет администраторов</p>
            <div class="form-group" style="margin-top: 1rem;">
                <label>Добавить администратора</label>
                <div class="input-group">
                    <input type="number" id="new-admin-id" placeholder="Telegram ID">
                    <button class="btn" onclick="addAdmin()">Добавить</button>
                </div>
            </div>
        `;
        return;
    }

    let html = `
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Добавить администратора</label>
            <div class="input-group">
                <input type="number" id="new-admin-id" placeholder="Telegram ID">
                <button class="btn" onclick="addAdmin()">Добавить</button>
            </div>
        </div>
    `;

    html += adminIds.map(id => `
        <div class="list-item">
            <div>
                <span>ID: ${id}</span>
            </div>
            <div class="list-item-actions">
                <span class="tag tag-enabled">Админ</span>
                <button class="btn btn-danger btn-small" onclick="removeAdmin(${id})">✕</button>
            </div>
        </div>
    `).join('');

    document.getElementById('admins-content').innerHTML = html;
}

async function addAdmin() {
    const adminId = document.getElementById('new-admin-id').value;
    if (!adminId) {
        alert('Введите Telegram ID');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/admin/settings/admin_ids`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ admin_id: parseInt(adminId) })
        });

        if (response.ok) {
            document.getElementById('new-admin-id').value = '';
            loadAdmins();
        } else {
            const error = await response.json();
            alert(error.detail || 'Ошибка добавления');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка добавления администратора');
    }
}

async function removeAdmin(adminId) {
    if (!confirm(`Удалить администратора ${adminId}?`)) return;

    try {
        const response = await fetch(`${API_URL}/api/admin/settings/admin_ids/${adminId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            loadAdmins();
        } else {
            alert('Ошибка удаления');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка удаления администратора');
    }
}

// ==================== Init ====================

document.addEventListener('DOMContentLoaded', checkAuth);
