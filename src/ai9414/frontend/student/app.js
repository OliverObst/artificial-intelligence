const state = {
  manifest: null,
  session: null,
  serverTrace: null,
  serverSnapshots: [],
  playTimer: null,
  view: {
    playbackSpeed: 1,
    showExploredEdges: true,
    showPrunedBranches: true,
  },
  player: {
    stepIndex: 0,
    mode: "playback",
    liveTrace: null,
    liveSnapshots: [],
    size: "small",
    seed: "",
    message: "",
  },
};

const $ = (id) => document.getElementById(id);

const PYTHON_STUB = `from __future__ import annotations

from typing import Any

from ai9414.search import run_labyrinth_solver


Cell = tuple[int, int]


def parse_cell(raw: list[int] | tuple[int, int]) -> Cell:
    """
    Convert a cell from JSON format into a Python tuple.

    Input:
        raw: A row-column pair such as [1, 1] or (1, 1).

    Output:
        A tuple such as (1, 1).

    Example:
        parse_cell([3, 5]) returns (3, 5).
    """
    return (int(raw[0]), int(raw[1]))


def is_open_cell(labyrinth: dict[str, Any], cell: Cell) -> bool:
    """
    Return True if the given cell can be entered by the search.

    Input:
        labyrinth: A dictionary with keys such as 'rows', 'cols', 'grid',
            'start', and 'exit'.
        cell: A (row, col) pair.

    Output:
        True if the cell is inside the grid and is not a wall.
        False otherwise.

    Maze characters:
        '#': wall
        ' ': open cell
        'S': start
        'E': exit
    """
    row, col = cell
    rows = labyrinth["rows"]
    cols = labyrinth["cols"]
    grid = labyrinth["grid"]

    if row < 0 or row >= rows or col < 0 or col >= cols:
        return False

    return grid[row][col] != "#"


def get_neighbours(labyrinth: dict[str, Any], cell: Cell) -> list[Cell]:
    """
    Return all valid neighbouring cells in a fixed deterministic order.

    Movement order:
        up, right, down, left

    Important:
        The order matters. DFS will follow the first unvisited neighbour it sees.
        That means a different neighbour order changes the search trace.
    """
    row, col = cell
    candidates = [
        (row - 1, col),
        (row, col + 1),
        (row + 1, col),
        (row, col - 1),
    ]
    return [candidate for candidate in candidates if is_open_cell(labyrinth, candidate)]


def reconstruct_path(parents: dict[Cell, Cell | None], goal: Cell) -> list[Cell]:
    """
    Reconstruct the final path from the start cell to the goal cell.

    Input:
        parents: A dictionary mapping each visited cell to the cell from
            which it was first reached. The start cell should map to None.
        goal: The exit cell.
    """
    path: list[Cell] = []
    current: Cell | None = goal

    while current is not None:
        path.append(current)
        current = parents[current]

    path.reverse()
    return path


def make_trace_event(
    step: int,
    action: str,
    cell: Cell | None,
    parent: Cell | None,
    depth: int,
    stack: list[Cell],
) -> dict[str, Any]:
    """
    Build one trace event for the replay.

    The browser uses this event format directly.
    """
    return {
        "step": step,
        "action": action,
        "cell": None if cell is None else [cell[0], cell[1]],
        "parent": None if parent is None else [parent[0], parent[1]],
        "depth": depth,
        "stack": [[row, col] for (row, col) in stack],
    }


def solve_dfs(labyrinth: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the labyrinth using depth-first search and return a full result.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete iterative DFS.

    Student responsibilities:
        - generate valid neighbours
        - run DFS
        - record visited_order
        - reconstruct the final path
        - build the trace list

    ai9414 responsibilities:
        - start the local web server
        - expose the /solve endpoint
        - pass the labyrinth dictionary into this function
        - validate the result shape
        - send the result back to the browser

    Input format:
        {
            "rows": 6,
            "cols": 7,
            "grid": [
                "#######",
                "#S #  #",
                "#  # ##",
                "##   E#",
                "#     #",
                "#######"
            ],
            "start": [1, 1],
            "exit": [3, 5]
        }

    Required return format:
        {
            "algorithm": "dfs",
            "status": "found" or "not_found",
            "trace": [...],
            "path": [[row, col], ...],
            "visited_order": [[row, col], ...],
        }

    Trace actions:
        - start: emit once at the entrance
        - expand: emit when DFS moves into a new cell
        - backtrack: emit when DFS gives up on a branch and pops a cell
        - found: emit once when the exit is reached
        - fail: emit once if the stack empties and no exit path exists

    Suggested plan:
        1. Parse the start and exit cells.
        2. Initialise stack, visited, parents, trace, visited_order, and step.
        3. Emit the start event.
        4. While the stack is not empty:
           - inspect the top cell
           - if it is the goal, reconstruct the path, emit found, and return
           - otherwise take the first unvisited neighbour
           - if one exists, push it and emit expand
           - otherwise pop the current cell and emit backtrack
        5. If the loop finishes, emit fail and return not_found

    Important:
        Keep the result meaningful even without the browser visualisation.
        The browser should simply replay the DFS result you return here.
    """
    start = parse_cell(labyrinth["start"])
    goal = parse_cell(labyrinth["exit"])

    # TODO:
    # Replace the placeholder result below with a full iterative DFS.
    # You are expected to return a complete dictionary with keys:
    # algorithm, status, trace, path, visited_order.
    # The helper functions above are here to keep the task focused on DFS logic.
    trace = [make_trace_event(0, "start", start, None, 0, [start])]
    return {
        "algorithm": "dfs",
        "status": "error",
        "message": "Replace the placeholder code inside solve_dfs with your full DFS implementation.",
        "trace": trace,
        "path": [],
        "visited_order": [[start[0], start[1]]],
    }


if __name__ == "__main__":
    run_labyrinth_solver(solve_dfs)
`;

const PYTHON_REQUIREMENTS = `ai9414
`;

const PYTHON_README = `# labyrinth dfs solver

This folder runs a tiny local solver for the labyrinth search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the DFS logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_labyrinth.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_labyrinth.py and look at:

- get_neighbours(...)
- reconstruct_path(...)
- solve_dfs(...)

The main function is solve_dfs(...).
It receives a maze as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- visited_order
`;

