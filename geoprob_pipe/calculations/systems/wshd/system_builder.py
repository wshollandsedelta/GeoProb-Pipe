from __future__ import annotations

from geoprob_pipe.calculations.systems.base_objects.base_system_build import (
    BaseSystemBuilder,
)
from geoprob_pipe.calculations.systems.wshd.reliability_calculation import (
    WSHDCalculation,
)

# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from geoprob_pipe import GeoProbPipe

# TODO: Deze class voegt niets toe aan de base, geen bestaansrecht - VJ
class WSHDSystemBuilder(BaseSystemBuilder):
    def __init__(self, geopackage_filepath: str, to_run_vakken_ids: list[int]) -> None:
        super().__init__(
            geopackage_filepath=geopackage_filepath, to_run_vakken_ids=to_run_vakken_ids
        )
        self.system_class = WSHDCalculation
