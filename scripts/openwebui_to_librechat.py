#!/usr/bin/env python3
"""
Conversion script for OpenWebUI exports to LibreChat format.

Converts conversations exported from OpenWebUI (JSON format) to LibreChat-compatible
import format.

Usage:
    python3 openwebui_to_librechat.py <openwebui_file.json> [output_file.json]
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


class OpenWebUIToLibreChatConverter:
    """Converts OpenWebUI exports to LibreChat format."""

    def __init__(self, input_file: str, output_file: Optional[str] = None):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file) if output_file else self._generate_output_path()
        self.data = None
        self.conversations = []

    def _generate_output_path(self) -> Path:
        """Generates the output file name based on the input file."""
        stem = self.input_file.stem
        return self.input_file.parent / f"{stem}_librechat.json"

    def load_openwebui_export(self) -> bool:
        """Loads the OpenWebUI export file."""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Error: The file is not a valid JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading the file: {e}")
            return False

    def analyze_structure(self) -> Dict[str, Any]:
        """Analyzes the OpenWebUI file structure."""
        if self.data is None:
            return {"error": "No data loaded"}

        info = {
            "type": type(self.data).__name__,
            "is_list": isinstance(self.data, list),
            "is_dict": isinstance(self.data, dict),
        }

        if isinstance(self.data, list):
            info["length"] = len(self.data)
            if len(self.data) > 0:
                first_item = self.data[0]
                info["first_item_type"] = type(first_item).__name__
                if isinstance(first_item, dict):
                    info["first_item_keys"] = list(first_item.keys())
        elif isinstance(self.data, dict):
            info["keys"] = list(self.data.keys())

        return info

    def detect_format(self) -> str:
        """Detects the specific OpenWebUI export format."""
        if self.data is None:
            return "unknown"

        # OpenWebUI can export in various formats
        # Format 1: Array of conversations
        if isinstance(self.data, list) and len(self.data) > 0:
            first = self.data[0]
            if isinstance(first, dict):
                # Format with 'chat' and 'messages'
                if 'chat' in first and isinstance(first['chat'], dict):
                    return "openwebui_chat_format"
                # Format with 'messages' directly
                if 'messages' in first:
                    return "openwebui_messages_format"

        # Format 2: Object with 'conversations' or 'chats'
        if isinstance(self.data, dict):
            if 'conversations' in self.data:
                return "openwebui_conversations_dict"
            if 'chats' in self.data:
                return "openwebui_chats_dict"

        return "unknown"

    def convert(self) -> List[Dict[str, Any]]:
        """Converts all OpenWebUI conversations to LibreChat format."""
        if self.data is None:
            raise ValueError("No data loaded")

        format_type = self.detect_format()
        print(f"📋 Detected format: {format_type}")

        if format_type == "openwebui_chat_format":
            return self._convert_chat_format()
        elif format_type == "openwebui_messages_format":
            return self._convert_messages_format()
        elif format_type == "openwebui_conversations_dict":
            return self._convert_conversations_dict()
        elif format_type == "openwebui_chats_dict":
            return self._convert_chats_dict()
        else:
            raise ValueError(f"Unrecognized format: {format_type}")

    def _convert_chat_format(self) -> List[Dict[str, Any]]:
        """Converts the format with 'chat' structure."""
        librechat_conversations = []

        if self.data is None:
            return librechat_conversations

        for item in self.data:
            if not isinstance(item, dict) or 'chat' not in item:
                continue

            chat = item['chat']
            conversation = self._create_librechat_conversation(chat, item)
            librechat_conversations.append(conversation)

        return librechat_conversations

    def _convert_messages_format(self) -> List[Dict[str, Any]]:
        """Converts the format with 'messages' directly."""
        librechat_conversations = []

        if self.data is None:
            return librechat_conversations

        for item in self.data:
            if not isinstance(item, dict):
                continue

            conversation = self._create_librechat_conversation(item, item)
            librechat_conversations.append(conversation)

        return librechat_conversations

    def _convert_conversations_dict(self) -> List[Dict[str, Any]]:
        """Converts the format with 'conversations' dictionary."""
        librechat_conversations = []
        if self.data is None:
            return librechat_conversations

        conversations = self.data.get('conversations', {})

        for conv_id, conv_data in conversations.items():
            if isinstance(conv_data, dict):
                conversation = self._create_librechat_conversation(conv_data, conv_data)
                librechat_conversations.append(conversation)

        return librechat_conversations

    def _convert_chats_dict(self) -> List[Dict[str, Any]]:
        """Converts the format with 'chats' dictionary."""
        librechat_conversations = []

        if self.data is None:
            return librechat_conversations

        chats = self.data.get('chats', {})

        for chat_id, chat_data in chats.items():
            if isinstance(chat_data, dict):
                conversation = self._create_librechat_conversation(chat_data, chat_data)
                librechat_conversations.append(conversation)

        return librechat_conversations

    def _create_librechat_conversation(self, source_data: Dict, metadata: Dict) -> Dict[str, Any]:
        """Creates a LibreChat conversation from OpenWebUI data."""

        # Extract basic information
        title = self._extract_title(source_data, metadata)
        model = self._extract_model(source_data, metadata)

        # Extract and convert messages
        messages = self._extract_and_convert_messages(source_data)

        # Create LibreChat structure
        conversation_id = str(uuid.uuid4())

        librechat_conv = {
            "conversationId": conversation_id,
            "endpoint": self._map_endpoint(model),
            "title": title,
            "exportAt": datetime.now(timezone.utc).strftime("%H:%M:%S GMT%z"),
            "branches": False,
            "recursive": False,
            "options": {
                "presetId": None,
                "model": model,
                "chatGptLabel": None,
                "promptPrefix": None,
                "temperature": 1,
                "top_p": 1,
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "resendFiles": True,
                "imageDetail": "auto",
                "endpoint": self._map_endpoint(model),
                "title": title
            },
            "messages": messages
        }

        return librechat_conv

    def _extract_title(self, source_data: Dict, metadata: Dict) -> str:
        """Extracts the conversation title."""
        # Try various possible locations
        for key in ['title', 'name', 'subject']:
            if key in source_data and source_data[key]:
                return str(source_data[key])
            if key in metadata and metadata[key]:
                return str(metadata[key])

        return "Conversation imported from OpenWebUI"

    def _extract_model(self, source_data: Dict, metadata: Dict) -> str:
        """Extracts the model used."""
        for key in ['model', 'model_name', 'model_id']:
            if key in source_data and source_data[key]:
                return str(source_data[key])
            if key in metadata and metadata[key]:
                return str(metadata[key])

        return "gpt-3.5-turbo"  # Default model

    def _extract_timestamp(self, source_data: Dict, metadata: Dict) -> datetime:
        """Extracts the creation timestamp."""
        for key in ['created_at', 'createdAt', 'timestamp', 'date']:
            if key in source_data:
                return self._parse_timestamp(source_data[key])
            if key in metadata:
                return self._parse_timestamp(metadata[key])

        return datetime.now(timezone.utc)

    def _parse_timestamp(self, value: Any) -> datetime:
        """Converts various timestamp formats to datetime."""
        if isinstance(value, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(value, tz=timezone.utc)
        elif isinstance(value, str):
            # ISO format or other string formats
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return datetime.now(timezone.utc)
        elif isinstance(value, datetime):
            return value

        return datetime.now(timezone.utc)

    def _extract_and_convert_messages(self, source_data: Dict) -> List[Dict[str, Any]]:
        """Extracts and converts OpenWebUI messages to LibreChat format."""
        messages = []

        # Get OpenWebUI messages
        openwebui_messages = []

        # Format 1: Messages inside 'chat'
        if 'chat' in source_data and isinstance(source_data['chat'], dict):
            chat = source_data['chat']
            if 'messages' in chat:
                openwebui_messages = chat['messages']

        # Format 2: Messages directly
        elif 'messages' in source_data:
            openwebui_messages = source_data['messages']

        # Convert each message
        parent_id = "00000000-0000-0000-0000-000000000000"

        for msg in openwebui_messages:
            if not isinstance(msg, dict):
                continue

            librechat_msg = self._convert_message(msg, parent_id)
            messages.append(librechat_msg)
            parent_id = librechat_msg['messageId']

        return messages

    def _convert_message(self, openwebui_msg: Dict, parent_id: str) -> Dict[str, Any]:
        """Converts an OpenWebUI message to LibreChat format."""

        # Determine the role (user or assistant)
        role = openwebui_msg.get('role', 'user')
        is_user = role in ['user', 'human']

        # Extract message content
        content = self._extract_message_content(openwebui_msg)

        # Extract other information
        message_id = openwebui_msg.get('id', str(uuid.uuid4()))
        if not isinstance(message_id, str):
            message_id = str(message_id)

        timestamp = self._extract_timestamp(openwebui_msg, openwebui_msg)
        model = openwebui_msg.get('model', None)

        # Create LibreChat message
        librechat_msg = {
            "messageId": message_id,
            "conversationId": openwebui_msg.get('conversationId', str(uuid.uuid4())),
            "parentMessageId": parent_id,
            "sender": "user" if is_user else (model or "assistant"),
            "text": content,
            "isCreatedByUser": is_user,
            "model": model,
            "endpoint": self._map_endpoint(model),
            "error": False,
            "unfinished": False,
            "createdAt": timestamp.isoformat(),
            "updatedAt": timestamp.isoformat(),
            "user": openwebui_msg.get('user', None)
        }

        return librechat_msg

    def _extract_message_content(self, msg: Dict) -> str:
        """Extracts the message content from OpenWebUI."""
        # Format 1: Content in 'content'
        if 'content' in msg:
            content = msg['content']
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Multi-part format (text, images, etc.)
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        text_parts.append(part['text'])
                    elif isinstance(part, str):
                        text_parts.append(part)
                return '\n'.join(text_parts)

        # Format 2: Content in 'text'
        if 'text' in msg:
            return str(msg['text'])

        # Format 3: Content in 'message'
        if 'message' in msg:
            return str(msg['message'])

        return ""

    def _map_endpoint(self, model: Optional[str]) -> str:
        """Maps the model to the corresponding LibreChat endpoint."""
        if not model:
            return "openAI"

        model_lower = model.lower()

        # Anthropic models
        if 'claude' in model_lower:
            return "anthropic"

        # Google models
        if 'gemini' in model_lower or 'palm' in model_lower:
            return "google"

        # OpenAI models (default)
        if any(x in model_lower for x in ['gpt', 'o1', 'o3']):
            return "openAI"

        # Other models (Qwen, DeepSeek, etc.)
        return "openAI"  # Can be customized based on configured endpoints

    def save_librechat_export(self) -> bool:
        """Saves the converted conversations in LibreChat format."""
        try:
            # If there are multiple conversations, save as array
            # If there's only one, save as individual object
            if len(self.conversations) == 1:
                output_data = self.conversations[0]
            else:
                output_data = self.conversations

            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"❌ Error saving the file: {e}")
            return False

    def convert_and_save(self) -> bool:
        """Executes the complete conversion and saves the result."""
        print(f"📖 Loading file: {self.input_file}")

        if not self.load_openwebui_export():
            return False

        # Analyze structure
        structure = self.analyze_structure()
        print(f"📊 Structure: {structure}")

        # Convert
        print("🔄 Converting conversations...")
        try:
            self.conversations = self.convert()
            print(f"✅ {len(self.conversations)} conversations converted")
        except Exception as e:
            print(f"❌ Error during conversion: {e}")
            return False

        # Save
        print(f"💾 Saving file: {self.output_file}")
        if not self.save_librechat_export():
            return False

        print("✅ Conversion completed!")
        print(f"📁 Output file: {self.output_file}")
        print(f"📊 Conversations converted: {len(self.conversations)}")

        return True


def main():
    """Main function of the script."""
    if len(sys.argv) < 2:
        print("Usage: python3 openwebui_to_librechat.py <openwebui_file.json> [output_file.json]")
        print("\nExamples:")
        print("  python3 openwebui_to_librechat.py openwebui_export.json")
        print("  python3 openwebui_to_librechat.py openwebui_export.json output.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(input_file).exists():
        print(f"❌ Error: The file '{input_file}' does not exist")
        sys.exit(1)

    converter = OpenWebUIToLibreChatConverter(input_file, output_file)

    if not converter.convert_and_save():
        sys.exit(1)


if __name__ == "__main__":
    main()
