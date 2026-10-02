# TEST_INFRA.md: End-to-End Testing Infrastructure & 4-Tier Test Matrix

## 1. Executive Summary & Test Strategy

This document establishes the End-to-End (E2E) testing infrastructure for the **Bot-Posting Desktop GUI & Multi-Platform Auto-Posting** ecosystem. Following the Project Pattern test methodology:

- **Opaque-Box & Requirement-Driven**: Tests validate system behaviors and interface contracts directly against `ORIGINAL_REQUEST.md`, `PROJECT.md`, and technical specifications, rather than coupling to internal implementation details.
- **Strict Isolation & Idempotence**: Tests run using dedicated temporary files, sandbox directories, and non-destructive dry-run modes (`--dry-run`), ensuring production data in `data/` and user browser tabs remain pristine.
- **Progressive Testability**: Features are verified at their current milestone readiness level.
- **Authoritative Derivation**: Every test specifies an explicit source of truth (spec, RFC, standard, or oracle) for expected outcomes.

---

## 2. Directory Layout & Test Suite Architecture

```
/home/yusuf/Projects/Bot-Posting/
├── TEST_INFRA.md               # This document (E2E testing infrastructure specification)
├── TEST_READY.md               # Test suite readiness certification & test execution report
├── tests/
│   ├── __init__.py             # Test package marker
│   ├── test_e2e_suite.py       # Comprehensive 4-Tier test suite (Python unittest)
│   └── run_e2e.sh              # Standalone bash test execution script
├── data/                       # Production CSV data (Untouched by tests)
└── assets/                     # Sample media assets (Tested for codec/format validity)
```

### Execution Commands
- **Via standard unittest discovery**:
  ```bash
  /home/yusuf/Projects/Bot-Posting/.venv/bin/python -m unittest discover tests -v
  ```
- **Via direct test runner script**:
  ```bash
  /home/yusuf/Projects/Bot-Posting/.venv/bin/python tests/test_e2e_suite.py
  ```
- **Via bash wrapper**:
  ```bash
  bash tests/run_e2e.sh
  ```

---

## 3. 4-Tier Test Matrix

| Tier | Tier Name | Focus | Key Coverage Areas |
|---|---|---|---|
| **Tier 1** | **Feature Coverage** | Sanity, imports, CLI commands, contracts | GUI imports, cross-platform launchers, keyword scraper CLI, template builder CLI, CDP status endpoint, video/media codecs |
| **Tier 2** | **Boundary & Corner Cases** | Limits, special chars, error resilience | Empty seed, special characters/BOM, YouTube 100-char title truncation, offline CDP port 9222, missing media files, empty/all-success queues |
| **Tier 3** | **Cross-Feature Combinations** | Multi-module integration | Scrape -> Template -> CSV output pipeline, CDP attach & tab domain routing, atomic CSV status updates |
| **Tier 4** | **Real-World Scenarios** | Operational end-to-end execution | Full dry-run execution on Carousell/YouTube/Issuu, multi-post atomic CSV status transitions, cancellation safety |

---

## 4. Detailed Test Specifications

### Tier 1: Feature Coverage (Sanity & Contracts)

#### 1.1 `test_tier1_gui_import_and_contracts`
- **Objective**: Verify that `app_gui.py` imports without syntax or dependency errors, defines the `AutoPostingGUI` class, and exposes required tab methods.
- **Input**: `import app_gui` and inspection of `app_gui.AutoPostingGUI`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R1 and `PROJECT.md` § Architecture.
- **Expected Output**: Module imports cleanly; `AutoPostingGUI` contains `_setup_scraper_tab`, `_setup_builder_tab`, `_setup_poster_tab`, `log`, `_start_posting`, and `_stop_posting`.

#### 1.2 `test_tier1_gui_instantiation`
- **Objective**: Verify that `AutoPostingGUI()` instantiates cleanly without Tkinter geometry layout errors.
- **Input**: Instantiation of `AutoPostingGUI()` in a desktop environment.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` AC: *"GUI dapat diluncurkan dengan python app_gui.py atau shortcut .bat/.sh tanpa error library"*.
- **Expected Output**: GUI window initializes without `_tkinter.TclError`. *(Known defect: Line 462 bad option `-width` in `self.stop_btn.pack(side="left", width=120)`).*

#### 1.3 `test_tier1_launcher_scripts`
- **Objective**: Validate that all four launcher scripts exist, contain executable syntax, and reference `.venv` and `app_gui.py` or port `9222`.
- **Input**: Inspection of `launchers/start_gui_linux.sh`, `launchers/start_gui_windows.bat`, `launchers/start_chrome_linux.sh`, `launchers/start_chrome_windows.bat`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` AC and `PROJECT.md` Feature #10.
- **Expected Output**:
  - `start_gui_linux.sh`: Executable permission, invokes `app_gui.py`, checks `.venv/bin/python`.
  - `start_gui_windows.bat`: Invokes `app_gui.py`, checks `.venv\Scripts\python.exe`.
  - `start_chrome_linux.sh`: Specifies `--remote-debugging-port=9222`, user-data-dir, browser binary search.
  - `start_chrome_windows.bat`: Specifies `--remote-debugging-port=9222`.

