# Changelog

## [Unreleased] - Remove Web UI

This release removes the web server and UI functionality, simplifying the application to focus solely on watching directories and downloading from TorBox.

### Removed

- **Web UI**: Completely removed Flask-based web interface
- **Web Server**: Removed `web_server.py` and all related code
- **Static Assets**: Deleted `static/` and `templates/` directories
- **Dependencies**: Removed Flask from `requirements.txt`
- **Configuration**: Removed `WEB_PORT` environment variable
- **Docker Ports**: Removed port mapping `5151:5151` from docker-compose.yml
- **API Methods**: Removed `add_item_to_track()` method from watcher (was only used by web UI)

### Changed

- **Main Application**: Simplified `main.py` to run watcher directly without threading
- Application now runs as a single blocking process instead of multi-threaded web server + watcher

### Migration Guide

If you were using the web UI to manually add downloads to tracking, this functionality is no longer available. The application now only watches directories for `.torrent`, `.magnet`, and `.nzb` files dropped by Sonarr/Radarr.

**Docker Compose Changes:**
- Remove any port mappings for port 5151
- Remove `WEB_PORT` environment variable if set

### Rationale

The web UI was not commonly used, and removing it:
- Reduces application complexity
- Reduces dependencies (no Flask)
- Reduces Docker image size
- Simplifies deployment
- Focuses application on its core purpose: automated directory watching

---

## [Unreleased] - Add Dual Directory Mode for Sonarr/Radarr with Enhanced Reliability

This release adds support for watching separate directories for Sonarr and Radarr, implements failure tracking to prevent infinite retry loops, fixes ZIP handling issues, and improves overall reliability.

### Summary

- **Dual directory mode**: Separate watch/download paths for Sonarr and Radarr to enable better organization
- **Failure tracking**: Automatic removal of downloads after repeated API failures
- **Fixed ZIP handling**: Properly respect `ALLOW_ZIP` config and eliminate double-directory extraction
- **Backward compatible**: Legacy single-directory mode still supported

### Features Added

#### 1. Dual Directory Mode for Sonarr/Radarr
Watch and download to separate directories for each application:
- **Radarr**: `/app/watch/radarr` → `/app/downloads/radarr`  
- **Sonarr**: `/app/watch/sonarr` → `/app/downloads/sonarr`

New environment variables:
- `RADARR_WATCH_DIR` / `RADARR_DOWNLOAD_DIR`
- `SONARR_WATCH_DIR` / `SONARR_DOWNLOAD_DIR`

**Backward compatibility**: Setting any Sonarr/Radarr variable enables dual mode. Otherwise, legacy `WATCH_DIR` and `DOWNLOAD_DIR` are used (single directory, no subdirectories created).

#### 2. Failure Tracking System
Prevents infinite retry loops when API calls fail:
- Tracks consecutive failures per download
- Automatically removes downloads after `MAX_STATUS_CHECK_FAILURES` (default: 5)
- Resets counter on successful API calls
- Clear error logging when downloads are removed

Fixes issue where downloads with API errors (e.g., 500 errors) would be checked indefinitely.

#### 3. Fixed `ALLOW_ZIP` Configuration
**Changed default to `false`** and fixed implementation:
- Previously hardcoded `zip_link=true` in download requests regardless of config
- Now properly respects the `ALLOW_ZIP` setting when requesting download links
- Reduces unnecessary ZIP compression/extraction overhead

#### 4. Smart ZIP Extraction
Eliminates double-directory problem:
- Detects if ZIP contains a single top-level directory
- **Single folder**: Extracts directly (e.g., `Movie.2024/Movie.2024.mkv` instead of `Movie.2024/Movie.2024/Movie.2024.mkv`)
- **Multiple items**: Creates containing folder to prevent loose files
- Detailed logging of extraction method used

### Configuration Changes

**New Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `RADARR_WATCH_DIR` | `/app/watch/radarr` | Radarr watch directory (enables dual mode) |
| `RADARR_DOWNLOAD_DIR` | `/app/downloads/radarr` | Radarr download directory (enables dual mode) |
| `SONARR_WATCH_DIR` | `/app/watch/sonarr` | Sonarr watch directory (enables dual mode) |
| `SONARR_DOWNLOAD_DIR` | `/app/downloads/sonarr` | Sonarr download directory (enables dual mode) |
| `MAX_STATUS_CHECK_FAILURES` | `5` | Max consecutive failures before removing from tracking |

**Changed Defaults:**
- `ALLOW_ZIP`: `true` → `false` (reduces unnecessary compression)

### Files Changed

- `config.py`: Dual directory mode logic, new config options
- `watcher.py`: Dual directory scanning, failure tracking, pass `ALLOW_ZIP` to API
- `download_tracker.py`: Failure count tracking methods
- `file_processor.py`: Smart ZIP extraction, removed global download_dir
- `api_client.py`: Add `zip_link` parameter to download link methods
- `docker-compose.yml`: Updated volume mounts and environment variables
- `README.md`: Comprehensive documentation updates

**Stats:** 7 files changed, 254 insertions(+), 62 deletions(-)

### Migration Guide

#### Existing users (single directory mode)
No changes needed. The app will continue to work with existing `WATCH_DIR` and `DOWNLOAD_DIR` variables.

#### New dual directory setup
```yaml
volumes:
  - /mnt/user/downloads/temp:/app/watch
  - /mnt/user/downloads:/app/downloads
environment:
  - RADARR_WATCH_DIR=/app/watch/radarr
  - RADARR_DOWNLOAD_DIR=/app/downloads/radarr
  - SONARR_WATCH_DIR=/app/watch/sonarr
  - SONARR_DOWNLOAD_DIR=/app/downloads/sonarr
```

### Breaking Changes

- **`ALLOW_ZIP` default changed from `true` to `false`**: If you rely on ZIP compression, explicitly set `ALLOW_ZIP=true` in your environment variables.

### Bug Fixes

- Fixed `ALLOW_ZIP` config being ignored when requesting download links from TorBox API
- Fixed double-directory issue when extracting ZIPs with single top-level folder
- Fixed infinite retry loops on API errors by implementing failure tracking

### Testing Recommendations

- Verify dual directory mode creates and watches both directories
- Confirm legacy mode still works with `WATCH_DIR`/`DOWNLOAD_DIR`
- Test that `ALLOW_ZIP=false` downloads non-zipped files
- Verify downloads are removed after 5 consecutive API failures
- Check ZIP extraction creates single directory structure

### Related Commits

- `eb50481`: Actually respect the ALLOW_ZIP env
- `74b752f`: Force a build watch on docker compose  
- `f7845e4`: Force ZIPs to extract to a single top level directory if possible
- `a53f820`: Add MAX_STATUS_CHECK_FAILURES to prevent infinite tracking
- `7d72dc0`: Add dual directory mode for sonarr/radarr
