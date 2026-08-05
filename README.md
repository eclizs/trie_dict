## TRIE_DICT

### Tests

The C and Python suites are kept separate and can be run independently:

```bash
make test-c
make test-python
```

Run both suites with:

```bash
make test
```

Python integration tests use a fresh temporary SQLite database for each test and
never read from or write to the development `entries.db`.

### TODO: Auth + Multi-User Persistence

Design decisions from planning session, in implementation order.

#### Architecture shift
- [ ] Move from single global `app.state.root` to per-identity state: `app.state.roots: dict[str, ctypes.POINTER(TrieNode)]`, keyed by either an authenticated `user_id` or a guest `session_id`
- [ ] Every trie-touching endpoint (`/search`, `/insert`, `/delete`) resolves the correct root via the current identity before calling into C

#### Guest sessions
- [ ] Guests get a random UUID session ID in an httpOnly cookie on first visit, no login required
- [ ] Guest trie starts **empty** (no shared/seed dataset)
- [ ] Guest data lives **only in memory** — no DB row, no persistence
- [ ] Guest session TTL: **24 hours** since last access
- [ ] Lazy eviction (check-and-evict on request) — no background sweeper for now; revisit only if memory pressure is observed
- [ ] Explicit `/logout` endpoint frees memory immediately (`destroyTrieNode` + drop from `roots`), independent of TTL — TTL remains the fallback for abandoned/never-logged-out sessions
- [ ] Per-session lock required around trie access/eviction to prevent use-after-free when a request is in-flight during logout or TTL eviction

#### Registration / guest → user conversion
- [ ] On register: walk the guest trie via `findWords(root, "")`, bulk-insert results under the new `user_id` (avoids reassigning/moving C pointers between dict keys)
- [ ] After migration: destroy guest trie, remove guest session, issue authenticated session

#### Auth mechanism
- [ ] Password hashing via `bcrypt`/`passlib` — never roll custom hashing
- [ ] Session-based auth (signed cookie) preferred over JWT for now — fewer moving parts, no revocation/refresh-token complexity needed at this scale
- [ ] No email column currently planned → no self-service password reset path; decide fallback (admin reset, etc.)

#### Database schema (SQLAlchemy)
- [x] `User` table: `id`, `email` (unique), `password_hash`, `created_at`
- [x] `Entry` table (`dict_entries`): `id`, `user_id` (FK → `users.id`), `entry`
  - [x] `user_id` is **non-nullable** — guest entries never get a DB row
  - [x] Per-user uniqueness constraint: `UniqueConstraint("user_id", "entry")` — not global uniqueness, since different users can share a word
- [ ] Cascade delete on user removal, set at both levels (they cover different deletion paths):
  - [ ] `ForeignKey(..., ondelete="CASCADE")` — DB-level, fires even for raw SQL/non-ORM deletes
  - [ ] `relationship(..., cascade="all, delete-orphan")` — ORM-level, fires only through `session.delete()`
  - [ ] Confirm `PRAGMA foreign_keys=ON` is set per-connection in SQLite dev, since it's off by default and would otherwise hide a broken cascade until Postgres in prod
- [ ] Decide hard-delete vs soft-delete (`deleted_at`) for user removal — hard-delete is the current default but is not easily reversible

#### Storage engine: SQLite (dev) → Postgres (prod)
- [ ] Build and iterate against SQLite first
- [ ] Use SQLAlchemy generic types (`String`, `Integer`, `Boolean`, `DateTime`) instead of SQLite-specific raw SQL, so the Postgres swap is a connection string/driver change, not a rewrite
- [ ] Postgres migration justified by real problem (multi-worker write contention / SQLite file locking under concurrent access), not just "more professional" — do this at deploy time, once multiple workers are actually in play
- [x] Use async SQLAlchemy engine (`create_async_engine`) with `aiosqlite` (dev) / `asyncpg` (prod) to match FastAPI's async handlers — avoid retrofitting sync DB calls later

---

### Existing known gaps (pre-auth, still open)
- [ ] `parser.py`: multi-word return type bug (`param.split(" ")[0]` truncation) — dormant, will crash if such a type appears in a header prototype
- [ ] C-layer errors surface via `printf` to stdout, not propagated as HTTP responses
- [ ] Download filename hardcoded to `saved-words.txt` since textarea refactor
- [ ] Multi-worker state divergence: `asyncio.Lock` on `app.state` doesn't solve trie state diverging across separate OS worker processes (Postgres migration addresses the DB side of this; in-memory trie state per worker is still unresolved)
