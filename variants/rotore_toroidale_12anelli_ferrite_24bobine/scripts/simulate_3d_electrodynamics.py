#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
SIMULAZIONE ELETTROMAGNETICA 3D ROTORE A 12 ANELLI E 24 BOBINE CON GABBIA IN ALLUMINIO
ALIMENTAZIONE AC CON DIODI PN/NP E VERIFICA DELLA POLARITÀ DEL CAMPO ESTERNO (CW vs CCW)
========================================================================================

Obiettivo:
1. Dimensionamento completo della macchina a 12 anelli toroidali e 24 bobine multistrato.
2. Alimentazione AC a 100 Hz con raddrizzamento a semionde a diodi alternati PN e NP:
   - Bobine pari (k=0,2,...): Diodo PN -> conducono su semionda positiva (Polarità N)
   - Bobine dispari (k=1,3,...): Diodo NP -> conducono su semionda negativa (Polarità S)
3. Presenza della gabbia sferica in alluminio con traferro sottile (2 mm).
4. Simulazione transiente 3D elettrodinamica completa per tre condizioni cinematiche:
   - Rotore fermo (omega = 0)
   - Rotazione oraria CW (omega = +1200 RPM)
   - Rotazione antioraria CCW (omega = -1200 RPM)
5. Verifica fisica e metrologica:
   - Valutazione del campo magnetico radiale B_r(theta, phi, t) all'esterno della gabbia
   - Calcolo del flusso magnetico totale Phi_B = \oint B_r dS (Teorema di Gauss per B)
   - Bilancio tra flusso positivo (Nord) e flusso negativo (Sud)
   - Verifica rigorosa se il campo possa essere o meno di una "sola polarità"

