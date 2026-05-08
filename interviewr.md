# Interviewer Notes — Private

## The 3 Planted Bugs

### Bug 1 — Inverted filter logic (app.py, `filter_todos`)
- **Location:** `filter_todos()` function
- **Problem:** Uses `!=` instead of `==`, so `?completed=true` returns incomplete todos
- **Fix:** Change `todo["completed"] != completed` → `todo["completed"] == completed`
- **Failing test:** `test_filter_completed_todos`
- **What to watch:** Do they run tests first? Do they trace the logic or just guess?

### Bug 2 — Missing "low" in priority validation (app.py, `VALID_PRIORITIES`)
- **Location:** `VALID_PRIORITIES = ["medium", "high"]`
- **Problem:** "low" is missing, so any todo with priority "low" is rejected with 400
- **Fix:** Add `"low"` to the list
- **Failing test:** `test_create_todo_low_priority`
- **What to watch:** Do they notice the mismatch between the list and the docstring/stats endpoint?

### Bug 3 — Wrong HTTP status code on DELETE (app.py, `delete_todo`)
- **Location:** `delete_todo()` return statement
- **Problem:** Returns `201 Created` instead of `200 OK`
- **Fix:** Change `201` → `200`
- **Failing test:** `test_delete_todo`
- **What to watch:** Do they know HTTP semantics, or do they just change the number to pass the test?

## The Feature Task
Add `PATCH /todos/<id>/complete` — marks a todo as completed without needing a full PUT body.
Good solution looks like:
```python
@app.route("/todos/<todo_id>/complete", methods=["PATCH"])
def complete_todo(todo_id):
    todo = todos.get(todo_id)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404
    todo["completed"] = True
    return jsonify(todo), 200
```

## Adapting to Change (spring mid-interview)
Pick one of these to throw at them after they've started the feature:
- "Actually, the PATCH endpoint should also accept `?undo=true` to un-complete a todo."
- "The stats endpoint needs to also return the most recently created todo's title."
- "Change the PATCH route to `/todos/<id>/toggle` — it should flip the completed state."

## Interview Flow (15–20 min)
| Time | Activity |
|------|----------|
| 0–3 min | Fork repo, clone, run server, run tests — observe how they navigate GitHub |
| 3–10 min | Debug the 3 failing tests — watch their process |
| 10–16 min | Implement the PATCH feature |
| 16–20 min | Throw in the change request — watch how they adapt and communicate |

## Green Flags
- Runs tests before touching code
- Reads the test names to understand what's broken
- Explains their reasoning out loud
- Asks clarifying questions on the change request
- Clean, meaningful commit messages

## Red Flags
- Edits code without running tests first
- Fixes test assertions instead of the actual bug
- Silent when stuck — doesn't ask for help or think aloud
- No commits until everything is done
