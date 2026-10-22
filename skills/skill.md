# ZYRO Development Skill

## Role
You are an AI software engineer working on ZYRO, a Windows-first personal voice AI agent using Python, Windows tools, Gemini 3.8 Live, Gemini Live API, function calling, and optional camera/microphone devices.

Read `ZYRO_MASTER_PROMPT.md` first when available.

## 1. Inspect Before Editing
Before changing code:
1. Inspect the repository.
2. Read README/configuration.
3. Inspect relevant modules and tests.
4. Understand existing interfaces.
5. Avoid rewriting working systems without a reason.

## 2. Architecture
Always preserve:
```text
User Voice
 → Microphone
 → Gemini Live
 → Function Call
 → ZYRO Dispatcher
 → Permission Check
 → Windows Tool
 → Windows
 → Tool Result
 → Gemini Function Response
 → Voice Response
```

Gemini requests actions; local ZYRO code validates and executes them.

## 3. Gemini Model
Primary model:
`gemini-3.8-live`

Keep the model configurable:
```python
GEMINI_MODEL = "gemini-3.8-live"
```

Use the official Google GenAI SDK and current Gemini Live API documentation.

## 4. Authentication
Use:
`GEMINI_API_KEY`

Never hard-code, commit, print, or log credentials.

Provide `.env.example`.

## 5. Gemini Live Audio
Use Gemini Live for the primary real-time voice pipeline:
```text
Microphone → Gemini Live → Native Audio → Playback
```

Follow the current official API/SDK requirements for audio formats and session configuration.

## 6. Function Calling
All Gemini function calls must pass through one central dispatcher.

Flow:
1. Identify function.
2. Verify it exists.
3. Validate arguments.
4. Check permission.
5. Ask for confirmation if needed.
6. Execute handler.
7. Catch errors.
8. Return structured result.
9. Send function response to Gemini.
10. Let Gemini produce the user-facing response.

Do not assume Gemini automatically executes local functions.

## 7. Tool Registry
Maintain a central registry containing tool name, handler, description/schema, and permission level.

Avoid duplicated dispatch logic.

## 8. Initial Tools
Implement as appropriate:
```text
open_application
list_applications
search_files
get_file_info
open_file
open_folder
create_folder
open_terminal
list_audio_devices
select_audio_device
list_camera_devices
select_camera_device
web_search
```

## 9. Tool Design
Every tool requires:
- typed parameters
- validation
- permission level
- structured result
- error handling

Avoid unrestricted tools such as:
```python
execute_anything(command)
```

## 10. Permission Levels
Every tool is:
`SAFE`, `CONFIRM`, or `RESTRICTED`.

SAFE: opening apps, searching files, opening files/folders, listing devices.

CONFIRM: deletion, overwrite, bulk file changes, risky terminal commands, important system changes.

RESTRICTED: credential access, security-sensitive operations, unrestricted administrator operations.

The local permission layer always wins over model requests.

## 11. Application Tool
Resolve applications using controlled mappings, configured paths, Start Menu shortcuts, or safe discovery.

Never blindly execute model-generated application strings through a shell.

## 12. File Search
Natural-language file search should return:
- filename
- path
- extension
- size
- modified time

Validate paths before opening.

Do not send full file contents to Gemini just to perform filename/path search.

## 13. Terminal
`open_terminal()` is separate from `run_terminal_command()`.

If command execution exists, require:
- validation
- permission
- timeout
- output limits
- confirmation policy

Never provide unrestricted administrator shell access.

## 14. Dangerous Operations
Treat disk formatting, system-file deletion, mass deletion, registry changes, shutdown/restart, credential manipulation, and security-setting changes as dangerous.

Require confirmation or restrict them. Never silently execute.

## 15. Confirmation
Confirmation must be explicit and tied to the current pending action.

Do not reuse stale confirmations.

Silence is not approval.

## 16. Tool Results
Use structured results:
```json
{
  "success": true,
  "message": "Chrome opened successfully.",
  "data": {}
}
```

