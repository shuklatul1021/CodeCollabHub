from django import forms
from django.contrib.auth.models import User
from .models import Project, CodeFile, Task, ProjectMembership

class ProjectForm(forms.Form):
    name = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    language = forms.ChoiceField(choices=[
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('swift', 'Swift'),
        ('kotlin', 'Kotlin'),
        ('scala', 'Scala'),
        ('r', 'R'),
        ('matlab', 'MATLAB'),
        ('sql', 'SQL'),
        ('shell', 'Shell'),
        ('powershell', 'PowerShell'),
        ('markdown', 'Markdown'),
        ('plaintext', 'Plain Text'),
    ])
    is_public = forms.BooleanField(required=False)
    max_members = forms.IntegerField(min_value=2, max_value=20, initial=10)

    def save(self, owner):
        project = Project(
            name=self.cleaned_data['name'],
            description=self.cleaned_data['description'],
            language=self.cleaned_data['language'],
            is_public=self.cleaned_data['is_public'],
            max_members=self.cleaned_data['max_members'],
            owner=owner
        )
        project.save()
        return project

class CodeFileForm(forms.Form):
    filename = forms.CharField(max_length=255)
    language = forms.ChoiceField(choices=[
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('swift', 'Swift'),
        ('kotlin', 'Kotlin'),
        ('scala', 'Scala'),
        ('r', 'R'),
        ('matlab', 'MATLAB'),
        ('sql', 'SQL'),
        ('shell', 'Shell'),
        ('powershell', 'PowerShell'),
        ('markdown', 'Markdown'),
        ('plaintext', 'Plain Text'),
    ])
    
    def clean_filename(self):
        filename = self.cleaned_data.get('filename')
        if '/' in filename or '\\' in filename:
            raise forms.ValidationError("Filename cannot contain path separators (/ or \\)")
        return filename

    def save(self, project):
        code_file = CodeFile(
            filename=self.cleaned_data['filename'],
            language=self.cleaned_data['language'],
            project=project
        )
        code_file.save()
        return code_file

class TaskForm(forms.Form):
    title = forms.CharField(max_length=200)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    assigned_to = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    due_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    status = forms.ChoiceField(choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done')
    ])

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all project members (owner + members)
        member_ids = [member.user_id for member in project.members]
        member_ids.append(project.owner_id)
        self.fields['assigned_to'].queryset = User.objects.filter(id__in=member_ids)

    def save(self, project):
        task = Task(
            title=self.cleaned_data['title'],
            description=self.cleaned_data['description'],
            assigned_to=self.cleaned_data['assigned_to'],
            due_date=self.cleaned_data['due_date'],
            status=self.cleaned_data['status'],
            project=project
        )
        task.save()
        return task

class ProjectInviteForm(forms.Form):
    username = forms.CharField(max_length=150)
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(f"User '{username}' does not exist")
        return username
