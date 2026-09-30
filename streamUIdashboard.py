import json
import math
import random
import time
import datetime
import os
import pandas as pd
import streamlit as st


# =============================================================================
#  MOCK / DEFAULT DATA GENERATORS & LOADERS
# =============================================================================

def get_default_config():
    return {
        # Geometry
        'L': 155418.5, 'dx': 100.0, 'D_nom_in': 10.75, 'initial_id_in': 10.312,
        'eps_mm': 0.045, 'x_pt_m': 150000.0, 'valve_pos_m': 155418.5, 'g': 9.81,
        # Gas properties
        'T_celsius': 25.0, 'mu_dyn': 1.1e-5, 'R_gas': 424.0,
        'Z_factor': 0.996, 'gamma': 1.26,
        # Pressures
        'P_upstream_bar': 20.8, 'P_atm_bar': 1.0, 'V_tank': 50.0,
        # Valve parameters
        'xT': 0.9, 'Fp': 1.0, 'Cv_max': 500.0, 'K_multiplier': 5.0,
        't_valve_open_start': 30.0, 't_valve_opening': 5.0,
        't_valve_hold_open': 60.0, 't_valve_closing': 5.0, 'T_total': 500.0,
        # Optimization
        'profile_type': 'uniform', 'max_iter': 150, 'popsize': 15,
        'D_range_min_in': 8.10, 'D_range_max_in': 10.312,
        'lambda_smooth': 1e-6, 'lambda_tv': 1e-7, 'workers': 1,
    }


def make_mock_upstream_data():
    """Fallback generator matching Upstream_data.csv structure."""
    rows = []
    for t in range(0, 501, 5):
        field_p = 19.194 + (t / 500.0) * 3.6 + random.uniform(-0.05, 0.05)
        init_p = field_p - random.uniform(0.3, 0.8)
        opt_p = field_p + random.uniform(-0.02, 0.02)
        rows.append({
            'Time (s)': float(t),
            'Field_ Pressure (kgf)': round(field_p, 3),
            'Initial_estimation (kgf)': round(init_p, 3),
            'Optimized_estimation (kgf)': round(opt_p, 3)
        })
    return pd.DataFrame(rows)


def make_mock_downstream_data():
    """Fallback generator matching Downstream_data.csv structure."""
    rows = []
    for t in range(0, 501, 2):
        field_p = 2.69 + (t / 500.0) * 6.9 + random.uniform(-0.08, 0.08)
        rows.append({
            'Time (s)': float(t),
            'Field_ Pressure (Kgf)': round(field_p, 4)
        })
    return pd.DataFrame(rows)


def make_mock_elevation_data():
    """Fallback generator matching elevation_profile.csv structure."""
    rows = []
    for i in range(165):
        dist_km = round(i * (155.259 / 164), 3)
        elev_m = round(150.0 + 40.0 * math.sin(i / 10.0) + 20.0 * math.sin(i / 3.0), 2)
        rows.append({'Distance (km)': dist_km, 'Elevation (m)': elev_m})
    return pd.DataFrame(rows)


def make_mock_diameter_data():
    """Fallback generator matching diameter.csv structure."""
    rows = []
    for i in range(1551):
        dist_m = round(i * 100.27, 2)
        est_id = round(9.80 + 0.3 * math.sin(i / 20.0) + random.uniform(-0.2, 0.2), 2)
        est_id = max(8.10, min(10.312, est_id))
        rows.append({
            'Distance (m)': dist_m,
            'Outer Diameter (in)': 10.75,
            'Initial_Inner Diameter (in)': 10.312,
            'Estimated _ID (in)': est_id
        })
    return pd.DataFrame(rows)


def make_mock_convergence(max_iter):
    cost = [85.0 + random.uniform(-2, 2)]
    for i in range(1, max_iter):
        drop = 18.0 * math.exp(-i / 25.0) * random.uniform(0.4, 1.2)
        cost.append(max(11.5, cost[-1] - drop + random.uniform(-0.3, 0.15)))
    return cost


# =============================================================================
#  SESSION STATE / HELPERS
# =============================================================================

