# Voyonata — Errors Encountered & How They Were Fixed

A full chronological record of every bug, misconfiguration, and environment issue hit during development of the Voyonata AI trip planner, along with the root cause and the exact fix applied.

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
  File "backend/database/app/loader.py"
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

for item in raw_items:
    if not isinstance(item, dict):
        continue
```

---

### Error 3 — Stale `.pyc` bytecode giving misleading tracebacks

**Error:** After fixing Error 2, the server hot-reloaded but tracebacks pointed at logically impossible lines.

**Root Cause:** Python was displaying new source lines against old bytecode position offsets stored in stale `__pycache__` files.

**Fix:** Cleared all `__pycache__` directories and restarted:

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

### Error 4 — `ModuleNotFoundError: No module named 'boto3'`

**Error:**
```
ModuleNotFoundError: No module named 'boto3'
```

**Root Cause:** `pip install -r requirements.txt` was run **before** activating the virtual environment. All packages installed into the system Python, not the venv.

**Fix:** Activated the venv first, then reinstalled — or used the direct venv pip path (see Recurring Environment Issue below).

---

### Error 5 — Data load reported success but DynamoDB was empty

**Error:** `POST /admin/load-data` returned `{"written": 275}` but DynamoDB had zero items.

**Root Cause:** The `travel_data` table didn't exist yet. `create_table_if_not_exists()` was only called in the FastAPI `lifespan`. When the loader was invoked directly it skipped that step. `boto3`'s `batch_writer` silently failed to write to a non-existent table.

**Fix:** Added `create_table_if_not_exists()` at the top of `load_all_cities()`:

```python
def load_all_cities():
    create_table_if_not_exists()   # added — makes loader self-sufficient
    ...
```

---

## Phase 2 — Auth Service (`backend/auth-service`)

---

### Error 6 — `Failed to fetch` on the signup form

**Root Cause (multi-layered):**
1. SMTP crashed on the OTP send step, hanging the request
2. A stale uvicorn process from a previous run was answering requests with old broken code
3. Vite incremented its port from 5173 → 5174; CORS only allowed `5173` so the browser blocked every request

**Fix:**
- Removed OTP entirely — `POST /signup` now creates the user and returns a JWT directly
- Changed CORS from a hardcoded origins list to a regex:

```python
# Before (fragile)
allow_origins=["http://localhost:5173"]

# After (robust — accepts any localhost port)
allow_origin_regex=r"http://localhost(:\d+)?"
allow_credentials=False   # required when using regex
```

Applied the same CORS fix to all 4 services.

---

### Error 7 — `passlib`/`bcrypt` incompatibility

**Error:**
```
AttributeError: module 'bcrypt' has no attribute '__about__'
  File "passlib/handlers/bcrypt.py"
```

**Root Cause:** `passlib 1.7.4` uses `bcrypt.__about__.__version__` which was removed in `bcrypt 4.x`.

**Fix:** Replaced `passlib[bcrypt]` with Python's built-in `hashlib`:

```python
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

Removed `passlib[bcrypt]` and `bcrypt` from `requirements.txt`.

---

### Error 8 — JSX syntax error in `SignupPage.tsx`

**Error (Vite HMR):**
```
[plugin:vite:react-babel] Unexpected token (112:3)
  > 112 |   )}
```

**Root Cause:** After removing the OTP step from `SignupPage.tsx`, the JSX fragment wrapper `<>...</>` and its closing `)}` were left as orphaned tags.

**Fix:** Removed the orphaned fragment wrapper and stray `)}`, leaving a single clean `return (...)`.

---

### Error 9 — HTTP 500 on `POST /signup` (plain-text error body)

**Root Cause (two compounding issues):**
1. **Stale process** — old uvicorn still running on port 8001 with broken OTP code
2. **Empty venv** — running `python -m venv venv` wiped previously installed packages; `pip install` via Git Bash activation installed into system Python, not the venv

**Fix:**
- Killed all uvicorn processes on port 8001
- Used the direct venv pip path:

```bash
"D:\ai trip itinerary planner\backend\auth-service\venv\Scripts\pip.exe" install -r requirements.txt
```

---

### Error 10 — `ConditionalCheckFailedException` on duplicate signup

**Error:**
```
botocore.exceptions.ClientError: ConditionalCheckFailedException
```

**Root Cause:** `create_user()` uses `attribute_not_exists(email)` to guard against duplicates at the DynamoDB level — correct behaviour, but not caught in the route handler.

**Fix:** Added explicit handling to return HTTP 409:

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
  File "groq\_base_client.py"
  File "httpx._client.py"
