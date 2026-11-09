from __future__ import annotations

import os
from typing import TYPE_CHECKING

from plotly.graph_objects import Figure as PlotlyFigure

from geoprob_pipe.visualizations.maps.betamap import BetaMap
from geoprob_pipe.visualizations.maps.voorland import ForelandMap

if TYPE_CHECKING:
    from geoprob_pipe import GeoProbPipe


class Maps:
    def __init__(self, app_obj: GeoProbPipe) -> None:
        self.geoprob_pipe = app_obj

    @property
    def export_dir(self) -> str:
        path = os.path.join(self.geoprob_pipe.visualizations.export_dir, "maps")
        os.makedirs(path, exist_ok=True)
        return path

    def betamap(self, export: bool = False) -> PlotlyFigure:
        map_figure = BetaMap(self.geoprob_pipe, export=export)
        return map_figure.fig

    def foreland_map(self, export: bool = False) -> PlotlyFigure:
        map_figure = ForelandMap(self.geoprob_pipe, export=export)
        return map_figure.fig

    def export_maps(self) -> None:
        BetaMap(self.geoprob_pipe, export=True)
        ForelandMap(self.geoprob_pipe, export=True)
