# Falsification tests and non-conclusive results

This document records tests that must not be presented as evidence for the
main physical hypothesis.

## Existing verification suite

The suite in `variants/rotore_centrato_z0_resonance_sweep/verification_tests/`
uses the same central cylindrical mesh, 100 Hz excitation, 20 steps and
`RPM = 0` for its control cases.

### Test 1 — mantle sign reversal

- Changed: the sign of the off-diagonal anisotropic conductivity term, from
  the `+30` to the `-30` case.
- Unchanged: mesh, current geometry, current amplitude, phase progression,
  frequency and zero mechanical speed.
- Intended result: a specular force reversal.
- Recorded result: the expected symmetry failed; the reported symmetry error
  is about 174%.
- Limit: this tests material/tensor reversal and discretization sensitivity,
  not mechanical rotor reversal.

Reference: `verification_tests/config/case_test1_chirality_reversal.sif` and
`verification_tests/data/risultati_falsificazione_artefatti.json`.

### Test 2 — isotropic mantle

- Changed: the mantle tensor was replaced with an isotropic diagonal
  conductivity.
- Unchanged: mesh, current law, frequency and zero mechanical speed.
- Intended result: approximately zero residual force.
- Recorded result: a non-zero residual remained and the test failed.
- Limit: the result indicates numerical/model asymmetry; it does not prove a
  physical chiral force.

Reference: `verification_tests/config/case_test2_isotropic.sif`.

### Test 3 — phase inversion

- Changed: the signs in the phase formulas for the current sectors.
- Unchanged: geometry, mesh, mantle, `RPM = 0` and source locations.
- Recorded result: the force sign changed and the test passed its stated
  criterion.
- Limit: this is an electrical phase/sequence inversion, not a change from
  `omega = +omega0` to `omega = -omega0`.

Reference: `verification_tests/config/case_test3_phase_inversion.sif`.

## Independent reproduction

`verification_tests/data/independent_reproduction_debian13.json` reports the
same qualitative pattern: the mantle-reversal and isotropic controls fail,
while the phase-inversion control passes. This supports reproducibility of the
numerical test pattern, not the physical interpretation that was originally
sought.

## Lorentz force versus Maxwell stress

`data/validazione_mst_chiral_bias.json` reports a large discrepancy between
the volume Lorentz result and the Maxwell Stress Tensor result. Until the two
methods converge under mesh refinement and a controlled boundary construction,
micro-newton forces and derived torques remain non-conclusive.

## Resonance and kinematic sweeps

The resonance generator creates transient Elmer cases for non-negative RPM
values, but it uses the RPM parameter to prescribe source-position evolution.
The analytic kinematic and toroidal sweep scripts calculate quantities from
reference values and formulas. They are not a mechanical `+omega/-omega`
experiment.

## What these tests do not establish

They do not establish a spherical field, a radial vector field, a magnetic
monopole, a mechanical CW/CCW helicity inversion, a net reaction-free force,
or a torque on the real toroidal machine.
