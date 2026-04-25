# Strategy A: Demand Relative CES — Methodology (Not Executed)

## Status: DOCUMENTED BUT NOT FEASIBLE WITH CURRENT DATA

## Method

From the CES aggregator, the firm's FOC for formal vs informal labor yields:

  ln(LF/LI) = sigma * ln(wI/wF) + sigma * ln(omega/(1-omega)) + sigma * ln(z)

where z captures efficiency differentials.

Rearranging for an estimating equation across cells (sector x UF x firm_size x year):

  ln(L_F/L_I)_{jrt} = sigma * ln(w_I/w_F)_{jrt} + FE_j + FE_r + FE_t + epsilon_{jrt}

where j=sector, r=UF, t=year.

## Data Requirements

1. **Quantities**: Number of formal (L_F) and informal (L_I) workers by cell
   - Source: PNAD Continua microdata (not SIDRA aggregates)
   - Variables: V4029 (firm size), V4040 (carteira), V4039 (hours), UF, CNAE

2. **Prices**: Formal wage (w_F) and informal wage (w_I) by cell
   - Source: PNAD Continua microdata
   - Variable: V403012 or VD4019 (habitual income)
   - Must control for observable worker characteristics

## Why Not Feasible Now

1. Requires PNAD Continua MICRODATA (not available via SIDRA API)
2. Needs panel variation across cells (multiple years of microdata)
3. Endogeneity: wages and quantities are jointly determined
   - Need instruments (e.g., regional formalization shocks, Simples Nacional thresholds)
4. Cell size: many cells would have very few observations

## If Executed Later

- Download PNAD Continua microdata from IBGE FTP
- Construct cells: CNAE_2dig x UF x firm_size_bin x year
- Compute: ln(N_formal/N_informal) and ln(w_informal/w_formal) per cell
- Estimate by OLS with FEs
- If endogeneity suspected: IV using Simples Nacional cutoffs or state-level tax variation
- Expected: sigma in [0.5, 1.5] based on literature analogs

## Contribution to Decision

Strategy A would provide a DIRECT estimate of sigma.
Since it's not feasible now, we rely on Strategies B-D for the decision.
The wage premium discipline (Strategy B) provides the same information in a
model-consistent way, making Strategy A redundant unless we want an
estimation-based sigma that doesn't rely on the model structure.
