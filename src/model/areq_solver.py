"""TFP compensation with reoptimization preserved inside every root evaluation."""
from scipy.optimize import brentq
from .firm_problem import solve_group


def solve_Areq(groups,hF_cap,Y_target,theta,grid=3001,
                composition="reoptimized",return_details=False):
    """Return signed percent productivity change restoring gross output.

    Default reoptimizes NF at every A. Frozen fixes baseline NF_init (or
    NF_frozen explicitly supplied). Signed changes permit exact restoration
    even where the reform raises output. No arbitrary upper bracket is used.
    """
    if Y_target <= 0:
        raise ValueError("Output restoration requires a positive target")

    def at(mult):
        allocations = {name:solve_group(p,hF_cap,theta,mult,composition)
                       for name,p in groups.items()}
        return sum(s["Y"] for s in allocations.values()), allocations

    Y1,_ = at(1.)
    if abs(Y1/Y_target-1.) <= 1e-12:
        root = 1.
    elif composition == "frozen":
        root = Y_target/Y1
    else:
        # The maximized production response to a common productivity scalar
        # is monotone by revealed preference, since costs do not depend on A.
        if Y1 < Y_target:
            lower,upper = 1.,max(1.1,Y_target/Y1)
            for _ in range(80):
                if at(upper)[0] >= Y_target:
                    break
                upper *= 2.
            else:
                raise RuntimeError("Could not bracket output restoration above one")
        else:
            lower,upper = .5,1.
            for _ in range(80):
                if at(lower)[0] <= Y_target:
                    break
                lower *= .5
            else:
                raise RuntimeError("Could not bracket output restoration below one")
        root = brentq(lambda a:at(a)[0]-Y_target,lower,upper,xtol=1e-12,rtol=1e-12)
    output,allocations = at(root)
    error = output/Y_target-1.
    if abs(error) > 1e-9:
        raise RuntimeError(f"Output restoration failed: relative error {error}")
    details = {"A_req_pct":100.*(root-1.),"A_mult":root,"output":output,
               "target_output":Y_target,"relative_error":error,
               "composition":composition,"allocations":allocations,
               "nonnegative_gain_pct":max(0.,100.*(root-1.))}
    return details if return_details else details["A_req_pct"]

