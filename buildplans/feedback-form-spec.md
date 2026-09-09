# Feedback Form — v0.9.1 Spec

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

### 4. How much does this matter to you? (five-point scale, optional)

| 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| Not At All | A Little Frustrating | Annoying, But I Worked Around It | Really Hurts the Experience | Ruins My Enjoyment of the Game |

### 5. Name (short text, optional, shown only if not logged in)

If the user is authenticated, auto-associate the submission with their
account. If they're not logged in (haven't created an account yet, or
giving feedback from the login screen), show an optional name field so
they can identify themselves if they want to.

---

## Behavior

- Accessible from every screen (persistent button/link in the UI — footer,
  sidebar, or floating action button).
- On submit: store to a `feedback` table, show a brief "Thanks!" confirmation,
  clear the form. No redirect — they should be able to go right back to playing.
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
| `severity`    | INT, nullable               | 1-5 scale (null if skipped)              |
| `name`        | VARCHAR, nullable           | Only for unauthenticated users           |
| `page_url`    | VARCHAR                     | Auto-captured from the browser           |
| `created_at`  | TIMESTAMP                   | Defaults to now                          |
