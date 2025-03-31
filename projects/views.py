from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from .models import Project, ProjectMembership, CodeFile, FileVersion, Task, ProjectRequest
from .forms import ProjectForm, CodeFileForm, TaskForm, ProjectInviteForm
from .utils import check_user_access
import json

@login_required
def project_list(request):
    owned_projects = Project.objects.filter(owner=request.user)
    member_projects = Project.objects.filter(members=request.user).exclude(owner=request.user)
    public_projects = Project.objects.filter(is_public=True).exclude(owner=request.user).exclude(members=request.user)
    
    # Get pending requests for projects owned by the user
    pending_requests = ProjectRequest.objects.filter(
        project__owner=request.user,
        status='pending'
    ).select_related('requester', 'project')
    
    context = {
        'owned_projects': owned_projects,
        'member_projects': member_projects,
        'public_projects': public_projects,
        'pending_requests': pending_requests,
    }
    return render(request, 'projects/project_list.html', context)

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            
            # Add owner as first member with owner role
            ProjectMembership.objects.create(
                project=project,
                user=request.user,
                role='owner'
            )
            
            messages.success(request, 'Project created successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_owner = project.owner == request.user
    is_member = project.members.filter(id=request.user.id).exists()
    has_pending_request = ProjectRequest.objects.filter(
        project=project,
        requester=request.user,
        status='pending'
    ).exists()
    
    context = {
        'project': project,
        'is_owner': is_owner,
        'is_member': is_member,
        'has_pending_request': has_pending_request,
        'files': project.code_files.all(),
        'tasks': project.tasks.all(),
    }
    return render(request, 'projects/project_detail.html', context)

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Only project owner can edit project details
    if project.owner != request.user:
        return HttpResponseForbidden("Only the project owner can edit project details.")
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.name}" updated successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/create_project.html', {'form': form, 'edit_mode': True})

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Only project owner can delete the project
    if project.owner != request.user:
        return HttpResponseForbidden("Only the project owner can delete the project.")
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" deleted successfully!')
        return redirect('project_list')
    
    return render(request, 'projects/delete_project.html', {'project': project})

