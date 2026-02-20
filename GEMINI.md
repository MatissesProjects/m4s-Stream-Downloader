## Build & Run
- **Extension**: Run `npm run build` to compile the TS files into `extension/js/`. Load the `extension/` folder as an unpacked extension in Chrome.
- **Backend**: Navigate to `backend/`, install requirements `pip install -r requirements.txt`, and run `python main.py`.

## Shell & Commands (Windows PowerShell)
- **Command Chaining:** When running multiple commands in a single `run_shell_command` call, use the semicolon `;` as a separator instead of `&&`. 
    - *Correct:* `git status; git log`
    - *Incorrect:* `git status && git log` (Causes a ParserError in PowerShell).

## General rules

Always take the chunks we have worked on and break them into logical git commits

**ALWAYS build and run tests after making changes:**
1. **Build Extension:** `npm run build`
2. **Test Backend:** `cd backend; python -m pytest`

Always attempt to build anything that needs to be built
