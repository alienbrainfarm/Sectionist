# Running the backend on another machine

The backend and frontend are separate processes talking over HTTP, so they do
not have to run on the same computer. Put the backend on a machine with a GPU
and keep the interface on the laptop: a four-minute track drops from roughly
100 seconds on a laptop CPU to a few seconds on a modern GPU.

Nothing about the analysis changes — only where it runs.

```
laptop                          machine with a GPU
┌────────────────────┐          ┌──────────────────────┐
│ PyQt6 frontend     │  HTTP    │ Flask backend        │
│ SECTIONIST_BACKEND_│ ───────▶ │ SECTIONIST_HOST=0.0.0.0
│ URL=http://rig:8765│          │ :8765                │
└────────────────────┘          └──────────────────────┘
```

## On the machine with the GPU

### 1. Python and a virtual environment

Python 3.10 or 3.11 works best; the model's dependencies are pinned around it.

```bash
git clone https://github.com/alienbrainfarm/Sectionist.git
cd Sectionist/backend
python -m venv venv
```

Activate it — `venv\Scripts\activate` on Windows, `source venv/bin/activate`
elsewhere.

### 2. CUDA PyTorch first

Install PyTorch before the other requirements, or pip resolves the CPU build
and everything silently runs on the CPU. Blackwell cards (RTX 50 series) need
CUDA 12.8 wheels:

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
```

Check it actually sees the card:

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

It must print `True` and the card's name. If it prints `False`, fix this before
continuing; the rest of the setup will look correct and be slow.

### 3. Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-songformer.txt
pip install -r requirements-lyrics.txt
```

Optionally `requirements-stems.txt` if you want Demucs vocal separation (off by
default, and expensive — see the README).

Then download the segmentation model:

```bash
python -c "from huggingface_hub import snapshot_download; \
  snapshot_download('ASLP-lab/SongFormer', local_dir='../.hf-cache/SongFormer')"
```

That is ~2.8 GB. Beat This! fetches its own 77 MB checkpoint on the first
analysis.

### 4. Listen on the network

The default binds to `127.0.0.1`, which only accepts local connections.

```bash
# bash
SECTIONIST_HOST=0.0.0.0 python server.py
```

```powershell
# PowerShell
$env:SECTIONIST_HOST = "0.0.0.0"
python server.py
```

Note the machine's address (`ipconfig` on Windows, `ip addr` or `ifconfig`
elsewhere). Allow port 8765 through the firewall when prompted — Windows will
ask the first time, and the "private networks" option is the right one.

## On the laptop

```bash
curl http://<host>:8765/health
```

Expect `"engine": "songformer"` in the response. Then point the frontend at it:

```bash
cd frontend
source venv/bin/activate
SECTIONIST_BACKEND_URL=http://<host>:8765 python sectionist_gui.py
```

Stop any server running locally first so it is not holding memory for nothing.

## What runs where

| Work | Where | Notes |
| --- | --- | --- |
| Interface, playback, editing | laptop | Needs VLC |
| Segmentation, chords, key, beats | GPU machine | A few seconds per song |
| Lyrics transcription | GPU machine | CTranslate2 on CUDA, or CPU without it |

## Security

**The server has no authentication.** Anyone who can reach port 8765 can upload
audio and consume GPU time. That is fine on a home network; do not expose it to
the internet or port-forward it.

## Troubleshooting

**`/health` shows `librosa` instead of `songformer`** — the checkpoint is not
where the backend expects. Check it exists at `.hf-cache/SongFormer` inside the
repo, or set `SECTIONIST_MODEL_DIR`.

**`torch.cuda.is_available()` is `False`** — either the CPU wheel was installed
(re-run the CUDA install command) or the driver is older than the CUDA build.
`nvidia-smi` shows the driver version.

**Connection refused from the laptop** — the server is bound to `127.0.0.1`, or
the firewall is blocking 8765.

**Lyrics fail with a cuDNN error** — faster-whisper needs cuDNN 9 for CUDA 12.
Set `SECTIONIST_WHISPER_DEVICE=cpu`; transcription is fast enough that it
barely matters.

**Everything is slow despite the GPU** — check `/health` and the server startup
banner for the resolved device. `SECTIONIST_DEVICE=cuda` forces it and fails
loudly rather than falling back.
