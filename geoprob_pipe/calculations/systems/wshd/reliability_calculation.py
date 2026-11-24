from geoprob_pipe.calculations.systems.base_objects.system_calculation import (
    SystemCalculation,
)
from geoprob_pipe.calculations.systems.wshd.limit_state_functions import (
    calc_Z_h,
    calc_Z_p,
    calc_Z_project,
    calc_Z_u,
    limit_state_wshd,
)


class WSHDCalculation(SystemCalculation):
    """ Vooraf gedefinieerde System Reliability Calculation voor piping met het WBI-stijghoogtemodel. """

    def __init__(
            self,
            distributions: list[dict],
            correlations: list[tuple[str, str, float]]| None = None,
            reliability_settings: dict[str, str| float| int] | None= None
    ) -> None:
        super().__init__(
            distributions=distributions, correlations=correlations, reliability_settings=reliability_settings)
        self.setup.variables_function = limit_state_wshd
        self.setup.system_limit_states = [calc_Z_u, calc_Z_h, calc_Z_p]
        self.setup.project_limit_state = calc_Z_project
