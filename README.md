# EVE Frontier item extractor

A standalone, offline Go CLI for the local **Stillness** installation. Exports published item/type IDs, English names and descriptions, classification, base client metadata, and the best matching locally available original icons. No Python, game DLL loading, runtime network access, or external SQLite executable is required.

## Run (PowerShell)

```powershell
.\frontier-extract.exe -game 'C:\CCP\EVE Frontier' -out 'C:\source\eve-frontier-data-extractor\my-export'
```

The output directory **must not already exist**, its parent must exist, and it must be outside the game installation. Extraction stages output in that parent, then renames the completed directory into place. Use a new directory for each run.

Outputs:

- `static_data.db`: SQLite database with `Types`, `Groups`, and `Categories`. Types contain published records, base mass, volume, capacity, portion size, base price, optional market group, descriptions and icon references. Group and category tables contain all decoded definitions and English names. `PRAGMA user_version` is 1.
- `items.json`: sorted catalog with the same type metadata, localized group/category names, icon resource URI, image dimensions, availability, and per-item issues.
- `items.csv`: the same item fields in spreadsheet-friendly form. Formula-like text is prefixed with an apostrophe; JSON and SQLite retain exact text.
- `icons/<typeID>.<original extension>`: original image bytes, without resizing or conversion. Multiple items can share the same source icon.
- `report.json`: totals, missing localization/classification/icon counts, and the client MD5 checksums of resources read.

Base values are client type metadata, **not fitted ship statistics**. No ship-stat CSV or spatial data is produced. A published flag does not establish current availability. Nullable SQLite values represent absent optional data; CSV represents missing optional text and IDs as empty fields.

An absent icon remains an item with `icon_status: "missing"`, an empty `icon` path, and zero dimensions. Unreadable/corrupt image candidates are recorded under `issues`; another valid candidate can still be selected. Missing or invalid core metadata fails extraction without publishing output.

## Results from the inspected installation

| Result | Item count |
|---|---:|
| All client type records | 32,925 |
| Published types exported | 796 |
| Resolved English names | 796 |
| Items with an original icon | 785 |
| Items with a 512×512 icon | 265 |
| Items without a matching local icon | 11 |

**High-resolution artwork is not available for every item in these indexed files.** Of the exported icons, 504 are 64×64; the remainder are 512×512 or other native sizes. The extractor does not upscale, render 3D models, download artwork, or pretend a small icon is high resolution. “Published” is the client's flag, not a guarantee that an item is currently obtainable; some legacy/internal types carry that flag.

The included `output/` contains this extraction. Future installations can produce different totals.

## Build and test

Requires Go 1.24 or newer (uses `os.Root` for confined resource reads).

```powershell
go build -trimpath -ldflags='-s -w' -o frontier-extract.exe .
go test ./...
go vet ./...

# Optional read-only real-installation test:
$env:FRONTIER_GAME_TEST = 'C:\CCP\EVE Frontier'
go test -run TestInstalledGame -v
Remove-Item Env:FRONTIER_GAME_TEST

# Optional bounded parser fuzzing:
go test -run='^$' -fuzz=FuzzLocalization -fuzztime=10s -parallel=2
go test -run='^$' -fuzz=FuzzFSD -fuzztime=10s -parallel=2
```

The pure-Go `modernc.org/sqlite` driver is pinned in `go.mod` and `go.sum`; v1.46.1 is the newest release compatible with the project's Go 1.24 minimum (the current latest requires Go 1.26). Building downloads dependencies; extraction itself is offline. Tests use synthetic fixtures rather than checking proprietary game binaries into source.

## How it works

1. Read `index_stillness.txt` and follow its `app:/resfileindex.txt` and `app:/resfileindex_Windows.txt` entries into `ResFiles`. Never scan Utopia or mix its assets into Stillness.
2. Read the indexed `types.fsdbinary`, `groups.fsdbinary`, `categories.fsdbinary`, `iconids.fsdbinary`, `graphicids.fsdbinary`, and `localization_fsd_en-us.pickle` resources.
3. Decode known cFSD schemas directly in Go. Retain only types with a present, true `published` field; resolve type, group and category localization message IDs.
4. Find icons through explicit `iconID` mappings and `graphicID` icon folders. Recognize same-path size suffix variants, inspect actual image dimensions, and select the largest pixel area. Equal-area candidates are selected deterministically by resource URI.
5. Copy selected original images into the external output directory and write catalogs/report.

PNG and JPEG dimensions use Go's standard image header decoders. DDS files can be copied unchanged after header validation, not converted to PNG. A DDS-capable viewer is required if a future matching asset uses that format.

### Safety and limitations

- The game installation is only opened for reading. Game executables, compiled Python loaders, and Python pickle code are **never executed**. Ordinary filesystem reads can update access-time metadata; this is not a forensic acquisition tool.
- The localization parser accepts only the observed primitive protocol-4 container operations. Executable pickle operations are rejected. It discards unused localization metadata.
- Known 24-byte FSD schema fingerprints are pinned in `fsd.go`; an unknown fingerprint fails closed. A CCP schema change requires reviewing the new layout and updating code/tests.
- Resource paths must match the client's hashed-cache naming pattern. `os.Root` confines resource access to the installation. Reads are size-limited (64 MiB per resource), and parsers validate bounds/counts and impose resource limits.
- MD5 matches the client index and detects accidental corruption or stale files; it does **not** authenticate CCP content against malicious modification of both index and data.
- Output is never placed in the installation, and existing output is never intentionally overwritten. Do not move or replace installation/output-parent directories while extraction is running.
- Cached resources must already be installed. There is no downloader, game-client fallback, runtime Python dependency, or external image service.
- Game data and artwork remain subject to CCP's applicable terms. The Go code is independent of the game runtime; do not assume the extracted assets are licensed for redistribution.

See [REVIEW.md](REVIEW.md) for format observations and verification evidence.
