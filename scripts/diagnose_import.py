#!/usr/bin/env python3
"""
Script de diagnòstic per identificar el format de fitxers JSON d'importació de converses.
Analitza l'estructura del fitxer i determina quin format té segons els formats suportats per LibreChat.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


class ConversationFormatAnalyzer:
    """Analitza fitxers JSON per identificar el format de conversa."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data = None
        self.format_info = {}

    def load_file(self) -> bool:
        """Carrega el fitxer JSON."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Error: El fitxer no és un JSON vàlid: {e}")
            return False
        except Exception as e:
            print(f"❌ Error carregant el fitxer: {e}")
            return False

    def analyze(self) -> Dict[str, Any]:
        """Analitza l'estructura del fitxer i determina el format."""
        if self.data is None:
            return {"error": "No s'ha pogut carregar el fitxer"}

        result = {
            "file_path": str(self.file_path),
            "file_size": self.file_path.stat().st_size,
            "is_array": isinstance(self.data, list),
            "is_object": isinstance(self.data, dict),
            "top_level_keys": list(self.data.keys()) if isinstance(self.data, dict) else None,
            "array_length": len(self.data) if isinstance(self.data, list) else None,
            "detected_format": None,
            "confidence": None,
            "details": {},
            "supported_by_librechat": False,
            "recommendation": None
        }

        # Detectar format LibreChat natiu
        if self._is_librechat_format():
            result["detected_format"] = "LibreChat (natiu)"
            result["confidence"] = "alta"
            result["supported_by_librechat"] = True
            result["details"] = self._analyze_librechat_format()
            result["recommendation"] = "✅ Aquest format és compatible amb LibreChat"

        # Detectar format ChatGPT
        elif self._is_chatgpt_format():
            result["detected_format"] = "ChatGPT (OpenAI)"
            result["confidence"] = "alta"
            result["supported_by_librechat"] = True
            result["details"] = self._analyze_chatgpt_format()
            result["recommendation"] = "✅ Aquest format és compatible amb LibreChat"

        # Detectar format ChatbotUI
        elif self._is_chatbotui_format():
            result["detected_format"] = "ChatbotUI"
            result["confidence"] = "alta"
            result["supported_by_librechat"] = True
            result["details"] = self._analyze_chatbotui_format()
            result["recommendation"] = "✅ Aquest format és compatible amb LibreChat"

        # Detectar format Claude
        elif self._is_claude_format():
            result["detected_format"] = "Claude (Anthropic)"
            result["confidence"] = "alta"
            result["supported_by_librechat"] = True
            result["details"] = self._analyze_claude_format()
            result["recommendation"] = "✅ Aquest format és compatible amb LibreChat"

        # Format no reconegut
        else:
            result["detected_format"] = "Desconegut"
            result["confidence"] = "baixa"
            result["supported_by_librechat"] = False
            result["details"] = self._analyze_unknown_format()
            result["recommendation"] = "❌ Aquest format NO és compatible amb LibreChat. Cal convertir-lo."

        return result

    def _is_librechat_format(self) -> bool:
        """Verifica si és el format natiu de LibreChat."""
        if not isinstance(self.data, dict):
            return False

        has_conversation_id = "conversationId" in self.data
        has_messages = "messages" in self.data or "messagesTree" in self.data

        return has_conversation_id and has_messages

    def _is_chatgpt_format(self) -> bool:
        """Verifica si és el format de ChatGPT (OpenAI)."""
        if not isinstance(self.data, list):
            return False

        if len(self.data) == 0:
            return False

        # El primer element ha de tenir 'mapping'
        first_item = self.data[0]
        return isinstance(first_item, dict) and "mapping" in first_item

    def _is_chatbotui_format(self) -> bool:
        """Verifica si és el format de ChatbotUI."""
        if not isinstance(self.data, dict):
            return False

        has_version = "version" in self.data
        has_history = "history" in self.data and isinstance(self.data.get("history"), list)

        return has_version and has_history

    def _is_claude_format(self) -> bool:
        """Verifica si és el format de Claude (Anthropic)."""
        if not isinstance(self.data, list):
            return False

        if len(self.data) == 0:
            return False

        # El primer element ha de tenir 'chat_messages'
        first_item = self.data[0]
        return isinstance(first_item, dict) and "chat_messages" in first_item

    def _analyze_librechat_format(self) -> Dict[str, Any]:
        """Analitza els detalls del format LibreChat."""
        details = {
            "conversation_id": self.data.get("conversationId"),
            "title": self.data.get("title"),
            "endpoint": self.data.get("endpoint"),
            "has_recursive_structure": "messagesTree" in self.data,
            "message_count": 0
        }

        if "messages" in self.data:
            messages = self.data["messages"]
            if isinstance(messages, list):
                details["message_count"] = len(messages)
                details["messages_are_recursive"] = any("children" in msg for msg in messages if isinstance(msg, dict))

        if "messagesTree" in self.data:
            details["message_count"] = self._count_recursive_messages(self.data["messagesTree"])

        return details

    def _analyze_chatgpt_format(self) -> Dict[str, Any]:
        """Analitza els detalls del format ChatGPT."""
        details = {
            "conversation_count": len(self.data),
            "first_conversation_title": self.data[0].get("title") if self.data else None
        }

        if self.data and "mapping" in self.data[0]:
            mapping = self.data[0]["mapping"]
            details["message_count"] = len(mapping)

        return details

    def _analyze_chatbotui_format(self) -> Dict[str, Any]:
        """Analitza els detalls del format ChatbotUI."""
        details = {
            "version": self.data.get("version"),
            "conversation_count": len(self.data.get("history", [])),
            "has_folders": "folders" in self.data,
            "has_prompts": "prompts" in self.data
        }

        return details

    def _analyze_claude_format(self) -> Dict[str, Any]:
        """Analitza els detalls del format Claude."""
        details = {
            "conversation_count": len(self.data),
            "first_conversation_name": self.data[0].get("name") if self.data else None
        }

        if self.data and "chat_messages" in self.data[0]:
            details["first_conversation_message_count"] = len(self.data[0]["chat_messages"])

        return details

    def _analyze_unknown_format(self) -> Dict[str, Any]:
        """Analitza un format desconegut i proporciona informació útil."""
        details = {
            "analysis": "Format no reconegut. Analitzant estructura..."
        }

        if isinstance(self.data, dict):
            details["type"] = "object"
            details["keys"] = list(self.data.keys())[:20]  # Primeres 20 claus
            details["key_count"] = len(self.data.keys())

            # Intentar identificar patrons
            if "messages" in self.data:
                details["note"] = "Té 'messages' però falta 'conversationId'. Podria ser un format similar a LibreChat."
            elif "conversations" in self.data:
                details["note"] = "Té 'conversations'. Podria ser un format multi-conversa."

        elif isinstance(self.data, list):
            details["type"] = "array"
            details["length"] = len(self.data)

            if len(self.data) > 0:
                first_item = self.data[0]
                if isinstance(first_item, dict):
                    details["first_item_keys"] = list(first_item.keys())[:20]
                    details["first_item_key_count"] = len(first_item.keys())

                    # Intentar identificar patrons
                    if "role" in first_item and "content" in first_item:
                        details["note"] = "Sembla un format de missatges. Podria ser compatible amb LibreChat amb conversió."

        return details

    def _count_recursive_messages(self, messages_tree) -> int:
        """Compta recursivament el nombre de missatges en una estructura arbòria."""
        count = 0
        if isinstance(messages_tree, list):
            for msg in messages_tree:
                if isinstance(msg, dict):
                    count += 1
                    if "children" in msg:
                        count += self._count_recursive_messages(msg["children"])
        return count

    def print_report(self):
        """Imprimeix un informe complet de l'anàlisi."""
        result = self.analyze()

        print("\n" + "="*80)
        print("INFORME D'ANÀLISI DE FORMAT DE CONVERSA")
        print("="*80)

        print(f"\n📁 Fitxer: {result['file_path']}")
        print(f"📏 Mida: {result['file_size']} bytes")
        print(f"📊 Tipus: {'Array' if result['is_array'] else 'Objecte' if result['is_object'] else 'Desconegut'}")

        if result['is_array']:
            print(f"📝 Elements: {result['array_length']}")
        elif result['is_object'] and result['top_level_keys']:
            print(f"🔑 Claus principals: {', '.join(result['top_level_keys'][:10])}")
            if len(result['top_level_keys']) > 10:
                print(f"   ... i {len(result['top_level_keys']) - 10} claus més")

        print("\n" + "-"*80)
        print("DETECCIÓ DE FORMAT")
        print("-"*80)

        print(f"\n🎯 Format detectat: {result['detected_format']}")
        print(f"🎲 Confiança: {result['confidence']}")
        print(f"✅ Compatible amb LibreChat: {'SÍ' if result['supported_by_librechat'] else 'NO'}")

        if result['details']:
            print("\n" + "-"*80)
            print("DETALLS")
            print("-"*80)
            for key, value in result['details'].items():
                print(f"  • {key}: {value}")

        print("\n" + "-"*80)
        print("RECOMANACIÓ")
        print("-"*80)
        print(f"\n{result['recommendation']}")

        if not result['supported_by_librechat']:
            print("\n💡 Possibles solucions:")
            print("  1. Exportar les converses des del sistema original en un format compatible")
            print("  2. Utilitzar un script de conversió per transformar el format")
            print("  3. Importar manualment les converses una per una")

        print("\n" + "="*80)

        return result


def main():
    """Funció principal del script."""
    if len(sys.argv) < 2:
        print("Ús: python diagnose_import.py <fitxer_json>")
        print("\nExemples:")
        print("  python diagnose_import.py conversa.json")
        print("  python diagnose_import.py /ruta/al/fitxer.json")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"❌ Error: El fitxer '{file_path}' no existeix")
        sys.exit(1)

    analyzer = ConversationFormatAnalyzer(file_path)

    if not analyzer.load_file():
        sys.exit(1)

    analyzer.print_report()


if __name__ == "__main__":
    main()
