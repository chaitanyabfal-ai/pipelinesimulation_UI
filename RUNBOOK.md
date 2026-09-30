# Runbook: Gas MOC Smart Optimizer Dashboard

Run `streamUIdashboard.py` locally on Ubuntu with the same experience as the
Streamlit playground.

- App file: `streamUIdashboard.py`
- Dependencies: `streamlit`, `pandas` (numpy installed automatically)
- Runtime: Python 3 (system Python 3.x is fine)
- App URL after start: http://localhost:8501

---

## 1. Prerequisites check (one-time)

Open a terminal and confirm Python and pip are available:

```bash
python3 --version    # expect 3.x
pip3 --version       # expect a valid path
```

If `pip3` is missing, install it:

```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

## 2. Create a virtual environment (one-time)

```bash
cd /home/bfa/Gasoptimizer_UI
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Your prompt should now show `(.venv)` at the start. Every time you open a new
terminal, repeat this `source .venv/bin/activate` step before running the app.

## 3. Install dependencies (one-time, inside the venv)

```bash
pip install --upgrade pip
pip install streamlit pandas
```

Verify the installation:

```bash
python -c "import streamlit, pandas; print(streamlit.__version__, pandas.__version__)"
streamlit --version
```

Optionally pin the versions for repeatable setups:

```bash
pip freeze > requirements.txt
```

## 4. (Optional) Place input data files

The app works out of the box using built-in mock data generators. To use your
own PT / field data instead, place these CSVs in the project folder
(`/home/bfa/Gasoptimizer_UI`) or upload them through the sidebar. Local files
take priority over mock data.

| File | Required columns |
|------|------------------|
| `Upstream_data.csv` | `Time (s)`, `Field_ Pressure (kgf)`, `Initial_estimation (kgf)`, `Optimized_estimation (kgf)` |
| `Downstream_data.csv` | `Time (s)`, `Field_ Pressure (Kgf)` |
| `elevation_profile.csv` | `Distance (km)`, `Elevation (m)` |
| `diameter.csv` | `Distance (m)`, `Outer Diameter (in)`, `Initial_Inner Diameter (in)`, `Estimated _ID (in)` |

Column names must match exactly (including spaces and underscores).

## 5. Run the app

From the project root with the venv active:

```bash
streamlit run streamUIdashboard.py
```

Expected output:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://<your-lan-ip>:8501
```

Your default browser should open automatically. If not, manually open
http://localhost:8501.

Useful flags:

- Different port: `streamlit run streamUIdashboard.py --server.port 8502`
- Access from another device on the LAN:
  `streamlit run streamUIdashboard.py --server.address 0.0.0.0`
  then use the Network URL from the other device.
- Skip auto-open of the browser: add `--server.headless true`

## 6. Use the dashboard

1. In the sidebar under **Data Input Files**, click **Load All Example Data**
   (uses mock data if no CSVs are present), or upload/load your own
   Upstream, Downstream, and Elevation CSVs.
2. Check the **System Status** card at the bottom of the sidebar to confirm
   all datasets are loaded.
3. Adjust parameters if needed under **Configuration** (Pipeline Geometry,
   Gas Properties, Valve Parameters, Valve Timing, Optimization Settings).
4. Click **Run Initial Simulation** on the Results & KPI Overview tab.
5. Click **Run Differential Optimization** (enabled after step 4).
6. Review results across the tabs:
   - Results & KPI Overview - baseline vs optimized RMSE
   - Convergence History - cost vs iteration curve
   - Diameter Profile - per-segment estimated ID chart and table, with
     `diameter.csv` download button
   - Pressure Match - upstream/downstream field pressure traces
   - Error Analysis - residual stats and histogram
7. The **Application Runtime Log** expander at the bottom of the page shows
   load/run events.

## 7. Stop the app

Press `Ctrl+C` in the terminal where Streamlit is running.

Leave the virtual environment (optional, when done working):

```bash
deactivate
```

## 8. Restart later (every session)

```bash
cd /home/bfa/Gasoptimizer_UI
source .venv/bin/activate
streamlit run streamUIdashboard.py
```

## 9. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `streamlit: command not found` | The venv is not active. Run `source .venv/bin/activate`. |
| `ModuleNotFoundError: No module named 'streamlit'` | Dependencies not installed in the active venv. Re-run step 3. |
| Port 8501 already in use | Start on another port: `--server.port 8502`. |
| Browser did not open | Open http://localhost:8501 manually. |
| Data tab shows "Not loaded" | Click **Load All Example Data** or the individual Load buttons in the sidebar; loading is not automatic. |
| CSV load error / missing column | Check column headers match the table in step 4 exactly, including spaces and underscores. |
| `python3-venv` error during venv creation | Install it: `sudo apt install python3-venv`. |
| Old results persisting unexpectedly | Click **Rerun** in the Streamlit menu, or press `R`, to refresh the session. |
