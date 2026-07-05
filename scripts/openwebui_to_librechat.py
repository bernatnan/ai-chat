#!/usr/bin/env python3
"""
Script de conversió d'exportacions d'OpenWebUI a format LibreChat.

Converteix converses exportades des d'OpenWebUI (format JSON) a format compatible
amb la importació de LibreChat.

Ús:
    python3 openwebui_to_librechat.py <fitxer_openwebui.json> [fitxer_sortida.json]
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


class OpenWebUIToLibreChatConverter:
    """Converteix exportacions d'OpenWebUI a format LibreChat."""

    def __init__(self, input_file: str, output_file: Optional[str] = None):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file) if output_file else self._generate_output_path()
        self.data = None
        self.conversations = []

    def _generate_output_path(self) -> Path:
        """Genera el nom del fitxer de sortida basat en el fitxer d'entrada."""
        stem = self.input_file.stem
        return self.input_file.parent / f"{stem}_librechat.json"

    def load_openwebui_export(self) -> bool:
        """Carrega el fitxer d'exportació d'OpenWebUI."""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Error: El fitxer no és un JSON vàlid: {e}")
            return False
        except Exception as e:
            print(f"❌ Error carregant el fitxer: {e}")
            return False

    def analyze_structure(self) -> Dict[str, Any]:
        """Analitza l'estructura del fitxer d'OpenWebUI."""
        if self.data is None:
            return {"error": "No s'ha carregat cap dada"}

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
        """Detecta el format específic de l'exportació d'OpenWebUI."""
        if self.data is None:
            return "unknown"

        # OpenWebUI pot exportar en diversos formats
        # Format 1: Array de converses
        if isinstance(self.data, list) and len(self.data) > 0:
            first = self.data[0]
            if isinstance(first, dict):
                # Format amb 'chat' i 'messages'
                if 'chat' in first and isinstance(first['chat'], dict):
                    return "openwebui_chat_format"
                # Format amb 'messages' directament
                if 'messages' in first:
                    return "openwebui_messages_format"

        # Format 2: Objecte amb 'conversations' o 'chats'
        if isinstance(self.data, dict):
            if 'conversations' in self.data:
                return "openwebui_conversations_dict"
            if 'chats' in self.data:
                return "openwebui_chats_dict"

        return "unknown"

    def convert(self) -> List[Dict[str, Any]]:
        """Converteix totes les converses d'OpenWebUI a format LibreChat."""
        if self.data is None:
            raise ValueError("No s'han carregat dades")

        format_type = self.detect_format()
        print(f"📋 Format detectat: {format_type}")

        if format_type == "openwebui_chat_format":
            return self._convert_chat_format()
        elif format_type == "openwebui_messages_format":
            return self._convert_messages_format()
        elif format_type == "openwebui_conversations_dict":
            return self._convert_conversations_dict()
        elif format_type == "openwebui_chats_dict":
            return self._convert_chats_dict()
        else:
            raise ValueError(f"Format no reconegut: {format_type}")

    def _convert_chat_format(self) -> List[Dict[str, Any]]:
        """Converteix el format amb estructura 'chat'."""
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
        """Converteix el format amb 'messages' directament."""
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
        """Converteix el format amb diccionari de 'conversations'."""
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
        """Converteix el format amb diccionari de 'chats'."""
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
        """Crea una conversa en format LibreChat a partir de les dades d'OpenWebUI."""

        # Extreure informació bàsica
        title = self._extract_title(source_data, metadata)
        model = self._extract_model(source_data, metadata)

        # Extreure i convertir missatges
        messages = self._extract_and_convert_messages(source_data)

        # Crear estructura LibreChat
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
        """Extreu el títol de la conversa."""
        # Provar diverses ubicacions possibles
        for key in ['title', 'name', 'subject']:
            if key in source_data and source_data[key]:
                return str(source_data[key])
            if key in metadata and metadata[key]:
                return str(metadata[key])

        return "Conversa importada d'OpenWebUI"

    def _extract_model(self, source_data: Dict, metadata: Dict) -> str:
        """Extreu el model utilitzat."""
        for key in ['model', 'model_name', 'model_id']:
            if key in source_data and source_data[key]:
                return str(source_data[key])
            if key in metadata and metadata[key]:
                return str(metadata[key])

        return "gpt-3.5-turbo"  # Model per defecte

    def _extract_timestamp(self, source_data: Dict, metadata: Dict) -> datetime:
        """Extreu la marca de temps de creació."""
        for key in ['created_at', 'createdAt', 'timestamp', 'date']:
            if key in source_data:
                return self._parse_timestamp(source_data[key])
            if key in metadata:
                return self._parse_timestamp(metadata[key])

        return datetime.now(timezone.utc)

    def _parse_timestamp(self, value: Any) -> datetime:
        """Converteix diversos formats de timestamp a datetime."""
        if isinstance(value, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(value, tz=timezone.utc)
        elif isinstance(value, str):
            # ISO format o altres formats de cadena
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return datetime.now(timezone.utc)
        elif isinstance(value, datetime):
            return value

        return datetime.now(timezone.utc)

    def _extract_and_convert_messages(self, source_data: Dict) -> List[Dict[str, Any]]:
        """Extreu i converteix els missatges d'OpenWebUI a format LibreChat."""
        messages = []

        # Obtenir els missatges d'OpenWebUI
        openwebui_messages = []

        # Format 1: Missatges dins de 'chat'
        if 'chat' in source_data and isinstance(source_data['chat'], dict):
            chat = source_data['chat']
            if 'messages' in chat:
                openwebui_messages = chat['messages']

        # Format 2: Missatges directament
        elif 'messages' in source_data:
            openwebui_messages = source_data['messages']

        # Convertir cada missatge
        parent_id = "00000000-0000-0000-0000-000000000000"

        for msg in openwebui_messages:
            if not isinstance(msg, dict):
                continue

            librechat_msg = self._convert_message(msg, parent_id)
            messages.append(librechat_msg)
            parent_id = librechat_msg['messageId']

        return messages

    def _convert_message(self, openwebui_msg: Dict, parent_id: str) -> Dict[str, Any]:
        """Converteix un missatge d'OpenWebUI a format LibreChat."""

        # Determinar el rol (usuari o assistent)
        role = openwebui_msg.get('role', 'user')
        is_user = role in ['user', 'human']

        # Extreure el contingut del missatge
        content = self._extract_message_content(openwebui_msg)

        # Extreure altra informació
        message_id = openwebui_msg.get('id', str(uuid.uuid4()))
        if not isinstance(message_id, str):
            message_id = str(message_id)

        timestamp = self._extract_timestamp(openwebui_msg, openwebui_msg)
        model = openwebui_msg.get('model', None)

        # Crear missatge LibreChat
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
        """Extreu el contingut del missatge d'OpenWebUI."""
        # Format 1: Contingut en 'content'
        if 'content' in msg:
            content = msg['content']
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Format multi-part (text, images, etc.)
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        text_parts.append(part['text'])
                    elif isinstance(part, str):
                        text_parts.append(part)
                return '\n'.join(text_parts)

        # Format 2: Contingut en 'text'
        if 'text' in msg:
            return str(msg['text'])

        # Format 3: Contingut en 'message'
        if 'message' in msg:
            return str(msg['message'])

        return ""

    def _map_endpoint(self, model: Optional[str]) -> str:
        """Mapa el model a l'endpoint de LibreChat corresponent."""
        if not model:
            return "openAI"

        model_lower = model.lower()

        # Models d'Anthropic
        if 'claude' in model_lower:
            return "anthropic"

        # Models de Google
        if 'gemini' in model_lower or 'palm' in model_lower:
            return "google"

        # Models d'OpenAI (per defecte)
        if any(x in model_lower for x in ['gpt', 'o1', 'o3']):
            return "openAI"

        # Altres models (Qwen, DeepSeek, etc.)
        return "openAI"  # Es pot personalitzar segons els endpoints configurats

    def save_librechat_export(self) -> bool:
        """Guarda les converses convertides en format LibreChat."""
        try:
            # Si hi ha múltiples converses, guardar com a array
            # Si només hi ha una, guardar com a objecte individual
            if len(self.conversations) == 1:
                output_data = self.conversations[0]
            else:
                output_data = self.conversations

            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"❌ Error guardant el fitxer: {e}")
            return False

    def convert_and_save(self) -> bool:
        """Executa la conversió completa i guarda el resultat."""
        print(f"📖 Carregant fitxer: {self.input_file}")

        if not self.load_openwebui_export():
            return False

        # Analitzar estructura
        structure = self.analyze_structure()
        print(f"📊 Estructura: {structure}")

        # Convertir
        print("🔄 Convertint converses...")
        try:
            self.conversations = self.convert()
            print(f"✅ {len(self.conversations)} converses convertides")
        except Exception as e:
            print(f"❌ Error en la conversió: {e}")
            return False

        # Guardar
        print(f"💾 Guardant fitxer: {self.output_file}")
        if not self.save_librechat_export():
            return False

        print("✅ Conversió completada!")
        print(f"📁 Fitxer de sortida: {self.output_file}")
        print(f"📊 Converses convertides: {len(self.conversations)}")

        return True


def main():
    """Funció principal del script."""
    if len(sys.argv) < 2:
        print("Ús: python3 openwebui_to_librechat.py <fitxer_openwebui.json> [fitxer_sortida.json]")
        print("\nExemples:")
        print("  python3 openwebui_to_librechat.py openwebui_export.json")
        print("  python3 openwebui_to_librechat.py openwebui_export.json sortida.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(input_file).exists():
        print(f"❌ Error: El fitxer '{input_file}' no existeix")
        sys.exit(1)

    converter = OpenWebUIToLibreChatConverter(input_file, output_file)

    if not converter.convert_and_save():
        sys.exit(1)


if __name__ == "__main__":
    main()
