---
name: Preview routing for Python-backed web apps
description: How to keep a Python web implementation usable alongside a registered root web artifact.
---

For a durable browser preview, register a root web artifact and route its frontend through the shared API service; keep the Python implementation as a standalone runnable server when the user explicitly asks for Python.

**Why:** A standalone workflow on port 8000 did not own the root preview because the workspace already had registered services. The root artifact reliably owns the browser surface, while the API service handles relative `/api/*` requests.

**How to apply:** Preserve the Python app as a runnable source-of-truth example, and make the registered web artifact plus `/api/chat` route the working preview path.