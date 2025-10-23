# Closed Captioning Audit

A toolkit for auditing Canvas courses to confirm that instructional videos provide accessible captioning. The project bundles a command-line workflow and a Tkinter GUI that automate pulling course content from the Canvas API, checking caption availability on supported video platforms, and writing consolidated results for accessibility reviewers.

## Repository structure

| Path | Purpose |
| --- | --- |
| `runAudit.py` | Orchestrates a full audit by collecting Canvas course content, checking YouTube captions, and scanning embedded Canvas media pages. |
| `individualAudit.py` | Audits a single Canvas course without touching other course data. |
| `pullModules.py` | Fetches courses via the Canvas API, downloads module contents, and classifies video links by platform. |
| `youtubeVideo.py` | Normalizes YouTube URLs and verifies whether each video exposes captions via the YouTube Transcript API. |
| `panoptoVideo.py` | Checks Panopto recordings using the REST API when possible and falls back to Selenium to detect caption controls. |
| `sortEmbeddedVideos.py` | Launches Selenium to inspect Canvas pages that host embedded media and records caption availability. |
| `gui.py` | Desktop interface that wraps the scripts above for non-technical users. |
| `dataReset.py` | Utility that clears cached JSON results inside the `data/` directory tree. |
| `config/` | Stores user-specific tokens (`canvasAPI.py`, `panoptoKey.py`) and the displayed app version (`version.py`). |
| `requirements.txt` | Python dependencies required by the scripts and GUI. |
| `versionNotes` | High-level changelog for historical releases. |

The scripts expect a `data/` folder with two subdirectories: `data/courseModules/` for raw module listings and `data/sortedModules/` for platform-specific URL dumps. If those folders are absent, create them before running an audit.

## Prerequisites

* **Python**: 3.10 or newer.
* **Pip packages**: install the libraries listed in `requirements.txt` (`selenium`, `webdriver-manager`, `requests`, `youtube-transcript-api`).
* **Google Chrome**: Selenium downloads a compatible ChromeDriver via `webdriver-manager`, so the locally installed browser must be reachable on the machine running the audit.
* **Canvas access**: The auditing account must be enrolled in the target courses and permitted to view their videos. The Selenium workflow requires an interactive login the first time it runs.

Optional but recommended:

* Use a Python virtual environment to isolate dependencies.
* Store Canvas and Panopto credentials securely (for example, via environment variable injection before writing them to `config/`).

## Initial setup

1. **Clone the repository** and change into it.
2. **Create a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Prepare data folders**:
   ```bash
   mkdir -p data/courseModules data/sortedModules
   ```
5. **Configure API credentials**:
   * Open `config/canvasAPI.py` and paste your Canvas access token into `CANVAS_API_TOKEN`. Follow the instructions in Canvas to generate a new token when needed.
   * If Panopto support is enabled in your environment, place the OAuth client values in `config/panoptoKey.py`. The Panopto auditor first attempts to use the REST API (client credentials grant) and will prompt for a manual browser login if Selenium fallback is required.
6. **(Optional) Update the displayed version** by editing `config/version.py`.

## Running audits

### Full course portfolio audit (CLI)
Run every stage—course discovery, YouTube caption checks, and embedded Canvas scan—in sequence:
```bash
python runAudit.py
```
This command writes fresh data into the `data/` directory. A successful pass produces:
* `data/courses.json` – raw Canvas course metadata.
* `data/courses_ids.json` – course ID list used by subsequent steps.
* `data/courseModules/modules_<course_id>.json` – module URLs per course.
* `data/sortedModules/sorted_modules_<course_id>.json` – URLs grouped by platform.
* `data/audited_videos.json` – consolidated caption audit results across all platforms.

During Selenium-based checks (Canvas media pages or Panopto fallback), a browser window opens and a dialog requests confirmation once you finish logging in.

### Graphical interface
Launch the Tkinter GUI to run the same workflows without a terminal:
```bash
python gui.py
```
Key actions in the GUI:
* **Run Complete Audit** – wraps `runAudit.py`.
* **Run Individual Course Audit** – prompts for a course ID and delegates to `individualAudit.py`.
* **View Results** – opens `data/audited_videos.json` in the default viewer.
* **Settings** – updates `config/canvasAPI.py` with a new token.
* **Reset Data** – invokes `dataReset.py` to clear cached files.

### Individual course audit
Process a single course without touching other data:
```bash
python individualAudit.py <course_id>
```
This script downloads module content just for the provided ID, audits supported video types, and appends the results (including the course ID) to `data/audited_videos.json`.

