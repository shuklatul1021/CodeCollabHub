from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Project, CodeFile, FileVersion, Task

class ProjectsTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Login
        self.client.login(username='testuser', password='testpassword')
        
        # Create a test project
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            language='python',
            owner=self.user
        )
        
        # Create a test code file
        self.code_file = CodeFile.objects.create(
            project=self.project,
            filename='test.py',
            language='python'
        )
        
        # Create a file version
        self.file_version = FileVersion.objects.create(
            code_file=self.code_file,
            content='print("Hello, World!")',
            creator=self.user,
            version_number=1
        )

    def test_project_list(self):
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')

    def test_project_detail(self):
        response = self.client.get(reverse('project_detail', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')
        self.assertContains(response, 'test.py')

    def test_create_project(self):
        response = self.client.post(reverse('create_project'), {
            'name': 'New Project',
            'description': 'A new test project',
            'language': 'javascript'
        })
        self.assertEqual(response.status_code, 302)  # Redirects after creation
        self.assertTrue(Project.objects.filter(name='New Project').exists())

    def test_create_code_file(self):
        response = self.client.post(reverse('create_file', args=[self.project.id]), {
            'filename': 'new_file.py',
            'language': 'python'
        })
        self.assertEqual(response.status_code, 302)  # Redirects after creation
        self.assertTrue(CodeFile.objects.filter(filename='new_file.py').exists())

    def test_code_editor(self):
        response = self.client.get(reverse('code_editor', args=[self.project.id, self.code_file.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test.py')
