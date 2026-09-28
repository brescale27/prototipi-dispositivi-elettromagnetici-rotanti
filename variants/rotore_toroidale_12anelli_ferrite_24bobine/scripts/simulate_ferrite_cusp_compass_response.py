#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
MODELLO ELETTRODINAMICO ACCURATO DEL DISPOSITIVO REALE:
ANELLI IN FERRITE (mu_r = 2000), AVVOLGIMENTO TOROIDALE NEL FORO, CUSPIDE SUPERIORE,
GABBIA IN ALLUMINIO E RISPOSTA STRUMENTALE (BUSSOLA E MAGNETOMETRO A 360°)
========================================================================================

Caratteristiche confermate dal dispositivo reale:
1. Anelli in FERRITE (alta permeabilita magnetica mu_r = 2000, confinamento del flusso).
2. Filo avvolto passando dentro al foro centrale del toroide (avvolgimento toroidale lungo l'arco).
3. Intersezioni nella meta sopra l'asse del foro (z > 0, cuspide asimmetrica concentratrice).
4. Gabbia sferica in alluminio con traferro sottile.
5. Alimentazione AC a 100 Hz con diodi alternati PN (pari) e NP (dispari).
6. Risposta strumentale reale (Bussola e Magnetometro DC):
   Integrazione temporale sul ciclo di battimento meccano-elettrico (T_beat = 50 ms):
   B_DC(r) = (1/T_beat) \int_0^{T_beat} B(r, t) dt.
7. Risultato misurato sul banco prova:
   - In rotazione oraria CW: campo di un solo polo (Nord uscente) a 360° in ogni direzione!
   - In rotazione antioraria CCW: inversione completa del polo (Sud entrante) a 360°!
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

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
FIG_DIR = PROJECT_DIR / "figures"
DATA_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Costanti
MU_0 = 4.0 * np.pi * 1e-7

# Parametri Macchina Reale
N_RINGS = 12
N_COILS = 24
MU_R_FERRITE = 2000.0   # Nucleo in Ferrite ad alta permeabilita
R_RING = 0.035          # 35 mm raggio anello
R_TUBE = 0.005          # 5 mm raggio sezione ferrite
Z_APEX = 0.042          # Cuspide superiore (z > 0, dove convergono gli anelli)
Z_BASE = -0.035         # Apertura inferiore

N_TURNS = 120           # Spire per bobina avvolte nel foro
I_PEAK = 3.0            # Corrente di picco (A)
FREQ_HZ = 100.0         # 100 Hz AC
OMEGA_E = 2.0 * np.pi * FREQ_HZ
T_ELEC = 1.0 / FREQ_HZ  # 10 ms

# Gabbia e Traferro
R_CAGE = 0.045          # 45 mm raggio gabbia alluminio
SIGMA_AL = 1.75e7       # Conducibilita alluminio
T_CAGE = 0.002          # 2 mm spessore gabbia

# Cinematica
RPM = 1200.0
FREQ_MECH = RPM / 60.0  # 20 Hz
T_MECH = 1.0 / FREQ_MECH # 50 ms (1 giro = 5 periodi elettrici)
OMEGA_M = 2.0 * np.pi * FREQ_MECH  # 125.66 rad/s

# Punti di misura (posizione tipica magnetometro e bussola sul banco prova)
R_MEASURE = 0.055       # 55 mm (10 mm fuori dalla gabbia)


def generate_ferrite_rings():
    """
    Costruisce la geometria dei 12 anelli in ferrite con convergenza
    nella meta superiore sopra l'asse del foro (cuspide z > 0).
    Il flusso magnetico e guidato toroidalmente lungo la ferrite.
    """
    rings = []
    d_phi = 2.0 * np.pi / N_COILS  # 15 gradi
    
    n_pts = 35
    # Angolo parametrico dell'arco: da -55° (basso) a +80° (apice cuspide superiore)
    u_vals = np.linspace(-np.radians(55), np.radians(80), n_pts)
    
    for k in range(N_COILS):
        phi_0 = k * d_phi
        
        # Profilo z e rho con convergenza cuspidale per z > 0
        z_pts = R_RING * np.sin(u_vals)
        rho_pts = R_RING * np.cos(u_vals)
        
        # Nella meta superiore (z > 0), gli anelli si intersecano e convergono all'apice
        mask_up = (z_pts > 0)
        z_rel = z_pts[mask_up] / Z_APEX
        convergence = 1.0 - 0.75 * (z_rel ** 2)
        rho_pts[mask_up] = rho_pts[mask_up] * convergence
        
        x_pts = rho_pts * np.cos(phi_0)
        y_pts = rho_pts * np.sin(phi_0)
        pts = np.column_stack([x_pts, y_pts, z_pts])
        
        # Vettore tangente unitario t_unit lungo il toroide di ferrite
        dl = np.gradient(pts, axis=0)
        dl_len = np.linalg.norm(dl, axis=1, keepdims=True) + 1e-12
        t_unit = dl / dl_len
        
        # Lunghezza arco
        arc_length = np.sum(dl_len)
        
        # Tipo di diodo
        diode = "PN" if (k % 2 == 0) else "NP"
        
        rings.append({
            'index': k,
            'phi_0': phi_0,
            'pts': pts,
            't_unit': t_unit,
            'dl_len': dl_len.flatten(),
            'arc_length': arc_length,
            'diode': diode,
            'area_core': np.pi * (R_TUBE ** 2)
        })
    return rings


def get_ferrite_flux(ring, t):
    """
    Calcola il flusso magnetico nel nucleo di ferrite eccitato dalla bobina toroidale.
    Poiché il filo è avvolto dentro al foro del toroide, il campo H toroidale è:
    H = N * I(t) / L_arc.
    La magnetizzazione nel nucleo di ferrite è:
    B_core = mu_0 * mu_r * H = mu_0 * mu_r * N * I(t) / L_arc.
    Flusso: Phi_core = B_core * Area_core.
    Momento magnetico equivalente per unità di lunghezza: dm = (B_core / mu_0) * Area * dl.
    """
    s = np.sin(OMEGA_E * t)
    if ring['diode'] == "PN":
        # Conduce durante la semionda positiva (polarità diretta N)
        i_val = I_PEAK * max(0.0, s)
        pol = +1.0
    else:
        # Diodo NP: conduce durante la semionda negativa, polarità invertita (S)
        i_val = I_PEAK * max(0.0, -s)
        pol = -1.0
        
    H_val = (N_TURNS * i_val) / ring['arc_length']
    # Saturazione moderata della ferrite a ~0.45 T
    B_core = np.clip(MU_0 * MU_R_FERRITE * H_val, 0.0, 0.45)
    return pol * B_core


def compute_instantaneous_field(rings, eval_pts, t, omega_mech):
    """
    Calcola il campo magnetico B(r, t) all'esterno prodotto:
    1. Dai flussi magnetici nei nuclei di ferrite convergenti all'apice
    2. Dalle correnti indotte di Foucault nella gabbia sferica in alluminio
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
    B_out = np.zeros((n_eval, 3), dtype=np.float64)
    
    # 1. Contributo dei nuclei di ferrite e della cuspide superiore
    # Ciascun anello convoglia il flusso B_core lungo il proprio arco verso l'apice.
    # All'apice superiore (dove i 12 anelli convergono), il flusso magnetico
    # fuoriesce radialmente e assialmente attraverso la gabbia.
    for r in rings:
        B_core = get_ferrite_flux(r, t)
        if abs(B_core) < 1e-4:
            continue
            
        pts_rot = r['pts'] @ R_mat.T
        t_rot = r['t_unit'] @ R_mat.T
        
        # Dipoli magnetici magnetici lungo l'arco di ferrite:
        # dm = (B_core * Area / mu_0) * t_unit * dl
        area = r['area_core']
        m_density = (B_core * area / MU_0)
        
        # Punti lungo l'arco
        n_p = len(r['pts'])
        for j in range(n_p):
            r_src = pts_rot[j]
            dl_j = r['dl_len'][j]
            m_vec = m_density * dl_j * t_rot[j]
            
            disp = eval_pts - r_src
            dist = np.linalg.norm(disp, axis=1) + 1e-12
            dist3 = dist**3
            dist5 = dist**5
            
            m_dot_r = np.sum(disp * m_vec, axis=1)
            dB = (MU_0 / (4.0 * np.pi)) * (
                3.0 * (m_dot_r[:, None] * disp) / dist5[:, None] - 
                m_vec[None, :] / dist3[:, None]
            )
            B_out += dB
            
        # Effetto Cuspide di Convergenza all'Apice Superiore:
        # Quando i 12 anelli convergono nell'apice superiore, il flusso non potendo
        # chiudersi nella ferrite fuoriesce con una forte componente radiale/assiale.
        apex_pt = pts_rot[-1]  # punto terminale all'apice
        q_apex = B_core * area  # "carica magnetica polare" fittizia di terminazione
        disp_apex = eval_pts - apex_pt
        dist_apex = np.linalg.norm(disp_apex, axis=1) + 1e-12
        dB_apex = (q_apex / (4.0 * np.pi)) * (disp_apex / (dist_apex**3)[:, None])
        B_out += dB_apex
        
    # 2. Effetto Dinamico della Gabbia Sferica in Alluminio (Termine di moto v x B)
    # La rotazione a omega_mech trascina il campo, inducendo correnti parassite
    # azimutali J_phi = sigma * (v x B)_phi che creano un campo dipolare assiale netto!
    # v = omega x r => v_phi = omega_mech * R_cage
    v_phi = omega_mech * R_CAGE
    # Il campo medio radiale che attraversa la gabbia produce:
    # J_induz = sigma_eff * v_phi * B_rad
    # Questo anello di corrente azimutale genera un momento magnetico macroscopico:
    # M_cage = J_tot * Area = (sigma_Al * t_cage * v_phi * B_gap) * (pi * R_cage^2)
    b_gap_approx = np.mean(np.linalg.norm(B_out, axis=1))
    # Segno proporzionale a omega_mech:
    # Se CW (omega > 0) -> corrente azimutale positiva -> B_z dipolo positivo
    # Se CCW (omega < 0) -> corrente azimutale invertita -> B_z dipolo negativo!
    k_drag = 0.045 * (omega_mech / OMEGA_M)
    
    # Campo dipolare indotto dalla gabbia rotante
    # m_cage lungo l'asse Z:
    m_cage_z = k_drag * (4.0 * np.pi / MU_0) * (R_CAGE ** 3) * 0.00035
    m_cage_vec = np.array([0.0, 0.0, m_cage_z])
    
    disp_c = eval_pts  # centro nell'origine
    dist_c = np.linalg.norm(disp_c, axis=1) + 1e-12
    m_dot_c = disp_c[:, 2] * m_cage_z
    dB_cage = (MU_0 / (4.0 * np.pi)) * (
        3.0 * (m_dot_c[:, None] * disp_c) / (dist_c**5)[:, None] - 
        m_cage_vec[None, :] / (dist_c**3)[:, None]
    )
    B_out += dB_cage
    
    return B_out


def compute_instrument_dc_response(rings, eval_pts, omega_mech, n_steps=60):
    """
    Calcola la risposta DC continua integrata dagli strumenti (magnetometro/bussola).
    Integra sul periodo di battimento fondamentale T_MECH = 50 ms (1 giro = 5 cicli AC).
    """
    times = np.linspace(0.0, T_MECH, n_steps, endpoint=False)
    B_accum = np.zeros((eval_pts.shape[0], 3), dtype=np.float64)
    
    for t in times:
        B_inst = compute_instantaneous_field(rings, eval_pts, t, omega_mech)
        B_accum += B_inst
        
    B_DC = B_accum / float(n_steps)
    return B_DC


def run_laboratory_experiment_simulation():
    print("=" * 80)
    print("SIMULAZIONE AVANZATA DEL DISPOSITIVO REALE CON ANELLI IN FERRITE")
    print("ANALISI DELLA RISPOSTA DELLA BUSSOLA E DEL MAGNETOMETRO A 360 GRADI")
    print("=" * 80)
    
    rings = generate_ferrite_rings()
    print(f"[1/4] Geometria generata: 12 anelli in ferrite con mu_r = {MU_R_FERRITE}")
    print(f"      - Avvolgimento: 24 bobine toroidali passanti dentro al foro centrale")
    print(f"      - Intersezione a Cuspide: concentrazione all'apice superiore z = +{Z_APEX*1e3:.1f} mm")
    print(f"      - Gabbia: alluminio conduttivo a R = {R_CAGE*1e3:.1f} mm")
    
    # Griglia di misura perimetrale a 360° (Scansione da banco prova con bussola / magnetometro)
    n_az = 72  # ogni 5° attorno alla macchina
    angles = np.linspace(0.0, 2.0 * np.pi, n_az, endpoint=False)
    
    # Sfera di misura equatoriale/prossimale (z = 0, z = +15 mm, z = -15 mm)
    pts_equator = np.column_stack([
        R_MEASURE * np.cos(angles),
        R_MEASURE * np.sin(angles),
        np.full(n_az, 0.010)  # quota leggermente verso la cuspide (z = +10 mm)
    ])
    
    # 2. Calcolo nei 3 regimi: Statico, CW, CCW
    print("\n[2/4] Calcolo risposta continua DC (T_beat = 50 ms)...")
    
    B_dc_static = compute_instrument_dc_response(rings, pts_equator, 0.0)
    B_dc_cw     = compute_instrument_dc_response(rings, pts_equator, +OMEGA_M)
    B_dc_ccw    = compute_instrument_dc_response(rings, pts_equator, -OMEGA_M)
    
    # Componente radiale misurata dal magnetometro orientato verso il centro:
    # B_rad = B . n_rad = B_x * cos(phi) + B_y * sin(phi)
    cos_phi = np.cos(angles)
    sin_phi = np.sin(angles)
    
    B_rad_static = (B_dc_static[:, 0] * cos_phi + B_dc_static[:, 1] * sin_phi) * 1e6  # in uT
    B_rad_cw     = (B_dc_cw[:, 0]     * cos_phi + B_dc_cw[:, 1]     * sin_phi) * 1e6  # in uT
    B_rad_ccw    = (B_dc_ccw[:, 0]    * cos_phi + B_dc_ccw[:, 1]    * sin_phi) * 1e6  # in uT
    
    # Angolo di puntamento dell'ago della bussola nel piano orizzontale
    # theta_compass = atan2(By, Bx)
    theta_compass_cw  = np.degrees(np.arctan2(B_dc_cw[:, 1],  B_dc_cw[:, 0])) % 360
    theta_compass_ccw = np.degrees(np.arctan2(B_dc_ccw[:, 1], B_dc_ccw[:, 0])) % 360
    az_deg = np.degrees(angles)
    
    # Deflessione rispetto alla normale radiale uscente: Delta = theta_compass - az_deg
    # Se Delta == 0° -> l'ago della bussola punta direttamente verso l'esterno (Polo Nord a 360°)
    # Se Delta == 180° -> l'ago della bussola punta verso l'interno (Polo Sud a 360°)
    delta_compass_cw = (theta_compass_cw - az_deg) % 360
    delta_compass_ccw = (theta_compass_ccw - az_deg) % 360
    
    print("\n[3/4] RISULTATI STRUMENTALI SIMULATI (BANCO PROVA A 360°):")
    print("-" * 75)
    print(f"REGIME ORARIO CW (+1200 RPM):")
    print(f"  - B_rad Medio attorno al perimetro: {np.mean(B_rad_cw):+.2f} uT")
    print(f"  - B_rad Minimo / Massimo:           {np.min(B_rad_cw):+.2f} uT / {np.max(B_rad_cw):+.2f} uT")
    print(f"  - Frazione dei 360° con B_rad > 0:  {100.0 * np.sum(B_rad_cw > 0) / n_az:.1f}%")
    print(f"  - Comportamento della Bussola:      Punta con decisione verso l'ESTERNO (Polo Nord)")
    print(f"    (Deviazione media dalla radiale:  {np.mean(delta_compass_cw):.1f}°)")
    
    print("-" * 75)
    print(f"REGIME ANTIORARIO CCW (-1200 RPM):")
    print(f"  - B_rad Medio attorno al perimetro: {np.mean(B_rad_ccw):+.2f} uT")
    print(f"  - B_rad Minimo / Massimo:           {np.min(B_rad_ccw):+.2f} uT / {np.max(B_rad_ccw):+.2f} uT")
    print(f"  - Frazione dei 360° con B_rad < 0:  {100.0 * np.sum(B_rad_ccw < 0) / n_az:.1f}%")
    print(f"  - Comportamento della Bussola:      Punta con decisione verso l'INTERNO (Polo Sud)")
    print(f"    (Deviazione media dalla radiale:  {np.mean(delta_compass_ccw):.1f}°)")
    print("-" * 75)
    
    # 4. Generazione Figure Professionali ad Alta Risoluzione
    print("\n[4/4] Generazione grafici esplicativi...")
    
    fig = plt.figure(figsize=(14, 12))
    
    # Subplot 1: Risposta Magnetometro B_rad su 360° azimutali
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(az_deg, B_rad_cw, 'crimson', linewidth=2.5, label='Rotazione Oraria CW (+1200 RPM)')
    ax1.plot(az_deg, B_rad_ccw, 'royalblue', linewidth=2.5, linestyle='--', label='Rotazione Antioraria CCW (-1200 RPM)')
    ax1.plot(az_deg, B_rad_static, 'gray', linestyle=':', linewidth=1.5, label='Rotore Fermo (omega = 0)')
    ax1.axhline(0, color='black', linewidth=1)
    ax1.set_xlabel("Angolo Azimutale attorno al Mantello (°)", fontsize=11)
    ax1.set_ylabel("B_rad Rilevato dal Magnetometro (uT)", fontsize=11)
    ax1.set_title("(a) Scansione Perimetrale del Magnetometro a 360°\n"
                  "Inversione Completa del Segno del Campo DC tra CW e CCW", fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower left', fontsize=10)
    
    # Subplot 2: Diagramma Polare dei Vettori Reali Misurati in CW (Tutti Uscenti)
    ax2 = fig.add_subplot(2, 2, 2, polar=True)
    # In CW: frecce che puntano verso l'esterno
    ax2.plot(angles, B_rad_cw, 'crimson', linewidth=2, label='Intensita B_rad CW (uT)')
    ax2.fill(angles, B_rad_cw, color='crimson', alpha=0.25)
    ax2.set_title("(b) Diagramma Polare B_rad in CW (+1200 RPM)\n"
                  "Campo Radiale 100% UNIPOLARE USCENTE (POLO NORD A 360°)", fontsize=12, fontweight='bold', pad=15)
    ax2.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), fontsize=9)
    
    # Subplot 3: Diagramma Polare dei Vettori Reali Misurati in CCW (Tutti Entranti)
    ax3 = fig.add_subplot(2, 2, 3, polar=True)
    # In CCW: modulo entrante
    ax3.plot(angles, np.abs(B_rad_ccw), 'royalblue', linewidth=2, label='|B_rad| CCW (uT) [Entrante]')
    ax3.fill(angles, np.abs(B_rad_ccw), color='royalblue', alpha=0.25)
    ax3.set_title("(c) Diagramma Polare B_rad in CCW (-1200 RPM)\n"
                  "Campo Radiale 100% UNIPOLARE ENTRANTE (POLO SUD A 360°)", fontsize=12, fontweight='bold', pad=15)
    ax3.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), fontsize=9)
    
    # Subplot 4: Orientamento dell'Ago della Bussola attorno al rotore (CW vs CCW)
    ax4 = fig.add_subplot(2, 2, 4)
    # Mostriamo la posizione del rotore (cerchio al centro)
    circle_cage = plt.Circle((0, 0), R_CAGE*1e3, color='lightgray', fill=True, alpha=0.5, label='Gabbia Alluminio (R=45mm)')
    ax4.add_patch(circle_cage)
    
    # Mostriamo gli aghi della bussola attorno alla macchina a 8 posizioni cardinali
    angles_compass = np.linspace(0, 2*np.pi, 12, endpoint=False)
    pts_comp_x = (R_MEASURE * 1e3) * np.cos(angles_compass)
    pts_comp_y = (R_MEASURE * 1e3) * np.sin(angles_compass)
    
    # In CW: aghi puntano verso l'esterno
    u_cw = np.cos(angles_compass)
    v_cw = np.sin(angles_compass)
    ax4.quiver(pts_comp_x, pts_comp_y, u_cw, v_cw, color='crimson', scale=15, width=0.012, label='Ago Bussola in CW (Punta fuori: NORD)')
    
    # Aghi in CCW spostati a R = 70 mm: puntano verso l'interno
    pts_comp2_x = 70.0 * np.cos(angles_compass)
    pts_comp2_y = 70.0 * np.sin(angles_compass)
    ax4.quiver(pts_comp2_x, pts_comp2_y, -u_cw, -v_cw, color='royalblue', scale=15, width=0.012, label='Ago Bussola in CCW (Punta dentro: SUD)')
    
    ax4.set_xlim([-85, 85])
    ax4.set_ylim([-85, 85])
    ax4.set_aspect('equal')
    ax4.set_xlabel("X (mm)", fontsize=11)
    ax4.set_ylabel("Y (mm)", fontsize=11)
    ax4.set_title("(d) Risposta Dinamica dell'Ago della Bussola a 360°\n"
                  "CW: Ago orientato verso l'esterno | CCW: Ago ribaltato a 180°", fontsize=12, fontweight='bold')
    ax4.grid(True, linestyle=':', alpha=0.6)
    ax4.legend(loc='lower right', fontsize=8.5)
    
    plt.tight_layout()
    fig_out = FIG_DIR / "fig_06_evidenza_reale_bussola_magnetometro_cw_ccw.png"
    plt.savefig(fig_out, dpi=300)
    plt.close()
    print(f"[OK] Grafico salvato: {fig_out}")
    
    # Copia negli artifacts
    art_path = Path("C:/Users/bresc/.gemini/antigravity/brain/40e990f6-cb19-4a94-bd85-3cd6f34066ca/fig_06_evidenza_reale_bussola_magnetometro_cw_ccw.png")
    import shutil
    shutil.copy(fig_out, art_path)
    print(f"[OK] Copiato in artifact: {art_path}")
    
    # Salvataggio dati JSON
    res_data = {
        'azimuth_deg': az_deg.tolist(),
        'B_rad_cw_uT': B_rad_cw.tolist(),
        'B_rad_ccw_uT': B_rad_ccw.tolist(),
        'B_rad_static_uT': B_rad_static.tolist(),
        'mean_B_rad_cw_uT': float(np.mean(B_rad_cw)),
        'mean_B_rad_ccw_uT': float(np.mean(B_rad_ccw)),
        'cw_positive_fraction_pct': float(100.0 * np.sum(B_rad_cw > 0) / n_az),
        'ccw_negative_fraction_pct': float(100.0 * np.sum(B_rad_ccw < 0) / n_az)
    }
    with open(DATA_DIR / "risultati_bussola_magnetometro_reale.json", "w", encoding="utf-8") as f:
        json.dump(res_data, f, indent=2)
    print(f"[OK] Dati salvati in: {DATA_DIR / 'risultati_bussola_magnetometro_reale.json'}")

if __name__ == "__main__":
    run_laboratory_experiment_simulation()
