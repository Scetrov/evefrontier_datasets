# Read-only extraction review

## Scope

Inspected `C:\CCP\EVE Frontier\index_stillness.txt`, the Stillness resource indexes it references, the required indexed static/localization resources, relevant image assets, and bounded static byte/string views of `typesLoader.pyd`, `iconIDsLoader.pyd`, and `graphicIDsLoader.pyd`. The native loaders were **not loaded or executed**. This is a format investigation, not an exhaustive security assessment of the client.

The working directory was initially empty and not a Git repository. No repository instructions, existing implementation, or pre-commit configuration were present. Implementation and exports are local; nothing was committed or pushed.

## Existing tooling considered

- [VULTUR-EveFrontier/eve-frontier-tools](https://github.com/VULTUR-EveFrontier/eve-frontier-tools): Python/Node extraction pipeline, including type/name mappings.
- [anteris90/EF_Extractor](https://github.com/anteris90/EF_Extractor): Python extraction using compiled game loaders, followed by SQLite conversion.
- [EVE Frontier Icon Extractor gist](https://gist.github.com/murphyslaw/6ffdb9558206bc01a38aec9a8f33c332): icon export based on separately extracted data.

Their documentation/source was consulted statically, not installed or run. Following the reuse discussion, the requested choice was standalone Go, published types only, best original images, and JSON plus CSV. No third-party extractor source was copied into this implementation.

## Index chain

`index_stillness.txt` contains 427 application entries. Its `app:/resfileindex.txt` entry points to a hashed cache object containing 47,405 resources. The Windows resource index contributes 3,054 entries. Cache records identify resource URI, hashed path, MD5, uncompressed size, compressed size, and optionally mode. Locally cached resources inspected here contain the original, uncompressed bytes; sizes and MD5 are verified before decoding.

The extractor follows the cache objects identified by the top-level index, not an independently guessed version of the installed resource index. It does not need `code.ccp` or `manifest.dat` to extract these fields.

## Observed cFSD format

- Bytes 0–23: schema fingerprint; bytes 24–31: payload size.
- Payload starts at byte 32; stored pointers are payload-relative.
- Top-level dictionary root points to a vector of collision-bucket pointers.
- Root entry count is at file offset 40; bucket-vector count at offset 48; vector at 56.
- Bucket counts precede their data pointers by eight bytes; dictionary entries are 64-bit keys followed by inline values.
- Strings have an eight-byte length immediately before their payload-relative data pointer.

| Table | Value size | Relevant fields, relative to value |
|---|---:|---|
| types | 136 | graphicID 76; iconID 84; typeID 112; typeNameID 116; published byte 129; presence bits 132 |
| iconids | 24 | iconFile pointer 0; presence bits 20 |
| graphicids | 160 | iconInfo.folder pointer 48; iconInfo presence bits 56; outer presence bits 156 |

For types, graphicID/iconID/published use presence bits 4/5/13 respectively. For graphics, iconInfo uses outer bit 9; its folder uses inner bit 0. The iconFile pointer uses bit 0 at offset 20, **not offset 16**. Native-loader getter bytes provided independent static evidence for these offsets. Unit tests cover collision buckets and iconFile's presence-word offset.

Across all 32,925 decoded type entries, dictionary keys match the embedded type IDs. All 796 retained published types resolve to English names. Localization is a protocol-4 primitive tuple/dictionary structure: `('en-us', {messageID: (text, metadata, metadata), ...})`.

## Icon matching

Explicit icon mappings and graphic-folder mappings are both considered. Graphics use `<folder>/<graphicID>_<size>.<extension>`. Explicit icon variants retain directory and basename, changing only a recognized terminal resolution suffix and/or image extension. Numeric sprite-icon identity suffixes such as `_1` and `_2` are not merged.

All candidates are checked against actual image header dimensions and index checksums. No folder-wide image guessing, type-ID/graphic-ID conflation, upscaling, or model rendering is used. Missing icons are retained as missing in the catalog.

## Verification

Executed successfully with Go 1.27.0 on Windows/amd64:

- `go test -v ./...`: unit tests and fuzz seeds pass (real-installation test opt-in).
- `go test -run TestInstalledGame -v` with `FRONTIER_GAME_TEST`: 796 sorted, uniquely identified published items; 785 icons verified byte-for-byte against indexed cache originals; source index SHA-256 hashes unchanged across extraction.
- Ten seconds of localization fuzzing: 470,044 executions, no failures.
- Ten seconds of FSD fuzzing: 627,676 executions, no failures.
- `go vet ./...`: pass.
- `go build -trimpath -ldflags='-s -w' -o frontier-extract.exe .`: pass.

The real-installation test also confirms no missing names. Eleven missing icons are explicitly represented. Of the 785 exported images, 265 are 512×512, 504 are 64×64, and 16 have other native dimensions. Counts refer to items, not unique source images.

Checksums and byte comparisons are evidence about the files read, not a forensic proof that every byte in the installation remained unchanged. Source code opens game files read-only and has no game-directory write path.

## Security controls

Consulted the [current OWASP Top 10:2025](https://owasp.org/Top10/2025/) and [Go os.Root documentation](https://pkg.go.dev/os#Root). Applicable local-file controls include confined reads and external-only output (access control), no dynamic pickle operations and CSV formula escaping (injection), no external dependencies (supply-chain surface), checksums plus pinned schemas (data integrity), and bounded parsers/explicit failures (exception handling). This offline CLI has no authentication or network service surface.

No claims are made about unreviewed code, arbitrary future game schemas, asset redistribution rights, or extracting large artwork that is not actually present in the indexed local files.