const GRAPH_PYTHON_STUB = `from __future__ import annotations

from typing import Any

from ai9414.search import run_graph_solver


def normalise_node_id(raw: Any) -> str:
    """
    Convert one node id into a Python string.

    Example:
        normalise_node_id("A") returns "A".
    """
    return str(raw)


def build_adjacency(graph: dict[str, Any]) -> dict[str, list[str]]:
    """
    Build an adjacency list from the graph dictionary.

    The graph uses this format:
        {
            "nodes": [{"id": "A", "x": 0.1, "y": 0.2}, ...],
            "edges": [{"u": "A", "v": "B"}, ...],
            "start": "A",
            "goal": "G"
        }
    """
    adjacency = {str(node["id"]): [] for node in graph["nodes"]}
    for edge in graph["edges"]:
        left = str(edge["u"])
        right = str(edge["v"])
        adjacency[left].append(right)
        adjacency[right].append(left)
    for node_id in adjacency:
        adjacency[node_id].sort()
    return adjacency


def get_neighbours(adjacency: dict[str, list[str]], node_id: str) -> list[str]:
    """
    Return neighbouring nodes in deterministic DFS order.

    Important:
        The order matters. DFS follows the first unvisited neighbour it sees.
    """
    return list(adjacency[node_id])


def reconstruct_path(parents: dict[str, str | None], goal: str) -> list[str]:
    """
    Reconstruct the final path from the start node to the goal node.
    """
    path: list[str] = []
    current: str | None = goal
    while current is not None:
        path.append(current)
        current = parents[current]
    path.reverse()
    return path


def make_trace_event(
    step: int,
    action: str,
    node_id: str | None,
    parent: str | None,
    depth: int,
    stack: list[str],
) -> dict[str, Any]:
    """
    Build one trace event for the replay.

    The browser uses this event format directly.
    """
    return {
        "step": step,
        "action": action,
        "node": node_id,
        "parent": parent,
        "depth": depth,
        "stack": list(stack),
    }


def solve_dfs(graph: dict[str, Any]) -> dict[str, Any]:
    """
    Solve the graph using depth-first search and return a full result.

    This is the main function you are expected to implement.
    You should replace the TODO section below with a complete iterative DFS.

    Student responsibilities:
        - build or use an adjacency structure
        - run DFS
        - record visited_order
        - reconstruct the final path
        - build the trace list

    ai9414 responsibilities:
        - start the local web server
        - expose the /solve endpoint
        - pass the graph dictionary into this function
        - validate the result shape
        - send the result back to the browser

    Required return format:
        {
            "algorithm": "dfs",
            "status": "found" or "not_found",
            "trace": [...],
            "path": ["A", "B", "G"],
            "visited_order": ["A", "B", "D", "G"],
        }

    Trace actions:
        - start: emit once at the start node
        - expand: emit when DFS moves into a new node
        - backtrack: emit when DFS gives up on a branch and pops a node
        - found: emit once when the goal is reached
        - fail: emit once if the stack empties and no goal path exists
    """
    start = normalise_node_id(graph["start"])
    goal = normalise_node_id(graph["goal"])
    adjacency = build_adjacency(graph)
    _ = (goal, adjacency)

    # TODO:
    # Replace the placeholder result below with a full iterative DFS.
    trace = [make_trace_event(0, "start", start, None, 0, [start])]
    return {
        "algorithm": "dfs",
        "status": "error",
        "message": "Replace the placeholder code inside solve_dfs with your full DFS implementation.",
        "trace": trace,
        "path": [],
        "visited_order": [start],
    }


if __name__ == "__main__":
    run_graph_solver(solve_dfs)
`;

const GRAPH_PYTHON_REQUIREMENTS = `ai9414
`;

const GRAPH_PYTHON_README = `# graph dfs solver

This folder runs a tiny local solver for the spatial graph search example.
The web-app connection is handled for you by ai9414.
Your job is to implement the DFS logic.

## install

Install the dependency with:

    pip install -r requirements.txt

## run

Start the local solver with:

    python solve_graph.py

The solver starts on the local port expected by the browser app.

## what to implement

Open solve_graph.py and look at:

- build_adjacency(...)
- get_neighbours(...)
- reconstruct_path(...)
- solve_dfs(...)

The main function is solve_dfs(...).
It receives a graph as a Python dictionary and must return a dictionary containing:

- algorithm
- status
- trace
- path
- visited_order
`;

const $svgNode = (name, attributes = {}, text = "") => {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => {
    node.setAttribute(key, String(value));
  });
  if (text) {
    node.textContent = text;
  }
  return node;
};

const clone = (value) => JSON.parse(JSON.stringify(value));

const appType = () => state.manifest?.app_type;
const isLabyrinth = () => appType() === "labyrinth";
const isGraphDfs = () => appType() === "graph_dfs";
const isWeightedSearch = () => appType() === "search";
const isLivePythonApp = () => isLabyrinth() || isGraphDfs();

const CRC32_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let index = 0; index < 256; index += 1) {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) {
      value = (value & 1) !== 0 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    }
    table[index] = value >>> 0;
  }
  return table;
})();

function crc32(bytes) {
  let crc = 0xffffffff;
  bytes.forEach((byte) => {
    crc = CRC32_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  });
  return (crc ^ 0xffffffff) >>> 0;
}

function writeUint16(view, offset, value) {
  view.setUint16(offset, value, true);
}

function writeUint32(view, offset, value) {
  view.setUint32(offset, value >>> 0, true);
}

function concatUint8Arrays(chunks) {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const output = new Uint8Array(totalLength);
  let offset = 0;
  chunks.forEach((chunk) => {
    output.set(chunk, offset);
    offset += chunk.length;
  });
  return output;
}

function createZipArchive(files) {
  const encoder = new TextEncoder();
  const localParts = [];
  const centralParts = [];
  let localOffset = 0;

  files.forEach((file) => {
    const nameBytes = encoder.encode(file.name);
    const dataBytes = encoder.encode(file.content);
    const checksum = crc32(dataBytes);

    const localHeader = new Uint8Array(30);
    const localView = new DataView(localHeader.buffer);
    writeUint32(localView, 0, 0x04034b50);
    writeUint16(localView, 4, 20);
    writeUint16(localView, 6, 0);
    writeUint16(localView, 8, 0);
    writeUint16(localView, 10, 0);
    writeUint16(localView, 12, 0);
    writeUint32(localView, 14, checksum);
    writeUint32(localView, 18, dataBytes.length);
    writeUint32(localView, 22, dataBytes.length);
    writeUint16(localView, 26, nameBytes.length);
    writeUint16(localView, 28, 0);
    localParts.push(localHeader, nameBytes, dataBytes);

    const centralHeader = new Uint8Array(46);
    const centralView = new DataView(centralHeader.buffer);
    writeUint32(centralView, 0, 0x02014b50);
    writeUint16(centralView, 4, 20);
    writeUint16(centralView, 6, 20);
    writeUint16(centralView, 8, 0);
    writeUint16(centralView, 10, 0);
    writeUint16(centralView, 12, 0);
    writeUint16(centralView, 14, 0);
    writeUint32(centralView, 16, checksum);
    writeUint32(centralView, 20, dataBytes.length);
    writeUint32(centralView, 24, dataBytes.length);
    writeUint16(centralView, 28, nameBytes.length);
    writeUint16(centralView, 30, 0);
    writeUint16(centralView, 32, 0);
    writeUint16(centralView, 34, 0);
    writeUint16(centralView, 36, 0);
    writeUint32(centralView, 38, 0);
    writeUint32(centralView, 42, localOffset);
    centralParts.push(centralHeader, nameBytes);

    localOffset += localHeader.length + nameBytes.length + dataBytes.length;
  });

  const localData = concatUint8Arrays(localParts);
  const centralDirectory = concatUint8Arrays(centralParts);

  const endRecord = new Uint8Array(22);
  const endView = new DataView(endRecord.buffer);
  writeUint32(endView, 0, 0x06054b50);
  writeUint16(endView, 4, 0);
  writeUint16(endView, 6, 0);
  writeUint16(endView, 8, files.length);
  writeUint16(endView, 10, files.length);
  writeUint32(endView, 12, centralDirectory.length);
  writeUint32(endView, 16, localData.length);
  writeUint16(endView, 20, 0);

  return new Blob([localData, centralDirectory, endRecord], {
    type: "application/zip",
  });
}

