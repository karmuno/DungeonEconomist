# Engine Extraction Build Plan

Extract Venturekeep's reusable systems into an `engine/` git subtree that can be shared across multiple games.

## Architecture

```
venturekeep/
├── engine/                      ← git subtree → game-engine repo
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── auth.py              (JWT, bcrypt, token versioning)
│   │   ├── database.py          (SQLAlchemy setup, SQLite/Postgres switching)
│   │   ├── rate_limit.py        (IP-based rate limiter)
│   │   ├── base_models.py       (Account model, CurrencyMixin, TurnMixin)
│   │   ├── config_loader.py     (JSON config → typed Python objects)
│   │   ├── name_generator.py    (Pool-based procedural name generation)
│   │   └── schemas.py           (Base Pydantic schemas: auth, pagination)
│   └── frontend/
│       ├── components/
│       │   ├── ModalDialog.vue
│       │   ├── ProgressBar.vue
│       │   ├── StatusBadge.vue
│       │   ├── EmptyState.vue
│       │   ├── LoadingSpinner.vue
│       │   ├── InfoTooltip.vue
│       │   └── ConfirmButton.vue
│       ├── stores/
│       │   ├── auth.ts          (JWT lifecycle, session restore)
│       │   └── notifications.ts (Turn-based toast system)
│       ├── api/
│       │   └── client.ts        (HTTP client, auth header, token refresh)
│       ├── composables/
│       │   └── useModal.ts      (Generic modal state)
│       └── styles/
│           └── theme.css        (CSS variable definitions only)
├── app/                         ← Game-specific backend (imports engine.backend)
├── frontend/src/                ← Game-specific frontend (imports from engine/)
├── Dockerfile
└── docker-compose.yml
```

## Extraction Order

Dependencies flow downward — extract in this order so each phase builds on the last.

---

## Phase 1: Foundation Layer (no game logic)

These systems have zero game-specific code. Extract as-is with minimal changes.

### Step 1.1: Create engine directory structure

```bash
mkdir -p engine/backend engine/frontend/components engine/frontend/stores \
  engine/frontend/api engine/frontend/composables engine/frontend/styles
touch engine/__init__.py engine/backend/__init__.py
```

### Step 1.2: Extract database infrastructure

**Source:** `app/database.py`
**Target:** `engine/backend/database.py`

Copy the entire file. It's already generic:
- `DATABASE_URL` env var → Postgres; fallback → SQLite
- `SessionLocal` factory, `Base` declarative base, `get_db()` dependency
- Postgres health-check ping

**Changes needed:** None. Add a docstring explaining it's the engine's DB layer.

**Update VentureKeep imports:**
```python
# app/models.py, app/main.py, all routes
# Before: from app.database import ...
# After:  from engine.backend.database import Base, get_db, engine, SessionLocal
```

### Step 1.3: Extract authentication

**Source:** `app/auth.py`, `app/rate_limit.py`
**Target:** `engine/backend/auth.py`, `engine/backend/rate_limit.py`

Copy both files as-is. They have no game imports.

`auth.py` provides:
- `hash_password()`, `verify_password()`
- `create_access_token()`, `create_refresh_token()`, `decode_token()`
- `get_current_account()` FastAPI dependency
- `SECRET_KEY`, `ALGORITHM`, token expiry constants

`rate_limit.py` provides:
- `RateLimiter` class (in-memory, IP-based, configurable window/max)
- `rate_limit()` FastAPI dependency

**Changes needed:**
- `auth.py` imports Account model — add a type parameter or use a protocol so the engine doesn't depend on a specific Account model:
  ```python
  # engine/backend/auth.py
  from typing import Protocol

  class AccountProtocol(Protocol):
      id: int
      token_version: int

  def get_current_account(
      account_model: type,  # The game passes its Account class
      ...
  )
  ```
  Alternatively (simpler): keep `get_current_account` in the game layer and only extract the token/password utilities. This avoids overengineering.

**Recommended approach:** Extract only the pure functions (hash, verify, create/decode tokens). Keep `get_current_account()` in VentureKeep's `app/auth.py` as a thin wrapper that calls engine utilities.

**Update VentureKeep imports:**
```python
# app/auth.py (now a thin game-specific wrapper)
from engine.backend.auth import hash_password, verify_password, create_access_token, ...
```

### Step 1.4: Extract base Account model

**Source:** `app/models.py` (Account class)
**Target:** `engine/backend/base_models.py`

Extract a `BaseAccount` mixin or abstract model:
```python
# engine/backend/base_models.py
from sqlalchemy import Column, Integer, String, Boolean
from engine.backend.database import Base

class BaseAccount(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    token_version = Column(Integer, default=0)
```