#### 1.4 `test_tier1_cli_keyword_scraper`
- **Objective**: Test CLI and core scraping logic in `scraper_keyword.py`.
- **Input**: Seed keyword `"sawit test"`, writing to a temporary CSV.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R1 (Tab 1 Alphabet Soup) and `PROJECT.md` Feature #3.
- **Expected Output**: Returns exit code 0; generates CSV with columns `["keyword", "seed", "category_type", "scraped_at"]`; rows contain categories (`root`, `alphabet_*`, `number_*`, `modifier_*`).

#### 1.5 `test_tier1_template_builder`
- **Objective**: Test `format_title` and template generation for all 3 target platforms.
- **Input**: Raw keyword `"pupuk sawit"`, title pattern `"Jual {keyword_title} Murah"`, desc pattern `"Pesan {keyword}"`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R1 (Tab 2 Template Builder).
- **Expected Output**:
  - `format_title` replaces `{keyword_title}` with `"Pupuk Sawit"` and `{keyword}` with `"pupuk sawit"`.
  - Generates Carousell CSV with 10 required columns.
  - Generates YouTube CSV with 10 required columns.
  - Generates Issuu CSV with 7 required columns.

#### 1.6 `test_tier1_cdp_status_endpoint`
- **Objective**: Test CDP configuration and availability of Remote Debugging endpoint on port 9222.
- **Input**: Probe `http://localhost:9222/json/version` and instantiate `BrowserManager()`.
- **Authoritative Source**: `PROJECT.md` Feature #8 & `ORIGINAL_REQUEST.md` R1 (Tab 4).
- **Expected Output**: HTTP 200 with JSON payload containing `"Browser"` and `"webSocketDebuggerUrl"`.

#### 1.7 `test_tier1_video_codec_and_media_assets`
- **Objective**: Validate duration, video codec, audio codec, and container format of sample assets.
- **Input**: `assets/videos/sample_sawit_15s.mp4`, `assets/images/sample_pupuk.jpg`, `assets/docs/sample_katalog.pdf`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R3: *"Menghasilkan aset video sampel berdurasi 15-30 detik (assets/videos/sample_sawit_15s.mp4) dengan audio/visual yang valid."*
- **Expected Output**:
  - `sample_sawit_15s.mp4`: `h264` video stream, `aac` audio stream, duration between 14.5s and 30.5s.
  - `sample_pupuk.jpg`: Exists, valid JPEG magic bytes (`\xff\xd8\xff`).
  - `sample_katalog.pdf`: Exists, valid PDF magic bytes (`%PDF-`).

---

### Tier 2: Boundary & Corner Cases

#### 2.1 `test_tier2_empty_seed_handling`
- **Objective**: Verify that `scraper_keyword.py` rejects empty or whitespace-only seed strings.
- **Input**: CLI execution with `--seed ""` or `--seed "   "`.
- **Authoritative Source**: `PRD.md` § Error Handling & `ORIGINAL_REQUEST.md` R1.
- **Expected Output**: Exits with non-zero exit code (code 1) and prints an error message without writing an invalid CSV.

#### 2.2 `test_tier2_special_characters_and_encoding`
- **Objective**: Verify handling of Indonesian text, ampersands, quotes, and punctuation in keywords and CSVs.
- **Input**: Keywords with characters `"sawit & pupuk super (100% organik) 'terbaik' #1"`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R1 / Excel Compatibility requirement (`utf-8-sig`).
- **Expected Output**: `write_new_csv` and `read_csv_data` preserve exact characters across read/write cycles; UTF-8 BOM is preserved.

#### 2.3 `test_tier2_youtube_title_100_char_truncation`
- **Objective**: Verify that YouTube video titles exceeding 100 characters are strictly truncated.
- **Input**: Keyword resulting in a 125-character formatted title.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R1 and `PROJECT.md` Feature #6 / YouTube Studio 100-character constraint.
- **Expected Output**: Length of output title is `<= 100` characters, ending with `...`.

