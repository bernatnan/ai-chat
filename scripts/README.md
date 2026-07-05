# Scripts de Conversió de Converses

Aquest directori conté scripts per convertir converses entre diferents plataformes de xat amb IA.

## Scripts Disponibles

### 1. `diagnose_import.py` - Diagnòstic de Format

Analitza fitxers JSON d'exportació per identificar el format i determinar si són compatibles amb LibreChat.

**Ús:**
```bash
python3 diagnose_import.py <fitxer.json>
```

**Exemple:**
```bash
python3 diagnose_import.py ~/Downloads/conversa.json
```

**Sortida:**
- Format detectat (LibreChat, ChatGPT, ChatbotUI, Claude, OpenWebUI, etc.)
- Compatibilitat amb LibreChat
- Detalls de l'estructura
- Recomanacions

### 2. `openwebui_to_librechat.py` - Conversió OpenWebUI → LibreChat

Converteix exportacions d'OpenWebUI a format compatible amb LibreChat.

**Ús:**
```bash
python3 openwebui_to_librechat.py <fitxer_openwebui.json> [fitxer_sortida.json]
```

**Exemples:**
```bash
# Conversió bàsica (el fitxer de sortida tindrà el sufix _librechat.json)
python3 openwebui_to_librechat.py openwebui_export.json

# Especificar fitxer de sortida
python3 openwebui_to_librechat.py openwebui_export.json sortida.json
```

**Característiques:**
- ✅ Converteix múltiples converses
- ✅ Preserva timestamps
- ✅ Mapeja models als endpoints correctes
- ✅ Suporta diversos formats d'exportació d'OpenWebUI
- ✅ Converteix missatges multi-part (text + imatges)

**Formats d'OpenWebUI suportats:**
- Array de converses amb estructura `chat`
- Array de converses amb `messages` directament
- Diccionari amb clau `conversations`
- Diccionari amb clau `chats`

## Com Importar a LibreChat

### Pas 1: Exportar des d'OpenWebUI
1. Obre OpenWebUI
2. Ves a la conversa que vols exportar
3. Clica als tres punts (⋮)
4. Selecciona "Export"
5. Tria format JSON

### Pas 2: Convertir el fitxer
```bash
python3 openwebui_to_librechat.py openwebui_export.json
```

Això crearà un fitxer `openwebui_export_librechat.json`.

### Pas 3: Importar a LibreChat
1. Obre LibreChat
2. Clica a "Settings" (⚙️)
3. Ves a "Data Controls"
4. Clica a "Import Conversations"
5. Selecciona el fitxer `_librechat.json` generat

## Formats Suportats per LibreChat

LibreChat accepta nativament aquests formats:

| Format | Descripció | Identificador |
|--------|------------|---------------|
| **LibreChat** | Format natiu | `conversationId` + `messages` |
| **ChatGPT** | Exportació d'OpenAI | Array amb `mapping` |
| **ChatbotUI** | Format ChatbotUI | `version` + `history` |
| **Claude** | Exportació d'Anthropic | Array amb `chat_messages` |

## Formats No Nadius (Requereixen Conversió)

| Format | Script de Conversió |
|--------|---------------------|
| **OpenWebUI** | `openwebui_to_librechat.py` |

## Resolució de Problemes

### Error: "Unsupported import type"

**Causa:** El fitxer JSON no és en un format compatible amb LibreChat.

**Solució:**
1. Executa `diagnose_import.py` per identificar el format:
   ```bash
   python3 diagnose_import.py el_teu_fitxer.json
   ```
2. Si el format no és compatible, utilitza el script de conversió adequat
3. Torna a intentar la importació amb el fitxer convertit

### Error: "Only JSON files are allowed"

**Causa:** LibreChat només accepta fitxers JSON per a importació.

**Solució:** Assegura't que el fitxer té extensió `.json` i contingut JSON vàlid.

### Les converses es veuen buides

**Causa:** L'estructura dels missatges no s'ha convertit correctament.

**Solució:**
1. Obre el fitxer convertit amb un editor de text
2. Verifica que l'estructura sigui correcta
3. Si hi ha problemes, obre un issue al repositori

## Contribucions

Si necessites un script de conversió per a un altre format:
1. Executa `diagnose_import.py` per identificar l'estructura
2. Crea un nou script basat en `openwebui_to_librechat.py`
3. Fes un pull request amb el nou script

## Suport

Si trobes problemes o necessites ajuda:
- Obre un issue al repositori
- Inclou el fitxer d'exemple (sense dades sensibles)
- Inclou la sortida de `diagnose_import.py`
