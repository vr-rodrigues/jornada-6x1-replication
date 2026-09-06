"""Conditional gross marginal-product bridge; never an identified wage model.

Weekly pay is the marginal product of an additional worker. Hourly pay divides
that quantity by physical hours. Aggregate payrolls and denominators across
firms FIRST: a CES of summed inputs is not the production of heterogeneous firms.
"""
from copy import deepcopy
import numpy as np
from scipy.optimize import brentq

from src.model.simulation import run_simulation
from src.model.efficiency import eff, formal_hours_hetero
from src.model.ces_aggregator import ces_agg


def aggregate_bridge(simulation, theta=None, hours_bins=None):
    rows = []
    for name, p in simulation['groups'].items():
        s = simulation['baseline']['solutions'][name]
        th = p.get('theta', theta)
        if th is None:
            th = simulation.get('theta')
        if th is None:
            raise ValueError('The hours distribution must be explicit')
        mode = p.get('efficiency_mode', simulation.get('efficiency_mode', 'bilateral'))
        bins = p.get('hours_bins', hours_bins)
        havg, hf = formal_hours_hetero(p['h0'], p['kappa'], p['h_star'], th,
                                     efficiency_mode=mode, hours_bins=bins)
        hi = p['hI'] * eff(p['hI'], p['kappa'], p['h_star'], efficiency_mode=mode)
        lf, li = s['NF'] * hf, p['eta_I'] * s['NI'] * hi
        if min(lf, li) <= 0:
            raise ValueError('Wage bridge requires both labor types')
        labor = float(ces_agg(lf, li, p['omega'], p['sigma_sub']))
        rho = (p['sigma_sub'] - 1) / p['sigma_sub']
        # dY/dL_F and dY/dL_I, in units of effective labor.
        common = (1 - p['alpha']) * s['Y'] * labor ** (-rho)
        mpf = common * p['omega'] * lf ** (rho - 1)
        mpi = common * (1 - p['omega']) * li ** (rho - 1)
        wf, wi = mpf * hf, mpi * p['eta_I'] * hi
        rows.append(dict(group=name, NF=s['NF'], NI=s['NI'],
                         physical_hours_formal=s['NF']*havg,
                         physical_hours_informal=s['NI']*p['hI'],
                         payroll_formal=wf*s['NF'], payroll_informal=wi*s['NI'],
                         weekly_formal=wf, weekly_informal=wi,
                         hourly_formal=wf/havg, hourly_informal=wi/p['hI'],
                         effective_unit_ratio=mpf/mpi))
    sums = {key: sum(row[key] for row in rows) for key in
            ('NF','NI','physical_hours_formal','physical_hours_informal',
             'payroll_formal','payroll_informal')}
    pf, pi = sums['payroll_formal'], sums['payroll_informal']
    return dict(groups=rows, totals=sums,
                hourly_ratio=(pf/sums['physical_hours_formal'])/(pi/sums['physical_hours_informal']),
                weekly_ratio=(pf/sums['NF'])/(pi/sums['NI']),
                formal_payroll_share=pf/(pf+pi),
                interpretation='Gross marginal products; competitive pay mapping assumed, not implied by the fixed-N firm objective')


def calibrate_omega(targets, ratio_target, *, sigma_sub=1.326, measure='hourly',
                    efficiency_mode='bilateral', theta=None, hours_bins=None,
                    group_specs=None, share_basis='formal'):
    if measure not in ('hourly', 'weekly') or not np.isfinite(ratio_target) or ratio_target <= 0:
        raise ValueError('A positive, explicitly defined wage target is required')
    if theta is None:
        theta = [targets[f'THETA_{h}']['value'] for h in (36,40,44)]
    def at(w):
        sim = run_simulation(targets, sigma_sub=sigma_sub, omega=w, theta=theta,
                             group_specs=group_specs, efficiency_mode=efficiency_mode,
                             hours_bins=hours_bins, share_basis=share_basis)
        return aggregate_bridge(sim, theta, hours_bins)[measure+'_ratio']
    omega = brentq(lambda w: at(w)-ratio_target, 0.02, 0.98, xtol=1e-11)
    actual = at(omega)
    if abs(actual-ratio_target) > 1e-7:
        raise ArithmeticError('Wage bridge root did not restore its target')
    return dict(omega=omega, sigma_sub=sigma_sub, measure=measure,
                target=ratio_target, implied=actual, residual=actual-ratio_target,
                status='conditional_calibration_not_joint_identification',
                assumption='Gross marginal products proxy observed remuneration; tau/pi are not separately identified')
