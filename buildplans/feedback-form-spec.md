# Feedback Form — v0.9.1 Spec

**Status: implemented 2026-09-12** from the design handoff in `design_handoff_feedback_form/`
(the README there is the visual spec of record: colors, sizes, states, copy). Backend:
`app/routes/feedback.py`, migration `e6f2a3b4c5d7`, tests in `tests/test_main_utils.py`.
Frontend: `components/feedback/FeedbackModal.vue` (mounted once in `App.vue`) and
`FeedbackEntry.vue` (sidebar footer, and under the form on the auth pages, which have no
sidebar).

In-game feedback form for the playtest cohort. Goal: identify player
problems by asking the right questions and getting informative responses.
Must be easy to fill out, satisfying to submit multiple times.

---

## Fields

### 1. What kind of feedback is this? (dropdown, required)

- Something is broken
- I'm confused or stuck
- Something feels wrong
- I have an idea
- I like something

### 2. What were you doing? (short text, one line, required)

Placeholder text:
`e.g. "Sending my party into the dungeon" / "Trying to figure out upkeep" / "Just logged in."`

### 3. What's your feedback? (textarea, required)

No additional prompt — the dropdown already frames their thinking.

### 4. How important is this feedback? (four-point scale, optional)

Cody replaced the five-point severity scale with this one (2026-09-12). Clicking the
selected number again clears it.

| # | Title | Description |
|---|-------|-------------|
| 1 | Barely | I don't care if this issue is ever addressed. |
| 2 | Somewhat | It would be nice to see this issue get addressed. |
| 3 | Very | I would have a lot more fun if this issue were addressed. |
| 4 | Critically | I won't or can't play the game until the issue is addressed. |

### 5. Name (short text, optional, shown only if not logged in)

If the user is authenticated, auto-associate the submission with their
account. If they're not logged in (haven't created an account yet, or
giving feedback from the login screen), show an optional name field so
they can identify themselves if they want to.

---

## Behavior

- Accessible from every screen (persistent button/link in the UI — footer,
  sidebar, or floating action button).
- On submit: store to a `feedback` table, show a "Thanks!" confirmation with a receipt
  line (`feedback #id · category · severity n`), clear the form, and offer **Submit
  Another** or **Back to the Keep**. No redirect — they go right back to playing. The
  sidebar status line counts reports sent this session.
- Submit is disabled until the category is chosen and both required text fields are
  non-blank; there are no inline validation messages. A failed POST shows one red line
  above the actions and keeps the form filled.
- Anyone can post, so the endpoint shares the auth endpoints' per-IP throttle (20/min).
  A stale token is treated as anonymous rather than refused: feedback from a broken
  session is still feedback.
- Auto-capture the current page URL at submission time (don't ask the user
  to type it).
- If logged in, auto-attach user_id and keep_id (if they're in a keep).

## Schema

### `feedback` table

| Column        | Type                        | Notes                                    |
|---------------|-----------------------------|------------------------------------------|
| `id`          | INT PK                      | Auto-increment                           |
| `user_id`     | INT FK → accounts.id, nullable | Null if not logged in                 |
| `keep_id`     | INT FK → keeps.id, nullable | Null if not in a keep or not logged in   |
| `category`    | VARCHAR                     | One of the five dropdown values          |
| `doing`       | VARCHAR                     | "What were you doing?"                   |
| `feedback`    | TEXT                        | "What's your feedback?"                  |
| `severity`    | INT, nullable               | 1-4 scale (null if skipped)              |
| `name`        | VARCHAR, nullable           | Only for unauthenticated users           |
| `page_url`    | VARCHAR                     | Auto-captured from the browser           |
| `created_at`  | TIMESTAMP                   | Defaults to now                          |
