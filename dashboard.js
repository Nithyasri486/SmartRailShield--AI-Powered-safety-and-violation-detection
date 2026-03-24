// Toast notification function
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Launch module function
async function launchModule(moduleName) {
    const card = document.querySelector(`.module-card[data-module="${moduleName}"]`);
    const statusBadge = card.querySelector('.status-badge');
    
    // Add loading state
    card.classList.add('loading');
    statusBadge.innerHTML = '<span class="status-dot"></span><span>Launching...</span>';
    statusBadge.classList.add('running');
    
    try {
        const response = await fetch('/launch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ module: moduleName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`${getModuleName(moduleName)} launched successfully!`, 'success');
            statusBadge.innerHTML = '<span class="status-dot"></span><span>Running...</span>';
            
            // Reset after some time (modules will run independently)
            setTimeout(() => {
                card.classList.remove('loading');
                statusBadge.innerHTML = '<span class="status-dot"></span><span>Ready to Launch</span>';
                statusBadge.classList.remove('running');
            }, 3000);
        } else {
            throw new Error(data.message || 'Failed to launch module');
        }
        
    } catch (error) {
        console.error('Error launching module:', error);
        showToast(`Error: ${error.message}`, 'error');
        
        // Reset state
        card.classList.remove('loading');
        statusBadge.innerHTML = '<span class="status-dot"></span><span>Ready to Launch</span>';
        statusBadge.classList.remove('running');
    }
}

// Get friendly module name
function getModuleName(moduleName) {
    const names = {
        'fault': 'Machine Fault Detection',
        'drowsiness': 'Pilot Drowsiness Detection',
        'obstacle': 'Obstacle Detection',
        'anpr': 'License Plate Recognition'
    };
    return names[moduleName] || moduleName;
}

// Add hover effects and animations
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.module-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.zIndex = '10';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.zIndex = '1';
        });
    });
    
    // Add stagger animation on load
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case '1':
                e.preventDefault();
                launchModule('fault');
                break;
            case '2':
                e.preventDefault();
                launchModule('drowsiness');
                break;
            case '3':
                e.preventDefault();
                launchModule('obstacle');
                break;
            case '4':
                e.preventDefault();
                launchModule('anpr');
                break;
        }
    }
});
