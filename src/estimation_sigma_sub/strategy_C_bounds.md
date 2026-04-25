# Strategy C: Bounds / Set Identification for sigma_sub

## Method
Derive analytical bounds on sigma_sub using economic inequalities and model structure.

## Bound 1: Wage Premium (Tightest)

From the CES aggregator FOC, the formal/informal wage premium is:

  R = (omega/(1-omega)) * (LF/LI)^(rho-1) * z

where rho = (sigma-1)/sigma and z = eff_hF / (eta_I * hI * eI).

**Observed**: R in [1.15, 1.55] (MNR 2015, widened upper bound to cover sub-populations and alternative specifications)
**Implied at (omega, eta_I) = (0.622, 0.15)**: sigma in [1.065, 1.230]

This is the TIGHTEST bound because it uses model structure + one observable moment. Note that the mapping from R to sigma depends on (omega, eta_I); under the post-audit3 recalibration (narrow PNAD omega = 0.622, La Porta-Shleifer median eta_I = 0.15), the mapping shifts upward relative to prior versions.

## Bound 2: Economic Plausibility

**Lower bound**: sigma > 0 (by CES definition)
- sigma = 0: Leontief (fixed proportions) — implausible for labor types
- sigma < 1 implies near-complementarity; at observed eta_I = 0.15 this is inconsistent with the MNR wage premium

**Upper bound**: sigma < infinity (not perfect substitutes)
- If sigma -> infinity, formal and informal labor are identical
- But they clearly differ: productivity gap (eta_I << 1), different hours, different legal status
- sigma > 3 implies flat-enough isoquants that observed wage premia become uninformative

**Plausibility range**: sigma in [0.5, 3.0]
- This is very wide and uninformative by itself

## Bound 3: Katz-Murphy Analog

Katz & Murphy (1992) estimate sigma = 1.4-2.0 for skilled/unskilled labor substitution.

The formal/informal margin is DIFFERENT from skilled/unskilled:
- Formal/informal workers often have SIMILAR skills (same person can be either)
- The margin is driven by REGULATORY cost, not skill
- This is broadly consistent with sigma slightly above 1 at the recalibrated (omega, eta_I).

## Bound 4: Informality Response to Policy

In our model, a 1pp increase in formal wedge (tau) increases informality by:
- At sigma ~ 1.0: moderate response
- At sigma ~ 1.5: stronger response
- At sigma = 2.0+: strong response

**Observed**: Countries that reduce formalization costs (e.g., Simples Nacional in Brazil)
see moderate informality responses (Monteiro & Assuncao 2012: ~4-7pp for eligible firms).
This is consistent with sigma in [0.7, 1.5].

## Bound 5: Cross-Model Consistency

Ulyssea (2018, AER) calibrates a model with formal/informal firms (not CES between
labor types, but entry/exit at extensive margin). His estimated "substitution" operates
through firm-level choices, not a CES aggregator. Derenoncourt et al. (2025) document
a small formal-to-informal reallocation elasticity (~ -0.28) from the Brazilian minimum
wage, consistent with a mild but positive intra-firm sigma.

## Summary of Bounds

| Source | Lower Bound | Upper Bound | Confidence |
|--------|-------------|-------------|------------|
| CES + wage premium (at omega=0.622, eta_I=0.15) | 1.065 | 1.230 | HIGH (model-consistent) |
| Economic plausibility | 0.50 | 3.00 | LOW (very wide) |
| Katz-Murphy analog | 1.00 | 2.00 | LOW (different margin) |
| Policy response | 0.70 | 1.50 | MEDIUM |
| Ulyssea (2018) / DGLM (2025) | 0.70 | 1.30 | MEDIUM (different model) |

## Intersection

Within the wage-premium discipline, **sigma in [1.065, 1.230]** is the MODEL-CONSISTENT interval.

## Implication for A_req (conservative, at central omega = 0.622, eta_I = 0.15)

| sigma | A_req | Interpretation |
|-------|-------|---------------|
| 1.065 | 7.47% | Wage premium lower bound (R=1.15) |
| 1.15  | 7.98% | Central estimate (R approx 1.35) |
| 1.230 | 8.40% | Wage premium upper bound (R=1.55) |

## Conclusion

sigma_sub is identified within [1.065, 1.230] by the wage premium at the
recalibrated (omega, eta_I) = (0.622, 0.15). The three-way joint envelope
over (sigma, omega, eta_I) at the eight corners gives A_req in [6.90%, 9.01%]
under the conservative specification, and [5.59%, 7.29%] under the preferred
flat-below specification.
