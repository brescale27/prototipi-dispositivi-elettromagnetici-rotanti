"""Open-circuit limits: no conduction current and illustrative rotating charge pair.

The charge parameter is NOT inferred from a voltage or from the real machine.
No circuit closure, leakage, displacement-current or conductor polarization solver.
"""
import argparse
import json
from pathlib import Path
import numpy as np

K_E = 8.9875517923e9
K_B = 1e-7


def sample_grid():
    cz=1-2*(np.arange(12)+.5)/12
    az=2*np.pi*(np.arange(24)+.5)/24
    unit=np.array([[np.sqrt(1-c*c)*np.cos(p),np.sqrt(1-c*c)*np.sin(p),c]
                   for c in cz for p in az])
    return unit,np.repeat(np.arccos(cz),24),np.tile(az,12)


def charge_field(points,t,rpm,q_coulomb,layout):
    # Illustrative locations: neighboring meridian coil midpoints at equal radius.
    # These are point-charge limiting sources, not solved conductor charge densities.
    a=2*np.pi*(rpm/60)*t
    E=np.zeros_like(points);B=np.zeros_like(points)
    sources=([(q_coulomb,a),(-q_coulomb,a+np.deg2rad(15))]
             if layout=='pair' else
             [(q_coulomb*(-1)**k,a+np.deg2rad(15*k)) for k in range(24)])
    for charge,phi in sources:
        pos=.035*np.array([np.cos(phi),np.sin(phi),0.])
        vel=(2*np.pi*rpm/60)*np.array([-pos[1],pos[0],0.])
        delta=points-pos
        inv_r3=np.linalg.norm(delta,axis=1)**-3
        E+=K_E*charge*delta*inv_r3[:,None]
        B+=K_B*charge*np.cross(vel,delta)*inv_r3[:,None]
    return E,B


def run(path,q_nc=1.,steps=160,layout='pair'):
    unit,polar,az=sample_grid()
    out={'model':'open conductor path; illustrative fixed rotating charges, not inferred from connected wires',
         'charge_layout':layout,
         'charge_each_nC':q_nc,'sample_directions':288,'time_steps':steps,
         'polar_rad':polar.tolist(),'azimuth_rad':az.tolist(),'states':{}}
    for state,rpm in [('static',0),('cw',1200),('ccw',-1200)]:
        out['states'][state]={}
        for radius in [.055,.07,.1]:
            pts=unit*radius
            e=np.zeros_like(pts);b=np.zeros_like(pts)
            b2=np.zeros(len(pts));e2=np.zeros(len(pts));peak_b=0.
            for t in np.arange(steps)*(.05/steps):
                et,bt=charge_field(pts,t,rpm,q_nc*1e-9,layout)
                e+=et/steps;b+=bt/steps
                b2+=np.sum(bt*bt,axis=1)/steps
                e2+=np.sum(et*et,axis=1)/steps
                peak_b=max(peak_b,float(np.linalg.norm(bt,axis=1).max()))
            br=np.einsum('ij,ij->i',b,unit)
            horizontal=np.linalg.norm(b[:,:2],axis=1)
            headings=np.rad2deg(np.arctan2(b[:,1],b[:,0]))%360
            # Below 1 nT, headings have no practical compass interpretation.
            compass=[float(h) if mag>=1e-9 else None for h,mag in zip(headings,horizontal)]
            out['states'][state][str(radius)]={
                'E_xyz_V_m':e.tolist(),'B_xyz_T':b.tolist(),'B_radial_T':br.tolist(),
                'compass_heading_deg':compass,
                'flux_Wb':float(4*np.pi*radius**2*np.mean(br)),
                'radial_min_pT':float(br.min()*1e12),
                'radial_max_pT':float(br.max()*1e12),
                'B_max_pT':float(np.linalg.norm(b,axis=1).max()*1e12),
                'E_max_V_m':float(np.linalg.norm(e,axis=1).max()),
                'instantaneous_B_peak_pT':peak_b*1e12,
                'B_rms_pT':(np.sqrt(b2)*1e12).tolist(),
                'E_rms_V_m':np.sqrt(e2).tolist()}
            print(state,radius,'B radial pT',br.min()*1e12,br.max()*1e12,
                  'flux Wb',out['states'][state][str(radius)]['flux_Wb'],flush=True)
    Path(path).write_text(json.dumps(out,indent=2,allow_nan=False))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True)
    p.add_argument('--charge-nc',type=float,default=1.)
    p.add_argument('--steps',type=int,default=160)
    p.add_argument('--layout',choices=['pair','alternating24'],default='pair')
    args=p.parse_args()
    run(args.out,args.charge_nc,args.steps,args.layout)