#### 2.4 `test_tier2_offline_port_9222_handling`
- **Objective**: Verify that connecting to an offline or invalid CDP port does not crash the Python process via `sys.exit(1)`.
- **Input**: `BrowserManager(cdp_url="http://localhost:59999").connect()`.
- **Authoritative Source**: `PROJECT.md` § Interface Contracts: `connect() -> tuple[Browser, Page]: Connects to Chrome CDP, raises ConnectionError on failure (NO sys.exit)`.
- **Expected Output**: Raises `ConnectionError` (or raises caught exception) without killing the host process. *(Known defect: currently calls `sys.exit(1)`)*.

#### 2.5 `test_tier2_missing_media_file_detection`
- **Objective**: Verify that posters detect missing media files before upload.
- **Input**: Form processing with `image_paths="assets/images/non_existent_image_123.jpg"`.
- **Authoritative Source**: `PRD.md` § Error Handling.
- **Expected Output**: Raises `FileNotFoundError` or logs row failure without unhandled crash.

#### 2.6 `test_tier2_csv_all_success_and_empty_queue`
- **Objective**: Verify `get_pending_rows` accurately filters rows.
- **Input**:
  - List of rows all marked `status = "success"`.
  - Empty list of rows.
  - Rows with mixed statuses (`"pending"`, `""`, `"failed"`).
- **Authoritative Source**: `PROJECT.md` Feature #21.
- **Expected Output**: Returns empty list for all-success/empty; returns only non-success rows for mixed.

---

### Tier 3: Cross-Feature Combinations

#### 3.1 `test_tier3_scrape_template_csv_pipeline`
- **Objective**: Test the cross-module pipeline: Keyword Scraper -> CSV -> Template Builder -> 3 Platform CSVs.
- **Input**: Seed query `"pupuk kelapa sawit"`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` AC: *"Pengguna dapat mengoperasikan seluruh alur kerja (Scrape -> Filter -> Buat Template -> Mulai Posting)..."*
- **Expected Output**:
  - Scraper produces `keywords_temp.csv`.
  - Template builder transforms it into `carousell_temp.csv`, `youtube_temp.csv`, and `issuu_temp.csv`.
  - All 3 files are valid CSVs with `status = "pending"` for all rows.

#### 3.2 `test_tier3_cdp_attach_and_tab_detection`
- **Objective**: Verify `BrowserManager` attaches to Chrome and can route to tabs via domain hint without tab collisions.
- **Input**: Attach to active Chrome instance and call `get_or_create_page("carousell")` and `get_or_create_page("youtube")`.
- **Authoritative Source**: `PROJECT.md` Feature #12 & `BrowserManager` Interface Contract.
- **Expected Output**: Returns distinct Playwright `Page` instances matching the domain hint.

#### 3.3 `test_tier3_atomic_csv_status_updates`
- **Objective**: Verify atomic two-phase write updates without data corruption.
- **Input**: Sequential status updates to a temporary CSV.
- **Authoritative Source**: `PROJECT.md` Feature #21 & `modules/csv_handler.py`.
- **Expected Output**:
  - Row status transitions correctly to `"success"` with `post_url` and ISO `posted_at`.
  - Temporary `.tmp` file is replaced cleanly.
  - Subsequent read sees updated status with no loss of other rows or columns.

---

### Tier 4: Real-World Scenarios (Dry-Run & Full Lifecycle)

#### 4.1 `test_tier4_dry_run_pipeline_carousell`
- **Objective**: Execute Carousell auto-posting runner in `--dry-run` mode for 1 post on isolated CSV.
- **Input**: Isolated test CSV with Gardening product data and `--dry-run --max-posts 1`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R1/R3 and `poster_carousell.py`.
- **Expected Output**: Attaches via CDP, validates photo and fields, skips final publish button click, marks row `"success"` with dry-run URL.

#### 4.2 `test_tier4_dry_run_pipeline_youtube`
- **Objective**: Execute YouTube Studio auto-posting runner in `--dry-run` mode for 1 post on isolated CSV.
- **Input**: Isolated test CSV with sample video path, unlisted visibility, and `--dry-run --max-posts 1`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R1/R3 and `poster_youtube.py`.
- **Expected Output**: Attaches via CDP, navigates upload flow, selects Unlisted, skips final Done button, records status.

#### 4.3 `test_tier4_dry_run_pipeline_issuu`
- **Objective**: Execute Issuu auto-posting runner in `--dry-run` mode for 1 post on isolated CSV.
- **Input**: Isolated test CSV with sample PDF document and `--dry-run --max-posts 1`.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` R1/R3 and `poster_issuu.py`.
- **Expected Output**: Navigates to publisher dashboard (`https://issuu.com/home/publisher`), verifies upload form readiness, records status.