VentureKeep extends it:
```python
# app/models.py
from engine.backend.base_models import BaseAccount

class Account(BaseAccount):
    __tablename__ = "accounts"
    tutorial_step = Column(Integer, default=0)
    keeps = relationship("Keep", back_populates="account")
```

### Step 1.5: Extract frontend HTTP client

**Source:** `frontend/src/api/client.ts`
**Target:** `engine/frontend/api/client.ts`

Copy as-is. Rename the game-specific `X-Keep-Id` header to a generic `X-Session-Scope-Id`:
```typescript
// engine/frontend/api/client.ts
const SCOPE_HEADER = 'X-Session-Scope-Id'

export function setScopeId(id: string) { ... }
```

VentureKeep wraps it:
```typescript
// frontend/src/api/client.ts
import { client, setScopeId } from '@engine/api/client'
export { client }
export function setKeepId(id: string) { setScopeId(id) }
```

### Step 1.6: Extract frontend UI components

**Source:** `frontend/src/components/shared/`
**Target:** `engine/frontend/components/`

Copy these 7 components as-is:
- `ModalDialog.vue` — teleport modal with overlay, Escape key, title bar
- `ProgressBar.vue` — configurable progress visualization
- `StatusBadge.vue` — color-coded status display
- `EmptyState.vue` — placeholder with icon and message
- `LoadingSpinner.vue` — loading indicator
- `InfoTooltip.vue` — hover tooltip
- `ConfirmButton.vue` — button with confirmation step

**Changes needed:** Update any imports of CSS variables to use `engine/frontend/styles/theme.css`.

### Step 1.7: Extract CSS theme variables

**Source:** `frontend/src/assets/main.css` (CSS variable declarations only)
**Target:** `engine/frontend/styles/theme.css`

Extract only the `:root` CSS variable block:
```css
:root {
  --bg-primary: #000000;
  --bg-secondary: #0a0a0a;
  --bg-card: #111111;
  --text-primary: #e5e5e5;
  --text-secondary: #a3a3a3;
  --accent-green: #4ade80;
  --accent-red: #ef4444;
  --accent-blue: #60a5fa;
  --accent-gold: #fbbf24;
  --font-mono: 'Cascadia Code', 'Fira Code', monospace;
  --border-color: #333333;
  --border-radius: 6px;
}
```

Games import this as a base and override variables for their own theme. VentureKeep's `main.css` imports the engine theme then adds game-specific styles.

### Step 1.8: Extract auth store

**Source:** `frontend/src/stores/auth.ts`
**Target:** `engine/frontend/stores/auth.ts`

This store is mostly generic (login, register, logout, token refresh, session restore). The only game-specific part is `currentKeep` / `selectKeep`.

**Approach:** Extract the auth lifecycle (token management, session restore) into the engine. Leave keep selection in the game layer.

```typescript
// engine/frontend/stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const account = ref<AccountOut | null>(null)
  // login(), register(), logout(), fetchAccount(), tryRestore()
  // No keep/scope-specific logic
})
```

VentureKeep extends with keep management in its own store or composable.

### Step 1.9: Extract useModal composable

**Source:** `frontend/src/composables/useModal.ts`
**Target:** `engine/frontend/composables/useModal.ts`

Copy as-is. Fully generic.

---

## Phase 2: Game Framework Layer (generic game patterns, no RPG specifics)

These systems use game concepts (turns, currency, entities) but aren't tied to any specific game.

### Step 2.1: Extract turn-based notification system

**Source:** `frontend/src/stores/notifications.ts`
**Target:** `engine/frontend/stores/notifications.ts`

Replace "days" with "turns" throughout:

```typescript
// engine/frontend/stores/notifications.ts
interface Notification {
  id: number
  text: string
  type: 'success' | 'error' | 'info' | 'warning'
  createdTurn: number     // was: createdDay
  action?: NotificationAction
}

export const useNotificationsStore = defineStore('notifications', () => {
  const messages = ref<Notification[]>([])
  const EXPIRY_TURNS = 7  // configurable by game

  function add(text: string, type: string, currentTurn: number, action?: NotificationAction) {
    // Dedup: same text + same turn = skip
    if (messages.value.some(m => m.text === text && m.createdTurn === currentTurn)) return
    messages.value.push({ id: nextId++, text, type, createdTurn: currentTurn, action })
  }

  function onTurnAdvanced(currentTurn: number) {  // was: onDayAdvanced
    messages.value = messages.value.filter(m => currentTurn - m.createdTurn < EXPIRY_TURNS)
  }

  return { messages, add, remove, onTurnAdvanced, clear }
})
```

