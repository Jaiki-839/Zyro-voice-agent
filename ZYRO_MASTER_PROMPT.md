# ZYRO — Windows Voice AI Agent

## 1. Project Identity
You are building ZYRO, a Windows-first personal voice AI agent.

ZYRO should provide:
- natural voice conversation
- general AI answers
- Windows application launching
- file searching/opening
- folder operations
- terminal/CLI launching
- optional web search
- optional microphone and camera support
- optional DroidCam support as a normal Windows camera device

Target: Windows 10/11.

## 2. AI Model
Primary model:
`gemini-3.8-live`

Use the official Google GenAI SDK and Gemini Live API.

Gemini handles real-time voice interaction and function calling. ZYRO's local application executes Windows operations.

## 3. Authentication
Use:
`GEMINI_API_KEY`

Example:
```env
GEMINI_API_KEY=your_api_key_here
```

Never hard-code or commit API keys. Provide `.env.example`.

## 4. Architecture
```text
User → Microphone → Gemini Live → AI/Function Call
                                      ↓
                              ZYRO Tool Dispatcher
                                      ↓
                              Permission Check
                                      ↓
                                Windows Tool
                                      ↓
                                  Windows OS
                                      ↓
                              Tool Result → Gemini
                                      ↓
                               Native Audio → User
```

Critical rule: Gemini requests actions; ZYRO validates and executes them.

## 5. Gemini Live
Use Gemini Live as the primary voice pipeline:
```text
Microphone → Gemini Live → Native Audio → Speaker
```

Use audio response modality and current documented Live API audio formats. Follow current official SDK/API documentation rather than outdated examples.

## 6. Function Calling
Expose Windows capabilities through function declarations.

Example:
```text
User: "Open Chrome."
Gemini: open_application(name="Chrome")
ZYRO: validate → execute → return result
Gemini: spoken confirmation
```

Gemini must never directly execute operating-system commands.

## 7. Initial Tools
- `open_application`
- `list_applications`
- `search_files`
- `get_file_info`
- `open_file`
- `open_folder`
- `create_folder`
- `open_terminal`
- `list_audio_devices`
- `select_audio_device`
- `list_camera_devices`
- `select_camera_device`
- `web_search`

## 8. Tool Contract
Every tool must have:
- name
- description
- typed parameters
- validation
- permission level
- implementation
- structured result
- error handling

Example:
```json
{
  "success": true,
  "message": "Chrome opened successfully.",
  "data": {"application": "Chrome"}
}
```

## 9. Application Control
Support natural commands such as:
- "Open Chrome"
- "Launch Discord"
- "Open VS Code"
- "Open Settings"
- "Open Jaiki CLI"

Use a controlled application resolver. Do not blindly execute model-generated strings through a shell.

## 10. File Search
Support natural-language searches such as:
- "Find my physics notes."
- "Search for the PDF about motion."
- "Find my Python project."
- "Where is my resume?"
- "Find the latest chemistry PDF."

Return filename, full path, extension, size, and modified time. Ask for clarification when multiple results are equally plausible.

## 11. File Operations
Initial operations:
- search
- open
- create folder
- get information
- reveal in Explorer

Destructive operations such as delete, overwrite, bulk move, and bulk rename require confirmation.

## 12. Terminal
Opening a terminal is separate from executing a command.

`open_terminal()` is safe.

If `run_terminal_command()` is added, it must have validation, permission checks, timeout, output limits, and confirmation policy. Never provide unrestricted administrator shell access.

## 13. Device Support
Microphones:
- Windows default
- USB mic
- headset
- other Windows audio inputs

Cameras:
- built-in webcam
- USB webcam
- DroidCam
- other Windows-recognized cameras

DroidCam must not be a hard dependency; treat it as a normal Windows camera device when available.

## 14. Camera Privacy
Camera is OFF by default. Clearly show camera state in the UI. Do not continuously capture frames unless explicitly enabled.

## 15. Web Search
Use web search for current information or explicit search requests. Avoid unnecessary browsing for stable general questions.

## 16. Conversation
Maintain useful short-term context so references like "that file", "the second one", and "the latest one" can resolve against recent tool results.

## 17. Voice UX
Keep simple action responses short:
"Opening Chrome."

Support interruption/barge-in when technically available.

Never expose hidden chain-of-thought.

## 18. Confirmation
Permission levels:
- SAFE
- CONFIRM
- RESTRICTED

SAFE examples: open app, search files, open file/folder, list devices, web search.

CONFIRM examples: delete, overwrite, bulk operations, risky terminal commands, important system settings.

RESTRICTED examples: credential access, security-sensitive operations, unrestricted administrator operations.

Gemini cannot override local permissions.

## 19. Security Boundary
```text
Gemini → Function Call → ZYRO Dispatcher → Permission → Validation → Windows Tool → Windows
```

Gemini is not a Windows administrator. Never give the model unrestricted shell or filesystem access.

## 20. Recommended Structure
```text
zyro/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── core/
│   ├── agent.py
│   ├── router.py
│   ├── session.py
│   ├── permissions.py
│   └── tool_registry.py
├── gemini/
│   ├── live_client.py
│   ├── session_config.py
│   ├── function_calls.py
│   └── audio.py
├── audio/
│   ├── microphone.py
│   └── playback.py
├── tools/
│   ├── applications.py
│   ├── files.py
│   ├── windows.py
│   ├── terminal.py
│   ├── web.py
│   └── devices.py
├── devices/
│   ├── microphones.py
│   └── cameras.py
├── ui/
│   ├── main_window.py
│   ├── settings.py
│   └── devices.py
├── memory/
│   └── memory.py
├── skills/
│   └── skill.md
├── tests/
└── README.md
```

## 21. Configuration
```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-live
ZYRO_NAME=ZYRO
ZYRO_LOG_LEVEL=INFO
ZYRO_MOCK_MODE=false
ZYRO_DEFAULT_MIC=
ZYRO_DEFAULT_CAMERA=
```

## 22. Logging
Log session events, function calls, permission decisions, tool execution/results, device changes, and errors.

Never log API keys, passwords, tokens, or unnecessary private file contents.

## 23. Error Handling
Handle Gemini connection failures, microphone/audio failures, missing applications/files, permission errors, camera failures, tool failures, network failures, and timeouts gracefully.

Never expose raw stack traces during normal use.

## 24. Roadmap
### V0.1
- Gemini 3.8 Live
- voice input/output
- function calling
- open applications
- file search
- open files
- open terminal

### V0.2
- improved file search
- Explorer integration
- terminal tool
- web search
- confirmation system

### V0.3
- microphone manager
- camera manager
- DroidCam support
- settings UI

### V0.4
- wake word
- persistent memory
- background mode
- Windows startup

### Future
- vision
- automation
- plugins
- Discord integration
- Android companion
- multi-device support

## 25. Coding-Agent Rules
Before modifying ZYRO:
1. Read this file.
2. Read `skills/skill.md`.
3. Inspect existing architecture and tests.
4. Reuse existing tools.
5. Keep security boundaries intact.
6. Add tests.
7. Update documentation.
8. Keep the project runnable.

## 26. Definition of Done
A feature is complete only when it works on Windows, integrates with ZYRO, validates arguments, enforces permissions, handles errors, has relevant tests, updates documentation, and does not break existing functionality.

ZYRO is a real-time voice AI + controlled Windows tool system + permission layer + extensible desktop application.
