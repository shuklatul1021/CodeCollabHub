import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Project, CodeFile, FileVersion
from .utils import check_user_access

logger = logging.getLogger(__name__)

class CodeEditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.project_id = self.scope['url_route']['kwargs']['project_id']
            self.file_id = self.scope['url_route']['kwargs']['file_id']
            
            # Log connection attempt details
            logger.info(f"WebSocket connection attempt - Project: {self.project_id}, File: {self.file_id}")
            logger.info(f"Client: {self.scope.get('client', 'No client info')}")
            logger.info(f"Headers: {self.scope.get('headers', 'No headers')}")
            logger.info(f"User: {self.scope.get('user', 'Anonymous')}")
            
            # Check user authentication
            if not self.scope.get('user'):
                logger.error("WebSocket connection rejected: User not authenticated")
                await self.close(code=4001, reason="Authentication required")
                return
            
            # Check user access to project
            has_access = await self.check_project_access()
            if not has_access:
                logger.error(f"WebSocket connection rejected: User {self.scope['user']} does not have access to project {self.project_id}")
                await self.close(code=4003, reason="Access denied")
                return
            
            # Accept the connection
            await self.accept()
            logger.info(f"WebSocket connection accepted - Project: {self.project_id}, File: {self.file_id}")
            
            # Add user to the group
            await self.channel_layer.group_add(
                f"project_{self.project_id}_file_{self.file_id}",
                self.channel_name
            )
            
            # Notify others that a new user has joined
            await self.channel_layer.group_send(
                f"project_{self.project_id}_file_{self.file_id}",
                {
                    'type': 'user_joined',
                    'username': self.scope['user'].username
                }
            )
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}", exc_info=True)
            await self.close(code=1011, reason=str(e))
    
    @database_sync_to_async
    def check_project_access(self):
        try:
            project = Project.objects.get(id=self.project_id)
            return check_user_access(self.scope['user'], project)
        except Project.DoesNotExist:
            logger.error(f"Project {self.project_id} does not exist")
            return False
        except Exception as e:
            logger.error(f"Error checking project access: {str(e)}", exc_info=True)
            return False

    async def disconnect(self, close_code):
        try:
            logger.info(f"WebSocket disconnected - Code: {close_code}")
            await self.channel_layer.group_discard(
                f"project_{self.project_id}_file_{self.file_id}",
                self.channel_name
            )
            
            # Notify others that user has left
            await self.channel_layer.group_send(
                f"project_{self.project_id}_file_{self.file_id}",
                {
                    'type': 'user_left',
                    'username': self.scope["user"].username
                }
            )
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            logger.info(f"Received message type: {message_type}")
            
            if message_type == 'code_update':
                # Save the code changes to database
                await self.save_code_changes(text_data_json.get('content'))
                
                # Broadcast the changes to other users
                await self.channel_layer.group_send(
                    f"project_{self.project_id}_file_{self.file_id}",
                    {
                        'type': 'code_update',
                        'content': text_data_json.get('content'),
                        'user': self.scope["user"].username
                    }
                )
            elif message_type == 'cursor_update':
                await self.channel_layer.group_send(
                    f"project_{self.project_id}_file_{self.file_id}",
                    {
                        'type': 'cursor_update',
                        'position': text_data_json.get('position'),
                        'user': self.scope["user"].username
                    }
                )
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error processing message'
            }))

    @database_sync_to_async
    def save_code_changes(self, content):
        try:
            code_file = CodeFile.objects.get(id=self.file_id)
            latest_version = code_file.get_latest_version()
            next_version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Create new version
            FileVersion.objects.create(
                code_file=code_file,
                creator=self.scope['user'],
                content=content,
                version_number=next_version_number
            )
            
            logger.info(f"Code changes saved for file {self.file_id}, version {next_version_number}")
            return True
        except Exception as e:
            logger.error(f"Error saving code changes: {str(e)}")
            return False

    async def code_update(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'code_update',
                'content': event['content'],
                'user': event['user']
            }))
        except Exception as e:
            logger.error(f"Error in code_update: {str(e)}")

    async def cursor_update(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'cursor_update',
                'position': event['position'],
                'user': event['user']
            }))
        except Exception as e:
            logger.error(f"Error in cursor_update: {str(e)}")

    async def user_joined(self, event):
        # Send user joined notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username']
        }))

    async def user_left(self, event):
        # Send user left notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'username': event['username']
        }))