```

**Root Cause:** `groq 0.9.0` internally calls `httpx.Client(proxies=...)`. The `proxies` keyword was removed in `httpx 0.28.0`. The two packages were incompatible.

**Fix:** Upgraded groq in `requirements.txt`:

```
# Before
groq>=0.9.0

# After
groq>=0.13.0
```

Installed using the direct venv pip path:

```bash
"D:\ai trip itinerary planner\backend\rag\venv\Scripts\pip.exe" install "groq>=0.13.0"
```

---

### Error 12 — Groq 400 Bad Request `json_validate_failed` (inline annotation in JSON)

**Error:**
```
groq.BadRequestError: Error code: 400 - json_validate_failed
failed_generation: ...
  "estimated_cost_per_person": 38000.0, "/ 3,
```

**Root Cause:** The LLM (`llama-3.3-70b-versatile`) wrote an inline arithmetic annotation alongside the number — `38000.0, "/ 3"` — instead of computing the result. Groq's JSON-mode validator correctly rejected this as malformed JSON.

**Fix (two-layer defence):**

1. **System prompt** — added explicit WRONG/CORRECT examples:
```
WRONG:  "estimated_cost_per_person": 38000.0, "/ 3"
WRONG:  "estimated_cost_per_person": "38000 / 3"
CORRECT: "estimated_cost_per_person": 12666.67
```

2. **Regex repair fallback** in `itinerary.py` — `_repair_json()` detects the pattern and evaluates the division:
```python
def _repair_json(raw: str) -> str:
    def _fix(m):
        number = float(m.group(1))
        divisor = m.group(2).strip().lstrip("/").strip()
        try:
            return f"{number / float(divisor):.2f}"
        except Exception:
            return str(number)

    return re.sub(
        r'(-?\d+(?:\.\d+)?)\s*,\s*"[^"]*?/\s*(\d+(?:\.\d+)?)[^"]*"',
        _fix,
        raw,
    )
```

`_parse_response()` now tries `json.loads` first and only falls back to `_repair_json` + retry on `JSONDecodeError`.

---

### Error 13 — Duplicate `ItineraryResponse` definition in `models.py`

**Error:**
```
pydantic.errors.PydanticUserError: A non-annotated attribute was detected: `recommended_hotels`
```

**Root Cause:** When adding `HotelRecommendation` and updating `ItineraryResponse` to include `recommended_hotels`, the old `ItineraryResponse` class definition was left in the file. Python used the second (newer) definition but Pydantic's model resolution got confused by duplicate class names in the same module.

**Fix:** Removed the original `ItineraryResponse` definition, keeping only the updated one with `recommended_hotels: list[HotelRecommendation] = []`.

---

### Error 14 — TypeScript compile errors after updating `GeneratedItinerary` type

**Errors (multiple):**
```
Property 'cost' is missing in type
Property 'duration_hours' is missing in type
Property 'dailyCost' is missing in type
Property 'hotels' is missing in type
```

**Root Cause:** After adding new required fields (`cost`, `currency`, `duration_hours` on `Activity`; `dailyCost` on `DayItinerary`; `hotels`, `totalCostPerPerson`, `currency`, `budgetStatus` on `GeneratedItinerary`), the offline generator in `itineraryGenerator.ts` still used the old shape with none of these fields.

**Fix:** Added all missing fields with safe zero/empty defaults in `itineraryGenerator.ts`:

```typescript
// Activity literals
{ ..., cost: 0, currency: '', duration_hours: 1 }

// DayItinerary literals
{ ..., dailyCost: 0 }

// Return object
{ ..., hotels: [], totalCostPerPerson: 0, currency: '', budgetStatus: '' }
```

---

### Error 15 — `destination_overview` not generated by LLM

**Symptom:** The `destination_overview` object (weather summary, must-visit places, local dishes, culture insight) was always `null` in the response — the overview card never appeared in the UI.

**Root Cause (three contributing factors):**

1. `destination_overview` was positioned in the middle of a long JSON schema (after `budget_preference`, before `days`). LLMs fill JSON schemas roughly top-to-bottom, so fields buried in the middle of a large schema tend to get skipped when the model is focused on generating the much larger `days` array.

2. The user prompt ended with the schema block and had no explicit reminder about required fields. LLMs weight the end of the prompt heavily — anything stated only in the middle is easily forgotten.

3. The system prompt called it "DESTINATION OVERVIEW — fill this once at the top level" — the phrasing was too soft and did not signal that omission was an error.

**Fix (three-part):**

1. **Moved `destination_overview` to be the very first key** in `_JSON_SCHEMA` so the LLM generates it before the long `days` array:

```python
_JSON_SCHEMA = """{
  "destination_overview": {
    "weather_summary": "...",
    "must_visit_places": [...],
    "local_dishes": [...],
    "culture_insight": "..."
  },
  "city": "string",
  ...
```

2. **Added a MANDATORY FIELD CHECK block at the end of `_build_prompt`** (after the schema, where the LLM reads last):

```python
return f"""...
Generate the full {num_days}-day itinerary strictly following this JSON schema:
{_JSON_SCHEMA}