### Resetting cached data
Delete all generated JSON before a fresh run:
```bash
python dataReset.py
```
The command removes files under `data/`, `data/courseModules/`, and `data/sortedModules/`.

## Audit pipeline details

1. **Course & module ingestion (`pullModules.py`)**: Calls the Canvas API using `CANVAS_API_TOKEN`, collects module item URLs, and buckets them by platform with `sortUrls()`.
2. **YouTube caption verification (`youtubeVideo.py`)**: Normalizes short and long YouTube URLs, then queries the YouTube Transcript API to determine caption availability. Results append to `data/audited_videos.json` with `"type": "youtube"`.
3. **Panopto caption verification (`panoptoVideo.py`)**: Attempts to query the Panopto REST API for each discovered session ID; if the API denies access, Selenium opens the recording to search the player UI for caption controls. Each entry is saved with `"type": "panopto"`.
4. **Embedded Canvas media scan (`sortEmbeddedVideos.py`)**: Launches Chrome via Selenium, pauses for manual Canvas login, loads each Canvas-hosted media page, and checks for a captions control. Each URL yields a `"type": "Canvas"` entry in `data/audited_videos.json`.

If any step fails (for example, invalid JSON or API errors), the scripts emit diagnostic messages to the console. Fix the issue, delete stale files with `dataReset.py`, and rerun the audit.

## Working with the results

The primary output, `data/audited_videos.json`, is a list of dictionaries with the following shape:
```json
{
  "type": "youtube" | "Canvas" | "panopto",
  "url": "https://…",
  "has_captions": true | false,
  "course_id": "12345"        # present for individual audits
}
```
Reviewers can import this JSON into spreadsheets or dashboards to prioritize remediation work. Keep snapshots of this file for audit history before resetting the data directory.

## Maintaining video platform support

The project separates **link discovery** from **caption checks**, which makes adding or removing video platforms straightforward.

### Adding a new video type
1. **Classify the URLs**: Extend `sortUrls()` in `pullModules.py` with detection logic for the new host. Add a new key (for example, `"vimeo"`) to the returned dictionary and ensure the JSON written to `data/sortedModules/…` includes that list.
2. **Implement a checker**: Create a script similar to `youtubeVideo.py` that can determine caption availability for the new platform. Reuse the pattern of loading course IDs from `data/courses_ids.json`, iterating URLs from the sorted JSON files, and appending normalized results to `data/audited_videos.json`.
3. **Wire it into orchestration**: Import the new script in `runAudit.py` (and optionally `individualAudit.py`) and invoke it after the modules are pulled so that full audits include the platform automatically. Update `gui.py` if new buttons or status messaging are required.
4. **Document credentials**: If the platform requires API keys or OAuth clients, create a configuration file under `config/` similar to the existing Canvas and Panopto modules.

### Removing a video type
1. Remove the host-specific branch from `sortUrls()` so links fall back into `"other"` (or add new handling as needed).
2. Delete or disable the corresponding audit script and its invocation in `runAudit.py` / `individualAudit.py` / `gui.py`.
3. Update `data/audited_videos.json` consumers to expect the new set of `"type"` values.

Always run `dataReset.py` after modifying platform support to clear cached JSON created with the previous configuration.

## Troubleshooting & tips

* **Invalid or expired tokens**: API requests will fail with authorization errors. Generate a new token and re-run the audit.
* **Headless browser issues**: If Selenium has trouble starting Chrome, ensure Chrome is installed and update it to match the driver downloaded by `webdriver-manager`.
* **Pagination limits**: Large course portfolios may require multiple Canvas API pages. `pullModules.py` follows `Link` headers automatically, but rerun `runAudit.py` if network hiccups occur mid-fetch.
* **Rate limits**: Space out audits or add delays if Canvas or video APIs return throttling responses.

## Security considerations

* Treat `config/canvasAPI.py` and `config/panoptoKey.py` as secrets—never commit real tokens to version control.
* Rotate tokens regularly and invalidate them immediately if you suspect leakage.
* Store audit outputs on secured drives because course rosters and titles may be considered sensitive.

## Additional resources

* Canvas API documentation: <https://canvas.instructure.com/doc/api/>
* YouTube Transcript API documentation: <https://pypi.org/project/youtube-transcript-api/>

By following the steps above, new contributors and auditors can get productive quickly, extend platform coverage when needed, and keep accessibility data consistent across audits.
