"""
TODO: Bepaal waar de kwelweg de verschillende lijnen snijdt
TODO: Teken deze lijnen in een kaart
TODO: Teken de fictieve voorland lengte / lambda in de kaart
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from shapely.geometry import LineString
from shapely.ops import nearest_points

from geoprob_pipe.visualizations.maps.utils import add_line

if TYPE_CHECKING:
    from geoprob_pipe import GeoProbPipe

# TODO: Fix voor niet-Moria modellen
# TODO: fix voor niet alle vakken runnen
class ForelandMap:
    def __init__(self, geoprob_pipe: GeoProbPipe, export: bool = False) -> None:
        self.geoprob_pipe = geoprob_pipe
        self.export: bool = export
        self.output_dir: str = geoprob_pipe.visualizations.maps.export_dir
        self.gdf_buitenteen: gpd.GeoDataFrame = gpd.read_file(
            geoprob_pipe.input_data.app_settings.geopackage_filepath,
            layer="buitenteenlijn",
        ).to_crs("EPSG:28992")
        self.gdf_exit_points: gpd.GeoDataFrame = gpd.read_file(
            geoprob_pipe.input_data.app_settings.geopackage_filepath,
            layer="uittredepunten",
        ).to_crs("EPSG:28992")
        self.physical_values: pd.DataFrame = (
            geoprob_pipe.results.df_alphas_influence_factors_and_physical_values()
        )

        # Logic
        self._create_figure()
        self._add_lines()
        self._optionally_export()

    def _create_lines(self, scenario: str) -> gpd.GeoDataFrame:
        lines = []
        for _, row in self.gdf_exit_points.iterrows():
            exit_point = row.geometry
            buitenteen_geom = self.gdf_buitenteen.union_all()
            utp_id = row.uittredepunt_id

            try:
                seepage_length: float = self.physical_values.loc[
                    (self.physical_values["uittredepunt_id"] == utp_id)
                    & (self.physical_values["variable"] == "L_kwelweg")
                    & (self.physical_values["ondergrondscenario_id"] == scenario),
                    "physical_value",
                ].item()
            except Exception:
                continue

            fictitious_foreland_length = seepage_length - row.afstand_buitenteenlijn

            _, toe_point = nearest_points(
                exit_point,
                buitenteen_geom,
            )

            # richting uittredepunt -> buitenteen
            dx = toe_point.x - exit_point.x
            dy = toe_point.y - exit_point.y

            norm = np.hypot(dx, dy)

            if norm == 0:
                lines.append(None)
                continue

            ux = dx / norm
            uy = dy / norm

            # verlengd eindpunt
            extended_end = (
                toe_point.x + ux * fictitious_foreland_length,
                toe_point.y + uy * fictitious_foreland_length,
            )

            line = LineString(
                [
                    (exit_point.x, exit_point.y),
                    (toe_point.x, toe_point.y),
                    extended_end,
                ]
            )

            lines.append(line)
        return gpd.GeoDataFrame(
            geometry=lines,
            crs=self.gdf_exit_points.crs,
        )

    def _create_figure(self) -> None:
        self.fig = go.Figure()
        scenario_color: dict[str, str] = {
            "Zand Diep": "red",
            "Zand Midden": "Orange",
            "Zand Ondiep": "yellow",
        }
        # TODO: Zoek deze op uit de geopackage
        for scenario in ["Zand Diep", "Zand Midden", "Zand Ondiep"]:
            gdf_lines = self._create_lines(scenario)
            gdf_lines = gdf_lines.to_crs("EPSG:4326")
            for _, row in gdf_lines.iterrows():
                line = row.geometry

                x, y = line.xy

                self.fig.add_trace(
                    go.Scattermap(
                        lon=list(x),
                        lat=list(y),
                        mode="lines",
                        line={
                            "width": 3,
                            "color": scenario_color[scenario],
                        },
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )

        self.fig.update_layout(
            map={
                "style": "white-bg",
                "center": {
                    "lon": gdf_lines.geometry.centroid.x.mean(),
                    "lat": gdf_lines.geometry.centroid.y.mean(),
                },
                "zoom": 13,
                "layers": [
                    {
                        "below": "traces",
                        "sourcetype": "raster",
                        "source": [
                            (
                                "https://service.pdok.nl/brt/achtergrondkaart/"
                                "wmts/v2_0/grijs/"
                                "EPSG:3857/{z}/{x}/{y}.png"
                            )
                        ],
                    }
                ],
            },
        )

    def _add_lines(self) -> None:
        self.fig = add_line(self.geoprob_pipe, self.fig, "dijktraject", "black")
        self.fig = add_line(self.geoprob_pipe, self.fig, "intredelijn", "blue")
        self.fig = add_line(self.geoprob_pipe, self.fig, "binnenteenlijn", "purple")
        self.fig = add_line(self.geoprob_pipe, self.fig, "buitenteenlijn", "red")

    def _optionally_export(self) -> None:
        if self.export:
            self.fig.write_html(
                os.path.join(self.output_dir, "Voorlandlengtes.html"),
                include_plotlyjs="cdn",
            )
