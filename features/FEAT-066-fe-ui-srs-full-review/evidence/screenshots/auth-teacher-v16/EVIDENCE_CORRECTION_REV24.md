# EV-019 screenshot provenance correction

An Auth Rev24 capture helper initially used the Rev16 output directory. It overwrote these six EV-019 login images on 2026-11-11:

- `auth-teacher-1440.png`
- `auth-teacher-390.png`
- `auth-school-manager-1440.png`
- `auth-school-manager-390.png`
- `auth-platform-admin-1440.png`
- `auth-platform-admin-390.png`

It also overwrote `observations.json`. No backup of those original seven files was found. The eight Teacher route screenshots in this folder were not overwritten. The six login PNGs and observations currently here must be attributed to Rev24, not EV-019. Current Auth evidence is under `../auth-rev24/`; the original EV-019 description has been amended to record this provenance limitation.
