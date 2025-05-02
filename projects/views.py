from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Project, ProjectMembership, CodeFile, FileVersion, Task, ProjectRequest
from .forms import ProjectForm, CodeFileForm, TaskForm, ProjectInviteForm
from .utils import check_user_access
import json
from datetime import datetime

@login_required
def project_list(request):
    # Get projects owned by the user
    owned_projects = Project.objects.filter(owner=request.user)
    
    # Get projects where user is a member
    member_projects = Project.objects.filter(members=request.user).exclude(owner=request.user)
    
    # Get public projects (excluding those already owned or joined)
    public_projects = Project.objects.filter(
        is_public=True
    ).exclude(
        owner=request.user
    ).exclude(
        members=request.user
    )
    
    # Get pending requests for projects owned by the user
    pending_requests = ProjectRequest.objects.filter(
        project__owner=request.user,
        status='pending'
    )
    
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
            project = Project(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                language=form.cleaned_data['language'],
                owner=request.user,
                is_public=form.cleaned_data['is_public'],
                max_members=form.cleaned_data['max_members']
            )
            
            # Save the project first to get an ID
            project.save()
            
            # Now we can add the owner as a member
            project.members.add(request.user, through_defaults={'role': 'owner'})
            
            messages.success(request, 'Project created successfully!')
            return redirect('project_detail', project_id=str(project.id))
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})

