# Claims matrix

This file is the scientific index for the repository. `VERIFIED_FEM` means only
that an attributable Elmer case and FEM output are present; it does not mean
that the physical interpretation or the real machine has been validated.

| Claim | Evidence | File(s) | Status | Note |
|---|---|---|---|---|
| A 3-D transient magnetodynamic FEM pipeline exists | Elmer SIF files, Whitney A-V solver configuration and existing VTU outputs | `config/*.sif`, `variants/**/config/*.sif`, `variants/**/work_dirs/**/results/*.vtu` | `VERIFIED_FEM` | Applies to the listed simplified cases only. |
| Six alternating current regions can be excited with half-waves | MATC current law with positive/negative half-wave branches | `variants/rotore_centrato_poli_alternati_semionda/config/case_poli_alternati_semionda.sif` | `VERIFIED_FEM` | The geometry is cylindrical/central, not toroidal. |
| A spherical cage and orthogonal coil groups can be solved | Spherical mesh generator, SIF, VTU outputs | `variants/gabbia_sferica_doppio_rotore_90deg/` | `VERIFIED_FEM` | This is an orthogonal double-rotor surrogate, not the physical toroidal rotor. |
| The cage is a real woven copper mesh | Homogenized anisotropic material laws | `case_gabbia_sferica_doppio_rotore.sif`, `case_mesh_stirata.sif` | `PRELIMINARY` | The FEM uses equivalent tensors; explicit woven wires are not generally meshed. |
| A toroidal rotor with 2, 8 or 24 curved coils has been simulated by FEM | Python scripts, JSON/CSV benchmarks, but no corresponding toroidal SIF/mesh/VTU chain | `variants/rotore_toroidale_verticale_*` | `PRELIMINARY_ANALYTICAL` | Useful design scaffolding, not a FEM result. |
| Mechanical rotation is represented by a moving material | No moving mesh, angular velocity field, mechanical equation or `v×B` coupling in the relevant SIF files | `config/*.sif`, resonance and verification SIF generators | `NOT_IMPLEMENTED` | Some source locations are time-dependent; this is not sufficient. |
| CW/CCW changes the mechanical velocity sign | Existing tests change phase formulas or `dir_sign`; the verification cases use `RPM=0` and `w=0` | `variants/rotore_centrato_z0_resonance_sweep/verification_tests/` | `NON_CONCLUSIVE` | These are electrical-sequence tests, not `+omega/-omega` tests. |
| Raw FEM reaches eta_CP = 99.98% and AR = 0.15 dB | Independent reproduction reports 70.28% and AR 1.83 dB | `data/eta_cp_validation_results.json` | `NON_CONCLUSIVE` | 99.98% is explicitly identified as an analytical compensated target. |
| A radial or spherical external field is demonstrated | Radial projections, absolute values, Gauss residuals and sampled sphere metrics | `variants/rotore_centrato_poli_alternati_semionda/scripts/postprocess_poli_alternati.py` | `NON_CONCLUSIVE` | These diagnostics do not establish vector isotropy. |
| Lorentz-force chirality is physically established | Falsification test fails symmetry; Lorentz/MST comparison differs strongly | `verification_tests/data/`, `data/validazione_mst_chiral_bias.json` | `ARTIFACT` | Force and torque interpretation requires a new controlled model. |
| Power is invariant at 18.5 W in every campaign | Some analytic datasets impose or report this value; other datasets contain different totals | `data/*.json`, variant scripts | `NEEDS_REVIEW` | Must be checked from direct FEM energy balances per case. |
| Laboratory field validation exists | README contains a proposed scanner and acceptance protocol | `README.md` historical version / current roadmap | `NOT_IMPLEMENTED` | No laboratory measurement dataset is included. |

## Interpretation rule

An output VTU proves that a solver run produced a field for a particular
mathematical model. It does not prove that the model is the physical machine,
that a post-processed scalar is isotropic, or that a sign change came from
mechanical reversal.
