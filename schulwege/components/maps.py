from typing import List, Tuple, Union

import branca
from schulwege.models.project import Project
from schulwege.models.segment import Segment
import folium
import branca.colormap as cm
from collections import defaultdict


def overlay_segments(
    segments: List[Segment],
) -> List[Tuple[Tuple[float, float], Tuple[float, float], int, str]]:
    """Overlay segments and sum their frequencies."""

    segment_dict = defaultdict(int)
    for segment in segments:
        start = (segment.lat_from, segment.lon_from)
        end = (segment.lat_to, segment.lon_to)
        segment_dict[(start, end, segment.modality)] += segment.frequency

    overlaid_segments = [
        (start, end, frequency, modality)
        for (start, end, modality), frequency in segment_dict.items()
    ]
    return overlaid_segments


def merge_polylines(segments: List[Segment]) -> List[Tuple[List[Tuple[float, float]], int]]:

    segment_dict = defaultdict(int)
    for segment in segments:
        start = (segment.lat_from, segment.lon_from)
        end = (segment.lat_to, segment.lon_to)
        segment_dict[(start, end)] += segment.frequency

    overlaid_segments = [
        (start, end, frequency) for (start, end), frequency in segment_dict.items()
    ]

    merged_polylines = []
    for start, end, frequency in overlaid_segments:
        for polyline, line_frequency in merged_polylines:
            if polyline[-1] == start and line_frequency == frequency:
                polyline.append(end)
                break
        else:
            merged_polylines.append(([start, end], frequency))

    return merged_polylines


def get_center_coordinates(segments: List[Segment]) -> Tuple[float, float]:
    """Calculate the center coordinates of the segments."""
    latitudes = []
    longitudes = []
    for segment in segments:
        latitudes.extend([segment.lat_from, segment.lat_to])
        longitudes.extend([segment.lon_from, segment.lon_to])
    center_lat = sum(latitudes) / len(latitudes)
    center_lon = sum(longitudes) / len(longitudes)
    return center_lat, center_lon


def segment_heatmap(segments: List[Segment], n_colors: int = 10) -> Tuple[folium.Map, str]:

    merged_polylines = merge_polylines(segments)
    center_coordinates = get_center_coordinates(segments)
    map = folium.Map(location=center_coordinates, zoom_start=13)
    min_freq = min(freq for _, freq in merged_polylines)
    max_freq = max(freq for _, freq in merged_polylines)
    linear_colormap = cm.LinearColormap(
        colors=["green", "yellow", "red"],
        vmin=min_freq,
        vmax=max_freq,
    )
    step_colormap = linear_colormap.to_step(n=n_colors)
    for polyline, frequency in merged_polylines:
        color = step_colormap(frequency)
        folium.PolyLine(
            locations=polyline,
            color=color,
            weight=5,
            opacity=0.8,
            tooltip=f"Häufigkeit: {frequency}",
        ).add_to(map)

    return map, step_colormap._repr_html_()


def segment_modality_map(segments: List[Segment]) -> Tuple[folium.Map, str]:

    center_coordinates = get_center_coordinates(segments)
    map = folium.Map(location=center_coordinates, zoom_start=13)
    all_modalities = set(segment.modality for segment in segments)
    num_modalities = len(all_modalities)
    overlaid_segments = overlay_segments(segments)

    linear_colormap = cm.LinearColormap(
        colors=["blue", "orange", "purple"],
        vmin=0,
        vmax=num_modalities - 1,
    )
    modality_to_index = {modality: index for index, modality in enumerate(all_modalities)}
    step_colormap = linear_colormap.to_step(n=num_modalities)
    for start, end, frequency, modality in overlaid_segments:
        color = step_colormap(modality_to_index[modality])
        folium.PolyLine(
            locations=[start, end],
            color=color,
            weight=5,
            opacity=0.8,
            tooltip=f"Modality: {modality}, Frequency: {frequency}",
        ).add_to(map)

    legend_html = "<div style='font-weight: bold; margin-bottom: 8px;'>"
    # make a single row legend
    for modality, index in modality_to_index.items():
        color = step_colormap(index)
        legend_html += f"<span style='background-color:{color};padding:5px;margin-right:5px;color:white;'>{modality}</span>"
    legend_html += "</div>"

    return map, legend_html


def add_model_config_hints(map: folium.Map, project: Project, model_config: dict) -> None:

    routing = model_config.get("routing", [])
    for i, route_cfg in enumerate(routing):
        folium.Circle(
            location=project.main_location.coordinates,
            radius=route_cfg.get("max_radius", 0),
            color="black",
            fill=False,
            tooltip=(
                f"Max Radius für {route_cfg.get('modality_display_name', 'N/A')}: "
                f"{route_cfg.get('max_radius', 0)} Meter"
            ),
        ).add_to(map)

    return map


def export_project(project: Project) -> str:
    """Export project data to a temporary ZIP file and return the file path.
    In the ZIP file, include a CSV file with segment data and a JSON file with project metadata.
    """
    import csv
    import json
    import os
    import tempfile
    import zipfile

    temp_dir = tempfile.mkdtemp()
    csv_file_path = os.path.join(temp_dir, "segments.csv")
    json_file_path = os.path.join(temp_dir, "project_metadata.json")
    zip_file_path = os.path.join(temp_dir, f"project_{project.id}.zip")

    # Write segments to CSV
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = [
            "id",
            "lat_from",
            "lon_from",
            "lat_to",
            "lon_to",
            "modality",
            "frequency",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for segment in project.segments:
            writer.writerow(
                {
                    "id": segment.id,
                    "lat_from": segment.lat_from,
                    "lon_from": segment.lon_from,
                    "lat_to": segment.lat_to,
                    "lon_to": segment.lon_to,
                    "modality": segment.modality,
                    "frequency": segment.frequency,
                }
            )

    # Write project metadata to JSON
    project_metadata = {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at.isoformat(),
        "main_location": {
            "id": project.main_location.id,
            "name": project.main_location.name,
            "lat": project.main_location.lat,
            "lon": project.main_location.lon,
        },
    }
    with open(json_file_path, mode="w", encoding="utf-8") as json_file:
        json.dump(project_metadata, json_file, indent=4)

    # Create ZIP file
    with zipfile.ZipFile(zip_file_path, mode="w") as zipf:
        zipf.write(csv_file_path, arcname="segments.csv")
        zipf.write(json_file_path, arcname="project_metadata.json")

    return zip_file_path
