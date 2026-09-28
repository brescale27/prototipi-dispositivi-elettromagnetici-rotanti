#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
MODELLO DI RISPOSTA STRUMENTALE E FISICA DEL DISPOSITIVO REALE
ROTORE A 12 ANELLI (CUSPIDE ASIMMETRICA SUPERIORE) E 24 BOBINE CON DIODI PN/NP
INTEGRAZIONE TEMPORALE CONTINUA DC E INVERSIONE POLARE CON LA ROTAZIONE CW vs CCW
========================================================================================

Questo script simula fedelmente il comportamento osservato sul prototipo fisico di laboratorio:
1. Geometria reale a Cuspide Asimmetrica: i 12 anelli convergono e si intersecano
   nella metà superiore ("metà sopra l'asse del foro", z > 0, z_apice = +40 mm),
   mentre nella metà inferiore non vi è intersezione cuspidale ma apertura/ugello.
2. Avvolgimento toroidale con spire che passano attraverso il foro dell'anello:
   il flusso magnetico scorre lungo il circuito toroidale e viene espulso all'apice.
3. Risposta strumentale reale:
   I magnetometri da banco (sonde Hall DC o Fluxgate) e l'ago magnetico della bussola
   hanno una banda passante limitata (< 10-20 Hz) rispetto ai 100 Hz dell'alimentazione AC.
   Lo strumento integra il segnale ed estrae il CAMPO CONTINUO DC RESIDUO:
   B_DC(r) = (1/T) \int_0^T B(r, t) dt
4. Rottura di simmetria temporale dovuta all'avanzamento meccanico:
   Poiché a 1200 RPM il rotore avanza di 72° durante il periodo di 10 ms (36° per semionda),
   l'eccitazione a semionde con diodi PN (positiva) e NP (negativa) su bobine fisiche fisse
   sul rotore genera un MOMENTO DIPOLARE DC NETTO:
   - In rotazione oraria CW: B_DC genera polarità netta all'esterno della gabbia
   - In rotazione antioraria CCW: la polarità del campo DC esterno SI INVERTE COMPATTIAMENTE!
5. Dislocamento assiale del flusso di ritorno:
   Il flusso uscente concentrato sul perimetro/apice sovrasta la sensibilità della sonda,
   mentre il ritorno è diffuso e incanalato assialmente nell'ugello inferiore,
   spiegando l'anomalia di "singola polarità" rilevata strumentalmente a 360°.
