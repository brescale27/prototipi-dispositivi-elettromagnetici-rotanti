"""Closed-ring coil filament reference; no ferrite response or cage eddy currents.

Produces vector magnetometer samples on complete spheres and DC compass headings.
The stationary aluminum mesh is geometrically represented by its nominal outer radius;
its AC electromagnetic response requires a separate coupled solver.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.special import ellipk, ellipe

MU0 = 4 * np.pi * 1e-7
R_MAJOR = .035
R_WINDING = .005
R_CAGE_OUTER = .043
N_RINGS = 12
N_TURNS = 120
I_PEAK = 3.
F_ELEC = 100.
RPM = 1200.


def loop_field(points, center, axis, radius, current):
    """Biot-Savart field of a complete circular filament in an arbitrary plane."""
    delta = points - center
    z = delta @ axis
    radial = delta - z[:, None] * axis
    rho = np.linalg.norm(radial, axis=1)
    denom = (radius-rho)**2 + z*z
    outer = np.sqrt((radius+rho)**2 + z*z)
    m = np.clip(4*radius*rho / outer**2, 0, 1-1e-13)
    K, E = ellipk(m), ellipe(m)
    common = MU0*current/(2*np.pi*outer)
    bz = common*(K+(radius*radius-rho*rho-z*z)/denom*E)
    br = common*z/np.maximum(rho,1e-30)*(-K+(radius*radius+rho*rho+z*z)/denom*E)
    br = np.where(rho < 1e-12, 0., br)
    return bz[:,None]*axis + br[:,None]*radial/np.maximum(rho[:,None],1e-30)


def coils(turn_samples=12):
    """Twelve co-centered complete meridian rings, two wound free arcs per ring."""
    result=[]
    for ring in range(N_RINGS):
        phi=np.deg2rad(15*ring)
        e=np.array([np.cos(phi),np.sin(phi),0.])
        zhat=np.array([0.,0.,1.])
        for side,(lo,hi) in enumerate([(15.,165.),(195.,345.)]):
            # Each free arc lies between shared polar intersection zones.
            for udeg in lo+(np.arange(turn_samples)+.5)*(hi-lo)/turn_samples:
                u=np.deg2rad(udeg)
                center=R_MAJOR*(np.sin(u)*e+np.cos(u)*zhat)
                axis=np.cos(u)*e-np.sin(u)*zhat
                # Adjacent meridians and the two arcs of each ring have
                # opposing half-wave assignments.
                result.append((center,axis,(ring+side)%2,N_TURNS/turn_samples))
    return result


def field(points, t, rpm, source_loops):
    a=2*np.pi*(rpm/60)*t
    ca,sa=np.cos(a),np.sin(a)
    rot=np.array([[ca,-sa,0],[sa,ca,0],[0,0,1]])
    s=np.sin(2*np.pi*F_ELEC*t)
    currents=(I_PEAK*max(s,0),I_PEAK*min(s,0))
    b=np.zeros_like(points)
    for center,axis,parity,weight in source_loops:
        if currents[parity]:
            b+=loop_field(points,rot@center,rot@axis,R_WINDING,currents[parity]*weight)
    return b


def grid():
    # Equal-area midpoint points on closed measurement spheres.
    nlat,nlon=12,24
    cz=1-2*(np.arange(nlat)+.5)/nlat
    az=2*np.pi*(np.arange(nlon)+.5)/nlon
    unit=np.array([[np.sqrt(1-c*c)*np.cos(p),np.sqrt(1-c*c)*np.sin(p),c]
                   for c in cz for p in az])
    return unit,np.repeat(np.arccos(cz),nlon),np.tile(az,nlat)


def run(out, steps=20, turn_samples=12):
    unit,polar,az=grid()
    loops=coils(turn_samples)
    results={'model':'prescribed-current circular filament reference; no ferrite or aluminum mesh induction',
             'radii_m':[.055,.070,.100], 'polar_rad':polar.tolist(), 'azimuth_rad':az.tolist(),
             'time_steps':steps,'turn_quadrature_per_coil':turn_samples,'states':{}}
    for state,rpm in [('static',0.),('cw',RPM),('ccw',-RPM)]:
        results['states'][state]={}
        for radius in results['radii_m']:
            pts=unit*radius
            mean=np.zeros_like(pts)
            for t in np.arange(steps)*(.05/steps):
                mean+=field(pts,t,rpm,loops)/steps
            radial=np.einsum('ij,ij->i',mean,unit)
            horizontal=np.linalg.norm(mean[:,:2],axis=1)
            heading=np.rad2deg(np.arctan2(mean[:,1],mean[:,0]))%360
            heading=[float(h) if strength>1e-12 else None for h,strength in zip(heading,horizontal)]
            # A compass needs a known background field and instrument dynamics
            # for a physical prediction; this is the DC vector heading only.
            results['states'][state][str(radius)]={
                'B_xyz_T':mean.tolist(),'B_radial_T':radial.tolist(),
                'compass_heading_deg':heading,
                'flux_Wb':float(4*np.pi*radius**2*np.mean(radial)),
                'positive_radial_fraction':float(np.mean(radial>1e-12)),
                'negative_radial_fraction':float(np.mean(radial< -1e-12)),
                'radial_min_uT':float(radial.min()*1e6),
                'radial_max_uT':float(radial.max()*1e6),
                'max_B_uT':float(np.max(np.linalg.norm(mean,axis=1))*1e6)}
            print(state,radius,'flux',results['states'][state][str(radius)]['flux_Wb'],
                  'radial µT',results['states'][state][str(radius)]['radial_min_uT'],
                  results['states'][state][str(radius)]['radial_max_uT'],flush=True)
    Path(out).write_text(json.dumps(results,indent=2,allow_nan=False))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True)
    p.add_argument('--steps',type=int,default=20)
    p.add_argument('--turn-samples',type=int,default=12)
    args=p.parse_args()
    run(args.out,args.steps,args.turn_samples)