#### 4.4 `test_tier4_atomic_csv_lifecycle_simulation`
- **Objective**: Simulate full multi-post lifecycle across multiple rows with success and failure transitions.
- **Input**: CSV with 3 pending rows; row 0 succeeds, row 1 fails with error message, row 2 succeeds.
- **Authoritative Source**: `ORIGINAL_REQUEST.md` AC: *"Seluruh status postingan tercatat atomik di masing-masing file CSV (status, post_url, posted_at)"*.
- **Expected Output**:
  - Row 0 has `status = "success"` and `post_url`.
  - Row 1 has `status = "failed"` and `error_msg`.
  - Row 2 has `status = "success"` and `post_url`.
  - Total row count remains exactly 3; all columns preserved.

---

## 5. Authoritative Expected Output Derivation Table

| Test Case | Primary Input | Authoritative Source | Derived Expected Output |
|---|---|---|---|
| `test_tier1_gui_import` | `import app_gui` | `ORIGINAL_REQUEST.md` R1 | Clean import, `AutoPostingGUI` class defined |
| `test_tier1_gui_instantiation` | `AutoPostingGUI()` | `ORIGINAL_REQUEST.md` AC | Window instantiates without Tkinter geometry syntax error |
| `test_tier1_launchers` | Launcher script files | `PROJECT.md` Feature #10 | Shell/Batch scripts contain valid venv/entrypoint references |
| `test_tier1_scraper_cli` | `--seed "sawit test"` | Google Suggest Chrome API | CSV with columns `keyword,seed,category_type,scraped_at` |
| `test_tier1_template_builder` | Raw keyword CSV | `PROJECT.md` § Architecture | Carousell (10 cols), YouTube (10 cols), Issuu (7 cols) |
| `test_tier1_cdp_status` | `GET http://localhost:9222/json/version` | Chrome DevTools Protocol 1.3 | HTTP 200, JSON containing `Browser` & `webSocketDebuggerUrl` |
| `test_tier1_video_codec` | `assets/videos/sample_sawit_15s.mp4` | `ORIGINAL_REQUEST.md` R3 | `h264` video, `aac` audio, 15.0s duration |
| `test_tier2_empty_seed` | `--seed ""` | CLI spec & input validation | Exit code 1, error logged |
| `test_tier2_special_chars` | `&, %, ", ', UTF-8` | Excel BOM standard (`utf-8-sig`) | Exact string fidelity across save & reload |
| `test_tier2_yt_title_trunc` | Title > 100 chars | YouTube Studio limit | Title truncated to `<= 100` chars (`...` suffix) |
| `test_tier2_offline_cdp` | `http://localhost:59999` | `PROJECT.md` § Interface Contract | Raises `ConnectionError`, does NOT call `sys.exit` |
| `test_tier2_missing_media` | Invalid file path | Defensive IO contract | Raises `FileNotFoundError`, marks row `failed` |
| `test_tier3_pipeline` | Seed -> Scrape -> Build | `ORIGINAL_REQUEST.md` Workflow | 3 ready-to-post CSV files generated |
| `test_tier3_tab_routing` | `get_or_create_page` | `PROJECT.md` Feature #12 | Distinct tabs per domain without collisions |
| `test_tier3_atomic_write` | `update_row_status` | `PROJECT.md` Feature #21 | Two-phase `.tmp` atomic replace, uncorrupted CSV |
| `test_tier4_dry_run_all` | `--dry-run --max-posts 1` | `PROJECT.md` Milestones M1/M2 | Form validation and status logging without public publish |

---

## 6. Implementation Defect Tracking & Escalation Record

During test suite development and survey verification, the following implementation bugs were uncovered. In accordance with the TEST WRITER QA role, these are logged for escalation to the implementing agent:

1. **DEFECT-GUI-01 (`app_gui.py:462`)**:
   - *Observation*: `self.stop_btn.pack(side="left", width=120)` passes `width` to Tkinter `pack()`, raising `_tkinter.TclError: bad option "-width"`.
   - *Fix*: Move `width=120` to `ctk.CTkButton(...)` constructor.
   - *Escalated to*: Milestone M1 GUI Implementer.

2. **DEFECT-CDP-02 (`modules/browser_manager.py:38,43`)**:
   - *Observation*: `connect()` invokes `sys.exit(1)` upon connection failure. In a GUI thread, this terminates the host application.
   - *Fix*: Raise `ConnectionError` instead of calling `sys.exit(1)`.
   - *Escalated to*: Milestone M1 Concurrency / CDP Implementer.

3. **DEFECT-ISSUU-03 (`poster_issuu.py:34`)**:
   - *Observation*: `ISSUU_UPLOAD_URL = "https://issuu.com/home/publisher/upload"` yields HTTP 404.
   - *Fix*: Change URL to `https://issuu.com/home/publisher`.
   - *Escalated to*: Milestone M1 Automation Implementer.
