from django.contrib.auth import get_user_model
from .models import Project

def check_user_access(user, project):
    """
    Check if a user has access to a project.
    Returns True if the user is the owner or a member of the project.
    """
    if not user or user.is_anonymous:
        return False
        
    # Check if user is owner
    if project.owner == user:
        return True
        
    # Check if user is a member
    return project.members.filter(id=user.id).exists() 