@login_required
def create_file(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    if request.method == 'POST':
        form = CodeFileForm(request.POST)
        if form.is_valid():
            try:
                code_file = form.save(commit=False)
                code_file.project = project
                code_file.save()
                
                # Create initial empty version
                FileVersion.objects.create(
                    code_file=code_file,
                    creator=request.user,
                    content="",
                    version_number=1
                )
                
                messages.success(request, f'File "{code_file.filename}" created successfully!')
                return redirect('code_editor', project_id=project.id, file_id=code_file.id)
            except IntegrityError:
                messages.error(request, f'A file with the name "{form.cleaned_data["filename"]}" already exists in this project.')
    else:
        form = CodeFileForm(initial={'language': project.language})
    
    return render(request, 'projects/create_project.html', {
        'form': form, 
        'project': project,
        'is_file': True
    })

@login_required
def code_editor(request, project_id, file_id):
    project = get_object_or_404(Project, id=project_id)
    code_file = get_object_or_404(CodeFile, id=file_id, project=project)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    # Get latest content
    latest_version = code_file.get_latest_version()
    content = latest_version.content if latest_version else ""
    
    # Escape content for JavaScript
    content = content.replace('\\', '\\\\').replace('</script>', '<\\/script>')
    
    # Get other files in the project for navigation
    other_files = project.code_files.exclude(id=file_id).order_by('filename')
    
    context = {
        'project': project,
        'code_file': code_file,
        'content': content,
        'other_files': other_files,
    }
    return render(request, 'projects/editor.html', context)

@login_required
def file_history(request, project_id, file_id):
    project = get_object_or_404(Project, id=project_id)
    code_file = get_object_or_404(CodeFile, id=file_id, project=project)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    versions = code_file.versions.all().order_by('-version_number')
    
    context = {
        'project': project,
        'code_file': code_file,
        'versions': versions,
    }
    return render(request, 'projects/file_history.html', context)

@login_required
def delete_file(request, project_id, file_id):
    project = get_object_or_404(Project, id=project_id)
    code_file = get_object_or_404(CodeFile, id=file_id, project=project)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    if request.method == 'POST':
        filename = code_file.filename
        code_file.delete()
        messages.success(request, f'File "{filename}" deleted successfully!')
        return redirect('project_detail', project_id=project.id)
    
    return render(request, 'projects/delete_file.html', {'project': project, 'code_file': code_file})

@login_required
def invite_member(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Only project owner can invite members
    if project.owner != request.user:
        return HttpResponseForbidden("Only the project owner can invite members.")
    
    if request.method == 'POST':
        form = ProjectInviteForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = User.objects.get(username=username)
            
            # Check if user is already a member or owner
            if user == project.owner:
                messages.error(request, f'{username} is already the owner of this project.')
            elif project.members.filter(id=user.id).exists():
                messages.error(request, f'{username} is already a member of this project.')
            else:
                # Add user to project
                ProjectMembership.objects.create(user=user, project=project)
                messages.success(request, f'{username} has been added to the project!')
                return redirect('project_members', project_id=project.id)
    else:
        form = ProjectInviteForm()
    
    return render(request, 'projects/invite.html', {'form': form, 'project': project})

@login_required
def project_members(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    memberships = ProjectMembership.objects.filter(project=project).select_related('user')
    
    context = {
        'project': project,
        'memberships': memberships,
    }
    return render(request, 'projects/members.html', context)

@login_required
def remove_member(request, project_id, user_id):
    project = get_object_or_404(Project, id=project_id)
    user_to_remove = get_object_or_404(User, id=user_id)
    
    # Only project owner can remove members
    if project.owner != request.user:
        return HttpResponseForbidden("Only the project owner can remove members.")
    
    if request.method == 'POST':
        membership = get_object_or_404(ProjectMembership, project=project, user=user_to_remove)
        membership.delete()
        messages.success(request, f'{user_to_remove.username} has been removed from the project.')
        return redirect('project_members', project_id=project.id)
    
    return render(request, 'projects/remove_member.html', {
        'project': project,
        'user_to_remove': user_to_remove
    })

@login_required
def task_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    tasks = project.tasks.all().order_by('status', 'due_date')
    
    context = {
        'project': project,
        'tasks': tasks,
    }
    return render(request, 'projects/tasks.html', context)

@login_required
def create_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    if request.method == 'POST':
        form = TaskForm(project, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('task_list', project_id=project.id)
    else:
        form = TaskForm(project)
    
    return render(request, 'projects/task_form.html', {
        'form': form,
        'project': project,
        'action': 'Create'
    })

@login_required
def task_detail(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(Task, id=task_id, project=project)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    context = {
        'project': project,
        'task': task,
    }
    return render(request, 'projects/task_detail.html', context)

@login_required
def edit_task(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(Task, id=task_id, project=project)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    if request.method == 'POST':
        form = TaskForm(project, request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_list', project_id=project.id)
    else:
        form = TaskForm(project, instance=task)
    
    return render(request, 'projects/task_form.html', {
        'form': form,
        'project': project,
        'task': task,
        'action': 'Edit'
    })

@login_required
def delete_task(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(Task, id=task_id, project=project)
    
    # Check if user has access to the project
    if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
        return HttpResponseForbidden("You don't have access to this project.")
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('task_list', project_id=project.id)
    
    return render(request, 'projects/delete_task.html', {'project': project, 'task': task})

@login_required
@require_POST
def save_file(request, project_id, file_id):
    try:
        # Get the file
        code_file = CodeFile.objects.get(id=file_id, project_id=project_id)
        
        # Check user access
        if not check_user_access(request.user, code_file.project):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get the content from the request
        data = json.loads(request.body)
        content = data.get('content', '')
        
        # Get the latest version number
        latest_version = code_file.get_latest_version()
        next_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create new version
        FileVersion.objects.create(
            code_file=code_file,
            creator=request.user,
            content=content,
            version_number=next_version_number
        )
        
        return JsonResponse({'status': 'success'})
        
    except CodeFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def request_to_join(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is already a member
    if project.members.filter(id=request.user.id).exists():
        messages.error(request, 'You are already a member of this project.')
        return redirect('project_detail', project_id=project_id)
    
    # Check if user has a pending request
    if ProjectRequest.objects.filter(
        project=project,
        requester=request.user,
        status='pending'
    ).exists():
        messages.error(request, 'You already have a pending request for this project.')
        return redirect('project_detail', project_id=project_id)
    
    # Create new request
    message = request.POST.get('message', '')
    ProjectRequest.objects.create(
        project=project,
        requester=request.user,
        message=message
    )
    
    messages.success(request, 'Your request to join has been sent to the project owner.')
    return redirect('project_detail', project_id=project_id)

@login_required
@require_POST
def handle_join_request(request, request_id):
    project_request = get_object_or_404(ProjectRequest, id=request_id)
    
    # Check if user is the project owner
    if project_request.project.owner != request.user:
        messages.error(request, 'You do not have permission to handle this request.')
        return redirect('project_list')
    
    action = request.POST.get('action')
    
    if action == 'approve':
        # Check if project has reached max members
        if project_request.project.members.count() >= project_request.project.max_members:
            messages.error(request, 'Project has reached maximum number of members.')
            project_request.status = 'rejected'
            project_request.save()
            return redirect('project_list')
        
        # Add user as member
        ProjectMembership.objects.create(
            project=project_request.project,
            user=project_request.requester,
            role='member'
        )
        project_request.status = 'approved'
        messages.success(request, f'{project_request.requester.username} has been added to the project.')
    elif action == 'reject':
        project_request.status = 'rejected'
        messages.info(request, f'Request from {project_request.requester.username} has been rejected.')
    
    project_request.save()
    return redirect('project_list')
