from django import forms
from .models import Project, CodeFile, Task

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'is_public', 'max_members']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'max_members': forms.NumberInput(attrs={'min': 2, 'max': 20}),
        }

class CodeFileForm(forms.ModelForm):
    class Meta:
        model = CodeFile
        fields = ['filename', 'language']
        
    def clean_filename(self):
        filename = self.cleaned_data.get('filename')
        if '/' in filename or '\\' in filename:
            raise forms.ValidationError("Filename cannot contain path separators (/ or \\)")
        return filename

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit assigned_to choices to project members and owner
        self.fields['assigned_to'].queryset = project.get_all_members()

class ProjectInviteForm(forms.Form):
    username = forms.CharField(max_length=150)
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        from django.contrib.auth.models import User
        
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(f"User '{username}' does not exist")
        
        return username
