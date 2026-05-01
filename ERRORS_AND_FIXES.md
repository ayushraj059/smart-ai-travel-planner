# Voyonata — Errors Encountered & How They Were Fixed

A chronological record of every bug, misconfiguration, and environment issue hit during development, along with the root cause and fix applied.

---

## Phase 1 — Database Service (`backend/database`)

---

### Error 1 — Wrong uvicorn startup command

**Error:**
```
Error: Could not import module "app.main:uvicorn"
```

**Root Cause:** Typo in the startup command — `uvicorn` was mistakenly used as the application object name instead of `app`.

```bash
# Wrong
uvicorn app.main:uvicorn --reload

# Correct
uvicorn app.main:app --reload
```

**Fix:** Corrected the command to `uvicorn app.main:app --reload`.

---

### Error 2 — `AttributeError: 'str' object has no attribute 'get'`

**Error:**
```
AttributeError: 'str' object has no attribute 'get'
  File "backend/database/app/loader.py", line ...
```

**Root Cause:** `seoul_final.json` had a different structure from all other city files.

- All other city files: flat list `[{...}, {...}, ...]`
- Seoul: nested dict `{"attractions": [...], "restaurants": [...]}`

The loader iterated `data` directly and received a string dict key (`"attractions"`) instead of a place dict.

**Fix:** Updated `loader.py` to detect whether the JSON root is a list or a dict, then flatten accordingly:

```python
if isinstance(raw_data, dict):
    raw_items = []
    for sub_list in raw_data.values():
        if isinstance(sub_list, list):
            raw_items.extend(sub_list)
else:
    raw_items = raw_data

# Safety guard
for item in raw_items:
    if not isinstance(item, dict):
        continue
```

---

### Error 3 — Stale `.pyc` bytecode giving misleading tracebacks

**Error:** After fixing Error 2, the server hot-reloaded but Python 3.11's enhanced traceback was pointing at `raw_items = []` as the crashing line — which was logically impossible.

**Root Cause:** Python was displaying new source lines against old bytecode position offsets stored in stale `__pycache__` files. The line numbers in the traceback were wrong.

**Fix:** Cleared all `__pycache__` directories and restarted the server from scratch.

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

### Error 4 — `ModuleNotFoundError: No module named 'boto3'`

**Error:**
```
ModuleNotFoundError: No module named 'boto3'
```

**Root Cause:** `pip install -r requirements.txt` was run **before** activating the virtual environment. All packages installed into the system Python. The uvicorn server running inside the venv had zero packages installed.

**Fix:** Activated the venv first, then reinstalled:

```bash
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
```

---

### Error 5 — Data load reported success but DynamoDB was empty

**Error:** `POST /admin/load-data` returned `{"written": 275}` but querying DynamoDB returned no items.

**Root Cause:** The `travel_data` DynamoDB table did not exist yet. `create_table_if_not_exists()` was only called via the FastAPI `lifespan` (server startup). When the loader was invoked directly via `python -c "..."`, it skipped that step entirely.

`boto3`'s `batch_writer` silently failed to write to a non-existent table — it returned success counts without raising any exception.

**Fix:** Added `create_table_if_not_exists()` at the top of `load_all_cities()` so the loader is self-sufficient regardless of how it is called:

```python
def load_all_cities():
    create_table_if_not_exists()   # added
    ...
```

---

## Phase 2 — Auth Service (`backend/auth-service`)

---

### Error 6 — `Failed to fetch` on the signup form

**Error:** The signup form showed "Failed to fetch" or no response at all when submitting.

**Root Cause (multi-layered):**
1. SMTP was misconfigured / crashing on the OTP send step, causing the request to hang or 500
2. A stale uvicorn process from a previous run was still alive on port 8001, answering requests with the old broken code
3. Vite auto-incremented its dev server port from 5173 to 5174 (previous instance was still running), and the CORS `allow_origins` list only contained `http://localhost:5173` — the browser blocked the request before it reached the server

