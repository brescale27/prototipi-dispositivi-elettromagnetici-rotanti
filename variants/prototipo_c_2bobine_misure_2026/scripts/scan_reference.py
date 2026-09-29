"""Parametric Maxwell/Biot-Savart reference for the measured C-rotor prototype.

Known: two vertical arms 100 mm high, 100 mm separation, common rotating base.
Unknown: turns, coil radii, drive, rpm, cage conductivity/mesh, scan distance.
Numbers are normalized reference outputs, not a calibrated reproduction.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.special import ellipk, ellipe

MU0=4*np.pi*1e-7


def loop_b(points,center,radius,amp_turn):
    d=points-center
    z=d[:,2]
    rho=np.linalg.norm(d[:,:2],axis=1)
    den=(radius-rho)**2+z*z
    outer=np.sqrt((radius+rho)**2+z*z)
    m=np.clip(4*radius*rho/outer**2,0,1-1e-13)
    k,e=ellipk(m),ellipe(m)
    fac=MU0*amp_turn/(2*np.pi*outer)
    bz=fac*(k+(radius*radius-rho*rho-z*z)/den*e)
    br=np.where(rho>1e-12,fac*z/np.maximum(rho,1e-30)*(-k+(radius*radius+rho*rho+z*z)/den*e),0)
    out=np.zeros_like(points)
    out[:,2]=bz
    out[:,:2]=br[:,None]*d[:,:2]/np.maximum(rho[:,None],1e-30)
    return out


def profile(cage_radius=.075,clearance=.01):
    # Illustrative U-shaped meridian trajectory. Labels and normals included.
    zlo,zhi=-clearance,.1+clearance
    rad=cage_radius+clearance
    lo=np.column_stack([np.linspace(0,rad,17),np.zeros(17),np.full(17,zlo)])
    side=np.column_stack([np.full(25,rad),np.zeros(25),np.linspace(zlo,zhi,25)])
    up=np.column_stack([np.linspace(rad,0,17),np.zeros(17),np.full(17,zhi)])
    pts=np.concatenate([lo,side[1:],up[1:]])
    n=np.zeros_like(pts)
    n[:17,2]=-1
    n[17:41,0]=1
    n[41:,2]=1
    labels=['below']*17+['side']*24+['above']*16
    return pts,n,labels


def calculate(rpm, coil_radius=.005,turns=120,peak_current=1.,nloops=24,steps=80,second_arm_scale=1.):
    pts,n,labels=profile()
    out=np.zeros_like(pts)
    for t in np.arange(steps)*(.05/steps):
        a=2*np.pi*rpm/60*t
        s=np.sin(2*np.pi*100*t)
        currents=[peak_current*max(s,0),peak_current*min(s,0)]
        for arm,side in enumerate([1,-1]):
            xy=side*.05*np.array([np.cos(a),np.sin(a)])
            for z in (np.arange(nloops)+.5)*(.1/nloops):
                center=np.array([xy[0],xy[1],z])
                out+=loop_b(pts,center,coil_radius,currents[arm]*turns/nloops*(second_arm_scale if arm else 1.))/steps
    bn=np.einsum('ij,ij->i',out,n)
    return {'rpm':rpm,'point_xyz_m':pts.tolist(),'normal_xyz':n.tolist(),
            'region':labels,'B_device_xyz_T':out.tolist(),
            'B_normal_T':bn.tolist(),
            'min_B_normal_uT':float(bn.min()*1e6),
            'max_B_normal_uT':float(bn.max()*1e6),
            'positive_fraction':float(np.mean(bn>1e-12)),
            'negative_fraction':float(np.mean(bn< -1e-12))}


def main(path):
    data={'assumptions':{'arms_height_m':.1,'separation_m':.1,
           'illustrative_coil_radius_m':.005,'illustrative_turns':120,
           'current_peak_A_for_normalization':1.,'frequency_hz':100,
           'illustrative_cage_radius_m':.075,'scan_clearance_m':.01,
           'note':'no cage induction, core material, lead wires, Earth field or measured sensor pose'},
          'states':{}}
    for name,rpm,scale in [('stationary',0,1.),('cw_illustrative',1200,1.),('ccw_illustrative',-1200,1.),
                           ('cw_20pct_asymmetry',1200,.8),('ccw_20pct_asymmetry',-1200,.8)]:
        data['states'][name]=calculate(rpm,second_arm_scale=scale)
        data['states'][name]['second_arm_scale']=scale
        print(name,data['states'][name]['min_B_normal_uT'],
              data['states'][name]['max_B_normal_uT'])
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True)
    main(p.parse_args().out)
