# Sectionist

![CI](https://github.com/alienbrainfarm/Sectionist/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/alienbrainfarm/Sectionist/branch/main/graph/badge.svg)](https://codecov.io/gh/alienbrainfarm/Sectionist)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sectionist helps musicians take a song apart: it splits audio into labelled
sections (intro, verse, pre-chorus, chorus, bridge, instrumental, outro),
estimates key, tempo and chords, and shows everything on an editable timeline.

It is a PyQt6 desktop app talking to a local Flask backend over HTTP. Everything
runs on your machine — no accounts, no uploads, no cloud.

Segmentation can run on either of two engines: a fast heuristic built on
librosa, or the **SongFormer** model, which is far more accurate but needs an
optional download. The app detects which is available and picks the better one.

## Features

- 🎵 **Song structure segmentation** — labelled sections, not just boundaries
- 🎯 **Section confidence** — the model reports how sure it is, per section
- 📏 **Bar-aligned boundaries** — sections snap to detected downbeats, and bars are drawn in the timeline
- 🎹 **Key and tempo detection**, including key changes
- 🎸 **Chord detection** — beat-synchronous, with musical continuity, drawn on the timeline
- 📊 **Interactive timeline** — click, drag, split, join, rename sections; retype or re-boundary chords
- 🎧 **Playback with seeking**, driven by VLC
- 💾 **Save and reload** a song folder (audio copy plus `analysis.json`)
- 🎤 **Lyrics** — transcribed locally and shown beside the timeline
- 🧠 **Learns from your corrections** — train a small label model on songs you fix
- 🖥️ **Windows, macOS and Linux**

### Planned

- 📊 Bar lines drawn in the timeline
- 🎨 Enhanced look and feel
- 💾 Local database for song modifications
- 🎸 Chord mapping UI
- 📁 Export (PDF, text, MIDI)
- 🎤 Lyric extraction from audio
- 🔄 Batch processing

## Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | PyQt6 desktop app |
| Backend | Flask, served locally on `127.0.0.1:8765` |
| Audio analysis | librosa (tempo, key, chords) |
| Segmentation | SongFormer, optional; librosa heuristics as fallback |
| Beat tracking | Beat This!, optional |
| Playback | python-vlc (needs the VLC application installed) |

## Requirements

- **Python 3.10+**
- **VLC media player** — the `vlc` Python package is only a binding; it needs
  `libvlc` from the VLC app
- Optional, for the better engine: **PyTorch** and ~3 GB of disk for the
  SongFormer checkpoint. A CUDA GPU makes it fast; CPU works but takes about
  75 seconds per 3-minute track

## Quick start

### 1. Backend

```bash
cd backend
./start_server.sh
```

This creates a virtual environment, installs dependencies and serves
`http://127.0.0.1:8765`. On this path you get the heuristic engine.

### 2. Frontend

In a second terminal:

```bash
cd frontend
./setup.sh
source venv/bin/activate
python sectionist_gui.py
```

### 3. Analyse audio

- Drag a file onto the window, or click **Choose File**
- Click **Analyze Audio**
- Browse the sections in the timeline and the results panels
- Edit in place: drag a boundary, right-click to split, join or rename
- **Save Song** writes the audio and `analysis.json` into a folder you can
  reopen later — and that folder doubles as training data (see below)

## Enabling the SongFormer engine

The heuristic engine needs nothing extra. To switch to the model:

```bash
cd backend
source venv/bin/activate
pip install -r requirements-songformer.txt

python -c "from huggingface_hub import snapshot_download; \
  snapshot_download('ASLP-lab/SongFormer', local_dir='../.hf-cache/SongFormer')"
```

Restart the backend. `GET /health` confirms which engine is live:

```json
{"status": "healthy", "engine": "songformer",
 "engines": {"configured": "auto", "active": "songformer",
             "available": ["librosa", "songformer"]}}
```

Beat tracking is separate and much smaller. Install it on its own to get bar
lines and downbeat snapping without the segmentation model:

```bash
cd backend
pip install -r requirements-beats.txt   # PyTorch + Beat This!, ~80 MB of weights
```

`requirements-songformer.txt` already includes it.

### Choosing an engine

| `SECTIONIST_ENGINE` | Behaviour |
| --- | --- |
| `auto` (default) | `songformer` when its dependencies and checkpoint are present, otherwise `librosa` |
| `songformer` | Force the model; fail with a clear message if it is not installed |
| `librosa` | Force the heuristic pipeline |

### Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `SECTIONIST_ENGINE` | `auto` | `auto`, `songformer` or `librosa` |
| `SECTIONIST_DEVICE` | `auto` | `auto` (CUDA if present, else CPU), `cpu`, `mps`, `cuda` |
| `SECTIONIST_MODEL_DIR` | `.hf-cache/SongFormer` | Checkpoint location |
| `SECTIONIST_LABEL_MODEL` | `.hf-cache/label_model.npz` | Trained correction model |
| `SECTIONIST_HOST` / `SECTIONIST_PORT` | `127.0.0.1` / `8765` | Where the backend listens |
| `SECTIONIST_DEBUG` | off | `1` enables Flask's reloader and debugger |
| `TORCH_HOME` | `~/.cache/torch` | Where Beat This! keeps its 77 MB checkpoint |

The frontend honours `SECTIONIST_BACKEND_URL`, so the app can run on a laptop
while the analysis runs on a desktop GPU elsewhere on your network.

### Measured performance

SongFormer on an M1 Pro (16 GB), CPU:

| Audio | Time | Speed | Peak RAM |
| --- | --- | --- | --- |
| 34 s | 11 s | 3.1x realtime | — |
| 73 s | 22 s | 3.4x realtime | — |
| 192 s | 75 s | 2.5x realtime | 8.1 GB |

On Apple Silicon the GPU (MPS) is used by default and long tracks are processed
in overlapping 90-second windows, which keeps each pass in MPS's fast regime.
Measured on a memory-tight 16 GB M1 Pro, a 3:12 track took **57 s** that way
versus ~97 s on CPU. On a CUDA GPU the whole file runs in one pass in a few
seconds. Set `SECTIONIST_DEVICE=cpu` to override. Details in
[docs/MODEL_RESEARCH.md](docs/MODEL_RESEARCH.md).

## Learning from your corrections

Sections you fix in the app and save are training data. A small label model can
be fitted on top of the network's frozen outputs:

```bash
# Inspect the dataset without training
python tools/train_label_model.py --songs path/to/saved/songs --dry-run

# Train; the backend picks it up on the next start
python tools/train_label_model.py --songs path/to/saved/songs
```

This is a calibration layer over the model's per-section probabilities, not a
retraining of SongFormer, so it cannot invent structure the model missed. It
needs a few dozen corrected sections before it is worth anything; the tool warns
you below twelve.

## Project structure

```
Sectionist/
├── README.md
├── CONTRIBUTING.md
├── pyproject.toml                 # black configuration
├── .flake8                        # flake8 configuration
├── docs/
│   ├── PRD.md
│   ├── DEVELOPMENT.md
│   ├── CI_CD.md
│   ├── COMMUNICATION_PROTOCOL.md  # API contract
│   ├── AUDIO_PLAYBACK.md
│   ├── SECTION_EDITING_UI.md
│   ├── MODEL_RESEARCH.md          # why SongFormer, measurements, limitations
│   ├── IMPROVED_SEGMENTATION.md
│   ├── SEGMENTATION_ACCURACY_DISCUSSION.md
│   └── QUICK_START_SEGMENTATION_IMPROVEMENTS.md
├── backend/                       # Flask service
│   ├── server.py                  # HTTP API
│   ├── example.py                 # tempo, key, chords, heuristic segmentation
│   ├── improved_segmentation.py   # novelty-based segmentation
│   ├── analysis/
│   │   ├── __init__.py            # engine registry
│   │   ├── librosa_engine.py      # heuristic engine
│   │   ├── songformer_engine.py   # model engine
│   │   ├── beats.py               # Beat This! wrapper
│   │   ├── sections.py            # merging, naming, downbeat snapping
│   │   ├── calibration.py         # correction model
│   │   ├── lyrics.py              # Whisper transcription
│   │   ├── chunking.py            # overlapping windows for MPS
│   │   ├── chords.py              # beat-synchronous chord recognition
│   │   └── device.py              # device selection
│   ├── smoke_test.py              # end-to-end check against a running server
│   ├── benchmark_*.py             # standalone diagnostics, not pytest tests
│   ├── test_*.py                  # pytest suite
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── requirements-beats.txt
│   ├── requirements-lyrics.txt
│   ├── requirements-songformer.txt
│   └── start_server.sh
├── frontend/                      # PyQt6 desktop app
│   ├── sectionist_gui.py          # entry point
│   ├── main_window.py             # window, menus, results panels
│   ├── timeline_widget.py         # timeline rendering and editing
│   ├── audio_player.py            # VLC playback wrapper
│   ├── analysis_worker.py         # background HTTP worker
│   ├── chord_track.py             # chord lane painting and geometry
│   ├── lyrics_view.py             # lyrics panel and stanza formatting
│   ├── conftest.py                # pytest fixtures (offscreen Qt)
│   ├── test_*.py
│   ├── requirements.txt
│   └── setup.sh
└── tools/
    ├── train_label_model.py       # learn from corrected songs
    └── spike_songformer.py        # measure the model on any audio file
```

Model checkpoints and caches (`.hf-cache/`, `.torch-cache/`, `.venv-songformer/`)
are gitignored.

## Development setup

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python server.py

# Frontend (second terminal)
cd frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python sectionist_gui.py
```

## Testing

```bash
# Backend: analysis, engines, API, calibration
cd backend && source venv/bin/activate && pytest

# Frontend: runs headless, conftest.py sets the offscreen Qt platform
cd frontend && source venv/bin/activate && pytest

# End-to-end against a running backend
cd backend && python smoke_test.py
```

The backend suite does not need PyTorch: the model engine imports it lazily and
the registry reports it as unavailable, which is also how CI runs.

The `benchmark_*.py` scripts are standalone diagnostics rather than pytest
tests:

```bash
cd backend
python benchmark_advanced_segmentation.py
python benchmark_real_world_performance.py
```

Code style is enforced with black (88 columns) and flake8 across the backend,
frontend and tools:

```bash
black --check backend frontend tools
flake8 backend frontend tools
```

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and
pull request to `main` and `develop`:

| Job | What it does |
| --- | --- |
| **Backend** (Python 3.10 / 3.11 / 3.12) | flake8 and black on backend and tools, pytest with coverage, Codecov upload from 3.11 |
| **Frontend** | installs Qt and libvlc system libraries, lints, runs the PyQt6 suite headless |
| **Integration** | starts the server, waits for `/health`, runs `backend/smoke_test.py` |

See [docs/CI_CD.md](docs/CI_CD.md) for details.

## Development workflow

1. **Issues first** — every change starts with a GitHub issue
2. **Feature branches** — `feature/issue-name` or `bugfix/issue-name`
3. **Pull requests** — all changes go through review
4. **Tests** — new behaviour comes with tests
5. **Documentation** — update docs for user-facing changes

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guidelines.

## Roadmap

### Phase 1: Foundation ✅
- [x] Project setup and documentation
- [x] Development environment
- [x] Frontend/backend communication over HTTP

### Phase 2: Core audio analysis ✅
- [x] Audio loading and preprocessing
- [x] Song segmentation (heuristic)
- [x] Key and tempo detection
- [x] Chord detection (backend)

### Phase 3: User interface ✅
- [x] PyQt6 timeline visualisation
- [x] Cross-platform drag and drop
- [x] Section labelling and editing
- [x] Save/load of analysis results
- [ ] Results export

### Phase 4: Advanced analysis 🚧
- [x] Supervised segmentation (SongFormer engine)
- [x] Per-section confidence
- [x] Beat and downbeat detection
- [x] Downbeat-aligned section boundaries
- [x] Learning from user corrections
- [x] Chord track on the timeline
- [x] Chord editing (rename, drag boundaries)
- [x] Bar lines drawn in the timeline
- [x] Lyrics transcription and panel
- [ ] Chord vocabulary beyond major/minor triads
- [ ] Key change visualisation
- [ ] Local database for song modifications
- [ ] GPU batching and caching of embeddings

### Future
- [ ] Lyric extraction
- [ ] Export to notation software
- [ ] Batch processing
- [ ] Plugin architecture

## Documentation

- [Product requirements](docs/PRD.md)
- [Contributing guide](CONTRIBUTING.md)
- [Development setup](docs/DEVELOPMENT.md)
- [CI pipeline](docs/CI_CD.md)
- [API protocol](docs/COMMUNICATION_PROTOCOL.md)
- [Audio playback](docs/AUDIO_PLAYBACK.md)
- [Section editing UI](docs/SECTION_EDITING_UI.md)
- [Model research and measurements](docs/MODEL_RESEARCH.md)
- [Segmentation improvements](docs/IMPROVED_SEGMENTATION.md)

## Troubleshooting

### Backend

1. **"librosa not available"**
   ```bash
   cd backend && source venv/bin/activate
   pip install --force-reinstall librosa
   ```
2. **"Port already in use"** — something else holds 8765. Pick another port and
   point the frontend at it:
   ```bash
   SECTIONIST_PORT=5055 ./start_server.sh
   # other terminal:
   SECTIONIST_BACKEND_URL=http://127.0.0.1:5055 python sectionist_gui.py
   ```
   (Port 5000 is avoided by default because macOS hands it to the AirPlay
   Receiver, which made the old default flaky on Macs.)
3. **Missing dependencies** — `./start_server.sh` reinstalls everything.

### SongFormer

1. **`auto` still reports `librosa`** — the package or the checkpoint is missing.
   Check `curl http://127.0.0.1:8765/health`; the `available` list shows what the
   backend can actually see.
2. **`Could not initialise` / import errors after a manual install** — the model
   requires **transformers < 5**; 5.x breaks MuQ's constructor. The pinned
   requirements file handles this.
3. **Extremely slow analysis on an Apple Silicon Mac** — MPS was selected. Unset
   `SECTIONIST_DEVICE` (CPU is the default) or set it to `cpu`.
4. **First run hangs or fails offline** — the checkpoint fetches a Wav2Vec2
   config from Hugging Face at load time even when the weights are local, and
   Beat This! downloads its 77 MB checkpoint on first use into `TORCH_HOME`.
5. **Installing from scratch outside the requirements file** — `msaf` (imported
   by the checkpoint's evaluation code) breaks on modern scipy; patch
   `from scipy import inf` to `from numpy import inf`.

### Frontend

1. **"PyQt6 not found"** — `pip install PyQt6` inside the frontend venv.
2. **"Could not initialise VLC"** — install VLC. Debian/Ubuntu:
   `sudo apt-get install libvlc5 libvlccore9`; macOS: `brew install --cask vlc`.
3. **"Cannot connect to backend server"** — start the backend and check
   `curl http://127.0.0.1:8765/health`.
4. **Linux Qt issues** — `sudo apt-get install libgl1 libegl1 libxkbcommon0`.

### General

- Supported formats: MP3, WAV, AIFF, M4A, FLAC, OGG, AAC
- Maximum upload size: 100 MB
- Large files (over ~10 minutes) take a few minutes on CPU
- Everything is processed locally; no audio leaves the machine

## License

MIT — see [LICENSE](LICENSE). The optional SongFormer and MuQ model weights are
non-commercial (CC BY-NC 4.0), so a build using them may not be sold; the
heuristic engine has no such restriction. See
[docs/MODEL_RESEARCH.md](docs/MODEL_RESEARCH.md#licensing) for the full
breakdown.