**Fix:**
- Removed the OTP feature entirely from the auth service. `POST /signup` now creates the user and returns a JWT directly — no SMTP involved.
- Changed CORS from a hardcoded origins list to a regex that accepts any localhost port:

```python
# Before (fragile)
allow_origins=["http://localhost:5173"]

# After (robust)
allow_origin_regex=r"http://localhost(:\d+)?"
allow_credentials=False   # required when using regex/wildcard — browser rejects credentials=True
```

- Applied the same CORS fix to all 4 services (`auth-service`, `database`, `rag`, `user_details`).

---

### Error 7 — `passlib`/`bcrypt` incompatibility

**Error:**
```
AttributeError: module 'bcrypt' has no attribute '__about__'
  File "passlib/handlers/bcrypt.py"
```

**Root Cause:** `passlib==1.7.4` uses `bcrypt.__about__.__version__` to detect the bcrypt version. This attribute was removed in `bcrypt` 4.x. The two packages became incompatible.

**Fix:** Replaced `passlib[bcrypt]` entirely with Python's built-in `hashlib` (sha256 + random salt). No third-party dependency needed.

```python
# security.py — before (broken)
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

```python
# security.py — after (hashlib, no external dependency)
import hashlib, os

def hash_password(plain: str) -> str:
    salt = os.urandom(16).hex()
    h = hashlib.sha256(f"{salt}{plain}".encode()).hexdigest()
    return f"{salt}${h}"

def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split("$", 1)
        return hashlib.sha256(f"{salt}{plain}".encode()).hexdigest() == h
    except Exception:
        return False
```

`requirements.txt` — removed `passlib[bcrypt]==1.7.4` and `bcrypt==3.2.2`.

---

### Error 8 — JSX syntax error in `SignupPage.tsx`

**Error (Vite HMR):**
```
[plugin:vite:react-babel] Unexpected token (112:3)
  > 112 |   )}
```

**Root Cause:** After removing the OTP verification step from `SignupPage.tsx`, the JSX fragment wrapper `<>...</>` and its closing `)}` were left as orphaned tags. The component had two `return` paths — the OTP block was removed but its surrounding conditional render structure was not.

**Fix:** Removed the orphaned fragment wrapper and the stray `)}`, leaving a single clean `return (...)` in the component.

---

### Error 9 — HTTP 500 on `POST /signup` (plain-text error body)

**Error:** Swagger and frontend both received HTTP 500. The response body was a plain string, not JSON — suggesting the crash happened outside FastAPI's exception handler.

**Root Cause (two compounding issues):**

1. **Multiple stale uvicorn processes** — running `uvicorn` in a new terminal without killing the old one left the old process alive on port 8001. The operating system routed requests to the old process (old code with OTP logic), which crashed on SMTP.

2. **Empty venv** — the user had run `python -m venv venv` which wiped the previously installed packages. Then `pip install` via `source venv/Scripts/activate` in Git Bash installed packages into the **wrong Python interpreter** (system Python, not the venv's Python). The venv Python started the server but had no packages.

**Fix:**
- Killed all uvicorn processes on port 8001 before restarting.
- Installed packages using the venv's pip binary directly (not via activation):

```bash
# Wrong (Git Bash activation unreliable on Windows)
source venv/Scripts/activate
pip install -r requirements.txt

# Correct (direct path to venv's pip)
"D:\ai trip itinerary planner\backend\auth-service\venv\Scripts\pip.exe" install -r requirements.txt
```

---

### Error 10 — `ConditionalCheckFailedException` on duplicate signup

**Error:**
```
botocore.exceptions.ClientError: ConditionalCheckFailedException
```

**Root Cause:** `create_user()` in `dynamodb.py` uses a `ConditionExpression` (`attribute_not_exists(email)`) to prevent duplicate accounts at the DynamoDB level. This is correct behaviour — it fires when the email already exists.

**Fix:** Added explicit handling in the signup route:

```python
except ClientError as e:
    code = e.response["Error"]["Code"]
    if code == "ConditionalCheckFailedException":
        raise HTTPException(status_code=409, detail="Email already registered")
    raise HTTPException(status_code=500, detail=f"DB write error: {code}")
