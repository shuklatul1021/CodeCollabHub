from django.contrib import admin
from .models import Project, ProjectMembership, CodeFile, FileVersion, Task

class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1

class CodeFileInline(admin.TabularInline):
    model = CodeFile
    extra = 1

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'owner__username')
    inlines = [ProjectMembershipInline, CodeFileInline, TaskInline]

@admin.register(CodeFile)
class CodeFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'project', 'language', 'created_at', 'updated_at')
    list_filter = ('language', 'created_at')
    search_fields = ('filename', 'project__name')

@admin.register(FileVersion)
class FileVersionAdmin(admin.ModelAdmin):
    list_display = ('code_file', 'creator', 'version_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('code_file__filename', 'creator__username')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'status', 'due_date')
    list_filter = ('status', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'project__name', 'assigned_to__username')
