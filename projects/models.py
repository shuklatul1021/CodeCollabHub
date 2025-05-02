from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(default=datetime.utcnow)

    class Meta:
        ordering = ['-joined_at']
        unique_together = ['project', 'user']

class FileVersion(models.Model):
    content = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    version_number = models.IntegerField()
    created_at = models.DateTimeField(default=datetime.utcnow)
    code_file = models.ForeignKey('CodeFile', on_delete=models.CASCADE, related_name='versions', null=True, blank=True)

    class Meta:
        ordering = ['-version_number']

class CodeFile(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('csharp', 'C#'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('other', 'Other'),
    ]
    
    filename = models.CharField(max_length=255)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    created_at = models.DateTimeField(default=datetime.utcnow)
    updated_at = models.DateTimeField(default=datetime.utcnow)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='code_files')

    class Meta:
        ordering = ['-updated_at']
        unique_together = ['project', 'filename']

class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    created_at = models.DateTimeField(default=datetime.utcnow)
    updated_at = models.DateTimeField(default=datetime.utcnow)
    due_date = models.DateField(null=True, blank=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks')

    class Meta:
        ordering = ['-created_at']

class ProjectRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=datetime.utcnow)
    updated_at = models.DateTimeField(default=datetime.utcnow)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['project', 'requester']

    def __str__(self):
        return f"{self.requester.username}'s request to join {self.project.name}"

class Project(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('csharp', 'C#'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('html', 'HTML/CSS'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')
    created_at = models.DateTimeField(default=datetime.utcnow)
    updated_at = models.DateTimeField(default=datetime.utcnow)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    is_public = models.BooleanField(default=False)
    max_members = models.IntegerField(default=5, validators=[MinValueValidator(2), MaxValueValidator(20)])
    members = models.ManyToManyField(User, through='ProjectMembership', related_name='member_projects')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['owner', 'name']
    
    def __str__(self):
        return self.name
    
    def get_all_members(self):
        """Get all users (owner + members) associated with the project"""
        return User.objects.filter(
            models.Q(id__in=self.members.values_list('id', flat=True)) |
            models.Q(id=self.owner_id)
        )
