# Product Engineering Assignment — Optics Framework

**Role**: Product Engineer  
**Time budget**: 2–3 hours  
**Submission**: A link to your GitHub repository (fork or standalone)

> **Using AI tools (Copilot, Claude, ChatGPT, etc.) is completely fine.** We care about the quality of the code and thinking that comes out, not how you got there. Code quality will be evaluated closely — AI-generated code that you do not understand or cannot defend will be obvious.

---

## What Is Optics Framework?

[Optics Framework](https://github.com/mozarkai/optics-framework) is a production test automation framework for mobile and web apps. Tests are written in plain YAML/CSV (no code needed), run from a CLI or REST API, and use a layered detection strategy — XPath → OCR → image template matching — falling back automatically if one method fails.

**To set up the framework locally, refer to this [sample setup video](#).**

Here is what a typical test run looks like today from the user's perspective:

```
[INFO] Running: Login Flow
[INFO]   Module: Open App
[INFO]     Keyword: launch_app → PASS (1.2s)
[INFO]   Module: Enter Credentials
[INFO]     Keyword: tap_element("Username Field") → PASS (0.8s)
[INFO]     Keyword: enter_text("user@example.com") → PASS (0.4s)
[INFO]     Keyword: tap_element("Submit") → FAIL
[ERROR] E0302: Element not found after all strategies exhausted
```

That is all they get.

---

## The Problem

Optics runs tests well. It does almost nothing to help users *understand* the results.

When a run finishes, the output is a wall of internal log lines built for engineers. A QA lead checking overnight results, a product manager asking "did checkout pass?", or a non-technical tester trying to explain what broke — none of them can make sense of what they see today. There is no summary, no structure, no shareable artifact.

---

## Your Task

**Build a human-readable test run report for Optics Framework.**

After a test run completes, your feature should produce a clean, shareable report — **HTML or Markdown, your choice** — that communicates what happened to someone who was not watching the terminal. It should be useful, not just complete. A person should be able to open it, understand the result, and know what to do next.

---

## What the Report Should Contain

**1. Executive Summary**
Overall result (pass/fail), number of test cases, total duration. Should be readable at a glance.

**2. Per Test Case Results**
Name, status, and duration for each test case. Failed cases should be visually prominent.

**3. Step-Level Detail**
For each test case, the modules and keywords that ran, with their statuses and durations. The hierarchy (test case → module → keyword) already exists in the framework — reflect it.

**4. Failure Details**
When a step fails, show the error message. If a screenshot was captured at failure, include it inline.

**5. Run Metadata**
Start time, end time, total duration, and any available environment info (device type, driver, etc.).

---

## Where to Start in the Codebase

You do not need to understand the whole framework. These are the files that matter:

**`optics_framework/common/runner/printers.py`** — The `IResultPrinter` interface is what the test runner calls to report results. The existing `TreeResultPrinter` renders the live terminal tree. Implement this interface to collect the same data and generate your report instead. The data models you'll work with:

```python
class TestCaseResult(BaseModel):
    id: str;  name: str;  elapsed: str;  status: str;  modules: list

class ModuleResult(BaseModel):
    name: str;  elapsed: str;  status: str;  keywords: List[KeywordResult]

class KeywordResult(BaseModel):
    id: str;  name: str;  resolved_name: str
    elapsed: str;  status: str;  reason: str  # error message if failed
```

**`optics_framework/common/events.py`** — Alternatively, implement `EventSubscriber` and subscribe to all events during a run. Each `Event` has `entity_type`, `name`, `status`, `message`, `elapsed`, `start_time`, `end_time`, `args`, and `logs`. Either approach is valid — pick whichever gives you a cleaner design.

**`optics_framework/common/session_manager.py`** — The `Session` object holds `session_config.execution_output_path`, the directory where screenshots and logs are saved. Write your report here.

### How a run flows

```
CLI / API → TestRunner → (per step) → EventManager.publish_event()
                                    → IResultPrinter.print_tree_log()
                                                        ↑
                                          implement either of these
                                          to collect data, then write
                                          your report when the run ends
```

---

## Testing Without a Device

**You do not need a real phone or emulator.** Use this mock script to generate sample data and test your reporter in isolation:

```python
# run_demo.py
from optics_framework.common.runner.printers import (
    TestCaseResult, ModuleResult, KeywordResult
)

results = [
    TestCaseResult(
        id="tc-001", name="Login Flow", elapsed="4.2s", status="PASS",
        modules=[
            ModuleResult(name="Open App", elapsed="1.2s", status="PASS", keywords=[
                KeywordResult(id="k1", name="launch_app", resolved_name="launch_app(com.example.app)", elapsed="1.2s", status="PASS", reason=""),
            ]),
            ModuleResult(name="Enter Credentials", elapsed="3.0s", status="PASS", keywords=[
                KeywordResult(id="k2", name="tap_element", resolved_name='tap_element("Username Field")', elapsed="0.8s", status="PASS", reason=""),
                KeywordResult(id="k3", name="enter_text", resolved_name='enter_text("user@example.com")', elapsed="0.4s", status="PASS", reason=""),
                KeywordResult(id="k4", name="tap_element", resolved_name='tap_element("Submit")', elapsed="1.8s", status="PASS", reason=""),
            ]),
        ]
    ),
    TestCaseResult(
        id="tc-002", name="Checkout Flow", elapsed="6.7s", status="FAIL",
        modules=[
            ModuleResult(name="Add to Cart", elapsed="2.1s", status="PASS", keywords=[
                KeywordResult(id="k5", name="tap_element", resolved_name='tap_element("Product Card")', elapsed="0.9s", status="PASS", reason=""),
                KeywordResult(id="k6", name="tap_element", resolved_name='tap_element("Add to Cart")', elapsed="1.2s", status="PASS", reason=""),
            ]),
            ModuleResult(name="Confirm Payment", elapsed="4.6s", status="FAIL", keywords=[
                KeywordResult(id="k7", name="tap_element", resolved_name='tap_element("Pay Now")', elapsed="4.6s", status="FAIL", reason="E0302: Element not found after all strategies exhausted. Tried: XPath, OCR, Image Template."),
            ]),
        ]
    ),
]

# wire up your reporter here and write the output
```

---

## Deliverables

Three things, nothing more:

1. **Your reporter code** — the implementation, placed sensibly within the project structure (e.g., `optics_framework/common/runner/`).

2. **`run_demo.py` + a sample report** — a runnable script that generates a report from mock data, and the resulting `report.html` or `report.md` committed to the repo. This is the first thing we will open.

3. **A short note in `README.md`** — two questions, two or three sentences each:
   - Who is the primary reader of this report, and what do they do with it?
   - What would you do differently with another hour?

---

## Evaluation

| | |
|---|---|
| **The sample report** | Can a non-technical person understand it in 30 seconds? |
| **Code quality** | Clean, readable, fits naturally into the existing codebase patterns |
| **Integration** | Connects to real framework abstractions, not a standalone HTML script |
| **Product thinking** | Does the write-up show the candidate thought about the user, not just the task? |

A simple, well-designed report that is genuinely easy to read beats a feature-rich one that no one wants to open. We are not looking for production-grade code or a pixel-perfect UI — we are looking for clean thinking, clean code, and a genuine sense of who you are building for.
