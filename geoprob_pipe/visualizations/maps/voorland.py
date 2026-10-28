from __future__ import annotations

import os
import sqlite3
from typing import TYPE_CHECKING

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shapely import Point
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points

from geoprob_pipe.visualizations.maps.utils import add_line

if TYPE_CHECKING:
    from geoprob_pipe import GeoProbPipe


class ForelandMap:
    def __init__(self, geoprob_pipe: GeoProbPipe, export: bool = False) -> None:
        """Class voor het maken van de voorlandlengte kaart.

        :param geoprob_pipe: Hoofdobject
        :param export: bool voor de export van de html, defaults to False
        """
        self.geoprob_pipe: GeoProbPipe = geoprob_pipe
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
        
        con = sqlite3.connect(geoprob_pipe.input_data.app_settings.geopackage_filepath)
        self.df_scenario: pd.DataFrame = pd.read_sql(
            "SELECT * FROM scenario_invoer",
            con,
        )
        
        self.physical_values: pd.DataFrame = (
            geoprob_pipe.results.df_alphas_influence_factors_and_physical_values()
        )

        # Selecteer alleen utp die gerunt zijn.
        utps: list[int] = self.physical_values["uittredepunt_id"].unique().tolist()
        
        self.gdf_exit_points = self.gdf_exit_points[
            self.gdf_exit_points["uittredepunt_id"].isin(utps)
        ]

        # Logic
        self._create_figure()
        self._add_lines()
        self._optionally_export()

    def _create_lines(self, scenario: str) -> gpd.GeoDataFrame:
        """Method voor het bepalen van de lijn per uittredepunt.

        :param scenario: Naam van het scenario dat word opgehaald
        :return: GeoDataFrame met alle lijen die bij dit scenario horen.
        """
        lines: list[LineString] = []
        for _, row in self.gdf_exit_points.iterrows():
            exit_point: Point = row.geometry
            buitenteen_geom: BaseGeometry = self.gdf_buitenteen.union_all()
            utp_id: int = row.uittredepunt_id

            # Bepaal de fictieve voorlandlengte uit de kwelweglengte
            seepage_length: pd.Series = self.physical_values.loc[
                (self.physical_values["uittredepunt_id"] == utp_id)
                & (self.physical_values["variable"] == "L_kwelweg")
                & (self.physical_values["ondergrondscenario_id"] == scenario),
                "physical_value",
            ]
            
            if len(seepage_length) != 1:
                continue
            seepage_length = seepage_length.item()

            fictitious_foreland_length: float = seepage_length - row.afstand_buitenteenlijn

            _, toe_point = nearest_points(
                exit_point,
                buitenteen_geom,
            )

            # richting uittredepunt -> buitenteen
            dx: float = toe_point.x - exit_point.x
            dy: float = toe_point.y - exit_point.y

            norm: float = np.hypot(dx, dy)

            ux: float = dx / norm
            uy: float = dy / norm

            # verlengd eindpunt
            extended_end: tuple[float, float] = (
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
        """Method voor het opzetten van het plotly figuur met alle lijnen."""
        # Verzamel de scenario namen
        scenario_names: list[str] = self.df_scenario["naam"].dropna().unique().tolist()

        colors: list[str] = px.colors.qualitative.Plotly

        scenario_color: dict[str, str] = {
            scenario: colors[i % len(colors)]
            for i, scenario in enumerate(scenario_names)
        }

        self.fig = go.Figure()
        
        # Per scenario met aparte legenda naam de lijnen intekenen.
        for scenario in scenario_names:
            
            # Lege trace voor legenda
            self.fig.add_trace(
                go.Scattermap(
                    mode="lines",
                    lon=[None],
                    lat=[None],
                    name=scenario,
                    line={
                        "width": 3,
                        "color": scenario_color[scenario],
                    },
                    legendgroup=scenario,
                    visible="legendonly",
                )
            )
            
            gdf_lines: gpd.GeoDataFrame = self._create_lines(scenario)
            gdf_lines = gdf_lines.to_crs("EPSG:4326")
            
            # Lijnen op de kaart tekenen
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
                        legendgroup=scenario,
                        visible="legendonly",
                    )
                )
                
        union: BaseGeometry = gdf_lines.union_all()  # pyright: ignore[reportPossiblyUnboundVariable]
        point: Point = union.representative_point()

        center_lon: float = point.x
        center_lat: float = point.y
        
        # Achtergrondkaart
        self.fig.update_layout(
            map={
                "style": "white-bg",
                "center": {
                    "lon": center_lon,
                    "lat": center_lat,
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
        """Voeg de traject, intrede en teenlijnen toe aan de kaart."""
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