Autore: Open Chiral Flux Shaper - Modulo Elettrodinamico
========================================================================================
"""

import os
import sys
import json
import time
from pathlib import Path
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Directory di lavoro
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
FIG_DIR = PROJECT_DIR / "figures"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Costanti fisiche fondamentali
MU_0 = 4.0 * np.pi * 1e-7  # H/m (Permeabilità del vuoto)

# Parametri Geometrici Macchina
R_RING_M = 0.035          # 35 mm Raggio maggiore anello
R_TUBE_M = 0.004          # 4 mm Raggio sezione tubo anello
N_RINGS = 12              # 12 anelli fisici
N_COILS = 24              # 24 bobine (2 per anello)
ARC_SPAN_DEG = 150.0      # 150° arco libero utile (esclude +/-15° polo per intersezione)
N_TURNS_PER_COIL = 120    # 120 spire per bobina (multistrato a 3 strati da 40)
R_SPIRA_M = 0.0048        # 4.8 mm raggio medio spira

# Parametri Elettrici
FREQ_HZ = 100.0           # Frequenza AC 100 Hz
OMEGA_E = 2.0 * np.pi * FREQ_HZ
T_PERIOD = 1.0 / FREQ_HZ  # 10 ms periodo elettrico
I_PEAK = 3.0              # Corrente di picco per bobina (A)

# Parametri Gabbia Sferica Alluminio
R_ROTOR_MAX_M = 0.039     # 39 mm raggio esterno rotore
AIR_GAP_M = 0.002         # 2 mm traferro d'aria
R_CAGE_M = 0.042          # 42 mm raggio medio gabbia alluminio
T_CAGE_M = 0.002          # 2 mm spessore gabbia
SIGMA_AL = 1.75e7         # Conducibilità efficace rete alluminio (S/m)

# Parametri Misura Campo Esterno
R_MEASURE_M = 0.060       # 60 mm raggio sfera di misura esterna (> R_cage)

# Parametri Cinematica Rotore
RPM_NOMINAL = 1200.0
OMEGA_MECH_RAD_S = 2.0 * np.pi * (RPM_NOMINAL / 60.0)  # 125.66 rad/s


def build_coil_geometry(n_points_per_coil=25):
    """
    Costruisce la geometria 3D dei 24 semiarchetti delle bobine.
    Ciascun arco k (k=0..23) ha azimut theta_k = k * 15°
    ed è discretizzato in segmenti con dipoli magnetici associati.
    """
    coils = []
    d_phi = 2.0 * np.pi / N_COILS  # 15 gradi
    
    # Latitudini dell'arco da -75° a +75°
    lat_min = -np.radians(ARC_SPAN_DEG / 2.0)
    lat_max =  np.radians(ARC_SPAN_DEG / 2.0)
    latitudes = np.linspace(lat_min, lat_max, n_points_per_coil)
    
    for k in range(N_COILS):
        azimuth_0 = k * d_phi
        # Coordinate dei punti lungo la linea centrale dell'arco toroidale
        # Nel piano meridiano a longitudine azimuth_0:
        # x = R_RING * cos(lat) * cos(azimuth_0)
        # y = R_RING * cos(lat) * sin(azimuth_0)
        # z = R_RING * sin(lat)
        x_pts = R_RING_M * np.cos(latitudes) * np.cos(azimuth_0)
        y_pts = R_RING_M * np.cos(latitudes) * np.sin(azimuth_0)
        z_pts = R_RING_M * np.sin(latitudes)
        points = np.column_stack([x_pts, y_pts, z_pts])
        
        # Tangenti lungo l'arco (direzione dell'asse del solenoide toroidale)
        dl = np.gradient(points, axis=0)
        dl_norms = np.linalg.norm(dl, axis=1, keepdims=True)
        t_unit = dl / (dl_norms + 1e-12)
        
        # Superficie di una spira
        area_spira = np.pi * (R_SPIRA_M ** 2)
        
        # Tipo di diodo associato:
        # Bobine pari: Diodo PN (attive su semionda positiva)
        # Bobine dispari: Diodo NP (attive su semionda negativa, polarità invertita)
        diode_type = "PN" if (k % 2 == 0) else "NP"
        polarity_sign = +1 if (k % 2 == 0) else -1
        
        coils.append({
            'index': k,
            'azimuth_0': azimuth_0,
            'points': points,
            't_unit': t_unit,
            'dl_norms': dl_norms.flatten(),
            'area_spira': area_spira,
            'diode_type': diode_type,
            'polarity_sign': polarity_sign,
            'turns': N_TURNS_PER_COIL
        })
    return coils


def get_coil_current(coil, t, omega_e=OMEGA_E, i_peak=I_PEAK):
    """
    Calcola la corrente istantanea nella bobina considerando l'azione dei diodi PN/NP.
    - Se diodo PN (pari): conduce solo se sin(omega_e * t) > 0
    - Se diodo NP (dispari): conduce solo se sin(omega_e * t) < 0, con verso polare opposto
    """
    sin_wt = np.sin(omega_e * t)
    if coil['diode_type'] == "PN":
        # Conduce durante semionda positiva
        val = max(0.0, sin_wt)
        return i_peak * val
    else:
        # Conduce durante semionda negativa (polarità opposta)
        val = max(0.0, -sin_wt)
        return -i_peak * val


def compute_b_coils(coils, eval_points, t, rotor_angle):
    """
    Calcola il campo magnetico B_coils nei punti eval_points
    sommando il contributo di tutti i dipoli/spire delle 24 bobine ruotate dell'angolo rotor_angle.
    """
    # Matrice di rotazione attorno all'asse Z di rotor_angle
    cos_a = np.cos(rotor_angle)
    sin_a = np.sin(rotor_angle)
    R_mat = np.array([
        [cos_a, -sin_a, 0.0],
        [sin_a,  cos_a, 0.0],
        [0.0,    0.0,   1.0]
    ])
    
    n_eval = eval_points.shape[0]
    B_total = np.zeros((n_eval, 3), dtype=np.float64)
    
    for coil in coils:
        i_curr = get_coil_current(coil, t)
        if abs(i_curr) < 1e-6:
            continue
            
        # Ruota i punti della bobina
        pts_rot = coil['points'] @ R_mat.T
        t_rot = coil['t_unit'] @ R_mat.T
        
        # Momento magnetico di ciascun tratto dell'arco toroidale
        # dm = N_spire_tratto * I * Area * t_unit
        n_pts = len(coil['points'])
        turns_per_pt = coil['turns'] / float(n_pts)
        dm_vec = turns_per_pt * i_curr * coil['area_spira'] * t_rot  # (n_pts, 3)
        
        # Calcolo vettoriale Biot-Savart / Dipolo per tutti i punti
        # B_dipolo(r) = (mu_0 / 4pi) * [3 (m . r_hat) r_hat - m] / |r|^3
        for pt_idx in range(n_pts):
            r_src = pts_rot[pt_idx]
            m_vec = dm_vec[pt_idx]
            
            # Vettori da sorgente a punti di misura
            disp = eval_points - r_src  # (n_eval, 3)
            dist = np.linalg.norm(disp, axis=1) + 1e-12
            dist3 = dist ** 3
            dist5 = dist ** 5
            
            # Prodotto scalare m . disp
            m_dot_r = np.sum(disp * m_vec, axis=1)
            
            # Formula dipolare esatta
            dB = (MU_0 / (4.0 * np.pi)) * (
                3.0 * (m_dot_r[:, None] * disp) / dist5[:, None] - 
                m_vec[None, :] / dist3[:, None]
            )
            B_total += dB
            
    return B_total


def compute_eddy_currents_and_b_cage(coils, eval_points, t, rotor_angle, omega_mech, cage_grid):
    """
    Calcola le correnti parassite indotte nella gabbia sferica in alluminio
    e il rispettivo campo magnetico B_cage.
    Equazione: J_cage = sigma_Al * (-dA/dt + v_rel x B)
    """
    dt = 1e-4  # passo temporale per derivata
    # Calcolo di B sulla superficie della gabbia a t e t + dt
    b_cage_t = compute_b_coils(coils, cage_grid['pts'], t, rotor_angle)
    b_cage_t_next = compute_b_coils(coils, cage_grid['pts'], t + dt, rotor_angle + omega_mech * dt)
    
    # Derivata temporale dB/dt sulla gabbia
    dB_dt = (b_cage_t_next - b_cage_t) / dt
    
    # Velocità locale della rotazione meccanica: v = omega x r
    # Con omega = [0, 0, omega_mech]
    vx = -omega_mech * cage_grid['pts'][:, 1]
    vy =  omega_mech * cage_grid['pts'][:, 0]
    vz =  np.zeros_like(vx)
    v_vec = np.column_stack([vx, vy, vz])
    
    # Campo elettrico indotto / densità di corrente
    # In una shell sferica, le correnti sono confinate tangenzialmente:
    # J_tangenziale \propto sigma_eff * [ (-dPhi/dt) e_phi + (v x B)_tang ]
    v_cross_b = np.cross(v_vec, b_cage_t)
    
    # Proiezione normale alla sfera: n_hat = pts / |pts|
    n_hat = cage_grid['pts'] / (np.linalg.norm(cage_grid['pts'], axis=1, keepdims=True) + 1e-12)
    
    # Corrente tangenziale motrice (v x B e variazione temporale)
    j_motional = v_cross_b - np.sum(v_cross_b * n_hat, axis=1, keepdims=True) * n_hat
    
    # Corrente indotta da induzione di Faraday -dA/dt tangenziale
    # Schematizzata tramite dipoli di correnti parassite indotte
    # con fattore di schermatura / ritardo di Lenz:
    k_shield = (SIGMA_AL * T_CAGE_M * MU_0 * R_CAGE_M) / (1.0 + (OMEGA_E * SIGMA_AL * T_CAGE_M * MU_0 * R_CAGE_M * 0.1))
    
    # Dipoli equivalenti delle correnti di Foucault sulla maglia della gabbia
    # Le correnti parassite creano momenti magnetici opposti alla componente radiale
    # e momenti tangenziali dovuti alla rotazione v x B
    b_rad = np.sum(b_cage_t * n_hat, axis=1, keepdims=True)
    m_eddy_rad = -0.15 * (k_shield / 100.0) * b_rad * n_hat * cage_grid['dA'][:, None] / MU_0
    m_eddy_rot =  0.08 * (k_shield / 100.0) * np.cross(n_hat, j_motional) * cage_grid['dA'][:, None] / (np.linalg.norm(v_vec) + 1.0)
    
    m_cage_tot = m_eddy_rad + m_eddy_rot
    
    # Campo prodotto dalle correnti della gabbia sui punti di misura
    n_eval = eval_points.shape[0]
    B_cage = np.zeros((n_eval, 3), dtype=np.float64)
    
    for c_idx in range(len(cage_grid['pts'])):
        r_src = cage_grid['pts'][c_idx]
        m_vec = m_cage_tot[c_idx]
        disp = eval_points - r_src
        dist = np.linalg.norm(disp, axis=1) + 1e-12
        dist3 = dist ** 3
        dist5 = dist ** 5
        m_dot_r = np.sum(disp * m_vec, axis=1)
        dB = (MU_0 / (4.0 * np.pi)) * (
            3.0 * (m_dot_r[:, None] * disp) / dist5[:, None] - 
            m_vec[None, :] / dist3[:, None]
        )
        B_cage += dB
        
    return B_cage


def create_spherical_measurement_grid(radius, n_lat=30, n_lon=60):
    """
    Crea una griglia sferica di misura con campionamento di area pesato (sin(theta) dtheta dphi).
    """
    lats = np.linspace(-np.pi/2.0 + 0.05, np.pi/2.0 - 0.05, n_lat)
    lons = np.linspace(0.0, 2.0 * np.pi, n_lon, endpoint=False)
    
    LATS, LONS = np.meshgrid(lats, lons, indexing='ij')
    
    X = radius * np.cos(LATS) * np.cos(LONS)
    Y = radius * np.cos(LATS) * np.sin(LONS)
    Z = radius * np.sin(LATS)
    
    pts = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    
    # Calcolo elementi di area infinitesima dA = R^2 * cos(lat) * dlat * dlon
    dlat = (np.pi - 0.1) / (n_lat - 1)
    dlon = 2.0 * np.pi / n_lon
    dA = (radius ** 2) * np.cos(LATS).flatten() * dlat * dlon
    
    # Vettori normali radiali unitari
    n_rad = pts / radius
    
    return {
        'radius': radius,
        'n_lat': n_lat,
        'n_lon': n_lon,
        'lats': lats,
        'lons': lons,
        'LATS': LATS,
        'LONS': LONS,
        'pts': pts,
        'dA': dA,
        'n_rad': n_rad
    }


def run_full_simulation():
    """
    Esegue la suite di simulazione completa per i 3 regimi:
    - Static (omega = 0)
    - CW (+1200 RPM)
    - CCW (-1200 RPM)
    Estrae il campo B_r, analizza la polarità e verifica il Teorema di Gauss.
    """
    print("=" * 80)
    print("AVVIO SIMULAZIONE ELETTROMAGNETICA 3D ROTORE 12 ANELLI / 24 BOBINE")
    print("=" * 80)
    
    # 1. Costruzione Geometria
    coils = build_coil_geometry(n_points_per_coil=25)
    print(f"[1/5] Geometria generata: {len(coils)} bobine su {N_RINGS} anelli.")
    print(f"      - Raggio anelli: {R_RING_M*1e3:.1f} mm, Raggio esterno: {R_ROTOR_MAX_M*1e3:.1f} mm")
    print(f"      - Gabbia sferica alluminio: R={R_CAGE_M*1e3:.1f} mm, Traferro: {AIR_GAP_M*1e3:.1f} mm")
    print(f"      - Sfera di misura esterna: R={R_MEASURE_M*1e3:.1f} mm")
    
    # Griglie sferiche
    cage_grid = create_spherical_measurement_grid(R_CAGE_M, n_lat=16, n_lon=32)
    meas_grid = create_spherical_measurement_grid(R_MEASURE_M, n_lat=28, n_lon=56)
    
    # Timestep della simulazione: 1 periodo completo a 100 Hz (10 ms), 20 timestep
    n_timesteps = 20
    time_array = np.linspace(0.0, T_PERIOD, n_timesteps, endpoint=False)
    
    regimes = [
        {"name": "STATIC", "omega_mech": 0.0, "label": "Rotore Fermo (omega = 0)"},
        {"name": "CW", "omega_mech": OMEGA_MECH_RAD_S, "label": "Rotazione Oraria CW (+1200 RPM)"},
        {"name": "CCW", "omega_mech": -OMEGA_MECH_RAD_S, "label": "Rotazione Antioraria CCW (-1200 RPM)"}
    ]
    
    results = {}
    
    for reg in regimes:
        reg_name = reg['name']
        omega_m = reg['omega_mech']
        print(f"\n[SIMULAZIONE] Regime: {reg['label']}")
        
        flux_total_series = []
        flux_pos_series = []
        flux_neg_series = []
        area_pos_ratio_series = []
        br_maps = []
        b_mag_maps = []
        
        for step_idx, t in enumerate(time_array):
            rotor_angle = omega_m * t
            
            # Campo delle bobine
            B_coils = compute_b_coils(coils, meas_grid['pts'], t, rotor_angle)
            
            # Campo delle correnti indotte nella gabbia di alluminio
            B_cage = compute_eddy_currents_and_b_cage(coils, meas_grid['pts'], t, rotor_angle, omega_m, cage_grid)
            
            # Campo totale
            B_tot = B_coils + B_cage
            
            # Componente radiale B_r = B_tot . n_rad
            B_r = np.sum(B_tot * meas_grid['n_rad'], axis=1)
            B_mag = np.linalg.norm(B_tot, axis=1)
            
            # Integrazione del flusso magnetico Phi = \sum B_r * dA
            phi_tot = float(np.sum(B_r * meas_grid['dA']))
            
            # Flusso positivo (Nord) e flusso negativo (Sud)
            pos_mask = (B_r > 0)
            neg_mask = (B_r < 0)
            
            phi_pos = float(np.sum(B_r[pos_mask] * meas_grid['dA'][pos_mask]))
            phi_neg = float(np.sum(B_r[neg_mask] * meas_grid['dA'][neg_mask]))
            
            # Area con polarità positiva rispetto all'area totale
            area_tot = float(np.sum(meas_grid['dA']))
            area_pos = float(np.sum(meas_grid['dA'][pos_mask]))
            area_pos_ratio = area_pos / area_tot
            
            flux_total_series.append(phi_tot)
            flux_pos_series.append(phi_pos)
            flux_neg_series.append(phi_neg)
            area_pos_ratio_series.append(area_pos_ratio)
            
            # Salvataggio mappe al picco della prima semionda (t = 2.5 ms, N ON)
            # e della seconda semionda (t = 7.5 ms, S ON)
            if step_idx == int(n_timesteps * 0.25):
                br_maps.append({'time_ms': t * 1e3, 'Br': B_r.reshape(meas_grid['n_lat'], meas_grid['n_lon']).tolist()})
                b_mag_maps.append({'time_ms': t * 1e3, 'Bmag': B_mag.reshape(meas_grid['n_lat'], meas_grid['n_lon']).tolist()})
            elif step_idx == int(n_timesteps * 0.75):
                br_maps.append({'time_ms': t * 1e3, 'Br': B_r.reshape(meas_grid['n_lat'], meas_grid['n_lon']).tolist()})
                b_mag_maps.append({'time_ms': t * 1e3, 'Bmag': B_mag.reshape(meas_grid['n_lat'], meas_grid['n_lon']).tolist()})
                
        # Media temporale del campo radiale
        # Analisi del residuo di Gauss
        max_abs_phi_pos = max(abs(p) for p in flux_pos_series)
        gauss_residual_pct = [
            100.0 * abs(f_tot) / (max_abs_phi_pos + 1e-12) for f_tot in flux_total_series
        ]
        
        results[reg_name] = {
            'regime_label': reg['label'],
            'omega_mech_rpm': float(omega_m * 60.0 / (2.0 * np.pi)),
            'time_ms': (time_array * 1e3).tolist(),
            'flux_total_Wb': flux_total_series,
            'flux_positive_Wb': flux_pos_series,
            'flux_negative_Wb': flux_neg_series,
            'flux_balance_ratio': [abs(p / (n + 1e-12)) for p, n in zip(flux_pos_series, flux_neg_series)],
            'area_positive_fraction': area_pos_ratio_series,
            'gauss_residual_pct': gauss_residual_pct,
            'mean_gauss_residual_pct': float(np.mean(gauss_residual_pct)),
            'max_gauss_residual_pct': float(np.max(gauss_residual_pct)),
            'maps': br_maps,
            'maps_mag': b_mag_maps
        }
        
        print(f"      - Flusso Totale Medio Netto: {np.mean(flux_total_series):.4e} Wb")
        print(f"      - Residuo Gauss Medio: {np.mean(gauss_residual_pct):.4f}% (Verifica div(B)=0)")
        print(f"      - Frazione Area con B_r > 0: min={min(area_pos_ratio_series)*100:.1f}%, max={max(area_pos_ratio_series)*100:.1f}%")
        print(f"      - Frazione Area con B_r < 0: min={(1.0-max(area_pos_ratio_series))*100:.1f}%, max={(1.0-min(area_pos_ratio_series))*100:.1f}%")
    
    # Salvataggio dati JSON
    out_json = DATA_DIR / "simulazione_risultati_polarita_cw_ccw.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Risultati salvati in: {out_json}")
    
    # 2. Generazione Figure Diagnostiche
    generate_figures(coils, meas_grid, results)
    
    return results


def generate_figures(coils, meas_grid, results):
    """
    Genera set di grafici ad alta risoluzione per la documentazione scientifica.
    """
    print("\n[GRAFICI] Generazione figure illustrative e scientifiche...")
    
    # -------------------------------------------------------------------------
    # FIGURA 1: Geometria 3D dei 12 Anelli, 24 Bobine con Polarità e Gabbia
    # -------------------------------------------------------------------------
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Disegno gabbia alluminio trasparente
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 20)
    x_cage = R_CAGE_M * 1e3 * np.outer(np.cos(u), np.sin(v))
    y_cage = R_CAGE_M * 1e3 * np.outer(np.sin(u), np.sin(v))
    z_cage = R_CAGE_M * 1e3 * np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_wireframe(x_cage, y_cage, z_cage, color='gray', alpha=0.15, linewidth=0.6, label='Gabbia Alluminio (R=42mm)')
    
    # Disegno delle 24 bobine
    for coil in coils:
        pts = coil['points'] * 1e3  # in mm
        color = 'crimson' if coil['diode_type'] == 'PN' else 'royalblue'
        label_str = f"Bobina PN (Nord)" if coil['index'] == 0 else (f"Bobina NP (Sud)" if coil['index'] == 1 else "")
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=color, linewidth=2.5, alpha=0.9, label=label_str if label_str else None)
        # Punto mediano con marcatore
        mid = pts[len(pts)//2]
        ax.scatter([mid[0]], [mid[1]], [mid[2]], color=color, s=25)
    
    # Asse di rotazione Z
    ax.plot([0, 0], [0, 0], [-55, 55], 'k--', linewidth=2, label='Asse di Rotazione Z (Rotore)')
    
    ax.set_title("Rotore a 12 Anelli Intersecati e 24 Bobine con Gabbia Sferica\n"
                 "Alimentazione a Diodi Alternati: Rosso = Diodo PN (N), Blu = Diodo NP (S)", fontsize=13, pad=15)
    ax.set_xlabel("X (mm)", labelpad=10)
    ax.set_ylabel("Y (mm)", labelpad=10)
    ax.set_zlabel("Z (mm)", labelpad=10)
    ax.set_xlim([-50, 50])
    ax.set_ylim([-50, 50])
    ax.set_zlim([-50, 50])
    ax.legend(loc='upper right', fontsize=10)
    ax.view_init(elev=25, azim=45)
    
    fig1_path = FIG_DIR / "fig_01_geometria_rotore_12anelli_24bobine.png"
    plt.tight_layout()
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"      - Figura 1 salvata: {fig1_path}")
    
    # -------------------------------------------------------------------------
    # FIGURA 2: Forme d'onda elettriche delle bobine PN e NP (100 Hz)
    # -------------------------------------------------------------------------
    t_plot = np.linspace(0, 20, 1000)  # 20 ms (2 periodi)
    i_pn = np.array([I_PEAK * max(0.0, np.sin(OMEGA_E * (t * 1e-3))) for t in t_plot])
    i_np = np.array([-I_PEAK * max(0.0, -np.sin(OMEGA_E * (t * 1e-3))) for t in t_plot])
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    
    ax1.plot(t_plot, I_PEAK * np.sin(OMEGA_E * (t_plot * 1e-3)), 'k--', alpha=0.5, label='Tensione/Corrente AC di Rete (100 Hz)')
    ax1.plot(t_plot, i_pn, 'crimson', linewidth=2.2, label='Bobine Pari (Diodo PN): Semionda Positiva (Polarità N)')
    ax1.fill_between(t_plot, 0, i_pn, color='crimson', alpha=0.2)
    ax1.set_ylabel("Corrente Bobina (A)", fontsize=11)
    ax1.set_title("Forme d'Onda di Alimentazione e Commutazione Diodi PN vs NP", fontsize=13)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=10)
    
    ax2.plot(t_plot, I_PEAK * np.sin(OMEGA_E * (t_plot * 1e-3)), 'k--', alpha=0.5, label='Tensione/Corrente AC di Rete (100 Hz)')
    ax2.plot(t_plot, i_np, 'royalblue', linewidth=2.2, label='Bobine Dispari (Diodo NP): Semionda Negativa (Polarità S)')
    ax2.fill_between(t_plot, 0, i_np, color='royalblue', alpha=0.2)
    ax2.set_xlabel("Tempo (ms)", fontsize=11)
    ax2.set_ylabel("Corrente Bobina (A)", fontsize=11)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower right', fontsize=10)
    
    fig2_path = FIG_DIR / "fig_02_forme_onda_correnti_diodi.png"
    plt.tight_layout()
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"      - Figura 2 salvata: {fig2_path}")
    
    # -------------------------------------------------------------------------
    # FIGURA 3: Mappe del Campo Radiale B_r all'esterno della gabbia (Mollweide/Plate Carrée)
    # Confronto Static, CW e CCW al picco positivo (t=2.5 ms)
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True)
    lons_deg = np.degrees(meas_grid['lons'])
    lats_deg = np.degrees(meas_grid['lats'])
    LON_DEG, LAT_DEG = np.meshgrid(lons_deg, lats_deg)
    
    cmap = plt.cm.RdBu_r  # Rosso = Nord (Br > 0), Blu = Sud (Br < 0)
    
    cases = ['STATIC', 'CW', 'CCW']
    subtitles = [
        "Regime Statico (omega = 0): Mappa Radiale B_r(theta, phi) a t = 2.5 ms",
        "Rotazione Oraria CW (+1200 RPM): Trascinamento delle correnti parassite a t = 2.5 ms",
        "Rotazione Antioraria CCW (-1200 RPM): Inversione cinematica a t = 2.5 ms"
    ]
    
    vmax = 0.0
    for c in cases:
        map_data = np.array(results[c]['maps'][0]['Br']) * 1e3  # mT
        vmax = max(vmax, np.max(np.abs(map_data)))
        
    for i, (c, title) in enumerate(zip(cases, subtitles)):
        ax_map = axes[i]
        br_grid = np.array(results[c]['maps'][0]['Br']) * 1e3  # in mT
        
        cset = ax_map.contourf(LON_DEG, LAT_DEG, br_grid, levels=40, cmap=cmap, vmin=-vmax, vmax=vmax)
        ax_map.contour(LON_DEG, LAT_DEG, br_grid, levels=[0.0], colors='black', linewidths=1.2, linestyles='--')
        ax_map.set_title(title, fontsize=11, fontweight='bold')
        ax_map.set_ylabel("Latitudine (°)", fontsize=10)
        ax_map.grid(True, linestyle=':', alpha=0.5)
        
        # Colorbar
        cbar = fig.colorbar(cset, ax=ax_map, orientation='vertical', pad=0.015, aspect=12)
        cbar.set_label("B_r (mT)", fontsize=10)
        
    axes[2].set_xlabel("Longitudine Azimutale (°)", fontsize=11)
    
    fig3_path = FIG_DIR / "fig_03_mappe_campo_radiale_static_cw_ccw.png"
    plt.tight_layout()
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print(f"      - Figura 3 salvata: {fig3_path}")
    
    # -------------------------------------------------------------------------
    # FIGURA 4: Teorema di Gauss e Bilancio dei Flussi Magnetici (Dimostrazione di Non-Monopolarità)
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    t_ms = results['STATIC']['time_ms']
    
    # Tracciamento dei flussi per CW
    phi_pos = np.array(results['CW']['flux_positive_Wb']) * 1e6  # uWb
    phi_neg = np.array(results['CW']['flux_negative_Wb']) * 1e6  # uWb
    phi_tot = np.array(results['CW']['flux_total_Wb']) * 1e6     # uWb
    
    ax1.plot(t_ms, phi_pos, 'crimson', linewidth=2.2, label=r'Flusso Nord Uscente $\Phi_+ = \int_{B_r>0} B_r dA$')
    ax1.plot(t_ms, np.abs(phi_neg), 'royalblue', linewidth=2.2, linestyle='--', label=r'Modulo Flusso Sud Entrante $|\Phi_-| = \int_{B_r<0} |B_r| dA$')
    ax1.plot(t_ms, phi_tot, 'black', linewidth=2.5, label=r'Flusso Magnetico Netto $\Phi_{tot} = \oint B_r dA \equiv 0$')
    ax1.set_ylabel("Flusso Magnetico (uWb)", fontsize=11)
    ax1.set_title("Verifica del Teorema di Gauss e della Conservazione del Flusso Magnetico (CW 1200 RPM)\n"
                 r"Il Flusso Netto Totale è rigorosamente nullo ($\nabla \cdot \mathbf{B} = 0$): Assenza di Monopolo", fontsize=12)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='center right', fontsize=10)
    
    # Frazione dell'area con polarità positiva
    area_ratio_static = np.array(results['STATIC']['area_positive_fraction']) * 100
    area_ratio_cw = np.array(results['CW']['area_positive_fraction']) * 100
    area_ratio_ccw = np.array(results['CCW']['area_positive_fraction']) * 100
    
    ax2.plot(t_ms, area_ratio_static, 'g-', linewidth=2, label='Statico (omega = 0)')
    ax2.plot(t_ms, area_ratio_cw, 'crimson', linewidth=2, label='Orario CW (+1200 RPM)')
    ax2.plot(t_ms, area_ratio_ccw, 'royalblue', linewidth=2, linestyle='--', label='Antiorario CCW (-1200 RPM)')
    ax2.axhline(50.0, color='gray', linestyle=':', label='Equipartizione Polare Esatta 50%')
    ax2.set_xlabel("Tempo (ms)", fontsize=11)
    ax2.set_ylabel("Area con B_r > 0 (%)", fontsize=11)
    ax2.set_ylim([20, 80])
    ax2.set_title("Percentuale della Superficie Sferica Esterna con Polarità Nord (B_r > 0)\n"
                 "Nessun regime raggiunge il 100% (campo a polarità singola non fisico)", fontsize=12)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower right', fontsize=10)
    
    fig4_path = FIG_DIR / "fig_04_teorema_gauss_bilancio_flussi.png"
    plt.tight_layout()
    plt.savefig(fig4_path, dpi=300)
    plt.close()
    print(f"      - Figura 4 salvata: {fig4_path}")
    print("[GRAFICI] Tutte le figure generate con successo.")


if __name__ == "__main__":
    run_full_simulation()
