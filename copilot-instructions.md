# Copilot Instructions for Dune Companion PC App

## Table of Contents

<!--
* [Project Purpose](#project-purpose)
* [Architecture Principles](#architecture-principles)
* [Data Handling](#data-handling)

  * [Primary Data Storage](#primary-data-storage)
  * [Data Sources](#data-sources)
  * [Display Format](#display-format)
  * [Exporting Data](#exporting-data)
* [Online/Offline Behavior](#onlineoffline-behavior)
* [Development Notes](#development-notes)
* [Primary Navigation and UI Structure](#primary-navigation-and-ui-structure)
* [Data Model Overview](#data-model-overview)
* [Naming Conventions](#naming-conventions)
* [MVP Feature Scope](#mvp-feature-scope)
* [Library and Tooling Choices](#library-and-tooling-choices)
* [DOs for Copilot](#dos-for-copilot)
* [DON'Ts for Copilot](#donts-for-copilot)
* [Status](#status)
-->



## Project Purpose

The Dune Companion PC App is an offline-first reference and planning tool for the game *Dune: Awakening*. It is intended to run on Windows PCs as a standalone desktop application.

The primary goal is to provide players with an always-available companion app that allows them to:

* Browse game reference material without relying on in-game menus.
* View and plan crafting recipes.
* View resource information and gathering locations.
* Explore lore and wiki content.
* Plan skill trees and base blueprints (graphical components).
* Optionally interact with an AI-powered strategy assistant when online.

The app must be fully usable offline, with enhanced features available when online.

## Architecture Principles

* **Offline-first** architecture.
* All primary data is stored locally.
* No features should fail or crash when offline.
* Modular service architecture with clear separation between data layer, business logic, and presentation layer.
* Local data can be manually imported and exported by the user.
* The app should support exporting data as **Markdown** and/or **JSON**.

## Data Handling

### Primary Data Storage

* Use **SQLite** as the primary database engine.
* Use **JSON** for configuration and external data import/export.
* User settings/preferences may be stored in simple config files (JSON, INI, or similar).

### Data Sources

* Local data will initially be gathered from the **official Dune: Awakening online resources** and selected **reputable community online sources**.
* Game data will be imported from external files (manually initiated by the user).
* AI chat history may be optionally cached locally.

### Display Format

* Primary display format for reference material should be **Markdown** rendered in-app.
* Skill trees, base blueprints, and other graphical elements should use appropriate custom UI components (not Markdown).

### Exporting Data

* The app must provide a built-in **Export Data** feature.
* Supported export formats:

  * JSON
  * Markdown
* Users should not require an external SQLite management tool to access their data.

## Online/Offline Behavior

* The app must detect online status.
* Core functionality must remain fully usable when offline.
* When online, the app may:

  * Access an AI API (GPT-4o) to provide dynamic strategy and reference assistance.
  * Optionally check for data updates (manual trigger only).
* Online features must degrade gracefully when offline (clear messaging, no crashes).

## Development Notes

* Target language: **Python**.
* Target platform: **Windows 10+ desktop**.
* IDE: **Visual Studio Code**.

## Primary Navigation and UI Structure

* The app will be open on a **second screen** during gameplay and used as a **reference/planning tool** when not playing.
* The primary objective is to create a **useful reference and planning app**, with strong **Dune-themed visuals**.
* The app will use a **sidebar navigation** model for major functional areas (Crafting, Resources, Skill Tree, Base Builder, Lore & Wiki, AI Assistant, Settings).
* The app will also include a standard **menu bar** for configuration and secondary operations (Export, Import, Settings, About, etc.).
* **Split-screen/multi-window support** is not planned at this stage (may revisit if use-case arises).
* The app will support a **single light mode** with strong Dune theming (backgrounds, icons, fonts, colours). No dark/light mode toggle planned.
* **Hotkey support** is undecided and may be revisited in future UX discussions.

## Data Model Overview

**Core Entities**

* Resource
* Crafting Recipe
* Skill Tree Node / Skill Build
* Base Blueprint / Base Design
* Lore / Wiki Entry
* AI Chat History (optional)
* User Settings
* User Notes (optional, freeform notes linked to entities)

**Entity Relationships**

* Resources ↔ Recipes (many-to-many)
* Recipes → Resources, Tools/Stations
* Skill Tree Nodes → Tree structure (parent/child relations)
* Base Blueprints → Hierarchical structure of components/modules
* Lore Entries → Standalone (tagged for search)
* AI Chat History → Simple timestamped log
* User Notes → Linked to any entity (by type + ID)

**Data Update & Versioning**

* Game data will be sourced via **static imports** and potentially via **API calls to online resources**.
* The app will prioritise **latest available data** rather than maintaining version history.
* It is not required to track per-entity versioning — more important to keep the database current and accurate.

**User-modifiable Data**

* Users will be able to **manually add/modify progress-related data**, such as discovered skills and recipes.
* Until an official API allows for automated sync with the game, **manual tracking of progress** will be supported.
* This implies the app schema should support:

  * User flags for "discovered/unlocked" status on applicable entities.
  * User-generated notes or annotations on entities.
  * User-created Skill Builds and Base Blueprints.

## Naming Conventions

**Database Tables (SQLite)**

* Lowercase, singular or plural depending on natural meaning.
* Underscore-separated for multi-word names.

Example:

```
resource
crafting_recipe
skill_tree_node
base_blueprint
lore_entry
ai_chat_history
user_setting
user_note
```

**Fields / Columns**

* Lowercase, underscore-separated.
* Use clear names — no unnecessary abbreviations.
* Use `id` as primary key field for all tables.
* Foreign keys should use `{related_table}_id` pattern.

Example:

```
id
name
description
rarity
created_at
updated_at
resource_id
recipe_id
parent_node_id
base_blueprint_id
user_id
entity_type
entity_id
note_text
```

**Python Variables / Classes**

* Classes: PascalCase
  Example: `Resource`, `CraftingRecipe`, `SkillTreeNode`, `BaseBlueprint`
* Variables: snake\_case
  Example: `resource`, `crafting_recipe`, `skill_tree_node`, `base_blueprint`

**Markdown / Export Files**

* File names: lowercase, hyphen-separated

Example:

```
resource-database.md
crafting-recipes.md
skill-tree-builds.md
base-blueprints.md
lore-entries.md
ai-chat-history.md
```

**Summary — Rule of Thumb for Project**

| Layer              | Convention                  |
| ------------------ | --------------------------- |
| DB tables          | lowercase, snake\_case      |
| DB fields          | lowercase, snake\_case      |
| Python Classes     | PascalCase                  |
| Python variables   | snake\_case                 |
| Markdown filenames | lowercase, hyphen-separated |

## MVP Feature Scope

**Core App Infrastructure**

* App starts and runs in window.
* Sidebar navigation.
* Menu bar with Export, Import, Settings.
* Dune-themed light UI.

**Data Layer**

* Local SQLite database.
* Import game data from JSON.
* Export data to JSON + Markdown.

**Modules**

| Module           | MVP Scope                                                        |
| ---------------- | ---------------------------------------------------------------- |
| Resources        | List view + Detail view (Markdown-rendered)                      |
| Crafting Recipes | List view + Detail view (Markdown-rendered)                      |
| Skill Tree       | View only (graphical tree), no edit/planner yet                  |
| Base Blueprint   | Placeholder screen or simple list (planning phase)               |
| Lore / Wiki      | List + Markdown detail view                                      |
| AI Assistant     | Optional in MVP, depends on readiness — initial placeholder okay |
| Settings         | Manual Import/Export, About screen, Online status indicator      |

**User-modifiable Data**

* Ability to mark Resources and Recipes as "discovered/unlocked."
* Ability to add simple User Notes linked to entities.

**Features Not Required for MVP**

* Skill Tree full planner with save/load builds.
* Base Blueprint full designer/editor.
* AI chat history storage and advanced features.
* Full user account/profile system.
* Community sharing features.
* Advanced search/filter across all modules.
* Advanced export formats (PDF, image exports).
* Multi-window / split screen.

## Library and Tooling Choices

**GUI Framework**

* **PySide6**

  * Native Windows desktop app feel.
  * Easy to theme for Dune style.
  * Flexible for sidebar/menu navigation.

**SQLite Access**

* **sqlite3** (built-in Python library)

  * Simple, built-in, reliable.
  * Use directly for MVP.

**Markdown Rendering**

* **Qt rich text support** initially.
* Optionally **markdown2 + Qt WebView** for more complex features later.

**Async / API Calls**

* **httpx**

  * Modern, fast async HTTP client.
  * Use for AI Assistant and background checks.

**Packaging & Distribution**

* **PyInstaller**

  * Simple to create Windows EXE.
  * Use the `--onedir` option (NOT `--onefile`) to produce a directory-based distribution.
  * This ensures the app can access local assets (Markdown files, icons, data files) without embedding everything in a single large EXE.
  * Easy for personal use and sharing.


## Project Folder Structure

**Root project folder: `dune_companion_pc/`**

```
dune_companion_pc/

├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py             # App entry point
│   ├── gui/                # GUI screens and components
│   ├── data/               # Data access layer
│   ├── services/           # Business logic services
│   ├── utils/              # Helper utilities

├── assets/                 # Static assets
│   ├── icons/
│   ├── fonts/
│   ├── backgrounds/
│   ├── markdown_templates/

├── scripts/                # Standalone scripts
│   ├── import_test_data.py
│   ├── export_all_data.py
│   ├── generate_test_db.py

├── data/                   # Local data store (SQLite DB, imported JSON)
│   ├── dune_companion.db
│   ├── imported_json/

├── tests/                  # Tests
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_import_service.py
│   ├── test_export_service.py
│   ├── test_services.py

├── .venv/                  # Python virtual environment (created by VSC — keep in project root)
├── README.md
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Optional project metadata
├── .gitignore
├── Copilot-Instructions.md
```

**.gitignore Guidance**

```
# Python
.venv/
__pycache__/
*.pyc

# OS
.DS_Store

# Logs
*.log

# Data
/data/dune_companion.db
/data/imported_json/

# Packaging
/dist/
/build/
```

**Notes:**

* `.venv/` should be used to ensure project dependencies are isolated and consistent.
* Local user data (`dune_companion.db` and `imported_json/`) should not be committed to Git.
* `dist/` and `build/` should be ignored — PyInstaller artifacts.

## DOs for Copilot

* DO suggest idiomatic Python 3.12+ code.
* DO use SQLite via well-supported Python libraries.
* DO structure the app with modular layers (data access, business logic, UI).
* DO support clean export/import pipelines for data.
* DO assume Markdown will be the main display format for reference screens.
* DO ensure offline-first behavior in all features.
* DO suggest appropriate GUI patterns for a desktop app.
* DO use Python `@dataclass` for data models unless more complex validation requires Pydantic.
* DO use full Python type annotations for all function signatures and return types.
* DO write unit tests using `pytest`.
* DO structure tests using the Arrange-Act-Assert pattern.
* DO mock external API calls using `pytest-mock` or equivalent.
* DO use the app’s `utils/logger.py` for all logging, not `print()` statements.
* DO make AI API calls async and cancelable to avoid blocking the UI.
* DO not place app code in `data/`. `data/` is for user content and local DB only.## DON'Ts for Copilot

## DON'Ts for Copilot

* DON'T suggest NoSQL or cloud-first databases.
* DON'T assume the app will have permanent internet connectivity.
* DON'T use web server frameworks unless explicitly requested.
* DON'T tightly couple data access to UI components.
* DON'T assume user will use external DB tools to manage app data.

## Status

This is a **working document**. It will be updated as planning progresses.

---