MANDATORY FIELD CHECK — your JSON object MUST contain ALL of these top-level keys:
  ✓ destination_overview  (object with: weather_summary, must_visit_places, local_dishes, culture_insight)
  ✓ days                  (array of day objects)
  ✓ recommended_hotels    (array of hotel objects)
  ✓ summary               (object with totals and highlights)
Do NOT omit destination_overview — it is required for every response."""
```

3. **Strengthened the system prompt label** from `"DESTINATION OVERVIEW — fill this once"` to `"DESTINATION OVERVIEW (REQUIRED — must be present in EVERY response)"` with explicit language that omitting it is a critical error.

---

## Recurring Environment Issue — Windows venv pip installing to wrong Python

This pattern surfaced in **Errors 4, 9, and 11** and is the single most common environment issue on this project.

**Symptom:** `pip install` appears to succeed but the server crashes with `ModuleNotFoundError` because the venv is empty.

**Root Cause:** On Windows, `source venv/Scripts/activate` in Git Bash does not reliably point `pip` at the venv's Python. The shell resolves `pip` to the system Python, so packages install globally.

**Fix — always use the absolute path to the venv's pip.exe:**

```bash
# auth-service
"D:\ai trip itinerary planner\backend\auth-service\venv\Scripts\pip.exe" install -r requirements.txt

# rag service
"D:\ai trip itinerary planner\backend\rag\venv\Scripts\pip.exe" install -r requirements.txt

# database service
"D:\ai trip itinerary planner\backend\database\venv\Scripts\pip.exe" install -r requirements.txt
```

Verify activation worked before trusting `pip`:

```bash
which pip   # must show a path inside the venv, not system Python
```

---

## Summary Table

| # | Service | Error | Root Cause | Fix |
|---|---|---|---|---|
| 1 | database | Wrong uvicorn command | Typo: `app.main:uvicorn` | Correct to `app.main:app` |
| 2 | database | `AttributeError: 'str' has no attribute 'get'` | Seoul JSON nested dict vs flat list | Detect and flatten nested JSON |
| 3 | database | Misleading traceback line numbers | Stale `__pycache__` after hot-reload | Clear `__pycache__`, restart server |
| 4 | database | `ModuleNotFoundError: boto3` | pip ran before venv activation | Activate venv first or use direct pip path |
| 5 | database | Load success but DynamoDB empty | Table missing; boto3 silently ignored writes | Call `create_table_if_not_exists()` inside loader |
| 6 | auth | `Failed to fetch` on signup | CORS port mismatch + stale process + SMTP crash | Remove OTP; use `allow_origin_regex`; kill old process |
| 7 | auth | `bcrypt.__about__` AttributeError | passlib 1.7.4 + bcrypt 4.x incompatible | Replace with stdlib `hashlib` |
| 8 | frontend | JSX syntax error in SignupPage | Orphaned `<>` fragment after OTP removal | Remove orphaned fragment wrapper |
| 9 | auth | HTTP 500 plain-text on signup | Stale process on port + empty venv | Kill old process; use direct venv pip path |
| 10 | auth | `ConditionalCheckFailedException` | DynamoDB condition prevented duplicate email | Catch and return HTTP 409 |
| 11 | rag | `proxies` TypeError on Groq call | groq 0.9.0 + httpx 0.28 incompatible | Upgrade to `groq>=0.13.0` |
| 12 | rag | Groq 400 `json_validate_failed` | LLM wrote `38000.0, "/ 3"` inline annotation | Harden system prompt + `_repair_json()` regex fallback |
| 13 | rag | Pydantic duplicate class error | Old `ItineraryResponse` left after update | Remove duplicate model definition |
| 14 | frontend | TypeScript missing-property errors | `itineraryGenerator.ts` used stale Activity shape | Add missing fields with zero/empty defaults |
| 15 | rag | `destination_overview` always null | Field buried in schema; no end-of-prompt reminder | Move to schema top; add MANDATORY FIELD CHECK at prompt end |
| — | all | Wrong Python gets packages | Git Bash `source activate` unreliable on Windows | Always use `venv\Scripts\pip.exe` directly |
