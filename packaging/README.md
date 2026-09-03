# Building standalone desktop builds

Windows, macOS, and Linux builds are produced automatically by
[`.github/workflows/build.yml`](../.github/workflows/build.yml) (each on its own native GitHub
Actions runner -- PyInstaller can't cross-compile). Push a tag matching `v*` to build all three
and attach them to a new GitHub Release, or run the workflow manually
(`workflow_dispatch`) to get downloadable build artifacts without creating a release.

## Building locally

```sh
pip install -r requirements.txt -r requirements-build.txt
pyinstaller packaging/SailplaneCalc.spec
```

Output lands in `dist/`: `dist/SailplaneCalc/` (Windows and Linux) or `dist/SailplaneCalc.app`
(macOS).

## Known limitations

- **Linux**: built against whatever glibc the GitHub Actions `ubuntu-latest` runner ships.
  glibc is forward- but not backward-compatible, so the build may not run on notably older
  distros (pre-Ubuntu-22.04-era glibc). Not addressed with a manylinux-style container build for
  this project's scale -- if it ever matters, that's the fix.
- **Unsigned builds**: these builds are not code-signed. Windows SmartScreen will warn on first
  launch (click "More info" -> "Run anyway"), and macOS Gatekeeper will block the app (right-click
  the app -> "Open" to bypass once).
- **No custom icon yet**: builds ship with each OS's default executable icon. See the commented
  `icon=` lines in `SailplaneCalc.spec` for where to add one.
