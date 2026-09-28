# Repository classification and non-destructive reorganization plan

No files are moved or deleted by this plan. The current paths are retained to
avoid breaking scripts and to preserve provenance.

## KEEP

- `config/*.sif` and their existing root result directories.
- FEM variant SIF files, Elmer mesh databases and existing VTU outputs where a
  solver chain is identifiable.
- `variants/gabbia_sferica_doppio_rotore_90deg/` FEM cases and outputs.
- `variants/rotore_centrato_poli_alternati_semionda/` FEM case and outputs.
- `variants/rotore_centrato_z0_resonance_sweep/` case generators and control
  cases, with their limitations documented separately.
- Post-processors that read VTU data directly.

## PRELIMINARY

- `variants/rotore_toroidale_verticale_2bobine_vertice/`.
- `variants/rotore_toroidale_verticale_8bobine_curve/`.
- `variants/rotore_toroidale_verticale_24bobine_curve/`.
- `scripts/run_toroidal_*`, `scripts/run_toroidale_*`,
  `scripts/run_kinematic_regimes_simulation.py` and
  `scripts/run_polarization_spherical_sweep.py`.
- Benchmark JSON/CSV files produced by analytic or parametrized scripts.

## HISTORICAL

- `_archive_backup/**`.
- Old SIF files, meshes, figures, reports and scripts retained there.
- The pre-restructure README is recoverable from the local Git tag
  `pre-scientific-restructure-20260926`.

## ARTIFACT / NON-CONCLUSIVE

- `variants/rotore_centrato_z0_resonance_sweep/verification_tests/data/`.
- `data/validazione_mst_chiral_bias.json`.
- Derived force, torque or CW/CCW figures based only on those tests.

## NEEDS REVIEW

- Root-level benchmark JSON files whose provenance is not a direct VTU
  post-process.
- Figures described as “measured” without a laboratory data source.
- Duplicate cached `case.sif`, VTU and JSON files in `work_dirs` and variant
  data directories.
- Scripts whose names suggest FEM but contain only analytical formulas.

## Future logical layout

The following is a future organizational target, not an instruction to move
files now:

```text
validated/
preliminary/
historical/
artifacts/
future_fem_model/
documentation/
```

Before any physical move, a provenance manifest should record the source path,
mesh, SIF, solver version, output directory and generating script for each
result.
