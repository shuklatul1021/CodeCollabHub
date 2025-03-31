document.addEventListener('DOMContentLoaded', function() {
    // Task filtering
    const taskFilterSelect = document.getElementById('task-filter');
    const taskSearchInput = document.getElementById('task-search');
    const assigneeFilterSelect = document.getElementById('assignee-filter');
    
    if (taskFilterSelect) {
        taskFilterSelect.addEventListener('change', filterTasks);
    }
    
    if (taskSearchInput) {
        taskSearchInput.addEventListener('input', filterTasks);
    }
    
    if (assigneeFilterSelect) {
        assigneeFilterSelect.addEventListener('change', filterTasks);
    }
    
    // Drag and drop for tasks (status change)
    const taskItems = document.querySelectorAll('.task-item');
    const taskColumns = document.querySelectorAll('.task-column');
    
    if (taskItems.length > 0 && taskColumns.length > 0) {
        setupDragAndDrop();
    }
    
    // Task status update
    const statusSelects = document.querySelectorAll('.task-status-select');
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            const taskId = this.dataset.taskId;
            const projectId = this.dataset.projectId;
            const status = this.value;
            
            updateTaskStatus(projectId, taskId, status);
        });
    });
});

function filterTasks() {
    const statusFilter = document.getElementById('task-filter')?.value || 'all';
    const searchTerm = (document.getElementById('task-search')?.value || '').toLowerCase();
    const assigneeFilter = document.getElementById('assignee-filter')?.value || 'all';
    
    const taskItems = document.querySelectorAll('.task-item');
    
    taskItems.forEach(task => {
        const status = task.dataset.status;
        const title = task.querySelector('.task-title').textContent.toLowerCase();
        const description = task.querySelector('.task-description')?.textContent.toLowerCase() || '';
        const assignee = task.dataset.assignee;
        
        // Apply status filter
        const statusMatch = statusFilter === 'all' || status === statusFilter;
        
        // Apply search filter
        const searchMatch = title.includes(searchTerm) || description.includes(searchTerm);
        
        // Apply assignee filter
        const assigneeMatch = assigneeFilter === 'all' || assignee === assigneeFilter || 
                              (assigneeFilter === 'unassigned' && !assignee);
        
        // Show/hide the task based on all filters
        if (statusMatch && searchMatch && assigneeMatch) {
            task.style.display = '';
        } else {
            task.style.display = 'none';
        }
    });
    
    // Update counters for each status column
    updateTaskCounters();
}

function updateTaskCounters() {
    const taskColumns = document.querySelectorAll('.task-column');
    
    taskColumns.forEach(column => {
        const status = column.dataset.status;
        const visibleTasks = column.querySelectorAll('.task-item:not([style*="display: none"])').length;
        const counter = column.querySelector('.task-counter');
        
        if (counter) {
            counter.textContent = visibleTasks;
        }
    });
}

function setupDragAndDrop() {
    const taskItems = document.querySelectorAll('.task-item');
    const taskColumns = document.querySelectorAll('.task-column');
    
    // Make tasks draggable
    taskItems.forEach(task => {
        task.setAttribute('draggable', true);
        
        task.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('text/plain', task.dataset.taskId);
            this.classList.add('dragging');
        });
        
        task.addEventListener('dragend', function() {
            this.classList.remove('dragging');
        });
    });
    
    // Make columns drop targets
    taskColumns.forEach(column => {
        column.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });
        
        column.addEventListener('dragleave', function() {
            this.classList.remove('drag-over');
        });
        
        column.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            
            const taskId = e.dataTransfer.getData('text/plain');
            const newStatus = this.dataset.status;
            const projectId = document.querySelector('.task-board').dataset.projectId;
            
            const draggedTask = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
            
            if (draggedTask && draggedTask.dataset.status !== newStatus) {
                // Move the task to the new column
                this.querySelector('.task-list').appendChild(draggedTask);
                
                // Update the task's status data attribute
                draggedTask.dataset.status = newStatus;
                
                // Update the task status on the server
                updateTaskStatus(projectId, taskId, newStatus);
            }
        });
    });
}

function updateTaskStatus(projectId, taskId, status) {
    // Get CSRF token from the cookie
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/projects/${projectId}/tasks/${taskId}/edit/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: `status=${status}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification('Task status updated successfully', 'success');
            
            // Update task UI if needed
            const taskItem = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
            if (taskItem) {
                // Update status classes
                taskItem.className = taskItem.className.replace(/task-item-\w+/, `task-item-${status}`);
                
                // Update status text if present
                const statusText = taskItem.querySelector('.task-status');
                if (statusText) {
                    statusText.textContent = getStatusLabel(status);
                }
            }
        } else {
            showNotification(data.error || 'Failed to update task status', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating task status:', error);
        showNotification('Failed to update task status', 'error');
    });
}

function getStatusLabel(status) {
    switch (status) {
        case 'todo': return 'To Do';
        case 'in_progress': return 'In Progress';
        case 'review': return 'Review';
        case 'done': return 'Done';
        default: return status;
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `task-notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide and remove notification
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Add task management styles
(function addTaskStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .task-board {
            display: flex;
            gap: 1rem;
            overflow-x: auto;
            padding-bottom: 1rem;
        }
        
        .task-column {
            flex: 1;
            min-width: 250px;
            background-color: #f8f9fa;
            border-radius: 4px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .task-column-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(0, 0, 0, 0.1);
        }
        
        .task-column-title {
            font-weight: bold;
            font-size: 1rem;
            display: flex;
            align-items: center;
        }
        
        .task-counter {
            background-color: rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            padding: 0.1rem 0.5rem;
            font-size: 0.8rem;
            margin-left: 0.5rem;
        }
        
        .task-list {
            min-height: 200px;
        }
        
        .task-item {
            padding: 0.75rem;
            background-color: white;
            border-radius: 4px;
            margin-bottom: 0.5rem;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .task-item:hover {
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .task-item.dragging {
            opacity: 0.5;
            transform: scale(0.95);
        }
        
        .task-column.drag-over {
            background-color: #e9ecef;
        }
        
        .task-title {
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .task-description {
            font-size: 0.875rem;
            color: #6c757d;
            margin-bottom: 0.5rem;
        }
        
        .task-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: #6c757d;
        }
        
        .task-assignee {
            display: flex;
            align-items: center;
        }
        
        .task-assignee-avatar {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: #6c757d;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            margin-right: 0.25rem;
        }
        
        .task-due-date {
            color: #dc3545;
        }
        
        .task-filters {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        
        .task-filter {
            flex: 1;
            min-width: 150px;
        }
        
        .task-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.3s, transform 0.3s;
            z-index: 1000;
        }
        
        .task-notification.show {
            opacity: 1;
            transform: translateY(0);
        }
        
        .task-notification.success {
            background-color: #28a745;
        }
        
        .task-notification.error {
            background-color: #dc3545;
        }
        
        @media (max-width: 768px) {
            .task-board {
                flex-direction: column;
            }
            
            .task-column {
                min-width: auto;
            }
        }
    `;
    document.head.appendChild(style);
})();
