document.addEventListener('DOMContentLoaded', function() {
    // Confirm deletion for projects and files
    const deleteButtons = document.querySelectorAll('.confirm-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Copy invite link to clipboard
    const inviteLinkButton = document.getElementById('copy-invite-link');
    if (inviteLinkButton) {
        inviteLinkButton.addEventListener('click', function() {
            const inviteLink = document.getElementById('invite-link');
            
            // Create a temporary input element
            const tempInput = document.createElement('input');
            tempInput.value = inviteLink.textContent;
            document.body.appendChild(tempInput);
            
            // Select and copy the link
            tempInput.select();
            document.execCommand('copy');
            
            // Remove the temporary element
            document.body.removeChild(tempInput);
            
            // Show feedback
            const originalText = inviteLinkButton.textContent;
            inviteLinkButton.textContent = 'Copied!';
            inviteLinkButton.classList.add('btn-success');
            
            // Reset button after a delay
            setTimeout(function() {
                inviteLinkButton.textContent = originalText;
                inviteLinkButton.classList.remove('btn-success');
            }, 2000);
        });
    }
    
    // File filters
    const fileFilterInput = document.getElementById('file-filter');
    if (fileFilterInput) {
        fileFilterInput.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            const fileItems = document.querySelectorAll('.file-list li');
            
            fileItems.forEach(item => {
                const fileName = item.querySelector('a').textContent.toLowerCase();
                if (fileName.includes(filterValue)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Activate tab functionality for project sections
    const tabButtons = document.querySelectorAll('.tab-button');
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Get the tab ID from data attribute
                const tabId = this.dataset.tab;
                
                // Hide all tab contents
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Deactivate all tab buttons
                tabButtons.forEach(btn => {
                    btn.classList.remove('active');
                });
                
                // Activate clicked tab
                this.classList.add('active');
                document.getElementById(tabId).classList.add('active');
                
                // Store active tab in local storage
                localStorage.setItem('activeProjectTab', tabId);
            });
        });
        
        // Load active tab from local storage or activate first tab
        const activeTab = localStorage.getItem('activeProjectTab');
        if (activeTab && document.getElementById(activeTab)) {
            document.querySelector(`[data-tab="${activeTab}"]`).click();
        } else {
            tabButtons[0].click();
        }
    }
    
    // Dropdown functionality
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle dropdown menu
            const dropdownMenu = this.nextElementSibling;
            dropdownMenu.classList.toggle('show');
            
            // Close other dropdowns
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                if (menu !== dropdownMenu) {
                    menu.classList.remove('show');
                }
            });
        });
    });
    
    // Close dropdowns when clicking elsewhere
    document.addEventListener('click', function() {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    });
    
    // Form validation for project creation/editing
    const projectForm = document.getElementById('project-form');
    if (projectForm) {
        projectForm.addEventListener('submit', function(e) {
            const projectName = document.getElementById('id_name').value.trim();
            if (projectName === '') {
                e.preventDefault();
                showFormError('id_name', 'Project name is required');
            }
        });
    }
    
    // Form validation for file creation
    const fileForm = document.getElementById('file-form');
    if (fileForm) {
        fileForm.addEventListener('submit', function(e) {
            const fileName = document.getElementById('id_filename').value.trim();
            if (fileName === '') {
                e.preventDefault();
                showFormError('id_filename', 'Filename is required');
            } else if (!/^[a-zA-Z0-9_.-]+$/.test(fileName)) {
                e.preventDefault();
                showFormError('id_filename', 'Filename contains invalid characters');
            }
        });
    }
});

function showFormError(fieldId, message) {
    const field = document.getElementById(fieldId);
    field.classList.add('error');
    
    // Remove any existing error message
    const existingError = field.parentElement.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    errorMessage.textContent = message;
    field.parentElement.appendChild(errorMessage);
    
    // Focus the field
    field.focus();
}

// Add CSS for dropdown and form error styling
(function addProjectStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .dropdown {
            position: relative;
            display: inline-block;
        }
        
        .dropdown-menu {
            display: none;
            position: absolute;
            right: 0;
            z-index: 1000;
            min-width: 160px;
            padding: 0.5rem 0;
            margin: 0.125rem 0 0;
            background-color: #fff;
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 0.25rem;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.175);
        }
        
        .dropdown-menu.show {
            display: block;
        }
        
        .dropdown-item {
            display: block;
            width: 100%;
            padding: 0.25rem 1.5rem;
            clear: both;
            text-align: inherit;
            white-space: nowrap;
            background-color: transparent;
            border: 0;
            text-decoration: none;
            color: #212529;
        }
        
        .dropdown-item:hover {
            background-color: #f8f9fa;
        }
        
        /* Tab styles */
        .tabs {
            display: flex;
            border-bottom: 1px solid #dee2e6;
            margin-bottom: 1rem;
        }
        
        .tab-button {
            padding: 0.5rem 1rem;
            cursor: pointer;
            border: 1px solid transparent;
            border-top-left-radius: 0.25rem;
            border-top-right-radius: 0.25rem;
            margin-bottom: -1px;
        }
        
        .tab-button:hover {
            border-color: #e9ecef #e9ecef #dee2e6;
        }
        
        .tab-button.active {
            color: #495057;
            background-color: #fff;
            border-color: #dee2e6 #dee2e6 #fff;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Form error styles */
        .form-control.error {
            border-color: #dc3545;
        }
        
        .error-message {
            color: #dc3545;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
    `;
    document.head.appendChild(style);
})();
