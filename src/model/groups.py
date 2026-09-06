"""Calibrated groups with explicit employment-share accounting and assumptions."""
import numpy as np
from .efficiency import calibrate_kappa, formal_hours_avg, hours_distribution
from .calibration import calibrate_wedges

# Legacy inputs, retained as assumptions until verified empirical replacements.
# "share" is participation in FORMAL employment, never total employment.
DEFAULT_GROUP_SPECS = {
    "Pequenas":{"share":.59,"inf_target":.50,"gamma_F":.12,"K_share":.35},
    "Grandes":{"share":.41,"inf_target":.20,"gamma_F":.03,"K_share":.65},
}


def formal_to_total_shares(formal_shares,informality):
    """s_total[g] proportional to s_formal[g]/(1-informality[g])."""
    names = list(formal_shares)
    if set(names) != set(informality):
        raise ValueError("Share and informality groups differ")
    shares = np.array([formal_shares[g] for g in names],dtype=float)
    inf = np.array([informality[g] for g in names],dtype=float)
    if (np.any(shares < 0) or not np.isfinite(shares).all() or
            not np.isclose(shares.sum(),1.,atol=1e-10,rtol=0) or
            np.any(inf < 0) or np.any(inf >= 1) or not np.isfinite(inf).all()):
        raise ValueError("Shares must sum to 1 and informality must be in [0,1)")
    raw = shares/(1.-inf)
    return dict(zip(names,(raw/raw.sum()).tolist()))


def build_groups(targets,sigma_sub=1.15,omega=.622,group_specs=None,theta=None,
                 efficiency_mode="bilateral",hours_bins=None,share_basis="formal",
                 resource_costs=False,kappa_override=None):
    """Construct groups; omega is a technological assumption, not a jobs share.

    H_REF_EFFICIENCY optionally fixes the external elasticity reference hours.
    This is separate from the empirical hours distribution. kappa_override
    allows explicit sensitivity without fictitious below-peak identification.
    """
    v = lambda key:targets[key]["value"]
    if group_specs is None:
        specs = {g:dict(s) for g,s in DEFAULT_GROUP_SPECS.items()}
        for name,suffix in (("Pequenas","SMALL"),("Grandes","LARGE")):
            for field,prefix in (("share","SHARE"),("inf_target","INF"),
                                 ("gamma_F","GAMMA_F"),("K_share","K_SHARE")):
                key = f"{prefix}_{suffix}"
                if key in targets:
                    specs[name][field] = v(key)
    else:
        specs = group_specs
    alpha,eta_I,e_q = v("ALPHA"),v("ETA_I"),v("E_Q")
    h0,h1,h_star,hI,N_total = [v(k) for k in ("H0","H1","H_STAR","HI","N_TOTAL")]
    if theta is None:
        theta = [v("THETA_36"),v("THETA_40"),v("THETA_44")]
    theta,bins = hours_distribution(theta,hours_bins)
    h_ref = (v("H_REF_EFFICIENCY") if "H_REF_EFFICIENCY" in targets
             else formal_hours_avg(h0,theta,bins))
    kappa = (calibrate_kappa(h_ref,h_star,e_q,efficiency_mode)
             if kappa_override is None else float(kappa_override))
    shares = {g:spec.get("formal_share",spec.get("share")) for g,spec in specs.items()}
    if share_basis == "formal":
        total_shares = formal_to_total_shares(shares,{g:s["inf_target"] for g,s in specs.items()})
    elif share_basis == "total":
        # Explicit diagnostic only: reproduces the legacy interpretation.
        if not np.isclose(sum(shares.values()),1.,atol=1e-10,rtol=0):
            raise ValueError("Total shares must sum to 1")
        total_shares = shares
    else:
        raise ValueError("share_basis must be formal or total")
    if not np.isclose(sum(s["K_share"] for s in specs.values()),1.,atol=1e-10,rtol=0):
        raise ValueError("Capital shares must sum to one")
    common = {"A":1.,"alpha":alpha,"h0":h0,"h1":h1,"hI":hI,"h_star":h_star,
              "omega":omega,"sigma_sub":sigma_sub,"eta_I":eta_I,"kappa":kappa,
              "efficiency_mode":efficiency_mode,"hours_bins":bins.tolist(),
              "theta":theta.tolist(),"resource_costs":resource_costs,
              "h_ref_efficiency":h_ref,"share_basis_input":share_basis}
    groups = {}
    for name,spec in specs.items():
        Ng,Kg = N_total*total_shares[name],spec["K_share"]
        if Ng <= 0 or Kg <= 0:
            raise ValueError("Each modeled group needs positive labor and capital")
        wedge = calibrate_wedges(spec["inf_target"],Ng,h0,hI,1.,Kg,alpha,
                                 omega,sigma_sub,eta_I,kappa,h_star,theta,
                                 efficiency_mode,bins)
        groups[name] = {**common,**wedge,"N_total":Ng,"K":Kg,
                        "gamma_F":spec["gamma_F"],
                        "NF_init":Ng*(1-spec["inf_target"]),
                        "inf_target":spec["inf_target"],
                        "share_total":total_shares[name],
                        "input_share":shares[name]}
    formal_total = sum(p["NF_init"] for p in groups.values())
    for p in groups.values():
        p["share_formal_implied"] = p["NF_init"]/formal_total
    return groups,kappa,theta

