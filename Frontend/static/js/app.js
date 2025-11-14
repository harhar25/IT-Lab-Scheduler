class LabScheduler {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.currentUser = null;
        this.token = localStorage.getItem('auth_token');
        this.userData = localStorage.getItem('user_data');
        
        this.dashboardManager = null;
        this.scheduleManager = null;
        this.reservationsManager = null;
        this.notificationsManager = null;
        
        this.init();
    }

    async init() {
        await this.checkAuthStatus();
        this.setupEventListeners();
        this.initializeManagers();
    }

    async checkAuthStatus() {
        if (this.token && this.userData) {
            try {
                this.currentUser = JSON.parse(this.userData);
                this.showApp();
            } catch (error) {
                console.error('Error parsing user data:', error);
                this.showLogin();
            }
        } else {
            this.showLogin();
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.sidebar-menu li').forEach(item => {
            if (item.dataset.tab) {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.switchTab(item.dataset.tab);
                });
            }
        });

        // Logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
        
        // Global modal close
        const closeModal = document.querySelector('.close-modal');
        if (closeModal) {
            closeModal.addEventListener('click', () => {
                document.getElementById('schedule-modal').style.display = 'none';
            });
        }
        
        // Close modal when clicking outside
        const modal = document.getElementById('schedule-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        }
    }

    initializeManagers() {
        this.dashboardManager = new DashboardManager(this);
        this.scheduleManager = new ScheduleManager(this);
        this.reservationsManager = new ReservationsManager(this);
        this.notificationsManager = new NotificationsManager(this);
        
        // Make managers globally available for onclick handlers
        window.reservationsManager = this.reservationsManager;
    }

    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                this.logout();
                throw new Error('Authentication required');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification(error.message, 'error');
            throw error;
        }
    }

    showLogin() {
        const loginPage = document.getElementById('login-page');
        const app = document.getElementById('app');
        
        if (loginPage) loginPage.style.display = 'flex';
        if (app) app.style.display = 'none';
    }

    showApp() {
        const loginPage = document.getElementById('login-page');
        const app = document.getElementById('app');
        
        if (loginPage) loginPage.style.display = 'none';
        if (app) app.style.display = 'flex';
        
        this.updateUserInterface();
        this.loadDashboard();
    }

    updateUserInterface() {
        // Update user info in header
        const userName = document.getElementById('user-name');
        const userRole = document.getElementById('user-role');
        const userAvatar = document.getElementById('user-avatar');
        
        if (userName) userName.textContent = this.currentUser.full_name;
        if (userRole) userRole.textContent = this.capitalizeFirstLetter(this.currentUser.role);
        if (userAvatar) userAvatar.textContent = this.currentUser.full_name.charAt(0).toUpperCase();
        
        // Show/hide features based on role
        this.updateRoleBasedAccess();
    }

    updateRoleBasedAccess() {
        const role = this.currentUser.role;
        
        // Show/hide tabs based on role
        const reservationTab = document.getElementById('reservation-tab');
        const approvalsTab = document.getElementById('approvals-tab');
        const reportsTab = document.getElementById('reports-tab');
        
        if (reservationTab) {
            reservationTab.style.display = 
                role === 'instructor' || role === 'admin' ? 'list-item' : 'none';
        }
        
        if (approvalsTab) {
            approvalsTab.style.display = role === 'admin' ? 'list-item' : 'none';
        }
        
        if (reportsTab) {
            reportsTab.style.display = role === 'admin' ? 'list-item' : 'none';
        }
    }

    switchTab(tabName) {
        // Update active tab in sidebar
        document.querySelectorAll('.sidebar-menu li').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }
        
        // Update active tab content
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        const activeContent = document.getElementById(tabName);
        if (activeContent) {
            activeContent.classList.add('active');
        }
        
        // Update page title
        const pageTitle = document.getElementById('page-title');
        if (pageTitle) {
            pageTitle.textContent = this.capitalizeFirstLetter(tabName);
        }
        
        // Load tab-specific content
        this.loadTabContent(tabName);
    }

    async loadTabContent(tabName) {
        switch (tabName) {
            case 'dashboard':
                if (this.dashboardManager) {
                    await this.dashboardManager.loadDashboard();
                }
                break;
            case 'schedule':
                if (this.scheduleManager) {
                    await this.scheduleManager.loadSchedule();
                }
                break;
            case 'reservation':
                if (this.reservationsManager) {
                    await this.reservationsManager.loadReservationForm();
                }
                break;
            case 'approvals':
                if (this.reservationsManager) {
                    await this.reservationsManager.loadApprovals();
                }
                break;
            case 'reports':
                await this.loadReports();
                break;
        }
    }

    async loadDashboard() {
        if (this.dashboardManager) {
            await this.dashboardManager.loadDashboard();
        }
    }

    async loadReports() {
        try {
            const reportType = document.getElementById('report-type').value;
            const reportMonth = document.getElementById('report-month').value;
            
            let reportData;
            
            switch (reportType) {
                case 'monthly':
                    reportData = await this.apiCall(`/reports/monthly-usage?month=${reportMonth}`);
                    this.renderMonthlyReport(reportData);
                    break;
                case 'instructor':
                    reportData = await this.apiCall(`/reports/instructor-usage?month=${reportMonth}`);
                    this.renderInstructorReport(reportData);
                    break;
                case 'peak-hours':
                    reportData = await this.apiCall(`/reports/peak-hours?month=${reportMonth}`);
                    this.renderPeakHoursReport(reportData);
                    break;
            }
            
        } catch (error) {
            console.error('Failed to load reports:', error);
            this.showNotification('Failed to generate report', 'error');
        }
    }

    renderMonthlyReport(reportData) {
        const container = document.getElementById('report-content');
        
        let tableHTML = `
            <div class="table-container">
                <h2>Monthly Lab Usage Report - ${reportData.period}</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Lab</th>
                            <th>Total Hours</th>
                            <th>Utilization Rate</th>
                            <th>Most Used Day</th>
                            <th>Peak Hours</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        reportData.data.forEach(item => {
            tableHTML += `
                <tr>
                    <td>${item.lab_name}</td>
                    <td>${item.total_hours} hours</td>
                    <td>${item.utilization_rate}%</td>
                    <td>${item.peak_day}</td>
                    <td>${item.peak_hours}</td>
                </tr>
            `;
        });
        
        tableHTML += `</tbody></table></div>`;
        
        // Add peak hours visualization
        tableHTML += `
            <div class="card" style="margin-top: 20px;">
                <div class="card-header">
                    <h3>Peak Hours Analysis</h3>
                </div>
                <div style="padding: 20px;">
        `;
        
        reportData.peak_hours.forEach(hour => {
            tableHTML += `
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="width: 100px; text-align: right; margin-right: 10px;">${hour.time_slot}</div>
                    <div style="flex: 1; background: #ecf0f1; height: 20px; border-radius: 10px;">
                        <div style="background: #3498db; height: 100%; width: ${hour.utilization}%; border-radius: 10px;"></div>
                    </div>
                    <div style="width: 50px; text-align: right; margin-left: 10px;">${hour.utilization}%</div>
                </div>
            `;
        });
        
        tableHTML += `</div></div>`;
        container.innerHTML = tableHTML;
    }

    renderInstructorReport(reportData) {
        const container = document.getElementById('report-content');
        
        let tableHTML = `
            <div class="table-container">
                <h2>Instructor Usage Summary - ${reportData.period}</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Instructor</th>
                            <th>Total Reservations</th>
                            <th>Total Hours</th>
                            <th>Favorite Lab</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        reportData.data.forEach(item => {
            tableHTML += `
                <tr>
                    <td>${item.instructor_name}</td>
                    <td>${item.total_reservations}</td>
                    <td>${item.total_hours} hours</td>
                    <td>${item.favorite_lab}</td>
                </tr>
            `;
        });
        
        tableHTML += `</tbody></table></div>`;
        container.innerHTML = tableHTML;
    }

    renderPeakHoursReport(reportData) {
        const container = document.getElementById('report-content');
        
        let html = `
            <div class="card">
                <div class="card-header">
                    <h3>Peak Hours Analysis</h3>
                </div>
                <div style="padding: 20px;">
        `;
        
        Object.entries(reportData).forEach(([timeSlot, utilization]) => {
            html += `
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="width: 100px; text-align: right; margin-right: 10px;">${timeSlot}</div>
                    <div style="flex: 1; background: #ecf0f1; height: 20px; border-radius: 10px;">
                        <div style="background: #3498db; height: 100%; width: ${utilization}%; border-radius: 10px;"></div>
                    </div>
                    <div style="width: 50px; text-align: right; margin-left: 10px;">${utilization}%</div>
                </div>
            `;
        });
        
        html += `</div></div>`;
        container.innerHTML = html;
    }

    logout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        this.token = null;
        this.currentUser = null;
        this.showLogin();
        this.showNotification('You have been logged out', 'info');
    }

    showNotification(message, type = 'info') {
        if (this.notificationsManager) {
            this.notificationsManager.showManualNotification(
                type.charAt(0).toUpperCase() + type.slice(1),
                message,
                type
            );
        } else {
            // Fallback notification system
            this.showFallbackNotification(message, type);
        }
    }

    showFallbackNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 10px;
            transform: translateX(150%);
            transition: transform 0.3s;
        `;
        
        // Set background color based on type
        const colors = {
            success: '#2ecc71',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };
        
        notification.style.background = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.style.transform = 'translateX(0)', 100);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(150%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    setLoading(element, isLoading) {
        if (!element) return;
        
        const text = element.querySelector('span');
        const spinner = element.querySelector('.spinner');
        
        if (isLoading) {
            element.disabled = true;
            if (text) text.style.display = 'none';
            if (spinner) spinner.style.display = 'block';
            element.classList.add('loading');
        } else {
            element.disabled = false;
            if (text) text.style.display = 'block';
            if (spinner) spinner.style.display = 'none';
            element.classList.remove('loading');
        }
    }

    capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LabScheduler();
});