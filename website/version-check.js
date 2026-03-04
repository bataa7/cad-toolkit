// 版本管理和更新检查系统

let versionData = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadVersionInfo();
    checkForUpdates();
});

// 加载版本信息
async function loadVersionInfo() {
    try {
        const response = await fetch('version.json');
        versionData = await response.json();
        
        // 更新页面显示
        updateVersionDisplay();
        loadChangelog();
    } catch (error) {
        console.error('加载版本信息失败:', error);
    }
}

// 更新版本显示
function updateVersionDisplay() {
    if (!versionData) return;
    
    // 更新版本号
    const versionTitle = document.getElementById('version-title');
    if (versionTitle) {
        versionTitle.textContent = `CAD工具包 v${versionData.latest_version}`;
    }
    
    // 更新发布日期
    const releaseDate = document.getElementById('release-date');
    if (releaseDate) {
        releaseDate.textContent = `发布日期：${versionData.release_date}`;
    }
    
    // 更新文件大小
    const fileSize = document.getElementById('file-size');
    if (fileSize) {
        const sizeMB = (versionData.file_size / 1024 / 1024).toFixed(0);
        fileSize.textContent = `(${sizeMB} MB)`;
    }
    
    // 更新下载次数
    const downloadCount = document.getElementById('download-count');
    if (downloadCount && versionData.changelog[0]) {
        downloadCount.textContent = `下载次数：${versionData.changelog[0].download_count}`;
    }
}

// 加载更新日志
function loadChangelog() {
    if (!versionData || !versionData.changelog) return;
    
    const changelogContent = document.getElementById('changelog-content');
    if (!changelogContent) return;
    
    let html = '';
    
    versionData.changelog.forEach((version, index) => {
        const typeLabel = getVersionTypeLabel(version.type);
        const isLatest = index === 0;
        
        html += `
            <div class="changelog-item ${isLatest ? 'latest' : ''}">
                <div class="changelog-header">
                    <h4>
                        v${version.version}
                        ${isLatest ? '<span class="latest-badge">最新</span>' : ''}
                        <span class="version-type ${version.type}">${typeLabel}</span>
                    </h4>
                    <span class="changelog-date">${version.date}</span>
                </div>
                <ul class="changelog-list">
                    ${version.changes.map(change => `<li>${change}</li>`).join('')}
                </ul>
                ${version.download_count > 0 ? `<p class="changelog-stats">下载次数：${version.download_count}</p>` : ''}
            </div>
        `;
    });
    
    changelogContent.innerHTML = html;
}

// 获取版本类型标签
function getVersionTypeLabel(type) {
    const labels = {
        'major': '重大更新',
        'minor': '功能更新',
        'patch': '修复更新'
    };
    return labels[type] || '更新';
}

// 切换更新日志显示
function toggleChangelog() {
    const changelogSection = document.getElementById('changelog-section');
    if (changelogSection) {
        if (changelogSection.style.display === 'none') {
            changelogSection.style.display = 'block';
            changelogSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            changelogSection.style.display = 'none';
        }
    }
}

// 检查更新（模拟客户端检查）
function checkForUpdates() {
    // 从localStorage获取当前安装的版本
    const installedVersion = localStorage.getItem('installed_version');
    
    if (!installedVersion) {
        // 首次访问，显示欢迎提示
        return;
    }
    
    // 比较版本
    if (versionData && compareVersions(versionData.latest_version, installedVersion) > 0) {
        showUpdateNotification();
    }
}

// 版本比较
function compareVersions(v1, v2) {
    const parts1 = v1.split('.').map(Number);
    const parts2 = v2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
        const part1 = parts1[i] || 0;
        const part2 = parts2[i] || 0;
        
        if (part1 > part2) return 1;
        if (part1 < part2) return -1;
    }
    
    return 0;
}

// 显示更新通知
function showUpdateNotification() {
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = `
        <div class="update-content">
            <span class="update-icon">🔔</span>
            <div class="update-text">
                <strong>发现新版本！</strong>
                <p>CAD工具包 v${versionData.latest_version} 已发布</p>
            </div>
            <div class="update-actions">
                <a href="#download" class="btn-update">立即更新</a>
                <button onclick="closeUpdateNotification()" class="btn-close">稍后</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动显示
    setTimeout(() => {
        notification.classList.add('show');
    }, 1000);
}

// 关闭更新通知
function closeUpdateNotification() {
    const notification = document.querySelector('.update-notification');
    if (notification) {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }
}

// 跟踪下载
function trackDownload() {
    // 保存当前版本为已安装版本
    if (versionData) {
        localStorage.setItem('installed_version', versionData.latest_version);
        localStorage.setItem('install_date', new Date().toISOString());
    }
    
    // 这里可以添加下载统计逻辑
    console.log('下载已开始');
}

// 模拟版本更新推送（用于测试）
function simulateVersionUpdate(newVersion) {
    if (versionData) {
        versionData.latest_version = newVersion;
        showUpdateNotification();
    }
}
