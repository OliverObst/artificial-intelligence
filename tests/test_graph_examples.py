from ai9414.graph_astar.examples import build_examples as build_astar_examples
from ai9414.graph_bfs.examples import build_examples as build_bfs_examples
from ai9414.graph_dfs.examples import build_examples as build_dfs_examples
from ai9414.graph_gbfs.examples import build_examples as build_gbfs_examples
from ai9414.graph_ucs.examples import build_examples as build_ucs_examples
from ai9414.search.examples import build_examples as build_search_examples


def test_all_graph_examples_use_conventional_endpoint_labels():
    for build_examples in [
        build_dfs_examples,
        build_bfs_examples,
        build_search_examples,
        build_ucs_examples,
        build_gbfs_examples,
        build_astar_examples,
    ]:
        for example in build_examples().values():
            node_ids = [node.id for node in example.graph.nodes]
            assert example.graph.start == "S"
            assert example.graph.goal == "G"
            assert len(node_ids) == len(set(node_ids))
