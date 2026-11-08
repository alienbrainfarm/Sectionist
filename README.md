# Sectionist

![CI](https://github.com/alienbrainfarm/Sectionist/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/alienbrainfarm/Sectionist/branch/main/graph/badge.svg)](https://codecov.io/gh/alienbrainfarm/Sectionist)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sectionist is a cross-platform application that helps musicians analyze songs by splitting audio into meaningful sections (intro, verse, chorus, etc.), detecting key changes, and mapping basic chords. It pairs a PyQt6 desktop frontend with a local Flask backend that does the audio/ML work with librosa.

**Current features:**

- 🎵 Song structure segmentation (intro, verse, chorus, bridge, outro)
- 🎹 Key and tempo detection, including detected key changes
- 🎸 Chord detection over time (backend)
- 📊 Interactive timeline: click, drag, split, join, and rename sections
- 🎧 Playback with seeking, driven by VLC
- 💾 Save and reload a song folder (audio copy + `analysis.json`)
- 🖥️ Runs on Windows, macOS, and Linux
- 📄 Extensive documentation in [`docs/`](docs/)

**Planned features:**

- 🎨 Enhanced look and feel
- 💾 Local database for song modifications
- 📊 Bar detection and display
- 🎸 Chord mapping UI
- 📁 Export (PDF, text, MIDI)
- 🎤 Lyric extraction from audio
- 🔄 Batch processing

## Tech stack

- **Frontend:** Python with PyQt6 (cross-platform GUI)
- **Backend:** Python, Flask + librosa (audio processing & MIR)
- **Audio playback:** python-vlc, which requires the VLC media player application
- **Communication:** local HTTP API on `127.0.0.1:5000`
- **Platforms:** Windows, macOS, Linux

## Prerequisites

- Python 3.10+
- VLC media player installed (the `vlc` Python package is only a binding; it needs `libvlc` from the VLC app)

## Quick start

### 1. Backend

```bash
cd backend
./start_server.sh
```

The script creates a virtual environment, installs the dependencies (librosa, Flask, etc.) and starts the server on `http://127.0.0.1:5000`.

### 2. Frontend

In a second terminal:

```bash
cd frontend
./setup.sh
source venv/bin/activate
python sectionist_gui.py
```

### 3. Analyze audio

- Drag and drop an audio file onto the window, or click **Choose File**
- Click **Analyze Audio**
- Browse the detected sections in the timeline and the results panels
- Edit sections in place: drag a boundary, right-click to split/join/rename
- Use **Save Song** to write the audio and `analysis.json` into a folder you can reopen later

## Analysis engines

Segmentation is pluggable. `SECTIONIST_ENGINE` selects the engine:

| Value | Behaviour |
| --- | --- |
| `auto` (default) | Use `songformer` when its dependencies and weights are present, otherwise `librosa` |
| `songformer` | Supervised segmentation (intro, verse, pre-chorus, chorus, bridge, instrumental, outro) |
| `librosa` | The original heuristic pipeline; always available |

The heuristic engine needs nothing extra. The SongFormer engine is optional
because it pulls in PyTorch and a ~2.8 GB checkpoint:

```bash
cd backend
pip install -r requirements-songformer.txt
python -c "from huggingface_hub import snapshot_download; \
  snapshot_download('ASLP-lab/SongFormer', local_dir='../.hf-cache/SongFormer')"
```

Measured on an M1 Pro, SongFormer takes about 75 s for a 3-minute track on CPU
(roughly 2.5x realtime, ~8 GB RAM); on a CUDA GPU it is a few seconds. It
defaults to CPU on Apple Silicon because the MPS backend slows down sharply on
long inputs.

| Variable | Default | Meaning |
| --- | --- | --- |
| `SECTIONIST_ENGINE` | `auto` | `auto`, `songformer` or `librosa` |
| `SECTIONIST_DEVICE` | `auto` | `auto` (CUDA if present, else CPU), `cpu`, `mps`, `cuda` |
| `SECTIONIST_MODEL_DIR` | `.hf-cache/SongFormer` | Checkpoint location |

With SongFormer installed, sections also carry the model's own confidence for
its label, and boundaries are snapped to detected downbeats so sections line up
with bars (beat tracking uses Beat This!, whose code and weights are MIT).

### Learning from corrections

Sections you fix in the app and save are training data. A small label model can
be fitted on top of the network's frozen outputs:

```bash
# See what would be used, without training
python tools/train_label_model.py --songs path/to/saved/songs --dry-run

# Train; the backend picks it up on the next start
python tools/train_label_model.py --songs path/to/saved/songs
```

This is a calibration layer over the model's per-section probabilities, not a
retraining of SongFormer. It needs a few dozen corrected sections to be worth
anything.

`GET /health` reports which engine is active. See
[docs/MODEL_RESEARCH.md](docs/MODEL_RESEARCH.md) for the evaluation behind this
and the known limitations.

## Project structure

```
Sectionist/
├── README.md
├── CONTRIBUTING.md
├── pyproject.toml            # black configuration
├── .flake8                   # flake8 configuration
├── docs/
│   ├── PRD.md                # Product requirements
│   ├── DEVELOPMENT.md        # Development guide
│   ├── CI_CD.md              # CI pipeline documentation
│   ├── COMMUNICATION_PROTOCOL.md  # API specification
│   ├── AUDIO_PLAYBACK.md     # Playback architecture
│   ├── SECTION_EDITING_UI.md # Manual section editing
│   ├── IMPROVED_SEGMENTATION.md
│   ├── SEGMENTATION_ACCURACY_DISCUSSION.md
│   └── QUICK_START_SEGMENTATION_IMPROVEMENTS.md
├── backend/                  # Flask + librosa service
│   ├── server.py             # HTTP API
│   ├── example.py            # Analysis pipeline (tempo/key/chords)
│   ├── analysis/             # Pluggable segmentation engines
│   ├── improved_segmentation.py  # Novelty-based segmentation
│   ├── smoke_test.py         # End-to-end check against a running server
│   ├── benchmark_*.py        # Standalone accuracy/performance benchmarks
│   ├── test_*.py             # pytest suite
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── requirements-songformer.txt  # Optional model dependencies
│   └── start_server.sh
└── frontend/                 # PyQt6 desktop app
    ├── sectionist_gui.py     # Entry point
    ├── main_window.py        # Window, menus, results display
    ├── timeline_widget.py    # Timeline rendering and editing
    ├── audio_player.py       # VLC playback wrapper
    ├── analysis_worker.py    # Background HTTP analysis worker
    ├── conftest.py           # pytest fixtures (offscreen Qt)
    ├── test_*.py             # pytest suite
    ├── requirements.txt
    └── setup.sh
```

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

Set `SECTIONIST_DEBUG=1` before starting the backend to enable Flask's debug mode (reloader and debugger).

## Testing

```bash
# Backend suite (audio analysis + API)
cd backend
source venv/bin/activate
pytest

# Frontend suite (runs headless; conftest.py sets the offscreen Qt platform)
cd frontend
source venv/bin/activate
pytest

# End-to-end check against a running backend
cd backend
python smoke_test.py
```

The `benchmark_*.py` scripts are standalone diagnostics rather than pytest tests; run them directly to inspect segmentation accuracy and runtime on synthetic material:

```bash
cd backend
python benchmark_advanced_segmentation.py
python benchmark_real_world_performance.py
```

Code style is enforced with `black` (line length 88) and `flake8`:

```bash
black --check .
flake8 .
```

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and pull request to `main` and `develop`:

| Job | What it does |
| --- | --- |
| **Backend** (Python 3.10 / 3.11 / 3.12) | installs dependencies, runs flake8, `black --check`, and pytest with coverage; uploads coverage from 3.11 |
| **Frontend** | installs Qt and libvlc system libraries, runs the PyQt6 test suite headless (`QT_QPA_PLATFORM=offscreen`) |
| **Integration** | starts the Flask server, waits for `/health`, then runs `backend/smoke_test.py` against it |

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
- [x] Development environment setup
- [x] Frontend/backend communication over HTTP

### Phase 2: Core audio analysis ✅
- [x] Audio loading and preprocessing
- [x] Song segmentation algorithm
- [x] Key and tempo detection
- [x] Chord detection (backend)

### Phase 3: User interface ✅
- [x] PyQt6 timeline visualisation
- [x] Cross-platform drag-and-drop
- [x] Section labelling and editing
- [x] Save/load of analysis results
- [ ] Results export

### Phase 4: Advanced features 🚧
- [ ] Enhanced frontend look and feel
- [ ] Local database for song modifications
- [ ] Bar detection and display
- [ ] Chord mapping UI
- [ ] Key change visualisation
- [ ] Improved segmentation accuracy
- [ ] Performance optimisation

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
- [Segmentation improvements](docs/IMPROVED_SEGMENTATION.md)

## Troubleshooting

### Backend

1. **"librosa not available"**
   ```bash
   cd backend && source venv/bin/activate
   pip install --force-reinstall librosa
   ```
2. **"Port already in use"** (port 5000)
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```
3. **Missing dependencies** — `./start_server.sh` reinstalls everything.

### Frontend

1. **"PyQt6 not found"** — `pip install PyQt6` inside the frontend venv.
2. **"Could not initialise VLC"** — install the VLC application. On Debian/Ubuntu: `sudo apt-get install libvlc5 libvlccore9`. On macOS: install VLC from `vlc.io` (or `brew install --cask vlc`).
3. **"Cannot connect to backend server"** — start the backend and check `curl http://127.0.0.1:5000/health`.
4. **Linux Qt issues** — `sudo apt-get install libgl1 libegl1 libxkbcommon0`.

### Performance

- Large files (over ~10 minutes) can take a couple of minutes to analyse
- Supported formats: MP3, WAV, AIFF, M4A, FLAC, OGG, AAC
- Maximum upload size: 100 MB

## License

MIT — see [LICENSE](LICENSE).
