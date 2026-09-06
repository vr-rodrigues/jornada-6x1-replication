"""Continuous baseline calibration with an explicit wedge normalization."""
from .firm_problem import production_marginals, solve_NF
from .efficiency import eff, formal_hours_hetero


def _target_derivative(target_inf, N_total,h0,hI,A,K,alpha,omega,
                        sigma_sub,eta_I,kappa,h_star,theta,
                        efficiency_mode="bilateral",hours_bins=None):
    if not 0 < target_inf < 1:
        raise ValueError("Finite normalized wedge calibration requires interior informality")
    NF, NI = N_total*(1-target_inf), N_total*target_inf
    _, eff_hF = formal_hours_hetero(h0,kappa,h_star,theta,efficiency_mode,hours_bins)
    mp = production_marginals(NF,NI,eff_hF,hI*eff(hI,kappa,h_star,efficiency_mode),
                              eta_I,A,K,alpha,omega,sigma_sub)
    return mp["MP_NF"]-mp["MP_NI"]


def calibrate_wedges(target_inf, N_total,h0,hI,A,K,alpha,omega,sigma_sub,
                      eta_I,kappa,h_star,theta,efficiency_mode="bilateral",
                      hours_bins=None):
    """Impose tau>=0, pi>=0, tau*pi=0, selecting the minimum nonnegative pair.

    One informality moment only identifies tau-pi*NI = dY/dNF. If dY/dNF>=0
    choose (tau,pi)=(dY/dNF,0); otherwise choose (0,-dY/dNF/NI).
    This is a normalization, not separate empirical identification of costs.
    Adjustment is zero at its baseline NF_init.
    """
    derivative = _target_derivative(target_inf,N_total,h0,hI,A,K,alpha,omega,
                                    sigma_sub,eta_I,kappa,h_star,theta,
                                    efficiency_mode,hours_bins)
    return {"formal_wedge":max(derivative,0.),
            "pi_m":max(-derivative,0.)/(N_total*target_inf),
            "normalization":"tau>=0; pi>=0; tau*pi=0; baseline FOC exact",
            "identified_combination_tau_minus_pi_NI":derivative}


def calibrate_wedge(target_inf, N_total,h0,hI,A,K,alpha,omega,sigma_sub,
                    eta_I,kappa,h_star,pi_m,theta,lo=0.,hi=25.,n_iter=60,
                    grid=3001,efficiency_mode="bilateral",hours_bins=None):
    """Legacy single-wedge interface, solved analytically from the target FOC.

    lo/hi/n_iter/grid are legacy compatibility parameters. Bounds are never
    silently returned when the moment cannot be fitted.
    """
    derivative = _target_derivative(target_inf,N_total,h0,hI,A,K,alpha,omega,
                                    sigma_sub,eta_I,kappa,h_star,theta,
                                    efficiency_mode,hours_bins)
    value = derivative + pi_m*N_total*target_inf
    if value < -1e-10:
        raise ValueError("Given pi_m requires a negative tau; use calibrate_wedges")
    return max(value,0.)


def calibrate_pi_m(target_inf,N_total,h0,hI,A,K,alpha,omega,sigma_sub,
                   eta_I,kappa,h_star,theta,lo=0.,hi=1.,grid=2001,
                   efficiency_mode="bilateral",hours_bins=None):
    """Nonnegative pi consistent with the complementarity normalization."""
    return calibrate_wedges(target_inf,N_total,h0,hI,A,K,alpha,omega,sigma_sub,
                            eta_I,kappa,h_star,theta,efficiency_mode,hours_bins)["pi_m"]


def calibrate_psi(w_hourly,h,nu):
    """Representative-agent GHH normalization: psi*h**nu=w."""
    if h <= 0 or nu <= -1:
        raise ValueError("Require h>0 and nu>-1")
    return w_hourly/h**nu

