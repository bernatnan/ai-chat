# Conversation Conversion Scripts

This directory contains scripts to convert conversations between different AI chat platforms.

## Available Scripts

### 1. `diagnose_import.py` - Format Diagnostics

Analyzes JSON export files to identify the format and determine if they are compatible with LibreChat.

**Usage:**
```bash
python3 diagnose_import.py <file.json>
```

**Example:**
```bash
python3 diagnose_import.py ~/Downloads/conversation.json
```

**Output:**
- Detected format (LibreChat, ChatGPT, ChatbotUI, Claude, OpenWebUI, etc.)
- LibreChat compatibility
- Structure details
- Recommendations

### 2. `openwebui_to_librechat.py` - OpenWebUI → LibreChat Conversion

Converts OpenWebUI exports to LibreChat-compatible format.

**Usage:**
```bash
python3 openwebui_to_librechat.py <openwebui_file.json> [output_file.json]
```

**Examples:**
```bash
# Basic conversion (output file will have _librechat.json suffix)
python3 openwebui_to_librechat.py openwebui_export.json

# Specify output file
python3 openwebui_to_librechat.py openwebui_export.json output.json
```

**Features:**
- ✅ Converts multiple conversations
- ✅ Preserves timestamps
- ✅ Maps models to correct endpoints
- ✅ Supports various OpenWebUI export formats
- ✅ Converts multi-part messages (text + images)

**Supported OpenWebUI formats:**
- Array of conversations with `chat` structure
- Array of conversations with `messages` directly
- Dictionary with `conversations` key
- Dictionary with `chats` key

## How to Import to LibreChat

### Step 1: Export from OpenWebUI
1. Open OpenWebUI
2. Go to the conversation you want to export
3. Click on the three dots (⋮)
4. Select "Export"
5. Choose JSON format

### Step 2: Convert the file
```bash
python3 openwebui_to_librechat.py openwebui_export.json
```

This will create an `openwebui_export_librechat.json` file.

### Step 3: Import to LibreChat
1. Open LibreChat
2. Click on "Settings" (⚙️)
3. Go to "Data Controls"
4. Click on "Import Conversations"
5. Select the generated `_librechat.json` file

## Formats Supported by LibreChat

LibreChat natively accepts these formats:

| Format | Description | Identifier |
|--------|-------------|------------|
| **LibreChat** | Native format | `conversationId` + `messages` |
| **ChatGPT** | OpenAI export | Array with `mapping` |
| **ChatbotUI** | ChatbotUI format | `version` + `history` |
| **Claude** | Anthropic export | Array with `chat_messages` |

## Non-Native Formats (Require Conversion)

| Format | Conversion Script |
|--------|-------------------|
| **OpenWebUI** | `openwebui_to_librechat.py` |

## Troubleshooting

### Error: "Unsupported import type"

**Cause:** The JSON file is not in a LibreChat-compatible format.

**Solution:**
1. Run `diagnose_import.py` to identify the format:
   ```bash
   python3 diagnose_import.py your_file.json
   ```
2. If the format is not compatible, use the appropriate conversion script
3. Try importing again with the converted file

### Error: "Only JSON files are allowed"

**Cause:** LibreChat only accepts JSON files for import.

**Solution:** Make sure the file has `.json` extension and valid JSON content.

### Conversations appear empty

**Cause:** The message structure was not converted correctly.

**Solution:**
1. Open the converted file with a text editor
2. Verify that the structure is correct
3. If there are problems, open an issue in the repository

## Contributions

If you need a conversion script for another format:
1. Run `diagnose_import.py` to identify the structure
2. Create a new script based on `openwebui_to_librechat.py`
3. Submit a pull request with the new script

## Support

If you find problems or need help:
- Open an issue in the repository
- Include the example file (without sensitive data)
- Include the output of `diagnose_import.py`