def initialize_session_state():
    defaults = {
        'upstream_df': None,
        'downstream_df': None,
        'elevation_df': None,
        'diameter_df': None,
        'n_segments': 1551,
        'initial_simulation': None,
        'opt_result': None,
        'log_messages': [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if 'config' not in st.session_state:
        st.session_state.config = get_default_config()


def log_message(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append(f"[{ts}] {msg}")


def update_segment_count():
    cfg = st.session_state.config
    try:
        L, dx = float(cfg.get('L', 155418.5)), float(cfg.get('dx', 100.0))
        st.session_state.n_segments = int(round(L / dx))
    except Exception:
        st.session_state.n_segments = 0


# Loader actions (Checking uploaded files or local files or mock fallback)
def load_upstream_data(file_obj=None):
    if file_obj is not None:
        df = pd.read_csv(file_obj).dropna(subset=['Time (s)'])
    elif os.path.exists('Upstream_data.csv'):
        df = pd.read_csv('Upstream_data.csv').dropna(subset=['Time (s)'])
    else:
        df = make_mock_upstream_data()
    st.session_state.upstream_df = df
    log_message(f"Loaded Upstream PT Data: {len(df)} records")


def load_downstream_data(file_obj=None):
    if file_obj is not None:
        df = pd.read_csv(file_obj).dropna(subset=['Time (s)'])
    elif os.path.exists('Downstream_data.csv'):
        df = pd.read_csv('Downstream_data.csv').dropna(subset=['Time (s)'])
    else:
        df = make_mock_downstream_data()
    st.session_state.downstream_df = df
    log_message(f"Loaded Downstream PT Data: {len(df)} records")


def load_elevation_data(file_obj=None):
    if file_obj is not None:
        df = pd.read_csv(file_obj).dropna()
    elif os.path.exists('elevation_profile.csv'):
        df = pd.read_csv('elevation_profile.csv').dropna()
    else:
        df = make_mock_elevation_data()
    st.session_state.elevation_df = df
    log_message(f"Loaded Elevation Profile: {len(df)} points")


def load_diameter_data(file_obj=None):
    if file_obj is not None:
        df = pd.read_csv(file_obj).dropna()
    elif os.path.exists('diameter.csv'):
        df = pd.read_csv('diameter.csv').dropna()
    else:
        df = make_mock_diameter_data()
    st.session_state.diameter_df = df
    log_message(f"Loaded Diameter Profile CSV: {len(df)} segments")


# =============================================================================
#  MOCK SIMULATION / OPTIMIZATION ACTIONS
# =============================================================================

def run_simulation():
    update_segment_count()
    if st.session_state.upstream_df is None and st.session_state.downstream_df is None:
        st.warning("Please load Upstream or Downstream PT data first from the sidebar.")
        return

    with st.spinner("Running initial MOC simulation..."):
        progress = st.progress(0.0, text="Computing MOC hydraulic state...")
        for i in range(10):
            time.sleep(0.04)
            progress.progress((i + 1) / 10.0, text=f"Simulation step {i + 1}/10")
        progress.empty()

    rmse_initial = 85.4
    st.session_state.initial_simulation = {
        'rmse_mbar': rmse_initial,
        'status': 'Complete'
    }
    log_message(f"Initial simulation complete. Baseline RMSE: {rmse_initial:.1f} mbar")
    st.success(f"Initial simulation complete - Baseline RMSE: {rmse_initial:.1f} mbar")


def run_optimization():
    if st.session_state.initial_simulation is None:
        st.warning("Please run initial simulation first.")
        return

    max_iter = int(st.session_state.config.get('max_iter', 150))
    with st.spinner("Executing Differential Evolution Optimizer..."):
        progress = st.progress(0.0, text="Optimizing per-segment pipe diameters...")
        for i in range(10):
            time.sleep(0.04)
            progress.progress((i + 1) / 10.0, text=f"Generation {(i + 1) * max_iter // 10}/{max_iter}")
        progress.empty()

    convergence = make_mock_convergence(max_iter)
    load_diameter_data()  # Load or populate output diameter profile CSV

    rmse_final = 12.8
    st.session_state.opt_result = {
        'convergence': convergence,
        'rmse_initial_mbar': st.session_state.initial_simulation['rmse_mbar'],
        'rmse_final_mbar': rmse_final,
    }
    log_message(f"Optimization complete. RMSE improved from {st.session_state.initial_simulation['rmse_mbar']:.1f} to {rmse_final:.1f} mbar")
    st.success(f"Optimization complete - RMSE: {st.session_state.initial_simulation['rmse_mbar']:.1f} -> {rmse_final:.1f} mbar")


# =============================================================================
#  SIDEBAR: DATA INPUTS & CONFIGURATION PANEL
# =============================================================================

def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Inputs & Config")

        # ---------------------------------------------------------------------
        # 1. FILE UPLOADERS & DATA BUTTONS
        # ---------------------------------------------------------------------
        st.subheader("📁 Data Input Files")

        # Upstream PT Data
        up_file = st.file_uploader("Upstream PT Data CSV", type=['csv'], key='up_uploader')
        col_u1, col_u2 = st.columns([1, 1])
        with col_u1:
            if st.button("Load Upstream", use_container_width=True):
                load_upstream_data(up_file)
                st.rerun()

        # Downstream PT Data
        down_file = st.file_uploader("Downstream PT Data CSV", type=['csv'], key='down_uploader')
        col_d1, col_d2 = st.columns([1, 1])
        with col_d1:
            if st.button("Load Downstream", use_container_width=True):
                load_downstream_data(down_file)
                st.rerun()

        # Elevation Profile
        elev_file = st.file_uploader("Elevation Profile CSV", type=['csv'], key='elev_uploader')
        col_e1, col_e2 = st.columns([1, 1])
        with col_e1:
            if st.button("Load Elevation", use_container_width=True):
                load_elevation_data(elev_file)
                st.rerun()

        if st.button("⚡ Load All Example Data", type="primary", use_container_width=True):
            load_upstream_data()
            load_downstream_data()
            load_elevation_data()
            load_diameter_data()
            st.rerun()

        st.divider()

        # ---------------------------------------------------------------------
        # 2. CONFIGURATION PARAMETERS
        # ---------------------------------------------------------------------
        cfg = st.session_state.config
        st.subheader("🛠️ Configuration")

        # Pipeline Geometry Expander
        with st.expander("Pipeline Geometry", expanded=False):
            cfg['L'] = st.number_input("Pipe Length (m)", value=float(cfg.get('L', 155418.5)), step=100.0)
            cfg['dx'] = st.number_input("Grid Spacing dx (m)", value=float(cfg.get('dx', 100.0)), step=10.0)
            cfg['D_nom_in'] = st.number_input("Nominal OD (in)", value=float(cfg.get('D_nom_in', 10.75)), step=0.1)
            cfg['initial_id_in'] = st.number_input("Initial ID (in)", value=float(cfg.get('initial_id_in', 10.312)), step=0.01)
            cfg['eps_mm'] = st.number_input("Roughness (mm)", value=float(cfg.get('eps_mm', 0.045)), step=0.001, format="%.4f")
            cfg['x_pt_m'] = st.number_input("PT Location (m)", value=float(cfg.get('x_pt_m', 150000.0)), step=100.0)
            cfg['valve_pos_m'] = st.number_input("Valve Location (m)", value=float(cfg.get('valve_pos_m', 155418.5)), step=100.0)
            update_segment_count()
            st.caption(f"Calculated Segments: **{st.session_state.n_segments}**")

        # Gas Properties Expander
        with st.expander("Gas Properties", expanded=False):
            cfg['T_celsius'] = st.number_input("Temperature (°C)", value=float(cfg.get('T_celsius', 25.0)), step=1.0)
            cfg['R_gas'] = st.number_input("Gas Constant R (J/kgK)", value=float(cfg.get('R_gas', 424.0)), step=1.0)
            cfg['mu_dyn'] = st.text_input("Dynamic Viscosity (Pa.s)", value=str(cfg.get('mu_dyn', 1.1e-5)))
            cfg['Z_factor'] = st.number_input("Compressibility Z", value=float(cfg.get('Z_factor', 0.996)), step=0.001, format="%.4f")
            cfg['gamma'] = st.number_input("Heat Ratio gamma", value=float(cfg.get('gamma', 1.26)), step=0.01)
            cfg['g'] = st.number_input("Gravity (m/s²)", value=float(cfg.get('g', 9.81)), step=0.1)

        # Valve Parameters Expander
        with st.expander("Valve Parameters (ISA/IEC)", expanded=False):
            cfg['xT'] = st.number_input("Terminal Press Ratio xT", value=float(cfg.get('xT', 0.9)), step=0.01)
            cfg['Fp'] = st.number_input("Piping Factor Fp", value=float(cfg.get('Fp', 1.0)), step=0.01)
            cfg['Cv_max'] = st.number_input("Cv_max (rated)", value=float(cfg.get('Cv_max', 500.0)), step=10.0)
            cfg['K_multiplier'] = st.number_input("K Multiplier", value=float(cfg.get('K_multiplier', 5.0)), step=0.5)
            cfg['P_upstream_bar'] = st.number_input("Upstream Press (bar)", value=float(cfg.get('P_upstream_bar', 20.8)), step=0.1)
            cfg['V_tank'] = st.number_input("Tank Volume (m³)", value=float(cfg.get('V_tank', 50.0)), step=1.0)

        # Valve Timing Expander
        with st.expander("Valve Timing (4-Phase Cycle)", expanded=False):
            cfg['t_valve_open_start'] = st.number_input("Open Start (s)", value=float(cfg.get('t_valve_open_start', 30.0)), step=1.0)
            cfg['t_valve_opening'] = st.number_input("Opening Ramp (s)", value=float(cfg.get('t_valve_opening', 5.0)), step=0.5)
            cfg['t_valve_hold_open'] = st.number_input("Hold Open (s)", value=float(cfg.get('t_valve_hold_open', 60.0)), step=1.0)
            cfg['t_valve_closing'] = st.number_input("Closing Ramp (s)", value=float(cfg.get('t_valve_closing', 5.0)), step=0.5)
            cfg['T_total'] = st.number_input("Total Time (s)", value=float(cfg.get('T_total', 500.0)), step=10.0)

        # Optimization Settings Expander
        with st.expander("Optimization Settings", expanded=False):
            cfg['profile_type'] = st.selectbox("Initial Profile", ['uniform', 'stepped', 'random'], index=0)
            cfg['max_iter'] = st.number_input("Max Iterations", value=int(cfg.get('max_iter', 150)), step=10)
            cfg['popsize'] = st.number_input("Population Size", value=int(cfg.get('popsize', 15)), step=1)
            cfg['D_range_min_in'] = st.number_input("Min ID Bound (in)", value=float(cfg.get('D_range_min_in', 8.10)), step=0.1)
            cfg['D_range_max_in'] = st.number_input("Max ID Bound (in)", value=float(cfg.get('D_range_max_in', 10.312)), step=0.1)

        st.divider()

        # System Status Summary Card
        st.markdown("### 📊 System Status")
        st.info(f"""
        **Upstream PT:** {'Loaded (' + str(len(st.session_state.upstream_df)) + ' pts)' if st.session_state.upstream_df is not None else '❌ Not loaded'}  
        **Downstream PT:** {'Loaded (' + str(len(st.session_state.downstream_df)) + ' pts)' if st.session_state.downstream_df is not None else '❌ Not loaded'}  
        **Elevation:** {'Loaded (' + str(len(st.session_state.elevation_df)) + ' pts)' if st.session_state.elevation_df is not None else '❌ Not loaded'}  
        **Diameter Profile:** {'Loaded (' + str(len(st.session_state.diameter_df)) + ' pts)' if st.session_state.diameter_df is not None else '❌ Not loaded'}  
        """)


# =============================================================================
#  TAB 1: RESULTS SUMMARY CARDBOARD
# =============================================================================

def render_results_tab():
    st.header("📊 Executive Results & Control Center")

    # Top Control Buttons Panel
    st.markdown("### 🚀 Simulation & Optimization Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Run Initial Simulation", type="primary", use_container_width=True):
            run_simulation()
    with col2:
        disabled = st.session_state.initial_simulation is None
        if st.button("⚡ Run Differential Optimization", use_container_width=True, disabled=disabled):
            run_optimization()

    st.divider()

    # Metrics Cardboard Section
    st.markdown("### 📈 Key Performance Indicators (KPIs)")

    up_cnt = len(st.session_state.upstream_df) if st.session_state.upstream_df is not None else 0
    down_cnt = len(st.session_state.downstream_df) if st.session_state.downstream_df is not None else 0
    dia_cnt = len(st.session_state.diameter_df) if st.session_state.diameter_df is not None else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Upstream Records", f"{up_cnt}", delta="Field PT")
    with c2:
        st.metric("Downstream Records", f"{down_cnt}", delta="Field PT")
    with c3:
        st.metric("Pipeline Segments", f"{dia_cnt if dia_cnt > 0 else st.session_state.n_segments}", delta="Discretized")
    with c4:
        st.metric("Pipeline Length", f"{st.session_state.config.get('L', 155418.5)/1000.0:.2f} km")

    st.divider()

    if st.session_state.opt_result is not None:
        r = st.session_state.opt_result
        st.markdown("### 🎯 Optimization Outcomes")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Baseline RMSE", f"{r['rmse_initial_mbar']:.1f} mbar")
        with m2:
            st.metric("Optimized RMSE", f"{r['rmse_final_mbar']:.1f} mbar", delta=f"-{r['rmse_initial_mbar'] - r['rmse_final_mbar']:.1f} mbar")
        with m3:
            st.metric("Improvement", f"{(1 - r['rmse_final_mbar'] / r['rmse_initial_mbar']) * 100:.1f}%")
        with m4:
            st.metric("Max Iterations", f"{int(st.session_state.config.get('max_iter', 150))}")
    else:
        st.info("💡 Load datasets and execute optimization to view optimized metrics cardboard.")


# =============================================================================
#  TAB 2: CONVERGENCE HISTORY
# =============================================================================

def render_convergence_tab():
    st.header("📉 Optimization Convergence History")

    if st.session_state.opt_result is None:
        st.info("No optimization results available yet. Run optimization to populate convergence metrics.")
        conv = make_mock_convergence(150)
    else:
        conv = st.session_state.opt_result['convergence']

    # Metrics cardboard
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Initial Objective Cost", f"{conv[0]:.2f} mbar")
    c2.metric("Midway Cost (50% iter)", f"{conv[len(conv)//2]:.2f} mbar")
    c3.metric("Final Best Cost", f"{conv[-1]:.2f} mbar", delta=f"-{conv[0] - conv[-1]:.2f} mbar")
    c4.metric("Total Iterations", f"{len(conv)}")

    st.subheader("Convergence Curve (Cost vs Iteration)")
    st.line_chart({"Cost (mbar)": conv})


# =============================================================================
#  TAB 3: DIAMETER PROFILE (OUTPUT DATA CSV)
# =============================================================================

def render_diameter_profile_tab():
    st.header("📏 Per-Segment Diameter Profile (`diameter.csv`)")

    if st.session_state.diameter_df is None:
        load_diameter_data()

    df = st.session_state.diameter_df

    # Summary Metrics Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Distance", f"{df['Distance (m)'].max()/1000.0:.2f} km")
    c2.metric("Outer Diameter", f"{df['Outer Diameter (in)'].iloc[0]:.2f} in")
    c3.metric("Initial Inner Dia", f"{df['Initial_Inner Diameter (in)'].iloc[0]:.3f} in")
    c4.metric("Mean Estimated ID", f"{df['Estimated _ID (in)'].mean():.2f} in")
    c5.metric("Min / Max ID", f"{df['Estimated _ID (in)'].min():.2f} / {df['Estimated _ID (in)'].max():.2f} in")

    st.subheader("Estimated Inner Diameter vs Distance Along Pipeline")
    st.line_chart(df.set_index("Distance (m)")[["Initial_Inner Diameter (in)", "Estimated _ID (in)"]])

    if st.session_state.elevation_df is not None:
        st.subheader("Pipeline Elevation Profile Overlay")
        st.line_chart(st.session_state.elevation_df.set_index("Distance (km)")["Elevation (m)"])

    st.subheader("📋 Output Data Table")
    st.dataframe(df, use_container_width=True, height=250)

    # Export Download Button
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Output `diameter.csv`",
        data=csv_bytes,
        file_name="diameter.csv",
        mime="text/csv",
        type="primary"
    )


# =============================================================================
#  TAB 4: PRESSURE MATCH (UPSTREAM & DOWNSTREAM)
# =============================================================================

def render_pressure_match_tab():
    st.header("🌊 Pressure Matching Analysis")

    col_up, col_down = st.columns(2)

    # Upstream Match
    with col_up:
        st.subheader("Upstream Pressure Match (`Upstream_data.csv`)")
        if st.session_state.upstream_df is not None:
            df_up = st.session_state.upstream_df
            st.line_chart(df_up.set_index("Time (s)")[
                [c for c in df_up.columns if c != "Time (s)"]
            ])

            u1, u2 = st.columns(2)
            u1.metric("Mean Upstream Field P", f"{df_up['Field_ Pressure (kgf)'].mean():.2f} kgf")
            if 'Optimized_estimation (kgf)' in df_up.columns:
                u2.metric("Mean Optimized P", f"{df_up['Optimized_estimation (kgf)'].mean():.2f} kgf")
        else:
            st.info("Load Upstream PT Data in sidebar to display curves.")

    # Downstream Match
    with col_down:
        st.subheader("Downstream Pressure Trace (`Downstream_data.csv`)")
        if st.session_state.downstream_df is not None:
            df_down = st.session_state.downstream_df
            st.line_chart(df_down.set_index("Time (s)")["Field_ Pressure (Kgf)"])

            d1, d2 = st.columns(2)
            d1.metric("Min Downstream P", f"{df_down['Field_ Pressure (Kgf)'].min():.2f} kgf")
            d2.metric("Max Downstream P", f"{df_down['Field_ Pressure (Kgf)'].max():.2f} kgf")
        else:
            st.info("Load Downstream PT Data in sidebar to display curves.")


# =============================================================================
#  TAB 5: ERROR ANALYSIS CARDBOARD
# =============================================================================

def render_error_analysis_tab():
    st.header("🎯 Residual & Error Distribution Analysis")

    if st.session_state.upstream_df is not None and 'Optimized_estimation (kgf)' in st.session_state.upstream_df.columns:
        df = st.session_state.upstream_df
        residuals_mbar = (df['Field_ Pressure (kgf)'] - df['Optimized_estimation (kgf)']) * 98.0665  # kgf to mbar approx
    else:
        residuals_mbar = pd.Series([random.gauss(0, 12) for _ in range(150)])

    mean_err = residuals_mbar.mean()
    std_err = residuals_mbar.std()
    max_err = residuals_mbar.abs().max()
    p95_err = residuals_mbar.abs().quantile(0.95)

    # Cardboard metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mean Residual", f"{mean_err:.2f} mbar")
    c2.metric("Std Deviation", f"{std_err:.2f} mbar")
    c3.metric("Max Absolute Error", f"{max_err:.2f} mbar")
    c4.metric("95th Percentile Error", f"{p95_err:.2f} mbar")

    st.divider()

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Residuals Over Time (mbar)")
        st.line_chart(residuals_mbar)
    with col_chart2:
        st.subheader("Error Histogram")
        st.bar_chart(residuals_mbar.value_counts(bins=15).sort_index())


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def main():
    st.set_page_config(
        page_title="Gas MOC Smart Optimizer - Hardcoded Dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Injected CSS for modern dashboard board styling
    st.markdown("""
    <style>
    .main > div {max-width: 1600px; margin: 0 auto;}
    div[data-testid="stMetricValue"] {font-size: 26px; font-weight: bold;}
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {height: 42px; padding: 0 18px; font-weight: 600;}
    </style>
    """, unsafe_allow_html=True)

    initialize_session_state()

    st.title("⚡ Gas MOC Smart Optimizer Dashboard")
    st.caption("Pure UI layout prototype matching input/output CSV structures with cardboards & metrics.")

    # Render Sidebar with Uploaders + Configuration Pane
    render_sidebar()

    # Main Tabs Area
    tabs = st.tabs([
        "📊 Results & KPI Overview",
        "📉 Convergence History",
        "📏 Diameter Profile (`diameter.csv`)",
        "🌊 Upstream & Downstream Pressure Match",
        "🎯 Error Analysis Board",
    ])

    with tabs[0]:
        render_results_tab()
    with tabs[1]:
        render_convergence_tab()
    with tabs[2]:
        render_diameter_profile_tab()
    with tabs[3]:
        render_pressure_match_tab()
    with tabs[4]:
        render_error_analysis_tab()

    # Application Execution Log at the bottom
    st.divider()
    with st.expander("📋 Application Runtime Log", expanded=False):
        for msg in st.session_state.log_messages[-50:]:
            st.text(msg)


if __name__ == "__main__":
    main()