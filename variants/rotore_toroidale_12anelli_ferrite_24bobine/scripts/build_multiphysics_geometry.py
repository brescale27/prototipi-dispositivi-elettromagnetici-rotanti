"""Gmsh OCC geometry scaffold for the complete rotating ring assembly.

Requires `gmsh` Python bindings. This creates physical volumes but is not an
Elmer input or a solved electromagnetic case. The cage is a homogenized shell;
explicit woven wires and coil conductor volumes are outstanding.
"""
import argparse
import math


def main(output, mesh_size):
    import gmsh
    gmsh.initialize()
    try:
        gmsh.model.add('closed_12_ring_rotor_stationary_cage')
        occ=gmsh.model.occ
        rings=[]
        for k in range(12):
            phi=math.radians(15*k)
            tag=occ.addTorus(0,0,0,.035,.004)
            # Initially the ring lies in XY; send its normal +Z into XY.
            occ.rotate([(3,tag)],0,0,0,-math.sin(phi),math.cos(phi),0,math.pi/2)
            rings.append((3,tag))
        # Fuse intersecting ferrite rings into one physical material domain.
        rotor,_=occ.fuse([rings[0]],rings[1:],removeObject=True,removeTool=True)
        outer=occ.addSphere(0,0,0,.043)
        inner=occ.addSphere(0,0,0,.041)
        cage,_=occ.cut([(3,outer)],[(3,inner)],removeObject=True,removeTool=True)
        domain=occ.addSphere(0,0,0,.15)
        volumes,_=occ.fragment([(3,domain)],rotor+cage)
        occ.synchronize()
        # Identify fragments by their center of mass / bounding box. Because
        # rings and shell are nested, use Gmsh's returned fragment mapping
        # only for inspection; classification must be validated visually.
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0),mesh_size)
        gmsh.option.setNumber('Mesh.Algorithm3D',10)
        gmsh.model.mesh.generate(3)
        gmsh.write(output)
        print('Created geometric mesh:',output)
        print('3D fragments:',len(gmsh.model.getEntities(3)))
        print('WARNING: material groups, coil volumes, cage weave and motion are not solved.')
    finally:
        gmsh.finalize()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='closed_ring_geometry.msh')
    p.add_argument('--mesh-size',type=float,default=.003)
    args=p.parse_args()
    main(args.out,args.mesh_size)