VentureKeep calls `onTurnAdvanced(currentDay)` from its game time store — the engine doesn't care what a "turn" represents.

### Step 2.2: Extract currency mixin

**Source:** `app/models.py` (currency helpers on Keep and Adventurer)
**Target:** `engine/backend/base_models.py` (add CurrencyMixin)

```python
# engine/backend/base_models.py
class CurrencyMixin:
    """Mixin for entities that hold multi-denomination currency.

    Subclasses must define columns for each denomination.
    Override DENOMINATION_RATES to customize (e.g., gold=100, silver=10, copper=1).
    """
    DENOMINATIONS = ['gold', 'silver', 'copper']
    DENOMINATION_RATES = {'gold': 100, 'silver': 10, 'copper': 1}

    def total_base_units(self) -> int:
        """Total value in smallest denomination."""
        return sum(
            getattr(self, denom) * rate
            for denom, rate in self.DENOMINATION_RATES.items()
        )

    def add_currency(self, base_units: int) -> None:
        """Add currency, filling from largest denomination down."""
        for denom in self.DENOMINATIONS:
            rate = self.DENOMINATION_RATES[denom]
            added = base_units // rate
            base_units %= rate
            setattr(self, denom, getattr(self, denom) + added)

    def subtract_currency(self, base_units: int) -> bool:
        """Subtract currency. Returns False if insufficient funds."""
        if self.total_base_units() < base_units:
            return False
        # Convert everything to base, subtract, redistribute
        total = self.total_base_units() - base_units
        for denom in self.DENOMINATIONS:
            rate = self.DENOMINATION_RATES[denom]
            setattr(self, denom, total // rate)
            total %= rate
        return True
```

VentureKeep's Keep and Adventurer models use the mixin:
```python
class Keep(CurrencyMixin, Base):
    treasury_gold = Column(Integer, default=0)
    # ...
```

### Step 2.3: Extract config loader pattern

**Source:** `app/class_config.py`, `app/buildings.py`, `app/monsters.py` (the loading pattern, not the game data)
**Target:** `engine/backend/config_loader.py`

```python
# engine/backend/config_loader.py
import json
from pathlib import Path
from typing import Any

class JsonConfig:
    """Load and query a JSON config file with caching."""

    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._data: dict[str, Any] | None = None

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            with open(self._path) as f:
                self._data = json.load(f)
        return self._data

    def get(self, *keys: str, default: Any = None) -> Any:
        """Nested key lookup: config.get('fighter', 'thac0', '1')"""
        obj = self.data
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key, default)
            else:
                return default
        return obj

    def reload(self) -> None:
        self._data = None
```

Games build their specific config accessors on top:
```python
# app/class_config.py
from engine.backend.config_loader import JsonConfig

classes = JsonConfig("app/data/classes.json")

def get_thac0(class_name: str, level: int) -> int:
    table = classes.get(class_name, "thac0")
    # ... game-specific THAC0 lookup logic
```

### Step 2.4: Extract name generator

**Source:** `app/names.py`
**Target:** `engine/backend/name_generator.py`

The core logic is generic: pick random items from categorized pools.

```python
# engine/backend/name_generator.py
import random
from engine.backend.config_loader import JsonConfig

class NameGenerator:
    """Generate names from categorized pools in a JSON file.

    Expected JSON format:
    {
      "category_name": {
        "first": ["Alice", "Bob"],
        "last": ["Smith", "Jones"],
        "titles": {"3": "Acolyte", "5": "Priest"}  // optional
      }
    }
    """

    def __init__(self, config_path: str):
        self.config = JsonConfig(config_path)

    def generate(self, category: str, parts: list[str] | None = None) -> str:
        """Generate a name from the given category.
        parts defaults to ["first", "last"].
        """
        parts = parts or ["first", "last"]
        pool = self.config.get(category)
        if not pool:
            return f"Unknown {category}"
        name_parts = []
        for part in parts:
            options = pool.get(part, [])
            if options:
                name_parts.append(random.choice(options))
        return " ".join(name_parts)

    def get_title(self, category: str, level: int) -> str | None:
        """Get a level-based title (e.g., cleric titles by level)."""
        titles = self.config.get(category, "titles") or {}
        # Find highest qualifying title
        best = None
        for lvl_str, title in sorted(titles.items(), key=lambda x: int(x[0])):
            if level >= int(lvl_str):
                best = title
        return best
```

### Step 2.5: Extract base Pydantic schemas

**Source:** `app/schemas.py` (auth-related schemas only)
**Target:** `engine/backend/schemas.py`

