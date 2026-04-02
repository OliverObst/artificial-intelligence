"""Shared ai9414 namespace for educational AI apps."""

from ai9414.core import BaseEducationalApp, launch_app
from ai9414.csp import CSPDemo
from ai9414.demo import PlaceholderDemo
from ai9414.delivery_csp import DeliveryCSPDemo
from ai9414.graph_astar import GraphAStarDemo
from ai9414.graph_bfs import GraphBfsDemo
from ai9414.graph_dfs import GraphDfsDemo
from ai9414.graph_gbfs import GraphGbfsDemo
from ai9414.graph_ucs import GraphUcsDemo
from ai9414.labyrinth import LabyrinthDemo
from ai9414.logic import DpllDemo
from ai9414.search import SearchDemo
from ai9414.strips import StripsDemo

__all__ = [
    "BaseEducationalApp",
    "CSPDemo",
    "DpllDemo",
    "DeliveryCSPDemo",
    "GraphAStarDemo",
    "GraphBfsDemo",
    "GraphDfsDemo",
    "GraphGbfsDemo",
    "GraphUcsDemo",
    "LabyrinthDemo",
    "PlaceholderDemo",
    "SearchDemo",
    "StripsDemo",
    "launch_app",
]
