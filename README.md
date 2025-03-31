# CodeCollab Hub

A real-time collaborative code editor platform built with Django and WebSockets.

## Distinctiveness and Complexity

CodeCollab Hub stands out from the standard social network project by offering a sophisticated real-time collaborative coding environment. Here's why it satisfies the distinctiveness and complexity requirements:

1. **Real-time Collaboration**: Unlike traditional social networks, this project implements WebSocket-based real-time collaboration, allowing multiple users to edit code simultaneously with live cursor tracking and instant updates.

2. **Version Control System**: The project includes a custom version control system that tracks code changes, maintains file history, and allows users to revert to previous versions.

3. **Project Management**: Beyond basic social features, it includes project management capabilities like task tracking, member roles, and project requests.

4. **Advanced Security**: Implements role-based access control, project privacy settings, and secure WebSocket connections.

5. **Rich Code Editor**: Integrates Monaco Editor (the same editor used in VS Code) with features like syntax highlighting, auto-completion, and real-time collaboration.

## Project Structure

```
codecollabhub/
├── codecollabhub/          # Main project directory
│   ├── asgi.py            # ASGI configuration for WebSocket support
│   ├── settings.py        # Project settings
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI configuration
├── projects/              # Main application
│   ├── consumers.py       # WebSocket consumer for real-time updates
│   ├── models.py          # Database models
│   ├── routing.py         # WebSocket URL routing
│   ├── urls.py            # Application URL routing
│   ├── utils.py           # Utility functions
│   └── views.py           # View functions
├── static/                # Static files
│   ├── css/              # CSS styles
│   └── js/               # JavaScript files
│       └── editor.js     # Editor functionality
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   └── projects/         # Project-specific templates
├── manage.py             # Django management script
└── requirements.txt      # Python dependencies
```

## Key Features

1. **Real-time Code Collaboration**
   - Live cursor tracking
   - Instant code updates
   - User presence indicators

2. **Project Management**
   - Create and manage coding projects
   - Invite collaborators
   - Set project privacy
   - Track tasks and progress

3. **Version Control**
   - Automatic version tracking
   - File history
   - Version comparison
   - Rollback capabilities

4. **User Management**
   - Role-based access control
   - Project membership requests
   - User permissions

## How to Run the Application

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up the Database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create a Superuser**
   ```bash
   python manage.py createsuperuser
   ```

4. **Run the Development Server**
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```
   ```bash
   daphne -b 127.0.0.1 -p 8000 codecollabhub.asgi:application
   ```

5. **Access the Application**
   - Open your browser and navigate to `http://127.0.0.1:8000`
   - Log in with your superuser credentials
   - Create a new project and start collaborating!

## Additional Information

1. **WebSocket Support**
   - The application uses Django Channels for WebSocket support
   - Real-time updates are handled through WebSocket connections
   - Connection status is monitored and displayed to users

2. **Security Features**
   - CSRF protection for all forms
   - Secure WebSocket connections
   - Role-based access control
   - Project privacy settings

3. **Browser Support**
   - Works best on modern browsers (Chrome, Firefox, Safari, Edge)
   - Requires JavaScript enabled
   - WebSocket support required

4. **Performance Considerations**
   - Uses in-memory channel layer for development
   - For production, Redis is recommended
   - Large files may require additional optimization

## Requirements

The following Python packages are required (see requirements.txt for versions):
- Django
- channels
- daphne
- django-crispy-forms
- crispy-tailwind

## Development Notes

1. **Code Style**
   - Follows PEP 8 guidelines
   - Uses Django's recommended coding style
   - Includes comprehensive comments

2. **Testing**
   - Unit tests included for core functionality
   - WebSocket tests for real-time features
   - Integration tests for project management

3. **Future Improvements**
   - Add file upload support
   - Implement code execution
   - Add more editor features
   - Enhance version control 