========================================================================================
"""

import os
import sys
import json
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
FIG_DIR = PROJECT_DIR / "figures"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

MU_0 = 4.0 * np.pi * 1e-7

# Parametri geometrici reali
N_RINGS = 12
N_COILS = 24
R_RING = 0.035       # 35 mm
R_TUBE = 0.004      # 4 mm
Z_APEX = 0.042      # 42 mm cuspide superiore (apice dove gli anelli convergono)
Z_BOTTOM = -0.035   # -35 mm apertura inferiore

# Parametri elettrici
FREQ_HZ = 100.0
OMEGA_E = 2.0 * np.pi * FREQ_HZ
T_PERIOD = 1.0 / FREQ_HZ  # 10 ms
I_PEAK = 3.0
N_TURNS = 120
R_SPIRA = 0.0048

# Gabbia e misura
R_CAGE = 0.045      # 45 mm
R_PROBE = 0.055     # 55 mm (10 mm fuori dalla gabbia, posizione tipica magnetometro)
RPM = 1200.0
OMEGA_M = 2.0 * np.pi * (RPM / 60.0)  # 125.66 rad/s


def build_asymmetric_rings_and_coils():
    """
    Costruisce la geometria asimmetrica a cuspide:
    I 12 anelli convergono nella metà sopra l'asse del foro (z > 0),
    toccandosi all'apice superiore (cuspide magnetica).
    """
    coils = []
    d_phi = 2.0 * np.pi / N_COILS  # 15 gradi
    
    # Per ciascuno dei 24 archi azimutali
    n_pts = 30
    # Latitudini asimmetriche: da -60° (ugello inferiore) a +80° (apice cuspide superiore)
    u_vals = np.linspace(-np.pi/3.0, np.pi/2.2, n_pts)
    
    for k in range(N_COILS):
        phi_0 = k * d_phi
        
        # Linea centrale dell'arco con deformazione verso l'apice superiore (cuspide kissing)
        # Raggio orizzontale r_xy si restringe all'apice (z > 0)
        # z si estende verso Z_APEX
        z_pts = R_RING * np.sin(u_vals)
        # Raggio orizzontale rho(z):
        # Per z > 0, gli anelli convergono verso l'asse Z (cuspide kissing all'apice)
        rho = R_RING * np.cos(u_vals)
        mask_upper = (z_pts > 0)
        # Fattore di convergenza verso l'apice
        convergence = 1.0 - 0.70 * (z_pts[mask_upper] / Z_APEX)**2
        rho[mask_upper] = rho[mask_upper] * convergence
        
        x_pts = rho * np.cos(phi_0)
        y_pts = rho * np.sin(phi_0)
        
        points = np.column_stack([x_pts, y_pts, z_pts])
        
        # Tangenti lungo l'arco (flusso magnetico guidato all'interno del circuito dell'anello)
        dl = np.gradient(points, axis=0)
        dl_norm = np.linalg.norm(dl, axis=1, keepdims=True) + 1e-12
        t_unit = dl / dl_norm
        
        # Diodo associato: pari = PN (conduce su semionda +), dispari = NP (conduce su semionda -)
        diode_type = "PN" if (k % 2 == 0) else "NP"
        
        coils.append({
            'index': k,
            'phi_0': phi_0,
            'points': points,
            't_unit': t_unit,
            'diode_type': diode_type,
            'area_spira': np.pi * (R_SPIRA**2),
            'turns': N_TURNS
        })
    return coils


def get_current(coil, t):
    s = np.sin(OMEGA_E * t)
    if coil['diode_type'] == "PN":
        return I_PEAK * max(0.0, s)
    else:
        # Diodo NP: conduce durante la semionda negativa, polarità invertita
        return -I_PEAK * max(0.0, -s)


def compute_instantaneous_b(coils, eval_pts, t, omega_mech):
    """
    Calcola il campo magnetico istantaneo B(eval_pts, t)
    con rotazione meccanica: phi(t) = phi_0 + omega_mech * t.
    """
    rotor_angle = omega_mech * t
    cos_a = np.cos(rotor_angle)
    sin_a = np.sin(rotor_angle)
    R_mat = np.array([
        [cos_a, -sin_a, 0.0],
        [sin_a,  cos_a, 0.0],
        [0.0,    0.0,   1.0]
    ])
    
    n_eval = eval_pts.shape[0]
    B_tot = np.zeros((n_eval, 3), dtype=np.float64)
    
    for coil in coils:
        i_curr = get_current(coil, t)
        if abs(i_curr) < 1e-6:
            continue
            
        pts_rot = coil['points'] @ R_mat.T
        t_rot = coil['t_unit'] @ R_mat.T
        
        n_pts = len(coil['points'])
        turns_per_pt = coil['turns'] / float(n_pts)
        dm_vec = turns_per_pt * i_curr * coil['area_spira'] * t_rot
        
        for pt_idx in range(n_pts):
            r_src = pts_rot[pt_idx]
            m_vec = dm_vec[pt_idx]
            
            disp = eval_pts - r_src
            dist = np.linalg.norm(disp, axis=1) + 1e-12
            dist3 = dist**3
            dist5 = dist**5
            
            m_dot_r = np.sum(disp * m_vec, axis=1)
            dB = (MU_0 / (4.0 * np.pi)) * (
                3.0 * (m_dot_r[:, None] * disp) / dist5[:, None] - 
                m_vec[None, :] / dist3[:, None]
            )
            B_tot += dB
            
    return B_tot


def compute_dc_time_average(coils, eval_pts, omega_mech, n_steps=40):
    """
    Esegue l'integrazione ciclica nel tempo su un periodo T per estrarre
    il campo continuo residuo DC: B_DC = (1/T) \int_0^T B(t) dt.
    Questo è ciò che lo strumento di laboratorio reale (magnetometro/bussola) misura!
    """
    time_array = np.linspace(0.0, T_PERIOD, n_steps, endpoint=False)
    B_accum = np.zeros((eval_pts.shape[0], 3), dtype=np.float64)
    
    for t in time_array:
        B_inst = compute_instantaneous_b(coils, eval_pts, t, omega_mech)
        B_accum += B_inst
        
    B_DC = B_accum / float(n_steps)
    return B_DC


def run_laboratory_response_analysis():
    print("=" * 80)
    print("MODELLO DI RISPOSTA STRUMENTALE REALE: INTEGRAZIONE CICLICA DC & INVERSIONE CW/CCW")
    print("=" * 80)
    
    coils = build_asymmetric_rings_and_coils()
    
    # 1. Punti di campionamento equatoriali (scansione perimetrale del banco prova a 360°)
    n_azimuth = 72  # ogni 5°
    azimuths = np.linspace(0.0, 2.0 * np.pi, n_azimuth, endpoint=False)
    eq_pts = np.column_stack([
        R_PROBE * np.cos(azimuths),
        R_PROBE * np.sin(azimuths),
        np.zeros(n_azimuth)  # z = 0 (equatore)
    ])
    
    # Punti di campionamento all'apice superiore (cuspide z = +48 mm)
    apex_pts = np.column_stack([
        0.015 * np.cos(azimuths),
        0.015 * np.sin(azimuths),
        np.full(n_azimuth, 0.048)
    ])
    
    # Punti all'ugello inferiore (z = -48 mm)
    bottom_pts = np.column_stack([
        0.015 * np.cos(azimuths),
        0.015 * np.sin(azimuths),
        np.full(n_azimuth, -0.048)
    ])
    
    # 2. Calcolo del campo DC per STATIC, CW e CCW
    cases = [
        {"key": "STATIC", "omega": 0.0, "label": "Rotore Fermo (omega = 0)"},
        {"key": "CW", "omega": OMEGA_M, "label": "Rotazione Oraria CW (+1200 RPM)"},
        {"key": "CCW", "omega": -OMEGA_M, "label": "Rotazione Antioraria CCW (-1200 RPM)"}
    ]
    
    results = {}
    
    for c in cases:
        k = c['key']
        om = c['omega']
        print(f"\n[CALCOLO DC] {c['label']}...")
        
        # Campo equatoriale
        B_dc_eq = compute_dc_time_average(coils, eq_pts, om)
        # Componente radiale all'equatore: B_rad = B_x cos(phi) + B_y sin(phi)
        B_rad_eq = B_dc_eq[:, 0] * np.cos(azimuths) + B_dc_eq[:, 1] * np.sin(azimuths)
        B_z_eq = B_dc_eq[:, 2]
        
        # Campo all'apice superiore (cuspide)
        B_dc_apex = compute_dc_time_average(coils, apex_pts, om)
        B_z_apex = B_dc_apex[:, 2]
        
        # Campo all'ugello inferiore
        B_dc_bottom = compute_dc_time_average(coils, bottom_pts, om)
        B_z_bottom = B_dc_bottom[:, 2]
        
        # Calcolo frazione dell'arco equatoriale con segno costante
        pos_fraction = np.sum(B_rad_eq > 0) / float(n_azimuth)
        
        results[k] = {
            'label': c['label'],
            'azimuth_deg': np.degrees(azimuths).tolist(),
            'B_rad_eq_uT': (B_rad_eq * 1e6).tolist(),
            'B_z_eq_uT': (B_z_eq * 1e6).tolist(),
            'mean_B_rad_eq_uT': float(np.mean(B_rad_eq) * 1e6),
            'mean_B_z_apex_uT': float(np.mean(B_z_apex) * 1e6),
            'mean_B_z_bottom_uT': float(np.mean(B_z_bottom) * 1e6),
            'pos_fraction_eq': float(pos_fraction)
        }
        
        print(f"      - B_rad Medio Equatore: {np.mean(B_rad_eq)*1e6:+.2f} uT")
        print(f"      - B_z Medio Apice Superiore (Cuspide): {np.mean(B_z_apex)*1e6:+.2f} uT")
        print(f"      - B_z Medio Ugello Inferiore: {np.mean(B_z_bottom)*1e6:+.2f} uT")
        print(f"      - Frazione Arco Equatoriale B_rad > 0: {pos_fraction*100:.1f}%")
        
    # Confronto diretto CW vs CCW
    cw_mean_apex = results['CW']['mean_B_z_apex_uT']
    ccw_mean_apex = results['CCW']['mean_B_z_apex_uT']
    print("\n" + "=" * 80)
    print("VERIFICA DI INVERSIONE POLARE CON LA ROTAZIONE (CW vs CCW):")
    print(f"  - Campo DC Apice CW  (+1200 RPM): {cw_mean_apex:+.2f} uT")
    print(f"  - Campo DC Apice CCW (-1200 RPM): {ccw_mean_apex:+.2f} uT")
    print("=" * 80)
    
    # Generazione Grafico
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    az_deg = results['STATIC']['azimuth_deg']
    
    # 1. Scansione Equatoriale B_rad
    ax1.plot(az_deg, results['STATIC']['B_rad_eq_uT'], 'gray', linestyle=':', linewidth=2, label='Statico (omega = 0)')
    ax1.plot(az_deg, results['CW']['B_rad_eq_uT'], 'crimson', linewidth=2.5, label='Rotazione Oraria CW (+1200 RPM)')
    ax1.plot(az_deg, results['CCW']['B_rad_eq_uT'], 'royalblue', linewidth=2.5, linestyle='--', label='Rotazione Antioraria CCW (-1200 RPM)')
    ax1.axhline(0, color='black', linewidth=0.8)
    ax1.set_ylabel("B_rad DC Equatoriale (uT)", fontsize=11)
    ax1.set_title("Scansione Strumentale da Banco Prova attorno al Perimetro (R = 55 mm)\n"
                  "Risposta DC Integrata del Magnetometro Triassiale sui 360° Azimutali", fontsize=12)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=10)
    
    # 2. Asimmetria Assiale Verticale e Inversione di Polarità
    categories = ['Ugello Inferiore (Z = -48 mm)', 'Equatore (Z = 0)', 'Apice Cuspide (Z = +48 mm)']
    x_idx = np.arange(len(categories))
    width = 0.28
    
    cw_vals = [results['CW']['mean_B_z_bottom_uT'], results['CW']['mean_B_rad_eq_uT'], results['CW']['mean_B_z_apex_uT']]
    ccw_vals = [results['CCW']['mean_B_z_bottom_uT'], results['CCW']['mean_B_rad_eq_uT'], results['CCW']['mean_B_z_apex_uT']]
    stat_vals = [results['STATIC']['mean_B_z_bottom_uT'], results['STATIC']['mean_B_rad_eq_uT'], results['STATIC']['mean_B_z_apex_uT']]
    
    ax2.bar(x_idx - width, stat_vals, width, label='Statico', color='gray', alpha=0.7)
    ax2.bar(x_idx, cw_vals, width, label='Orario CW (+1200 RPM)', color='crimson')
    ax2.bar(x_idx + width, ccw_vals, width, label='Antiorario CCW (-1200 RPM)', color='royalblue')
    
    ax2.set_xticks(x_idx)
    ax2.set_xticklabels(categories, fontsize=11)
    ax2.set_ylabel("Componente Dominante DC (uT)", fontsize=11)
    ax2.axhline(0, color='black', linewidth=0.8)
    ax2.set_title("Inversione di Segno del Campo Esterno all'Apice e all'Ugello dipendente dalla Rotazione (CW vs CCW)", fontsize=12)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower left', fontsize=10)
    
    fig_path = FIG_DIR / "fig_05_risposta_reale_dc_cw_ccw.png"
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"\n[GRAFICO] Figura salvata: {fig_path}")
    
    # Copia nella cartella artifacts
    artifact_dir = Path("C:/Users/bresc/.gemini/antigravity/brain/40e990f6-cb19-4a94-bd85-3cd6f34066ca")
    if artifact_dir.exists():
        import shutil
        shutil.copy(fig_path, artifact_dir / "fig_05_risposta_reale_dc_cw_ccw.png")
        print(f"[ARTIFACT] Copiata figura in: {artifact_dir / 'fig_05_risposta_reale_dc_cw_ccw.png'}")
        
    out_json = DATA_DIR / "risultati_risposta_reale_dc.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[DATI] Salvati in: {out_json}")


if __name__ == "__main__":
    run_laboratory_response_analysis()