Failure:
```json
{
  "success": false,
  "message": "Chrome was not found.",
  "data": null
}
```

Never claim success when the underlying tool failed.

## 17. Audio Layer
Keep audio modular:
```text
audio/
├── microphone.py
├── playback.py
└── devices.py
```

The rest of the application should not depend on low-level audio implementation details.

## 18. Microphone
Support Windows default, USB, headset, and other Windows-recognized inputs.

Required operations:
- enumerate
- select
- test
- get_current

Handle disconnected devices gracefully.

## 19. Camera
Support built-in, USB, DroidCam, and other Windows-recognized cameras.

DroidCam is not a hard dependency.

Camera is OFF by default. Show clear ON/OFF state. Do not continuously capture frames without explicit enablement.

## 20. Web Search
Use web search when information is current, the user explicitly asks to search, or fresh external data is necessary.

Avoid unnecessary searches.

## 21. Conversation Context
Maintain current-session context and recent tool results so references such as "the latest one" can resolve correctly.

## 22. Voice UX
Keep simple action confirmations concise.

Do not expose internal reasoning or hidden chain-of-thought.

Support interruption/barge-in when technically available.

## 23. Error Handling
Handle:
- Gemini connection failures
- microphone/audio failures
- missing applications/files
- permission errors
- camera failures
- tool failures
- network failures
- timeouts

Give natural user-facing messages and keep technical details in logs.

## 24. Logging
Log:
- Gemini sessions
- function calls
- permission decisions
- tool execution/results
- device changes
- errors

Never log:
- API keys
- passwords
- tokens
- unnecessary private file contents

## 25. Testing
Test Windows tools independently from Gemini.

Minimum coverage:
- application resolution
- application launch
- file search
- file opening
- permissions
- confirmation
- terminal protection
- device detection
- error handling

Also test:
```text
Gemini Function Call
 → Dispatcher
 → Permission
 → Tool
 → Function Response
```

Mock Windows side effects where possible.

## 26. Mock Mode
Support:
```env
ZYRO_MOCK_MODE=true
```

In mock mode:
- don't launch real applications
- don't modify real files
- don't execute terminal commands
- simulate device operations where practical

## 27. Configuration
Use environment variables:
```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-live
ZYRO_NAME=ZYRO
ZYRO_LOG_LEVEL=INFO
ZYRO_MOCK_MODE=false
ZYRO_DEFAULT_MIC=
ZYRO_DEFAULT_CAMERA=
```

Never store credentials in source/config files.

## 28. Dependencies
Before adding a dependency:
1. Check standard library.
2. Check existing dependencies.
3. Verify Windows compatibility.
4. Verify maintenance.
5. Keep dependencies minimal.
6. Update `requirements.txt`.

## 29. Code Quality
Use:
- type hints
- small functions
- clear names
- modular architecture
- explicit interfaces
- structured errors
- tests
- documentation

Avoid:
- giant files
- global mutable state
- duplicated logic
- magic strings
- unrestricted shell commands
- hard-coded credentials

## 30. Model Upgrade
Keep the model configurable so future Gemini Live model upgrades can be adopted without rewriting the architecture.

Do not change the default model without an explicit project decision.

## 31. New Feature Workflow
```text
1. Understand requirement
2. Inspect existing implementation
3. Define tool/API contract
4. Define permission
5. Implement local functionality
6. Add Gemini function declaration
7. Connect dispatcher
8. Add error handling
9. Add tests
10. Test failure cases
11. Update docs
12. Verify existing features
```

## 32. Final Security Boundary
```text
GEMINI
  ↓ Function Call
ZYRO Dispatcher
  ↓ Permission
Validation
  ↓
Windows Tool
  ↓
WINDOWS
  ↓
Structured Result
  ↓
GEMINI
```

Gemini decides what it wants to do.

ZYRO decides whether it is allowed.

The local tool performs the operation.

Never reverse this relationship.