@login_required
def project_detail(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        is_owner = project.owner_id == request.user.id
        is_member = project.members.filter(id=request.user.id).exists()
        has_pending_request = project.requests.filter(
            requester=request.user,
            status='pending'
        ).exists()
        
        context = {
            'project': project,
            'is_owner': is_owner,
            'is_member': is_member,
            'has_pending_request': has_pending_request,
            'files': list(project.code_files.all()),
            'tasks': list(project.tasks.all()),
        }
        return render(request, 'projects/project_detail.html', context)
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def edit_project(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Only project owner can edit project details
        if project.owner_id != request.user.id:
            return HttpResponseForbidden("Only the project owner can edit project details.")
        
        if request.method == 'POST':
            form = ProjectForm(request.POST)
            if form.is_valid():
                project.name = form.cleaned_data['name']
                project.description = form.cleaned_data['description']
                project.language = form.cleaned_data['language']
                project.is_public = form.cleaned_data['is_public']
                project.max_members = form.cleaned_data['max_members']
                project.save()
                messages.success(request, f'Project "{project.name}" updated successfully!')
                return redirect('project_detail', project_id=str(project.id))
        else:
            form = ProjectForm(initial={
                'name': project.name,
                'description': project.description,
                'language': project.language,
                'is_public': project.is_public,
                'max_members': project.max_members,
            })
        
        return render(request, 'projects/create_project.html', {
            'form': form, 
            'edit_mode': True,
            'project': project  # Pass the project object to the template
        })
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def delete_project(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Only project owner can delete the project
        if project.owner_id != request.user.id:
            return HttpResponseForbidden("Only the project owner can delete the project.")
        
        if request.method == 'POST':
            project_name = project.name
            project.delete()
            messages.success(request, f'Project "{project_name}" deleted successfully!')
            return redirect('project_list')
        
        return render(request, 'projects/delete_project.html', {'project': project})
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def create_file(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                project.members.filter(id=request.user.id).exists()):
            return HttpResponseForbidden("You don't have access to this project.")
        
        if request.method == 'POST':
            form = CodeFileForm(request.POST)
            if form.is_valid():
                filename = form.cleaned_data['filename']
                
                # Debug: Print all existing files
                existing_files = project.code_files.all()
                print(f"Existing files in project {project.id}:")
                for file in existing_files:
                    print(f"- {file.filename} (id: {file.id})")
                
                # Check if file with same name already exists
                if project.code_files.filter(filename=filename).exists():
                    messages.error(request, f'A file with the name "{filename}" already exists in this project.')
                    return render(request, 'projects/create_file.html', {
                        'form': form,
                        'project': project,
                        'existing_files': existing_files  # Pass existing files to template
                    })
                
                # Create new file
                code_file = CodeFile(
                    filename=filename,
                    language=form.cleaned_data['language'],
                    project=project
                )
                code_file.save()
                
                # Create initial empty version
                FileVersion.objects.create(
                    content="",
                    creator=request.user,
                    version_number=1,
                    code_file=code_file
                )
                
                messages.success(request, f'File "{code_file.filename}" created successfully!')
                return redirect('code_editor', project_id=str(project.id), file_id=str(code_file.id))
        else:
            form = CodeFileForm()
        
        return render(request, 'projects/create_file.html', {
            'form': form,
            'project': project,
            'existing_files': project.code_files.all()  # Pass existing files to template
        })
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')
    except Exception as e:
        messages.error(request, f'An error occurred while creating the file: {str(e)}')
        return redirect('project_detail', project_id=str(project_id))

@login_required
def code_editor(request, project_id, file_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                project.members.filter(id=request.user.id).exists()):
            return HttpResponseForbidden("You don't have access to this project.")
        
        # Get the code file
        code_file = CodeFile.objects.get(id=file_id, project=project)
        
        # Get the latest version's content
        latest_version = FileVersion.objects.filter(code_file=code_file).order_by('-version_number').first()
        content = latest_version.content if latest_version else ""
        
        return render(request, 'projects/code_editor.html', {
            'project': project,
            'code_file': code_file,
            'content': content
        })
    except (Project.DoesNotExist, CodeFile.DoesNotExist):
        messages.error(request, 'File not found.')
        return redirect('project_detail', project_id=str(project_id))

@login_required
def file_history(request, project_id, file_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                any(m.user_id == request.user.id for m in project.members)):
            return HttpResponseForbidden("You don't have access to this project.")
        
        # Find the file in the project
        code_file = next((f for f in project.code_files if str(f.id) == file_id), None)
        if not code_file:
            messages.error(request, 'File not found.')
            return redirect('project_detail', project_id=str(project.id))
        
        # Get versions in reverse chronological order
        versions = sorted(code_file.versions, key=lambda v: v.version_number, reverse=True)
        
        context = {
            'project': project,
            'code_file': code_file,
            'versions': versions,
        }
        return render(request, 'projects/file_history.html', context)
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def delete_file(request, project_id, file_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                any(m.user_id == request.user.id for m in project.members)):
            return HttpResponseForbidden("You don't have access to this project.")
        
        # Find and remove the file
        for i, code_file in enumerate(project.code_files):
            if str(code_file.id) == file_id:
                project.code_files.pop(i)
                project.save()
                messages.success(request, f'File "{code_file.filename}" deleted successfully!')
                return redirect('project_detail', project_id=str(project.id))
        
        messages.error(request, 'File not found.')
        return redirect('project_detail', project_id=str(project.id))
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def invite_member(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Only project owner can invite members
        if project.owner_id != request.user.id:
            return HttpResponseForbidden("Only the project owner can invite members.")
        
        if request.method == 'POST':
            form = ProjectInviteForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                try:
                    user = User.objects.get(username=username)
                    
                    # Check if user is already a member
                    if project.members.filter(id=user.id).exists():
                        messages.error(request, f'User "{username}" is already a member of this project.')
                        return redirect('project_members', project_id=str(project.id))
                    
                    # Add user as member
                    project.members.add(user, through_defaults={'role': 'member'})
                    project.save()
                    
                    messages.success(request, f'User "{username}" added to the project successfully!')
                    return redirect('project_members', project_id=str(project.id))
                except User.DoesNotExist:
                    messages.error(request, f'User "{username}" does not exist.')
        else:
            form = ProjectInviteForm()
        
        return render(request, 'projects/invite_member.html', {
            'form': form,
            'project': project
        })
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def project_members(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                project.members.filter(id=request.user.id).exists()):
            return HttpResponseForbidden("You don't have access to this project.")
        
        context = {
            'project': project,
            'owner': project.owner,
            'memberships': project.projectmembership_set.all(),
        }
        return render(request, 'projects/project_members.html', context)
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def remove_member(request, project_id, user_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Only project owner can remove members
        if project.owner_id != request.user.id:
            return HttpResponseForbidden("Only the project owner can remove members.")
        
        try:
            user = User.objects.get(id=user_id)
            if project.members.filter(id=user.id).exists():
                project.members.remove(user)
                project.save()
                messages.success(request, f'Member "{user.username}" removed from the project successfully!')
            else:
                messages.error(request, 'Member not found.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            
        return redirect('project_members', project_id=str(project.id))
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def task_list(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                any(m.user_id == request.user.id for m in project.members)):
            return HttpResponseForbidden("You don't have access to this project.")
        
        context = {
            'project': project,
            'tasks': project.tasks,
        }
        return render(request, 'projects/task_list.html', context)
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def create_task(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                any(m.user_id == request.user.id for m in project.members)):
            return HttpResponseForbidden("You don't have access to this project.")
        
        if request.method == 'POST':
            form = TaskForm(project, request.POST)
            if form.is_valid():
                task = Task(
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    assigned_to_id=form.cleaned_data['assigned_to'].id if form.cleaned_data['assigned_to'] else None,
                    assigned_to_username=form.cleaned_data['assigned_to'].username if form.cleaned_data['assigned_to'] else None,
                    status=form.cleaned_data['status'],
                    due_date=form.cleaned_data['due_date']
                )
                
                project.tasks.append(task)
                project.save()
                
                messages.success(request, 'Task created successfully!')
                return redirect('task_list', project_id=str(project.id))
        else:
            form = TaskForm(project)
        
        return render(request, 'projects/create_task.html', {
            'form': form,
            'project': project
        })
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def task_detail(request, project_id, task_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                any(m.user_id == request.user.id for m in project.members)):
            return HttpResponseForbidden("You don't have access to this project.")
        
        # Find the task
        task = next((t for t in project.tasks if str(t.id) == task_id), None)
        if not task:
            messages.error(request, 'Task not found.')
            return redirect('task_list', project_id=str(project.id))
        
        context = {
            'project': project,
            'task': task,
        }
        return render(request, 'projects/task_detail.html', context)
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def edit_task(request, project_id, task_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                any(m.user_id == request.user.id for m in project.members)):
            return HttpResponseForbidden("You don't have access to this project.")
        
        # Find the task
        task = next((t for t in project.tasks if str(t.id) == task_id), None)
        if not task:
            messages.error(request, 'Task not found.')
            return redirect('task_list', project_id=str(project.id))
        
        if request.method == 'POST':
            form = TaskForm(project, request.POST)
            if form.is_valid():
                task.title = form.cleaned_data['title']
                task.description = form.cleaned_data['description']
                task.assigned_to_id = form.cleaned_data['assigned_to'].id if form.cleaned_data['assigned_to'] else None
                task.assigned_to_username = form.cleaned_data['assigned_to'].username if form.cleaned_data['assigned_to'] else None
                task.status = form.cleaned_data['status']
                task.due_date = form.cleaned_data['due_date']
                
                project.save()
                messages.success(request, 'Task updated successfully!')
                return redirect('task_detail', project_id=str(project.id), task_id=str(task.id))
        else:
            initial_data = {
                'title': task.title,
                'description': task.description,
                'assigned_to': User.objects.get(id=task.assigned_to_id) if task.assigned_to_id else None,
                'status': task.status,
                'due_date': task.due_date,
            }
            form = TaskForm(project, initial=initial_data)
        
        return render(request, 'projects/create_task.html', {
            'form': form,
            'project': project,
            'task': task,
            'edit_mode': True
        })
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
def delete_task(request, project_id, task_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                any(m.user_id == request.user.id for m in project.members)):
            return HttpResponseForbidden("You don't have access to this project.")
        
        # Find and remove the task
        for i, task in enumerate(project.tasks):
            if str(task.id) == task_id:
                project.tasks.pop(i)
                project.save()
                messages.success(request, 'Task deleted successfully!')
                return redirect('task_list', project_id=str(project.id))
        
        messages.error(request, 'Task not found.')
        return redirect('task_list', project_id=str(project.id))
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('project_list')

@login_required
@require_POST
def save_file(request, project_id, file_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to the project
        if not (project.owner_id == request.user.id or 
                project.members.filter(id=request.user.id).exists()):
            return JsonResponse({'error': 'You don\'t have access to this project.'}, status=403)
        
        # Get the code file
        code_file = CodeFile.objects.get(id=file_id, project=project)
        
        # Get the content from the request
        data = json.loads(request.body)
        content = data.get('content', '')
        
        # Get the latest version number
        latest_version = FileVersion.objects.filter(code_file=code_file).order_by('-version_number').first()
        new_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create new version
        FileVersion.objects.create(
            content=content,
            creator=request.user,
            version_number=new_version_number,
            code_file=code_file
        )
        
        # Update file's updated_at timestamp
        code_file.updated_at = datetime.utcnow()
        code_file.save()
        
        return JsonResponse({
            'success': True,
            'version_number': new_version_number
        })
    except (Project.DoesNotExist, CodeFile.DoesNotExist):
        return JsonResponse({'error': 'File not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def request_to_join(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        
        # Check if project is public
        if not project.is_public:
            return JsonResponse({'error': 'This project is not public'}, status=403)
        
        # Check if user is already a member or owner
        if project.owner_id == request.user.id or any(m.user_id == request.user.id for m in project.members):
            return JsonResponse({'error': 'You are already a member of this project'}, status=400)
        
        # Check if user already has a pending request
        if any(req.requester_id == request.user.id and req.status == 'pending' for req in project.requests):
            return JsonResponse({'error': 'You already have a pending request for this project'}, status=400)
        
        # Create new request
        project.requests.append(ProjectRequest(
            requester_id=request.user.id,
            requester_username=request.user.username,
            status='pending',
            message=request.POST.get('message', '')
        ))
        project.save()
        
        return JsonResponse({'success': True})
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def handle_join_request(request, request_id):
    try:
        # Find the project with this request
        project = Project.objects.filter(requests__id=request_id).first()
        if not project:
            return JsonResponse({'error': 'Request not found'}, status=404)
        
        # Check if user is project owner
        if project.owner_id != request.user.id:
            return JsonResponse({'error': 'Only the project owner can handle join requests'}, status=403)
        
        # Find the request
        request_data = project.requests.filter(id=request_id).first()
        if not request_data:
            return JsonResponse({'error': 'Request not found'}, status=404)
        
        # Get action from request
        action = request.POST.get('action')
        if action not in ['approve', 'reject']:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        # Update request status
        request_data.status = 'approved' if action == 'approve' else 'rejected'
        request_data.save()
        
        # If approved, add user as member
        if action == 'approve':
            project.members.add(request_data.requester, through_defaults={'role': 'member'})
            project.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