function deepMerge(base, patch) {
  Object.entries(patch || {}).forEach(([key, value]) => {
    if (
      value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      base[key] &&
      typeof base[key] === "object" &&
      !Array.isArray(base[key])
    ) {
      deepMerge(base[key], value);
      return;
    }
    base[key] = clone(value);
  });
  return base;
}

function buildSnapshots(trace) {
  const initial = clone(trace.initial_state || {});
  const snapshots = [initial];
  let current = clone(initial);
  (trace.steps || []).forEach((step) => {
    current = deepMerge(clone(current), step.state_patch || {});
    snapshots.push(clone(current));
  });
  return snapshots;
}

function formatNumber(value, digits = 3) {
  return value === null || value === undefined ? "none" : Number(value).toFixed(digits);
}

function cellKey(cell) {
  return `${cell[0]},${cell[1]}`;
}

function edgeId(u, v) {
  return [u, v].sort().join("--");
}

function pathToEdgeIds(path) {
  const ids = new Set();
  for (let index = 0; index < path.length - 1; index += 1) {
    ids.add(edgeId(path[index], path[index + 1]));
  }
  return ids;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error?.message || "Request failed");
  }
  return payload;
}

async function postAction(action, payload = {}) {
  return requestJson("/api/action", {
    method: "POST",
    body: JSON.stringify({ action, payload }),
  });
}

async function loadApp() {
  const [manifest, session, trace, examplesPayload] = await Promise.all([
    requestJson("/api/manifest"),
    requestJson("/api/state"),
    requestJson("/api/trace"),
    requestJson("/api/examples"),
  ]);

  state.manifest = manifest;
  state.session = session;
  state.serverTrace = trace;
  state.serverSnapshots = buildSnapshots(trace);
  state.view.playbackSpeed = Number(session.options.playback_speed || 1);
  state.player.mode = "playback";
  if (session.data.live_python) {
    state.player.size = session.data.live_python.size;
    state.player.seed = session.data.live_python.seed;
  }
  populateExamples(examplesPayload.examples || []);
  syncControls();
  render();
}

