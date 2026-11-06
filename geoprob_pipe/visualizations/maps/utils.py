from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
import plotly.graph_objects as go
from shapely.geometry import GeometryCollection, LineString, MultiLineString

if TYPE_CHECKING:
    from geoprob_pipe import GeoProbPipe
    
    
def calculate_zoom(lat_range, lon_range):
    max_range = max(lat_range, lon_range)
    if max_range < 0.01:
        return 15
    elif max_range < 0.05:
        return 13
    elif max_range < 0.1:
        return 12
    elif max_range < 0.5:
        return 10
    elif max_range < 1.0:
        return 9
    else:
        return 8


def add_line(geoprob_pipe: GeoProbPipe, fig: go.Figure, layer: str, color: str):
    """Helperfunctie om de lijnen uit de geopackage te vinden en toe te voegen aan de map. Layer is de naam van de
    laag in de geopackage waar de lijn is opgeslagen. Color is de kleur van deze lijn in de map."""

    gdf_traject = gpd.read_file(
        geoprob_pipe.input_data.app_settings.geopackage_filepath, layer=layer
    )
    gdf_traject = gdf_traject.to_crs("EPSG:4326")

    def plot_linestring(ls, display):
        xs, ys = ls.xy
        xs = list(xs)
        ys = list(ys)
        fig.add_trace(
            go.Scattermap(
                lon=xs,
                lat=ys,
                mode="lines",
                line={"color":color, "width":1},
                hoverinfo="none",
                name=layer,
                legendgroup=layer,
                showlegend=display,
            )
        )

    show = True
    for geom in gdf_traject.geometry:
        if isinstance(geom, LineString):
            plot_linestring(geom, show)
            show = False

        elif isinstance(geom, MultiLineString):
            for line in geom.geoms:
                plot_linestring(line, show)
                show = False

        elif isinstance(geom, GeometryCollection):
            for g in geom.geoms:
                if isinstance(g, LineString):
                    plot_linestring(g, show)
                    show = False
                elif isinstance(g, MultiLineString):
                    for line in g.geoms:
                        plot_linestring(line, show)
                        show = False

        else:
            print("Skipping unsupported geometry:", geom.geom_type)

    return fig