```

---

## Phase 3 — RAG Service (`backend/rag`)

---

### Error 11 — `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`

**Error:**
```
TypeError: Client.__init__() got an unexpected keyword argument 'proxies'
  File "groq\_base_client.py", line 824, in __init__
    super().__init__(**kwargs)
  File "httpx._client.py"
```

**Root Cause:** `groq==0.9.0` internally calls `httpx.Client(proxies=...)`. The `proxies` keyword argument was **removed from httpx in version 0.28.0**. The installed `httpx==0.28.1` no longer accepts it, causing a crash on every request to Groq.

**Fix:** Updated `requirements.txt` to require a newer version of groq that is compatible with httpx 0.28+:

```
# Before
groq>=0.9.0

# After
groq>=0.13.0
```

Then installed into the venv using the direct pip path (same Windows venv issue as Error 9):

```bash
"D:\ai trip itinerary planner\backend\rag\venv\Scripts\pip.exe" install "groq>=0.13.0"
```

---

## Recurring Environment Issue — Windows venv pip installation going to wrong Python

This problem surfaced in **Errors 4, 9, and 11** and is worth documenting as a standalone pattern.

**Symptom:** `pip install` appears to succeed but the packages are missing when the service runs. The server starts but crashes with `ModuleNotFoundError`.

**Root Cause:** On Windows, `source venv/Scripts/activate` in Git Bash does not reliably activate the venv for pip. The shell's `pip` command resolves to the system Python's pip, not the venv's pip. Packages install globally, not into the venv.

**Fix — always use the absolute path to the venv's pip.exe:**

```bash
# For auth-service
"D:\ai trip itinerary planner\backend\auth-service\venv\Scripts\pip.exe" install -r requirements.txt

# For rag service
"D:\ai trip itinerary planner\backend\rag\venv\Scripts\pip.exe" install -r requirements.txt

# For database service
"D:\ai trip itinerary planner\backend\database\venv\Scripts\pip.exe" install -r requirements.txt
```

Or alternatively, verify activation worked before installing:

```bash
which pip   # should show a path inside the venv, not system Python
```

---

## Summary Table

| # | Service | Error | Root Cause | Fix |
|---|---|---|---|---|
| 1 | database | Wrong uvicorn command | Typo: `app.main:uvicorn` | Correct to `app.main:app` |
| 2 | database | `AttributeError: 'str' object has no attribute 'get'` | Seoul JSON nested dict vs flat list | Detect and flatten nested JSON structure |
| 3 | database | Misleading traceback line numbers | Stale `__pycache__` after hot-reload | Clear `__pycache__`, restart server |
| 4 | database | `ModuleNotFoundError: boto3` | pip ran before venv activation | Activate venv first; or use direct pip path |
| 5 | database | Load success but DynamoDB empty | Table didn't exist; boto3 silently ignored writes | Call `create_table_if_not_exists()` inside loader |
| 6 | auth | `Failed to fetch` on signup | CORS port mismatch + stale process + SMTP crash | Remove OTP; use `allow_origin_regex`; kill old process |
| 7 | auth | `bcrypt.__about__` AttributeError | passlib 1.7.4 + bcrypt 4.x incompatible | Replace with stdlib `hashlib` |
| 8 | frontend | JSX syntax error in SignupPage | Orphaned `<>` fragment after OTP removal | Remove orphaned fragment wrapper |
| 9 | auth | HTTP 500 plain-text on signup | Stale process on port + empty venv | Kill old process; use direct venv pip path |
| 10 | auth | `ConditionalCheckFailedException` | DynamoDB condition prevented duplicate email | Catch and return HTTP 409 |
| 11 | rag | `proxies` TypeError on Groq call | groq 0.9.0 + httpx 0.28 incompatible | Upgrade to `groq>=0.13.0` |
| — | all | Wrong Python gets packages | Git Bash `source activate` unreliable on Windows | Always use `venv\Scripts\pip.exe` directly |
