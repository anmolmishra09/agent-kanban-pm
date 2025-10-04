// Main UI JavaScript
document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle?.querySelector('.icon');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            let newTheme;
            
            if (currentTheme === 'light') {
                newTheme = 'dark';
                themeIcon.textContent = '☀️';
            } else if (currentTheme === 'dark') {
                newTheme = 'blue';
                themeIcon.textContent = '🌊';
            } else {
                newTheme = 'light';
                themeIcon.textContent = '🌙';
            }
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });

        // Set initial icon
        const savedTheme = localStorage.getItem('theme') || 'light';
        if (savedTheme === 'dark') themeIcon.textContent = '☀️';
        else if (savedTheme === 'blue') themeIcon.textContent = '🌊';
        else themeIcon.textContent = '🌙';
    }

    // View toggle
    const viewToggle = document.getElementById('view-toggle');
    const viewIcon = viewToggle?.querySelector('.icon');
    
    if (viewToggle) {
        viewToggle.addEventListener('click', function() {
            const currentView = document.documentElement.getAttribute('data-view') || 'grid';
            const newView = currentView === 'grid' ? 'list' : 'grid';
            
            document.documentElement.setAttribute('data-view', newView);
            localStorage.setItem('view', newView);
            viewIcon.textContent = newView === 'grid' ? '📊' : '📋';
            
            // Trigger view change event
            window.dispatchEvent(new CustomEvent('viewchange', { detail: { view: newView } }));
        });

        // Set initial icon
        const savedView = localStorage.getItem('view') || 'grid';
        viewIcon.textContent = savedView === 'grid' ? '📊' : '📋';
    }

    // Density selector
    const densitySelect = document.getElementById('density-select');
    
    if (densitySelect) {
        // Set saved value
        const savedDensity = localStorage.getItem('density') || 'comfortable';
        densitySelect.value = savedDensity;
        
        densitySelect.addEventListener('change', function() {
            const density = this.value;
            document.documentElement.setAttribute('data-density', density);
            localStorage.setItem('density', density);
        });
    }

    // Auto-refresh data every 30 seconds
    if (typeof window.refreshData === 'function') {
        setInterval(window.refreshData, 30000);
    }
});

// Utility function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
}

// Export for use in other scripts
window.formatDate = formatDate;
