#!/usr/bin/env python3
"""
Diagnostic script to identify the format of conversation import JSON files.
Analyzes the file structure and determines which format it has according to LibreChat supported formats.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


class ConversationFormatAnalyzer:
    """Analyzes JSON files to identify the conversation format."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.data = None
        self.format_info = {}

    def load_file(self) -> bool:
        """Loads the JSON file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Error: The file is not a valid JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading the file: {e}")
            return False

    def analyze(self) -> Dict[str, Any]:
        """Analyzes the file structure and determines the format."""
        if self.data is None:
            return {"error": "Could not load the file"}

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

        # Detect native LibreChat format
        if self._is_librechat_format():
            result["detected_format"] = "LibreChat (native)"
            result["confidence"] = "high"
            result["supported_by_librechat"] = True
            result["details"] = self._analyze_librechat_format()
            result["recommendation"] = "✅ This format is compatible with LibreChat"

        # Detect ChatGPT format
        elif self._is_chatgpt_format():
            result["detected_format"] = "ChatGPT (OpenAI)"
            result["confidence"] = "high"
            result["supported_by_librechat"] = True
            result["details"] = self._analyze_chatgpt_format()
            result["recommendation"] = "✅ This format is compatible with LibreChat"

        # Detect ChatbotUI format
        elif self._is_chatbotui_format():
            result["detected_format"] = "ChatbotUI"
            result["confidence"] = "high"
            result["supported_by_librechat"] = True
            result["details"] = self._analyze_chatbotui_format()
            result["recommendation"] = "✅ This format is compatible with LibreChat"

        # Detect Claude format
        elif self._is_claude_format():
            result["detected_format"] = "Claude (Anthropic)"
            result["confidence"] = "high"
            result["supported_by_librechat"] = True
            result["details"] = self._analyze_claude_format()
            result["recommendation"] = "✅ This format is compatible with LibreChat"

        # Unrecognized format
        else:
            result["detected_format"] = "Unknown"
            result["confidence"] = "low"
            result["supported_by_librechat"] = False
            result["details"] = self._analyze_unknown_format()
            result["recommendation"] = "❌ This format is NOT compatible with LibreChat. It needs to be converted."

        return result

    def _is_librechat_format(self) -> bool:
        """Checks if it's the native LibreChat format."""
        if not isinstance(self.data, dict):
            return False

        has_conversation_id = "conversationId" in self.data
        has_messages = "messages" in self.data or "messagesTree" in self.data

        return has_conversation_id and has_messages

    def _is_chatgpt_format(self) -> bool:
        """Checks if it's the ChatGPT (OpenAI) format."""
        if not isinstance(self.data, list):
            return False

        if len(self.data) == 0:
            return False

        # The first element must have 'mapping'
        first_item = self.data[0]
        return isinstance(first_item, dict) and "mapping" in first_item

    def _is_chatbotui_format(self) -> bool:
        """Checks if it's the ChatbotUI format."""
        if not isinstance(self.data, dict):
            return False

        has_version = "version" in self.data
        has_history = "history" in self.data and isinstance(self.data.get("history"), list)

        return has_version and has_history

    def _is_claude_format(self) -> bool:
        """Checks if it's the Claude (Anthropic) format."""
        if not isinstance(self.data, list):
            return False

        if len(self.data) == 0:
            return False

        # The first element must have 'chat_messages'
        first_item = self.data[0]
        return isinstance(first_item, dict) and "chat_messages" in first_item

    def _analyze_librechat_format(self) -> Dict[str, Any]:
        """Analyzes the details of the LibreChat format."""
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
        """Analyzes the details of the ChatGPT format."""
        details = {
            "conversation_count": len(self.data),
            "first_conversation_title": self.data[0].get("title") if self.data else None
        }

        if self.data and "mapping" in self.data[0]:
            mapping = self.data[0]["mapping"]
            details["message_count"] = len(mapping)

        return details

    def _analyze_chatbotui_format(self) -> Dict[str, Any]:
        """Analyzes the details of the ChatbotUI format."""
        details = {
            "version": self.data.get("version"),
            "conversation_count": len(self.data.get("history", [])),
            "has_folders": "folders" in self.data,
            "has_prompts": "prompts" in self.data
        }

        return details

    def _analyze_claude_format(self) -> Dict[str, Any]:
        """Analyzes the details of the Claude format."""
        details = {
            "conversation_count": len(self.data),
            "first_conversation_name": self.data[0].get("name") if self.data else None
        }

        if self.data and "chat_messages" in self.data[0]:
            details["first_conversation_message_count"] = len(self.data[0]["chat_messages"])

        return details

    def _analyze_unknown_format(self) -> Dict[str, Any]:
        """Analyzes an unknown format and provides useful information."""
        details = {
            "analysis": "Format not recognized. Analyzing structure..."
        }

        if isinstance(self.data, dict):
            details["type"] = "object"
            details["keys"] = list(self.data.keys())[:20]  # First 20 keys
            details["key_count"] = len(self.data.keys())

            # Try to identify patterns
            if "messages" in self.data:
                details["note"] = "Has 'messages' but missing 'conversationId'. Could be a LibreChat-like format."
            elif "conversations" in self.data:
                details["note"] = "Has 'conversations'. Could be a multi-conversation format."

        elif isinstance(self.data, list):
            details["type"] = "array"
            details["length"] = len(self.data)

            if len(self.data) > 0:
                first_item = self.data[0]
                if isinstance(first_item, dict):
                    details["first_item_keys"] = list(first_item.keys())[:20]
                    details["first_item_key_count"] = len(first_item.keys())

                    # Try to identify patterns
                    if "role" in first_item and "content" in first_item:
                        details["note"] = "Looks like a message format. Could be compatible with LibreChat with conversion."

        return details

    def _count_recursive_messages(self, messages_tree) -> int:
        """Recursively counts the number of messages in a tree structure."""
        count = 0
        if isinstance(messages_tree, list):
            for msg in messages_tree:
                if isinstance(msg, dict):
                    count += 1
                    if "children" in msg:
                        count += self._count_recursive_messages(msg["children"])
        return count

    def print_report(self):
        """Prints a complete analysis report."""
        result = self.analyze()

        print("\n" + "="*80)
        print("CONVERSATION FORMAT ANALYSIS REPORT")
        print("="*80)

        print(f"\n📁 File: {result['file_path']}")
        print(f"📏 Size: {result['file_size']} bytes")
        print(f"📊 Type: {'Array' if result['is_array'] else 'Object' if result['is_object'] else 'Unknown'}")

        if result['is_array']:
            print(f"📝 Elements: {result['array_length']}")
        elif result['is_object'] and result['top_level_keys']:
            print(f"🔑 Main keys: {', '.join(result['top_level_keys'][:10])}")
            if len(result['top_level_keys']) > 10:
                print(f"   ... and {len(result['top_level_keys']) - 10} more keys")

        print("\n" + "-"*80)
        print("FORMAT DETECTION")
        print("-"*80)

        print(f"\n🎯 Detected format: {result['detected_format']}")
        print(f"🎲 Confidence: {result['confidence']}")
        print(f"✅ Compatible with LibreChat: {'YES' if result['supported_by_librechat'] else 'NO'}")

        if result['details']:
            print("\n" + "-"*80)
            print("DETAILS")
            print("-"*80)
            for key, value in result['details'].items():
                print(f"  • {key}: {value}")

        print("\n" + "-"*80)
        print("RECOMMENDATION")
        print("-"*80)
        print(f"\n{result['recommendation']}")

        if not result['supported_by_librechat']:
            print("\n💡 Possible solutions:")
            print("  1. Export conversations from the original system in a compatible format")
            print("  2. Use a conversion script to transform the format")
            print("  3. Manually import conversations one by one")

        print("\n" + "="*80)

        return result


def main():
    """Main function of the script."""
    if len(sys.argv) < 2:
        print("Usage: python diagnose_import.py <json_file>")
        print("\nExamples:")
        print("  python diagnose_import.py conversation.json")
        print("  python diagnose_import.py /path/to/file.json")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"❌ Error: The file '{file_path}' does not exist")
        sys.exit(1)

    analyzer = ConversationFormatAnalyzer(file_path)

    if not analyzer.load_file():
        sys.exit(1)

    analyzer.print_report()


if __name__ == "__main__":
    main()