```python
# engine/backend/schemas.py
from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AccountBase(BaseModel):
    username: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
```

Game-specific schemas stay in `app/schemas.py` and import base schemas.

---

## Phase 3: Import Rewiring & Verification

After extraction, update all imports in VentureKeep to point to `engine/`.

### Step 3.1: Update Python imports

Search and replace across `app/`:
```
from app.database import → from engine.backend.database import
from app.auth import (hash_password|verify_password|create_.*_token|decode_token) → from engine.backend.auth import
from app.rate_limit import → from engine.backend.rate_limit import
```

Keep game-specific wrappers in `app/` (e.g., `app/auth.py` still has `get_current_account()`).

### Step 3.2: Update frontend imports

Configure a path alias in `vite.config.ts`:
```typescript
resolve: {
  alias: {
    '@engine': path.resolve(__dirname, '../engine/frontend'),
    '@': path.resolve(__dirname, 'src'),
  }
}
```

Update `tsconfig.json` paths:
```json
{
  "compilerOptions": {
    "paths": {
      "@engine/*": ["../engine/frontend/*"],
      "@/*": ["./src/*"]
    }
  }
}
```

Then update imports:
```typescript
// Before
import ModalDialog from '@/components/shared/ModalDialog.vue'
import { useNotificationsStore } from '@/stores/notifications'
// After
import ModalDialog from '@engine/components/ModalDialog.vue'
import { useNotificationsStore } from '@engine/stores/notifications'
```

### Step 3.3: Update Dockerfile

Add engine directory to the Docker build context:
```dockerfile
COPY engine/ ./engine/
COPY app/ ./app/
```

Ensure Python can find the engine package:
```dockerfile
ENV PYTHONPATH="${PYTHONPATH}:/app"
```

### Step 3.4: Verify

1. **Backend tests:** `pytest tests/` — all existing tests must pass
2. **Frontend build:** `cd frontend && npm run build` — no import errors
3. **Type check:** `mypy .` and `npx vue-tsc --noEmit`
4. **Lint:** `ruff check .` and `cd frontend && npx eslint .`
5. **Run locally:** `python -m app.main` + `cd frontend && npm run dev` — full functionality works
6. **Docker:** `docker compose up --build` — app starts and serves correctly

---

## Phase 4: Git Subtree Setup

Once everything works with the `engine/` directory:

### Step 4.1: Create the engine repo

```bash
gh repo create game-engine --private --description "Reusable turn-based game engine"
```

### Step 4.2: Push engine subtree

```bash
git remote add game-engine git@github.com:YOUR_USERNAME/game-engine.git
git subtree push --prefix=engine game-engine main
```

### Step 4.3: Document the workflow

Add to the engine repo's README:

```markdown
# Game Engine

Reusable backend + frontend systems for turn-based games.

## Using in a new game

git subtree add --prefix=engine git@github.com:YOUR_USERNAME/game-engine.git main --squash

## Syncing changes

# Pull engine updates into your game
git subtree pull --prefix=engine game-engine main --squash

# Push engine changes from your game back upstream
git subtree push --prefix=engine game-engine main
```

---

## What's NOT Extracted (stays game-specific)

These systems are deeply tied to Venturekeep's RPG mechanics and stay in `app/`:

| System | Why it stays |
|---|---|
| `expedition.py` (combat engine) | OSE-specific THAC0, morale, turn undead, class abilities |
| `progression.py` (leveling) | OSE XP tables, class-specific HP dice |
| `models.py` (Keep, Adventurer, Party, Expedition, Building, MagicItem) | Game-specific entities |
| `treasure.py`, `magic_items.py` | OSE loot tables |
| `monsters.py` + `data/monsters.json` | OSE monster stats |
| `buildings.py` + `data/buildings.json` | VentureKeep building tiers and bonuses |
| All game routes (`routes/*.py`) | Game-specific API endpoints |
| Tutorial content (step hints) | VentureKeep onboarding flow |
| All game-specific Vue components | Adventurer cards, expedition UI, party management |

However, these systems follow *patterns* established by the engine (JsonConfig, CurrencyMixin, NameGenerator) and could be replicated for a different game using the same architecture.

---

## Estimated Effort

| Phase | Work | Time |
|---|---|---|
| Phase 1 (Foundation) | Move files, update imports, test | 1-2 sessions |
| Phase 2 (Framework) | Generalize notifications/currency/config, test | 1 session |
| Phase 3 (Rewiring) | Update all imports, fix build, verify | 1 session |
| Phase 4 (Subtree) | Create repo, push, document | 30 min |

Total: ~4 focused sessions.
