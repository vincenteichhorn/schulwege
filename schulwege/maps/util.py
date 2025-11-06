import osmnx as ox


def get_tempo_routes(graph, speed_kmh: float):
    """Get subgraph with edges that have speed less than or equal to speed_kmh."""
    edges = ox.graph_to_gdfs(graph, nodes=False)
    edges["maxspeed"] = edges["maxspeed"].apply(
        lambda x: (
            float(x[0])
            if isinstance(x, list) and x and x[0].replace(".", "", 1).isdigit()
            else float("inf")
        )
    )
    edges = edges[edges["maxspeed"] != float("inf")]

    return edges[edges["maxspeed"] <= speed_kmh]
