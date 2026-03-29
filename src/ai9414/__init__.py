"""Shared ai9414 namespace for educational AI apps."""

from ai9414.core import BaseEducationalApp, launch_app
from ai9414.demo import PlaceholderDemo
from ai9414.graph_dfs import GraphDfsDemo
from ai9414.labyrinth import LabyrinthDemo
from ai9414.search import SearchDemo

__all__ = [
    "BaseEducationalApp",
    "GraphDfsDemo",
    "LabyrinthDemo",
    "PlaceholderDemo",
    "SearchDemo",
    "launch_app",
]
