// Car Service Management System - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add fade-in animation to cards
    var cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        setTimeout(function() {
            card.classList.add('fade-in');
        }, index * 100);
    });

    // Form validation enhancement
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }
    )
    enhanceSearch();

    // Photo upload preview
    setupPhotoPreview();

    // Auto-save functionality for forms
    setupAutoSave();
});

// Animate progress bars
function animateProgressBars() {
    var progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(function(bar) {
        var width = bar.style.width || bar.getAttribute('aria-valuenow') + '%';
        bar.style.width = '0%';
        setTimeout(function() {
            bar.style.width = width;
        }, 500);
    });
}

// Enhanced search functionality
function enhanceSearch() {
    var searchInputs = document.querySelectorAll('input[type="search"]');
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var searchTerm = this.value.toLowerCase();
            var rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                var text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                    row.classList.add('fade-in');
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });
}

// Photo upload preview
function setupPhotoPreview() {
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            var files = e.target.files;
            var previewContainer = input.parentNode.querySelector('.preview-container');
            
            if (!previewContainer) {
                previewContainer = document.createElement('div');
                previewContainer.className = 'preview-container mt-2';
                input.parentNode.appendChild(previewContainer);
            }
            
            previewContainer.innerHTML = '';
            
            Array.from(files).forEach(function(file) {
                if (file.type.startsWith('image/')) {
                    var reader = new FileReader();
                    reader.onload = function(e) {
                        var img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'img-thumbnail me-2 mb-2';
                        img.style.width = '100px';
                        img.style.height = '100px';
                        img.style.objectFit = 'cover';
                        previewContainer.appendChild(img);
                    };
                    reader.readAsDataURL(file);
                }
            });
        });
    });
}

// Auto-save functionality
function setupAutoSave() {
    var autoSaveInputs = document.querySelectorAll('[data-autosave]');
    autoSaveInputs.forEach(function(input) {
        var timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                saveData(input);
            }, 1000);
        });
    });
}

// Save data function
function saveData(input) {
    var vehicleNumber = input.getAttribute('data-vehicle');
    var fieldType = input.getAttribute('data-field');
    var value = input.type === 'checkbox' ? input.checked : input.value;
    
    var endpoint = '';
    var data = {};
    
    switch(fieldType) {
        case 'registration':
            endpoint = `/update_registration/${vehicleNumber}`;
            data = { is_completed: value };
            break;
        case 'claim':
            endpoint = `/update_claim/${vehicleNumber}`;
            data = { claim_number: value };
            
            // Validate claim number for duplicates
            if (value.trim()) {
                fetch('/validate_claim', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        claim_number: value,
                        vehicle_number: vehicleNumber
                    })
                })
                .then(response => response.json())
                .then(result => {
                    if (result.is_duplicate) {
                        showNotification(result.message, 'error');
                        return;
                    }
                });
            }
            break;
        case 'approval':
            endpoint = `/update_approval/${vehicleNumber}`;
            data = { is_approved: value };
            break;
    }
    
    if (endpoint) {
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Data saved successfully', 'success');
            } else {
                showNotification('Error saving data', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error saving data', 'error');
        });
    }
}

// Show notification
function showNotification(message, type) {
    var notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.remove();
    }, 3000);
}

// Utility functions
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Export functions for global use
window.CarServiceApp = {
    showNotification: showNotification,
    formatNumber: formatNumber,
    formatDate: formatDate,
    saveData: saveData
};