function populateExamples(examples) {
  const select = $("example-select");
  select.innerHTML = "";
  examples.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = isLabyrinth() ? `${name}` : name;
    if (name === state.session.example_name) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function populateSizeOptions() {
  const select = $("size-select");
  const availableSizes = state.session?.data?.live_python?.available_sizes || ["small", "medium", "large"];
  select.innerHTML = "";
  availableSizes.forEach((size) => {
    const option = document.createElement("option");
    option.value = size;
    option.textContent = size;
    if (size === state.player.size) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function syncControls() {
  populateSizeOptions();
  $("speed-select").value = String(state.view.playbackSpeed);
  $("show-explored").checked = state.view.showExploredEdges;
  $("show-pruned").checked = state.view.showPrunedBranches;
  $("mode-select").value = state.player.mode;
  $("size-select").value = state.player.size;
  $("seed-input").value = state.player.seed || "";
}

function setMessage(message) {
  state.player.message = message;
}

function stopPlay() {
  if (state.playTimer) {
    window.clearInterval(state.playTimer);
    state.playTimer = null;
  }
}

function playIntervalMs() {
  return Math.round(850 / state.view.playbackSpeed);
}

function blankLabyrinthTrace(labyrinth) {
  const start = labyrinth.start;
  return {
    app_type: "labyrinth",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated labyrinth",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a labyrinth, then solve it in live Python mode.",
      algorithm_label: "Depth-first search",
      algorithm_note:
        "This view is ready for DFS reachability. Solve the current labyrinth with Python to populate the trace.",
      goal_label: "Find any path from start to exit",
      labyrinth,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: `(${start[0]},${start[1]})`,
            cell: clone(start),
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        current_route: [clone(start)],
        visited_order: [clone(start)],
        dead_end_cells: [],
        final_path: [],
        explored_count: 1,
        current_depth: 0,
        status: "searching",
        found: false,
      },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function blankGraphDfsTrace(graph) {
  const start = graph.start;
  return {
    app_type: "graph_dfs",
    initial_state: {
      example_title: state.session?.data?.example_title || "Generated graph",
      example_subtitle:
        state.session?.data?.example_subtitle ||
        "Generate a graph, then solve it in live Python mode.",
      algorithm_label: "Depth-first search",
      algorithm_note:
        "This view is ready for DFS reachability. Solve the current graph with Python to populate the trace.",
      goal_label: "Find any path from start to goal",
      graph,
      tree: {
        nodes: [
          {
            tree_id: "t0",
            graph_node: start,
            parent: null,
            depth: 0,
            path_cost: 0,
            status: "active",
            order: 0,
            x: 0.5,
            y: 0.12,
          },
        ],
      },
      search: {
        active_tree_node: "t0",
        active_tree_path: ["t0"],
        current_graph_path: [start],
        visited_order: [start],
        dead_end_nodes: [],
        final_graph_path: [],
        explored_graph_edges: [],
        explored_count: 1,
        current_depth: 0,
        status: "searching",
        found: false,
      },
    },
    steps: [],
    summary: { step_count: 0, result: "ready" },
  };
}

function layoutTreeNodes(nodes) {
  const children = new Map();
  const depthMap = new Map();
  const orderMap = new Map();
  nodes.forEach((node) => {
    const parentKey = node.parent || "__root__";
    if (!children.has(parentKey)) {
      children.set(parentKey, []);
    }
    children.get(parentKey).push(node.tree_id);
    depthMap.set(node.tree_id, Number(node.depth));
    orderMap.set(node.tree_id, Number(node.order));
  });
  Array.from(children.values()).forEach((siblings) => {
    siblings.sort((left, right) => orderMap.get(left) - orderMap.get(right));
  });

  const xPositions = new Map();
  let cursor = 0;

  function assign(treeId) {
    const branch = children.get(treeId) || [];
    if (!branch.length) {
      cursor += 1;
      xPositions.set(treeId, cursor);
      return cursor;
    }
    const positions = branch.map(assign);
    const average = positions.reduce((sum, value) => sum + value, 0) / positions.length;
    xPositions.set(treeId, average);
    return average;
  }

  (children.get("__root__") || []).forEach(assign);
  const maxX = Math.max(...xPositions.values(), 1);
  const maxDepth = Math.max(...depthMap.values(), 0);

  return nodes.map((node) => ({
    ...node,
    x: 0.08 + ((xPositions.get(node.tree_id) - 1) / Math.max(maxX - 1, 1)) * 0.84,
    y: 0.12 + (depthMap.get(node.tree_id) / Math.max(maxDepth, 1)) * 0.76,
  }));
}

function buildLabyrinthTraceFromBackend(labyrinth, result) {
  if (!Array.isArray(result.trace) || !Array.isArray(result.path) || !Array.isArray(result.visited_order)) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByCell = new Map();
  const deadEndCells = [];
  const deadEndSet = new Set();
  const visitedOrder = [];
  const activeTreePath = [];
  let currentRoute = [clone(labyrinth.start)];
  let currentTreeId = "t0";
  let counter = 1;
  let finalPath = [];
  let searchStatus = "searching";

  const root = {
    tree_id: "t0",
    graph_node: `(${labyrinth.start[0]},${labyrinth.start[1]})`,
    cell: clone(labyrinth.start),
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByCell.set(cellKey(labyrinth.start), "t0");
  visitedOrder.push(clone(labyrinth.start));
  activeTreePath.push("t0");

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        current_route: clone(currentRoute),
        visited_order: clone(visitedOrder),
        dead_end_cells: clone(deadEndCells),
        final_path: clone(finalPath),
        explored_count: visitedOrder.length,
        current_depth: Math.max(currentRoute.length - 1, 0),
        status: searchStatus,
        found: finalPath.length > 0,
      },
    };
  }

  result.trace.forEach((step, index) => {
    const action = step.action;
    const cell = Array.isArray(step.cell) ? clone(step.cell) : null;
    const parent = Array.isArray(step.parent) ? clone(step.parent) : null;

    if (action === "start") {
      currentRoute = clone(step.stack || [labyrinth.start]);
      searchStatus = "searching";
    } else if (action === "expand") {
      const parentId = treeIdByCell.get(cellKey(parent));
      const treeId = `t${counter}`;
      counter += 1;
      treeNodes.set(treeId, {
        tree_id: treeId,
        graph_node: `(${cell[0]},${cell[1]})`,
        cell,
        parent: parentId,
        depth: Number(step.depth || 0),
        path_cost: Number(step.depth || 0),
        status: "active",
        order: visibleTreeIds.length,
      });
      visibleTreeIds.push(treeId);
      treeIdByCell.set(cellKey(cell), treeId);
      currentRoute = clone(step.stack || []);
      if (!visitedOrder.some((item) => cellKey(item) === cellKey(cell))) {
        visitedOrder.push(cell);
      }
      activeTreePath.length = 0;
      currentRoute.forEach((routeCell) => {
        const routeTreeId = treeIdByCell.get(cellKey(routeCell));
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      currentTreeId = treeId;
      if (parentId && treeNodes.get(parentId)) {
        treeNodes.get(parentId).status = "expanded";
      }
      searchStatus = "searching";
    } else if (action === "backtrack") {
      currentRoute = clone(step.stack || []);
      activeTreePath.length = 0;
      currentRoute.forEach((routeCell) => {
        const routeTreeId = treeIdByCell.get(cellKey(routeCell));
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      const backtrackedTreeId = treeIdByCell.get(cellKey(cell));
      if (backtrackedTreeId && treeNodes.get(backtrackedTreeId)) {
        treeNodes.get(backtrackedTreeId).status = "backtracked";
      }
      if (cell && !deadEndSet.has(cellKey(cell))) {
        deadEndSet.add(cellKey(cell));
        deadEndCells.push(cell);
      }
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
      searchStatus = "backtracking";
    } else if (action === "found") {
      if (cell && !treeIdByCell.has(cellKey(cell))) {
        const parentId = treeIdByCell.get(cellKey(parent));
        const treeId = `t${counter}`;
        counter += 1;
        treeNodes.set(treeId, {
          tree_id: treeId,
          graph_node: `(${cell[0]},${cell[1]})`,
          cell,
          parent: parentId,
          depth: Number(step.depth || 0),
          path_cost: Number(step.depth || 0),
          status: "final",
          order: visibleTreeIds.length,
        });
        visibleTreeIds.push(treeId);
        treeIdByCell.set(cellKey(cell), treeId);
      }
      currentRoute = clone(step.stack || []);
      finalPath = clone(step.stack || []);
      activeTreePath.length = 0;
      currentRoute.forEach((routeCell) => {
        const routeTreeId = treeIdByCell.get(cellKey(routeCell));
        if (routeTreeId) {
          activeTreePath.push(routeTreeId);
          treeNodes.get(routeTreeId).status = "final";
        }
      });
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      searchStatus = "exit found";
    } else if (action === "fail") {
      currentRoute = [];
      activeTreePath.length = 0;
      currentTreeId = null;
      searchStatus = "no path";
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start DFS"
          : action === "expand"
            ? `Expand (${cell[0]},${cell[1]})`
            : action === "backtrack"
              ? `Backtrack from (${cell[0]},${cell[1]})`
              : action === "found"
                ? "Exit found"
                : "No path found",
      annotation:
        action === "start"
          ? "The maze is ready. DFS starts at the entrance."
          : action === "expand"
            ? `DFS steps into (${cell[0]},${cell[1]}) and keeps exploring.`
            : action === "backtrack"
              ? `DFS retreats from (${cell[0]},${cell[1]}) after reaching a dead end.`
              : action === "found"
                ? "DFS has reached the exit and the successful path is now highlighted."
                : "DFS has exhausted the reachable maze without finding an exit.",
      teaching_note:
        action === "found"
          ? "Plain DFS stops as soon as it finds any exit path."
          : "The tree shows search history, while the maze view shows spatial movement.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankLabyrinthTrace(labyrinth).initial_state;
  initialState.example_title = "Live Python labyrinth";
  initialState.example_subtitle = "Trace returned by your local Python DFS backend.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "labyrinth",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function buildGraphDfsTraceFromBackend(graph, result) {
  if (!Array.isArray(result.trace) || !Array.isArray(result.path) || !Array.isArray(result.visited_order)) {
    throw new Error("Solver returned invalid data.");
  }

  const rawSnapshots = [];
  const treeNodes = new Map();
  const visibleTreeIds = [];
  const treeIdByNode = new Map();
  const deadEndNodes = [];
  const deadEndSet = new Set();
  const visitedOrder = [];
  const activeTreePath = [];
  const exploredEdgeIds = new Set();
  let currentGraphPath = [graph.start];
  let currentTreeId = "t0";
  let counter = 1;
  let finalGraphPath = [];
  let searchStatus = "searching";

  const root = {
    tree_id: "t0",
    graph_node: graph.start,
    parent: null,
    depth: 0,
    path_cost: 0,
    status: "active",
    order: 0,
    x: 0.5,
    y: 0.12,
  };
  treeNodes.set("t0", root);
  visibleTreeIds.push("t0");
  treeIdByNode.set(graph.start, "t0");
  visitedOrder.push(graph.start);
  activeTreePath.push("t0");

  function snapshot() {
    return {
      tree: {
        nodes: visibleTreeIds.map((treeId) => clone(treeNodes.get(treeId))),
      },
      search: {
        active_tree_node: currentTreeId,
        active_tree_path: clone(activeTreePath),
        current_graph_path: clone(currentGraphPath),
        visited_order: clone(visitedOrder),
        dead_end_nodes: clone(deadEndNodes),
        final_graph_path: clone(finalGraphPath),
        explored_graph_edges: Array.from(exploredEdgeIds).map((id) => id.split("--")),
        explored_count: visitedOrder.length,
        current_depth: Math.max(currentGraphPath.length - 1, 0),
        status: searchStatus,
        found: finalGraphPath.length > 0,
      },
    };
  }

  result.trace.forEach((step) => {
    const action = step.action;
    const nodeId = typeof step.node === "string" ? step.node : null;
    const parent = typeof step.parent === "string" ? step.parent : null;

    if (action === "start") {
      currentGraphPath = clone(step.stack || [graph.start]);
      searchStatus = "searching";
    } else if (action === "expand") {
      const parentId = treeIdByNode.get(parent);
      const treeId = `t${counter}`;
      counter += 1;
      treeNodes.set(treeId, {
        tree_id: treeId,
        graph_node: nodeId,
        parent: parentId,
        depth: Number(step.depth || 0),
        path_cost: Number(step.depth || 0),
        status: "active",
        order: visibleTreeIds.length,
      });
      visibleTreeIds.push(treeId);
      treeIdByNode.set(nodeId, treeId);
      if (parent && nodeId) exploredEdgeIds.add(edgeId(parent, nodeId));
      currentGraphPath = clone(step.stack || []);
      if (!visitedOrder.includes(nodeId)) {
        visitedOrder.push(nodeId);
      }
      activeTreePath.length = 0;
      currentGraphPath.forEach((routeNode) => {
        const routeTreeId = treeIdByNode.get(routeNode);
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      currentTreeId = treeId;
      if (parentId && treeNodes.get(parentId)) {
        treeNodes.get(parentId).status = "expanded";
      }
      searchStatus = "searching";
    } else if (action === "backtrack") {
      currentGraphPath = clone(step.stack || []);
      activeTreePath.length = 0;
      currentGraphPath.forEach((routeNode) => {
        const routeTreeId = treeIdByNode.get(routeNode);
        if (routeTreeId) activeTreePath.push(routeTreeId);
      });
      const backtrackedTreeId = treeIdByNode.get(nodeId);
      if (backtrackedTreeId && treeNodes.get(backtrackedTreeId)) {
        treeNodes.get(backtrackedTreeId).status = "backtracked";
      }
      if (nodeId && !deadEndSet.has(nodeId)) {
        deadEndSet.add(nodeId);
        deadEndNodes.push(nodeId);
      }
      currentTreeId = activeTreePath[activeTreePath.length - 1] || "t0";
      if (treeNodes.get(currentTreeId)) {
        treeNodes.get(currentTreeId).status = "active";
      }
      searchStatus = "backtracking";
    } else if (action === "found") {
      if (nodeId && !treeIdByNode.has(nodeId)) {
        const parentId = treeIdByNode.get(parent);
        const treeId = `t${counter}`;
        counter += 1;
        treeNodes.set(treeId, {
          tree_id: treeId,
          graph_node: nodeId,
          parent: parentId,
          depth: Number(step.depth || 0),
          path_cost: Number(step.depth || 0),
          status: "final",
          order: visibleTreeIds.length,
        });
        visibleTreeIds.push(treeId);
        treeIdByNode.set(nodeId, treeId);
      }
      currentGraphPath = clone(step.stack || []);
      finalGraphPath = clone(step.stack || []);
      activeTreePath.length = 0;
      currentGraphPath.forEach((routeNode) => {
        const routeTreeId = treeIdByNode.get(routeNode);
        if (routeTreeId) {
          activeTreePath.push(routeTreeId);
          treeNodes.get(routeTreeId).status = "final";
        }
      });
      currentTreeId = activeTreePath[activeTreePath.length - 1] || currentTreeId;
      searchStatus = "goal found";
    } else if (action === "fail") {
      currentGraphPath = [];
      activeTreePath.length = 0;
      currentTreeId = null;
      searchStatus = "no path";
    }

    rawSnapshots.push({
      event_type: action,
      label:
        action === "start"
          ? "Start DFS"
          : action === "expand"
            ? `Expand ${nodeId}`
            : action === "backtrack"
              ? `Backtrack from ${nodeId}`
              : action === "found"
                ? "Goal found"
                : "No path found",
      annotation:
        action === "start"
          ? "The graph is ready. DFS starts at the start node."
          : action === "expand"
            ? `DFS steps into ${nodeId} and keeps exploring.`
            : action === "backtrack"
              ? `DFS retreats from ${nodeId} after exhausting that branch.`
              : action === "found"
                ? "DFS has reached the goal and the successful path is now highlighted."
                : "DFS has exhausted the reachable graph without finding the goal.",
      teaching_note:
        action === "found"
          ? "Plain DFS stops as soon as it finds any goal path."
          : "The tree shows search history, while the graph view shows movement through the original problem.",
      snapshot: snapshot(),
    });
  });

  const laidOutNodes = layoutTreeNodes(visibleTreeIds.map((treeId) => treeNodes.get(treeId)));
  const layoutById = new Map(laidOutNodes.map((node) => [node.tree_id, node]));

  const initialState = blankGraphDfsTrace(graph).initial_state;
  initialState.example_title = "Live Python graph";
  initialState.example_subtitle = "Trace returned by your local Python DFS backend.";
  initialState.tree.nodes = initialState.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);

  const steps = rawSnapshots.map((entry, index) => {
    const snapshot = clone(entry.snapshot);
    snapshot.tree.nodes = snapshot.tree.nodes.map((node) => layoutById.get(node.tree_id) || node);
    return {
      index,
      event_type: entry.event_type,
      label: entry.label,
      annotation: entry.annotation,
      teaching_note: entry.teaching_note,
      state_patch: snapshot,
    };
  });

  return {
    app_type: "graph_dfs",
    initial_state: initialState,
    steps,
    summary: { step_count: steps.length, result: result.status || "found" },
  };
}

function activeTraceContext() {
  if (isWeightedSearch()) {
    return { trace: state.serverTrace, snapshots: state.serverSnapshots };
  }

  const blankTrace = isLabyrinth()
    ? blankLabyrinthTrace(state.session.data.labyrinth)
    : blankGraphDfsTrace(state.session.data.graph);
  const blankSnapshots = buildSnapshots(blankTrace);

  if (state.player.mode === "live") {
    if (state.player.liveTrace) {
      return { trace: state.player.liveTrace, snapshots: state.player.liveSnapshots };
    }
    return { trace: blankTrace, snapshots: blankSnapshots };
  }

  if ((state.serverTrace.steps || []).length > 0) {
    return { trace: state.serverTrace, snapshots: state.serverSnapshots };
  }
  return { trace: blankTrace, snapshots: blankSnapshots };
}

function currentTrace() {
  return activeTraceContext().trace;
}

function currentData() {
  const { snapshots } = activeTraceContext();
  const index = Math.max(0, Math.min(state.player.stepIndex, snapshots.length - 1));
  return snapshots[index] || {};
}

function currentStep() {
  const trace = currentTrace();
  if (!trace.steps?.length || state.player.stepIndex === 0) {
    const data = currentData();
    return {
      event_type: "initialise",
      label: "Initial state",
      annotation: data.algorithm_note || "The replay is ready.",
      teaching_note: "Step forward or press play to start the replay.",
    };
  }
  return trace.steps[state.player.stepIndex - 1];
}

function maxStepCount() {
  return currentTrace().steps?.length || 0;
}

function statusLabel(data, step) {
  if (isLabyrinth() || isGraphDfs()) {
    return data.search?.status || "ready";
  }
  if (data.search?.finished) return "finished";
  if (step.event_type === "backtrack") return "backtracking";
  return "running";
}

function renderPanelCopy(data) {
  if (isLabyrinth()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "The tree grows in DFS order and keeps backtracked branches visible.";
    $("right-panel-title").textContent = "Labyrinth";
    $("right-panel-subtitle").textContent = "The maze view shows the current route, dead ends, and the final discovered path.";
  } else if (isGraphDfs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "The tree grows in DFS order and keeps backtracked branches visible.";
    $("right-panel-title").textContent = "Spatial Graph";
    $("right-panel-subtitle").textContent = "The graph view shows the current route, explored edges, dead ends, and the final discovered path.";
  } else {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Search states appear here as the DFS tree expands.";
    $("right-panel-title").textContent = "Geometric Graph";
    $("right-panel-subtitle").textContent = "The weighted graph stays fixed while the replay highlights the active branch.";
  }
}

function renderMetrics(data) {
  if (isLabyrinth()) {
    $("metric-1-label").textContent = "Explored cells";
    $("metric-1-value").textContent = String(data.search?.explored_count || 0);
    $("metric-2-label").textContent = "Current depth";
    $("metric-2-value").textContent = String(data.search?.current_depth || 0);
    $("metric-3-label").textContent = "Status";
    $("metric-3-value").textContent = data.search?.status || "searching";
    $("metric-4-label").textContent = "Seed";
    $("metric-4-value").textContent = String(data.labyrinth?.seed ?? "none");
    return;
  }

  if (isGraphDfs()) {
    $("metric-1-label").textContent = "Explored nodes";
    $("metric-1-value").textContent = String(data.search?.explored_count || 0);
    $("metric-2-label").textContent = "Current depth";
    $("metric-2-value").textContent = String(data.search?.current_depth || 0);
    $("metric-3-label").textContent = "Status";
    $("metric-3-value").textContent = data.search?.status || "searching";
    $("metric-4-label").textContent = "Seed";
    $("metric-4-value").textContent = String(data.graph?.seed ?? "none");
    return;
  }

  $("metric-1-label").textContent = "Current path cost";
  $("metric-1-value").textContent = formatNumber(data.search?.current_cost);
  $("metric-2-label").textContent = "Best cost";
  $("metric-2-value").textContent = formatNumber(data.search?.best_cost);
  $("metric-3-label").textContent = "Solutions found";
  $("metric-3-value").textContent = String(data.stats?.solutions_found || 0);
  $("metric-4-label").textContent = "Pruned branches";
  $("metric-4-value").textContent = String(data.stats?.pruned || 0);
}

function renderTree(data) {
  const svg = $("search-tree-svg");
  svg.innerHTML = "";
  const nodes = (data.tree?.nodes || []).filter(
    (node) => !state.view.showPrunedBranches || node.status !== "pruned"
  );
  if (!nodes.length) return;

  const nodeMap = new Map(nodes.map((node) => [node.tree_id, node]));
  const activePath = new Set(data.search.active_tree_path || []);
  const bestPath = new Set(data.search.best_tree_path || []);
  const finalPath = new Set((data.search.final_tree_path || []).concat(data.search.active_tree_path || []));
  const links = $svgNode("g");
  const circles = $svgNode("g");

  nodes.forEach((node) => {
    if (!node.parent || !nodeMap.has(node.parent)) return;
    const parent = nodeMap.get(node.parent);
    const classes = ["tree-link"];
    if (activePath.has(node.tree_id) && activePath.has(node.parent)) classes.push("active");
    if (bestPath.has(node.tree_id) && bestPath.has(node.parent)) classes.push("best");
    if (finalPath.has(node.tree_id) && finalPath.has(node.parent)) classes.push("final");
    if (node.status === "pruned") classes.push("pruned");
    links.appendChild(
      $svgNode("line", {
        class: classes.join(" "),
        x1: parent.x * 1000,
        y1: parent.y * 700,
        x2: node.x * 1000,
        y2: node.y * 700,
      })
    );
  });

  nodes.forEach((node) => {
    const classes = ["tree-node", node.status];
    if (data.search.active_tree_node === node.tree_id) classes.push("active");
    if (activePath.has(node.tree_id)) classes.push("branch");
    if (bestPath.has(node.tree_id)) classes.push("best");
    if (finalPath.has(node.tree_id)) classes.push("final");
    const group = $svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    group.appendChild($svgNode("circle", { class: "tree-node-circle", r: isLabyrinth() ? 38 : 34 }));
    const label = isLabyrinth() ? String(node.graph_node).replace(", ", ",") : node.graph_node;
    group.appendChild(
      $svgNode(
        "text",
        { class: isLabyrinth() ? "tree-node-label tree-node-label-labyrinth" : "tree-node-label", y: isLabyrinth() ? 4 : -6 },
        label
      )
    );
    if (isWeightedSearch()) {
      group.appendChild($svgNode("text", { class: "tree-node-cost", y: 24 }, formatNumber(node.path_cost)));
    }
    circles.appendChild(group);
  });

  svg.appendChild(links);
  svg.appendChild(circles);
}

function renderWeightedGraph(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const graph = data.graph;
  if (!graph) return;

  const nodeMap = new Map(graph.nodes.map((node) => [node.id, node]));
  const currentPath = new Set(data.search.current_graph_path || []);
  const bestPath = new Set(data.search.best_graph_path || []);
  const finalPath = new Set(data.search.final_graph_path || []);
  const exploredEdgeIds = new Set(
    (data.search.explored_graph_edges || []).map(([u, v]) => edgeId(u, v))
  );
  const currentEdgeIds = pathToEdgeIds(data.search.current_graph_path || []);
  const bestEdgeIds = pathToEdgeIds(data.search.best_graph_path || []);
  const finalEdgeIds = pathToEdgeIds(data.search.final_graph_path || []);
  const consideredEdgeId = data.search.considered_edge
    ? edgeId(data.search.considered_edge[0], data.search.considered_edge[1])
    : null;

  const baselines = $svgNode("g");
  const costs = $svgNode("g");
  const overlays = $svgNode("g");
  const nodes = $svgNode("g");

  graph.edges.forEach((edge) => {
    const left = nodeMap.get(edge.u);
    const right = nodeMap.get(edge.v);
    const lineProps = {
      x1: left.x * 1000,
      y1: left.y * 700,
      x2: right.x * 1000,
      y2: right.y * 700,
    };
    baselines.appendChild($svgNode("line", { class: "graph-edge", ...lineProps }));
    costs.appendChild(
      $svgNode(
        "text",
        {
          class: "graph-cost",
          x: ((left.x + right.x) / 2) * 1000,
          y: ((left.y + right.y) / 2) * 700 - 8,
        },
        Number(edge.cost).toFixed(2)
      )
    );

    const id = edge.id || edgeId(edge.u, edge.v);
    if (state.view.showExploredEdges && exploredEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay explored", ...lineProps }));
    }
    if (bestEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay best", ...lineProps }));
    }
    if (currentEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay current", ...lineProps }));
    }
    if (consideredEdgeId === id) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay considered", ...lineProps }));
    }
    if (finalEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay final", ...lineProps }));
    }
  });

  graph.nodes.forEach((node) => {
    const classes = ["graph-node"];
    if (node.id === graph.start) classes.push("start");
    if (node.id === graph.goal) classes.push("goal");
    if (currentPath.has(node.id)) classes.push("current");
    if (bestPath.has(node.id)) classes.push("best");
    if (finalPath.has(node.id)) classes.push("final");
    const activeNode = (data.search.current_graph_path || []).slice(-1)[0];
    if (activeNode === node.id) classes.push("active");
    const group = $svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    group.appendChild($svgNode("circle", { class: "graph-node-circle", r: 30 }));
    group.appendChild($svgNode("text", { class: "graph-node-label" }, node.id));
    nodes.appendChild(group);
  });

  svg.appendChild(baselines);
  svg.appendChild(costs);
  svg.appendChild(overlays);
  svg.appendChild(nodes);
}

function renderGraphDfs(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const graph = data.graph;
  if (!graph) return;

  const nodeMap = new Map(graph.nodes.map((node) => [node.id, node]));
  const currentPath = new Set(data.search.current_graph_path || []);
  const visitedNodes = new Set(data.search.visited_order || []);
  const deadEndNodes = new Set(data.search.dead_end_nodes || []);
  const finalPath = new Set(data.search.final_graph_path || []);
  const exploredEdgeIds = new Set(
    (data.search.explored_graph_edges || []).map(([u, v]) => edgeId(u, v))
  );
  const currentEdgeIds = pathToEdgeIds(data.search.current_graph_path || []);
  const finalEdgeIds = pathToEdgeIds(data.search.final_graph_path || []);

  const baselines = $svgNode("g");
  const overlays = $svgNode("g");
  const nodes = $svgNode("g");

  graph.edges.forEach((edge) => {
    const left = nodeMap.get(edge.u);
    const right = nodeMap.get(edge.v);
    const lineProps = {
      x1: left.x * 1000,
      y1: left.y * 700,
      x2: right.x * 1000,
      y2: right.y * 700,
    };
    baselines.appendChild($svgNode("line", { class: "graph-edge", ...lineProps }));

    const id = edge.id || edgeId(edge.u, edge.v);
    if (exploredEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay explored", ...lineProps }));
    }
    if (currentEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay current", ...lineProps }));
    }
    if (finalEdgeIds.has(id)) {
      overlays.appendChild($svgNode("line", { class: "graph-overlay final", ...lineProps }));
    }
  });

  graph.nodes.forEach((node) => {
    const classes = ["graph-node"];
    if (node.id === graph.start) classes.push("start");
    if (node.id === graph.goal) classes.push("goal");
    if (visitedNodes.has(node.id)) classes.push("visited");
    if (deadEndNodes.has(node.id)) classes.push("dead-end");
    if (currentPath.has(node.id)) classes.push("current");
    if (finalPath.has(node.id)) classes.push("final");
    const activeNode = (data.search.current_graph_path || []).slice(-1)[0];
    if (activeNode === node.id) classes.push("active");
    const group = $svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    group.appendChild($svgNode("circle", { class: "graph-node-circle", r: 28 }));
    group.appendChild($svgNode("text", { class: "graph-node-label" }, node.id));
    nodes.appendChild(group);
  });

  svg.appendChild(baselines);
  svg.appendChild(overlays);
  svg.appendChild(nodes);
}

function renderLabyrinth(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const labyrinth = data.labyrinth;
  if (!labyrinth) return;

  const rows = labyrinth.rows;
  const cols = labyrinth.cols;
  const cellSize = Math.min(880 / cols, 620 / rows);
  const offsetX = (1000 - cols * cellSize) / 2;
  const offsetY = (700 - rows * cellSize) / 2;
  const currentRoute = new Set((data.search.current_route || []).map(cellKey));
  const visited = new Set((data.search.visited_order || []).map(cellKey));
  const deadEnds = new Set((data.search.dead_end_cells || []).map(cellKey));
  const finalPath = new Set((data.search.final_path || []).map(cellKey));

  const gridGroup = $svgNode("g");
  const textGroup = $svgNode("g");

  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const cell = [row, col];
      const key = cellKey(cell);
      const value = labyrinth.grid[row][col];
      const classes = ["maze-cell"];
      if (value === "#") {
        classes.push("wall");
      } else {
        classes.push("open");
        if (visited.has(key)) classes.push("visited");
        if (deadEnds.has(key)) classes.push("dead-end");
        if (currentRoute.has(key)) classes.push("current");
        if (finalPath.has(key)) classes.push("final");
        if (row === labyrinth.start[0] && col === labyrinth.start[1]) classes.push("start");
        if (row === labyrinth.exit[0] && col === labyrinth.exit[1]) classes.push("exit");
      }

      gridGroup.appendChild(
        $svgNode("rect", {
          class: classes.join(" "),
          x: offsetX + col * cellSize,
          y: offsetY + row * cellSize,
          width: cellSize,
          height: cellSize,
          rx: Math.max(1, cellSize * 0.14),
        })
      );

      if (value === "S" || value === "E") {
        textGroup.appendChild(
          $svgNode(
            "text",
            {
              class: "maze-cell-label",
              x: offsetX + col * cellSize + cellSize / 2,
              y: offsetY + row * cellSize + cellSize / 2 + Math.min(cellSize * 0.18, 6),
            },
            value
          )
        );
      }
    }
  }

  svg.appendChild(gridGroup);
  svg.appendChild(textGroup);
}

function renderControls() {
  const livePythonApp = isLivePythonApp();
  $("example-control-label").textContent = livePythonApp ? "Configuration" : "Example";
  $("size-control-label").textContent = isGraphDfs() ? "Graph size" : "Labyrinth size";
  $("generate-button").textContent = isGraphDfs() ? "Generate new graph" : "Generate new labyrinth";
  $("mode-control").classList.toggle("hidden", !livePythonApp);
  $("size-control").classList.toggle("hidden", !livePythonApp);
  $("seed-control").classList.toggle("hidden", !livePythonApp);
  $("generate-button").classList.toggle("hidden", !livePythonApp);
  $("solve-python-button").classList.toggle("hidden", !livePythonApp);
  $("download-stub-button").classList.toggle("hidden", !livePythonApp);
  $("reload-button").classList.toggle("hidden", livePythonApp);
  $("search-toggle-grid").classList.toggle("hidden", !isWeightedSearch());
  $("search-legend").classList.toggle("hidden", !isWeightedSearch());
  $("labyrinth-legend").classList.toggle("hidden", !isLabyrinth());
  $("graph-dfs-legend").classList.toggle("hidden", !isGraphDfs());
}

function render() {
  const trace = currentTrace();
  const data = currentData();
  const step = currentStep();
  const max = maxStepCount();

  $("app-title").textContent = state.manifest.app_title;
  $("app-subtitle").textContent =
    data.example_subtitle || state.session.data.example_subtitle || state.session.example_name || "default";
  $("mode-badge").textContent = state.manifest.mode;
  $("execution-badge").textContent = isLivePythonApp() ? state.player.mode : state.manifest.execution_mode;
  $("algorithm-badge").textContent = data.algorithm_label || "search replay";
  $("status-value").textContent = statusLabel(data, step);
  $("step-event").textContent = step.event_type || "initialise";
  $("step-label").textContent = step.label;
  $("step-annotation").textContent = step.annotation || "";
  $("step-note").textContent = step.teaching_note || "";
  $("step-range").max = String(max);
  $("step-range").value = String(state.player.stepIndex);
  $("step-readout").textContent = `${state.player.stepIndex} / ${max}`;
  $("previous-button").disabled = state.player.stepIndex === 0;
  $("next-button").disabled = state.player.stepIndex >= max;
  $("play-button").disabled = max === 0;
  $("pause-button").disabled = !state.playTimer;
  renderPanelCopy(data);
  renderMetrics(data);
  renderControls();

  const banner = $("message-banner");
  if (state.player.message) {
    banner.textContent = state.player.message;
    banner.classList.remove("hidden");
  } else {
    banner.textContent = "";
    banner.classList.add("hidden");
  }

  renderTree(data);
  if (isLabyrinth()) {
    renderLabyrinth(data);
  } else if (isGraphDfs()) {
    renderGraphDfs(data);
  } else {
    renderWeightedGraph(data);
  }
}

function startPlay() {
  stopPlay();
  state.playTimer = window.setInterval(() => {
    if (state.player.stepIndex >= maxStepCount()) {
      stopPlay();
      render();
      return;
    }
    state.player.stepIndex += 1;
    render();
  }, playIntervalMs());
  render();
}

async function refreshFromServer(response) {
  state.session = response.state || state.session;
  state.serverTrace = response.trace || state.serverTrace;
  state.serverSnapshots = buildSnapshots(state.serverTrace);
  state.player.stepIndex = 0;
  state.player.liveTrace = null;
  state.player.liveSnapshots = [];
  if (state.session.data.live_python) {
    state.player.size = state.session.data.live_python.size;
    state.player.seed = state.session.data.live_python.seed;
  }
  syncControls();
  render();
}

async function loadExample(name) {
  stopPlay();
  setMessage("");
  const response = await postAction("load_example", { name });
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  state.player.mode = "playback";
  await refreshFromServer(response);
}

async function generateLabyrinth() {
  stopPlay();
  setMessage("Generating a new solvable labyrinth.");
  render();
  const rawSeed = $("seed-input").value.trim();
  const payload = {
    command: "generate_labyrinth",
    size: $("size-select").value,
  };
  if (rawSeed) {
    payload.seed = Number(rawSeed);
  }
  const response = await postAction("app_command", payload);
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  state.player.mode = "playback";
  await refreshFromServer(response);
  setMessage("Generated a new labyrinth. Playback is ready, and you can switch to live Python mode to compare it with your own solver.");
  render();
}

async function generateGraph() {
  stopPlay();
  setMessage("Generating a new sparse graph.");
  render();
  const rawSeed = $("seed-input").value.trim();
  const payload = {
    command: "generate_graph",
    size: $("size-select").value,
  };
  if (rawSeed) {
    payload.seed = Number(rawSeed);
  }
  const response = await postAction("app_command", payload);
  const trace = await requestJson("/api/trace");
  response.trace = trace;
  state.player.mode = "playback";
  await refreshFromServer(response);
  setMessage("Generated a new graph. Playback is ready, and you can switch to live Python mode to compare it with your own solver.");
  render();
}

async function solveWithPython() {
  stopPlay();
  setMessage("");
  render();
  const backendUrl = state.session.data.live_python?.backend_url || "http://127.0.0.1:9414/solve";
  const problemPayload = isLabyrinth()
    ? { algorithm: "dfs", labyrinth: state.session.data.labyrinth }
    : { algorithm: "dfs", graph: state.session.data.graph };
  const problemData = isLabyrinth() ? state.session.data.labyrinth : state.session.data.graph;

  try {
    const response = await fetch(backendUrl, {
      method: "POST",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(problemPayload),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload?.message || "Python backend returned an error.");
    }
    state.player.liveTrace = isLabyrinth()
      ? buildLabyrinthTraceFromBackend(problemData, payload)
      : buildGraphDfsTraceFromBackend(problemData, payload);
    state.player.liveSnapshots = buildSnapshots(state.player.liveTrace);
    state.player.stepIndex = 0;
    state.player.mode = "live";
    syncControls();
    render();
  } catch (error) {
    let message = "Python backend not reachable. Start the local solver and try again.";
    if (
      error instanceof Error &&
      error.message &&
      !["Failed to fetch", "Load failed", "NetworkError when attempting to fetch resource."].includes(error.message)
    ) {
      message = error.message;
    }
    setMessage(message);
    render();
  }
}

function downloadPythonStub() {
  const archive = createZipArchive(
    isGraphDfs()
      ? [
          { name: "ai9414/solve_graph.py", content: GRAPH_PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: GRAPH_PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: GRAPH_PYTHON_README },
        ]
      : [
          { name: "ai9414/solve_labyrinth.py", content: PYTHON_STUB },
          { name: "ai9414/requirements.txt", content: PYTHON_REQUIREMENTS },
          { name: "ai9414/README.md", content: PYTHON_README },
        ]
  );
  const url = window.URL.createObjectURL(archive);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = isGraphDfs() ? "graph-dfs-python-stub.zip" : "labyrinth-dfs-python-stub.zip";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
  setMessage(
    isGraphDfs()
      ? "Downloaded graph-dfs-python-stub.zip."
      : "Downloaded labyrinth-dfs-python-stub.zip."
  );
  render();
}

function bindEvents() {
  $("previous-button").addEventListener("click", () => {
    stopPlay();
    state.player.stepIndex = Math.max(state.player.stepIndex - 1, 0);
    render();
  });
  $("next-button").addEventListener("click", () => {
    stopPlay();
    state.player.stepIndex = Math.min(state.player.stepIndex + 1, maxStepCount());
    render();
  });
  $("play-button").addEventListener("click", () => startPlay());
  $("pause-button").addEventListener("click", () => {
    stopPlay();
    render();
  });
  $("reset-button").addEventListener("click", () => {
    stopPlay();
    state.player.stepIndex = 0;
    render();
  });
  $("reload-button").addEventListener("click", async () => {
    if (!state.session.example_name) return;
    await loadExample(state.session.example_name);
  });
  $("example-select").addEventListener("change", async (event) => {
    if (isLivePythonApp()) {
      stopPlay();
      state.player.size = event.target.value;
      state.player.seed = "";
      $("size-select").value = state.player.size;
      $("seed-input").value = "";
      if (isGraphDfs()) {
        await generateGraph();
      } else {
        await generateLabyrinth();
      }
      return;
    }
    await loadExample(event.target.value);
  });
  $("mode-select").addEventListener("change", (event) => {
    stopPlay();
    state.player.mode = event.target.value;
    state.player.stepIndex = 0;
    if (state.player.mode === "playback") {
      setMessage("");
    } else if (!state.player.liveTrace) {
      setMessage(
        isGraphDfs()
          ? "Live Python mode is ready. Generate a graph or solve the current one with your backend."
          : "Live Python mode is ready. Generate a labyrinth or solve the current one with your backend."
      );
    }
    render();
  });
  $("size-select").addEventListener("change", (event) => {
    state.player.size = event.target.value;
  });
  $("seed-input").addEventListener("change", (event) => {
    state.player.seed = event.target.value;
  });
  $("speed-select").addEventListener("change", (event) => {
    state.view.playbackSpeed = Number(event.target.value);
  });
  $("show-explored").addEventListener("change", (event) => {
    state.view.showExploredEdges = event.target.checked;
    render();
  });
  $("show-pruned").addEventListener("change", (event) => {
    state.view.showPrunedBranches = event.target.checked;
    render();
  });
  $("step-range").addEventListener("input", (event) => {
    stopPlay();
    state.player.stepIndex = Math.max(0, Math.min(Number(event.target.value), maxStepCount()));
    render();
  });
  $("generate-button").addEventListener("click", async () => {
    if (isGraphDfs()) {
      await generateGraph();
      return;
    }
    await generateLabyrinth();
  });
  $("solve-python-button").addEventListener("click", solveWithPython);
  $("download-stub-button").addEventListener("click", downloadPythonStub);
}

window.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  try {
    await loadApp();
  } catch (error) {
    window.alert(error.message);
  }
});
