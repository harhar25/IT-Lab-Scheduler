class NotificationsManager {
    constructor(app) {
        this.app = app;
        this.notifications = [];
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Check for new notifications periodically
        setInterval(() => this.checkNotifications(), 30000); // Every 30 seconds
    }

    async checkNotifications() {
        if (!this.app.currentUser) return;
        
        try {
            const newNotifications = await this.app.apiCall('/notifications/?unread_only=true');
            
            // Show notifications that we haven't seen before
            newNotifications.forEach(notification => {
                if (!this.notifications.find(n => n.id === notification.id)) {
                    this.showNotification(notification);
                    this.notifications.push(notification);
                }
            });
            
        } catch (error) {
            console.error('Failed to check notifications:', error);
        }
    }

    showNotification(notification) {
        // Create notification element
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification ${this.getNotificationType(notification)}`;
        notificationElement.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(notification)}"></i>
            <div>
                <strong>${notification.title}</strong>
                <p>${notification.message}</p>
                <small>${new Date(notification.created_at).toLocaleTimeString()}</small>
            </div>
            <button class="close-notification" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add styles for the notification
        notificationElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-left: 4px solid ${this.getNotificationColor(notification)};
            max-width: 350px;
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        `;
        
        // Add to page
        document.body.appendChild(notificationElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notificationElement.parentNode) {
                notificationElement.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => {
                    if (notificationElement.parentNode) {
                        notificationElement.parentNode.removeChild(notificationElement);
                    }
                }, 300);
            }
        }, 5000);
    }

    getNotificationType(notification) {
        const typeMap = {
            'reservation_approved': 'success',
            'reservation_declined': 'error',
            'reservation_pending': 'info',
            'schedule_update': 'info',
            'system_alert': 'warning'
        };
        
        return typeMap[notification.notification_type] || 'info';
    }

    getNotificationIcon(notification) {
        const iconMap = {
            'reservation_approved': 'check-circle',
            'reservation_declined': 'times-circle',
            'reservation_pending': 'clock',
            'schedule_update': 'calendar-alt',
            'system_alert': 'exclamation-triangle'
        };
        
        return iconMap[notification.notification_type] || 'info-circle';
    }

    getNotificationColor(notification) {
        const colorMap = {
            'success': '#2ecc71',
            'error': '#e74c3c',
            'warning': '#f39c12',
            'info': '#3498db'
        };
        
        return colorMap[this.getNotificationType(notification)] || '#3498db';
    }

    async markAsRead(notificationId) {
        try {
            await this.app.apiCall(`/notifications/${notificationId}/read`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    }

    async getUnreadCount() {
        try {
            const notifications = await this.app.apiCall('/notifications/?unread_only=true');
            return notifications.length;
        } catch (error) {
            console.error('Failed to get unread count:', error);
            return 0;
        }
    }

    // Method to show manual notifications (for other parts of the app)
    showManualNotification(title, message, type = 'info') {
        const notification = {
            id: Date.now(),
            title: title,
            message: message,
            notification_type: type,
            created_at: new Date().toISOString()
        };
        
        this.showNotification(notification);
    }
}

// Add CSS for notifications
const notificationStyles = `
@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

.close-notification {
    background: none;
    border: none;
    color: #999;
    cursor: pointer;
    padding: 0;
    margin-left: auto;
}

.close-notification:hover {
    color: #666;
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);