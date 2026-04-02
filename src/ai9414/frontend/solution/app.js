const state = {
  trace: null,
  snapshots: [],
  stepIndex: 0,
  playTimer: null,
  view: {
    playbackSpeed: 1,
    showExploredEdges: true,
    showPrunedBranches: true,
    showPlannerTrace: false,
    showCspDomains: true,
    cspViewMode: "trace",
    planningSelectedAction: "",
  },
};

const $ = (id) => document.getElementById(id);
const clone = (value) => JSON.parse(JSON.stringify(value));
const appType = () => state.trace?.app_type;
const isStrips = () => appType() === "strips";
const isLogic = () => appType() === "logic";
const isFoundationModels = () => appType() === "foundation_models";
const isCsp = () => appType() === "csp";
const isDeliveryCsp = () => appType() === "delivery_csp";
const isCspFamily = () => isCsp() || isDeliveryCsp();
const isLabyrinth = () => appType() === "labyrinth";
const isGraphBfs = () => appType() === "graph_bfs";
const isGraphDfs = () => appType() === "graph_dfs";
const isGraphAStar = () => appType() === "graph_astar";
const isGraphGbfs = () => appType() === "graph_gbfs";
const isGraphUcs = () => appType() === "graph_ucs";
const isGraphReachability = () => isGraphDfs() || isGraphBfs();
const isWeightedSearch = () => appType() === "search";
const isWeightedGraphSearch = () => isWeightedSearch() || isGraphUcs() || isGraphGbfs() || isGraphAStar();

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

function svgNode(name, attributes = {}, text = "") {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => {
    node.setAttribute(key, String(value));
  });
  if (text) node.textContent = text;
  return node;
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

function formatLogicLiteral(literal) {
  return literal.replace("~", "¬");
}

async function loadTrace() {
  const response = await fetch("./trace.json");
  state.trace = await response.json();
  state.snapshots = buildSnapshots(state.trace);
  $("solution-title").textContent = state.trace.initial_state.example_title || "Solution replay";
  $("solution-subtitle").textContent = state.trace.initial_state.example_subtitle || "";
  $("solution-algorithm").textContent = state.trace.initial_state.algorithm_label || "search replay";
  render();
}

function currentData() {
  return state.snapshots[state.stepIndex] || {};
}

function currentStep() {
  if (!state.trace.steps?.length || state.stepIndex === 0) {
    return {
      event_type: "initialise",
      label: "Initial state",
      annotation: state.trace.initial_state.algorithm_note || "The replay is ready.",
      teaching_note: "Step forward or press play to start the replay.",
    };
  }
  return state.trace.steps[state.stepIndex - 1];
}

function renderPanelCopy() {
  if (isFoundationModels()) {
    $("left-panel-title").textContent = "Tokenisation State";
    $("left-panel-subtitle").textContent =
      "Static replay of the token sequence, token counts, comparisons, and BPE merge learning state.";
    $("right-panel-title").textContent = "Text View";
    $("right-panel-subtitle").textContent =
      "Static replay of the visible text with token boundaries drawn directly onto the input.";
    $("search-toggle-grid").classList.add("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("search-legend").classList.add("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  } else if (isCsp()) {
    $("left-panel-title").textContent = "CSP State";
    $("left-panel-subtitle").textContent = "Static replay of the variables, domains, and decision trace.";
    $("right-panel-title").textContent = "Map View";
    $("right-panel-subtitle").textContent = "Static replay of the map colouring and live domain changes on each region.";
    $("search-toggle-grid").classList.add("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.remove("hidden");
    $("csp-toggle-grid").classList.remove("hidden");
    $("search-legend").classList.add("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.remove("hidden");
  } else if (isDeliveryCsp()) {
    $("left-panel-title").textContent = "CSP State";
    $("left-panel-subtitle").textContent = "Static replay of the deliveries, domains, and decision trace.";
    $("right-panel-title").textContent = "Schedule Board";
    $("right-panel-subtitle").textContent = "Static replay of the delivery schedule board, assigned cells, and live candidate badges.";
    $("search-toggle-grid").classList.add("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.remove("hidden");
    $("csp-toggle-grid").classList.remove("hidden");
    $("search-legend").classList.add("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.remove("hidden");
  } else if (isStrips()) {
    $("left-panel-title").textContent = "Planning State";
    $("left-panel-subtitle").textContent =
      "Static replay of the symbolic state, applicable actions, and grounded plan.";
    $("right-panel-title").textContent = "Office World";
    $("right-panel-subtitle").textContent =
      "Static replay of the rendered office map that is derived from the symbolic facts.";
    $("search-toggle-grid").classList.add("hidden");
    $("planning-toggle-grid").classList.remove("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("search-legend").classList.add("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  } else if (isLogic()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Static replay of the DPLL assignment tree.";
    $("right-panel-title").textContent = currentData().problem_mode === "entailment" ? "Knowledge Base and CNF" : "Clause State";
    $("right-panel-subtitle").textContent =
      currentData().problem_mode === "entailment"
        ? "Static replay of the knowledge base view and the CNF used for the entailment test."
        : "Static replay of the clause statuses under the current partial assignment.";
    $("search-toggle-grid").classList.add("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("search-legend").classList.add("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.remove("hidden");
    $("csp-legend").classList.add("hidden");
  } else if (isLabyrinth()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Static replay of the DFS tree built while exploring the labyrinth.";
    $("right-panel-title").textContent = "Labyrinth";
    $("right-panel-subtitle").textContent = "Static replay of the maze route, dead ends, and final discovered path.";
    $("search-toggle-grid").classList.add("hidden");
    $("search-legend").classList.add("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("labyrinth-legend").classList.remove("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  } else if (isGraphBfs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Static replay of the BFS tree built while exploring the graph.";
    $("right-panel-title").textContent = "Spatial Graph";
    $("right-panel-subtitle").textContent = "Static replay of the highlighted route, explored edges, visited nodes, and final discovered path.";
    $("search-toggle-grid").classList.add("hidden");
    $("search-legend").classList.add("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.remove("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  } else if (isGraphDfs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Static replay of the DFS tree built while exploring the graph.";
    $("right-panel-title").textContent = "Spatial Graph";
    $("right-panel-subtitle").textContent = "Static replay of the graph route, explored edges, dead ends, and final discovered path.";
    $("search-toggle-grid").classList.add("hidden");
    $("search-legend").classList.add("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.remove("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  } else if (isGraphAStar()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Static replay of the A* tree built while exploring the weighted graph.";
    $("right-panel-title").textContent = "Weighted Spatial Graph";
    $("right-panel-subtitle").textContent = "Static replay of the cost-plus-heuristic frontier route and final optimal path.";
    $("search-toggle-grid").classList.remove("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("search-legend").classList.remove("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  } else if (isGraphGbfs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Static replay of the greedy best-first tree built while exploring the weighted graph.";
    $("right-panel-title").textContent = "Weighted Spatial Graph";
    $("right-panel-subtitle").textContent = "Static replay of the heuristic-driven route and the final path found.";
    $("search-toggle-grid").classList.remove("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("search-legend").classList.remove("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  } else if (isGraphUcs()) {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Static replay of the UCS tree built while exploring the weighted graph.";
    $("right-panel-title").textContent = "Weighted Spatial Graph";
    $("right-panel-subtitle").textContent = "Static replay of the cheapest frontier route and final optimal path.";
    $("search-toggle-grid").classList.remove("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("search-legend").classList.remove("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  } else {
    $("left-panel-title").textContent = "Search Tree";
    $("left-panel-subtitle").textContent = "Static replay of the precomputed search tree.";
    $("right-panel-title").textContent = "Geometric Graph";
    $("right-panel-subtitle").textContent = "Static replay of the weighted graph.";
    $("search-toggle-grid").classList.remove("hidden");
    $("planning-toggle-grid").classList.add("hidden");
    $("csp-view-control").classList.add("hidden");
    $("csp-toggle-grid").classList.add("hidden");
    $("search-legend").classList.remove("hidden");
    $("labyrinth-legend").classList.add("hidden");
    $("graph-dfs-legend").classList.add("hidden");
    $("logic-legend").classList.add("hidden");
    $("csp-legend").classList.add("hidden");
  }
}

function renderMetrics(data) {
  if (isFoundationModels()) {
    const stats = data.foundation_models?.stats || {};
    $("metric-1-label").textContent = "Characters";
    $("metric-1-value").textContent = String(stats.character_count || 0);
    $("metric-2-label").textContent = "Tokens";
    $("metric-2-value").textContent = String(stats.token_count || 0);
    $("metric-3-label").textContent = "Avg token length";
    $("metric-3-value").textContent = String(stats.average_token_length ?? 0);
    $("metric-4-label").textContent = "Context usage";
    $("metric-4-value").textContent = stats.context_usage || "0 / 64";
    return;
  }
  if (isCsp()) {
    const assigned = Object.keys(data.csp?.assignments || {}).length;
    const total = data.csp?.variables?.length || 0;
    $("metric-1-label").textContent = "Assigned variables";
    $("metric-1-value").textContent = `${assigned} / ${total}`;
    $("metric-2-label").textContent = "Pruned values";
    $("metric-2-value").textContent = String(data.stats?.prunes || 0);
    $("metric-3-label").textContent = "Backtracks";
    $("metric-3-value").textContent = String(data.stats?.backtracks || 0);
    $("metric-4-label").textContent = "Wipe-outs";
    $("metric-4-value").textContent = String(data.stats?.wipeouts || 0);
    return;
  }
  if (isDeliveryCsp()) {
    const assigned = Object.keys(data.delivery_csp?.assignments || {}).length;
    const total = data.delivery_csp?.variables?.length || 0;
    $("metric-1-label").textContent = "Assigned deliveries";
    $("metric-1-value").textContent = `${assigned} / ${total}`;
    $("metric-2-label").textContent = "Pruned values";
    $("metric-2-value").textContent = String(data.stats?.prunes || 0);
    $("metric-3-label").textContent = "Backtracks";
    $("metric-3-value").textContent = String(data.stats?.backtracks || 0);
    $("metric-4-label").textContent = "Wipe-outs";
    $("metric-4-value").textContent = String(data.stats?.wipeouts || 0);
    return;
  }
  if (isStrips()) {
    const planLength = data.planning?.plan?.length || 0;
    $("metric-1-label").textContent = "Plan step";
    $("metric-1-value").textContent = `${data.planning?.plan_index || 0} / ${planLength}`;
    $("metric-2-label").textContent = "Applicable actions";
    $("metric-2-value").textContent = String(data.planning?.applicable_actions?.length || 0);
    $("metric-3-label").textContent = "Expanded states";
    $("metric-3-value").textContent = String(data.stats?.expanded_states || 0);
    $("metric-4-label").textContent = "Frontier peak";
    $("metric-4-value").textContent = String(data.stats?.frontier_peak || 0);
    return;
  }
  if (isLogic()) {
    $("metric-1-label").textContent = "Assigned variables";
    $("metric-1-value").textContent = `${data.logic?.summary?.assigned_variables || 0} / ${data.logic?.summary?.total_variables || 0}`;
    $("metric-2-label").textContent = "Unit clauses";
    $("metric-2-value").textContent = String(data.logic?.summary?.unit || 0);
    $("metric-3-label").textContent = "Forced assignments";
    $("metric-3-value").textContent = String(data.stats?.forced_assignments || 0);
    $("metric-4-label").textContent = "Backtracks";
    $("metric-4-value").textContent = String(data.stats?.backtracks || 0);
    return;
  }
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
  if (isGraphReachability()) {
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
  if (isGraphAStar()) {
    $("metric-1-label").textContent = "Current heuristic";
    $("metric-1-value").textContent = formatNumber(data.search?.current_heuristic);
    $("metric-2-label").textContent = "Current priority";
    $("metric-2-value").textContent = formatNumber(data.search?.current_priority);
    $("metric-3-label").textContent = "Expanded nodes";
    $("metric-3-value").textContent = String(data.stats?.expanded || 0);
    $("metric-4-label").textContent = "Best cost";
    $("metric-4-value").textContent = formatNumber(data.search?.best_cost);
    return;
  }
  if (isGraphGbfs()) {
    $("metric-1-label").textContent = "Current heuristic";
    $("metric-1-value").textContent = formatNumber(data.search?.current_heuristic);
    $("metric-2-label").textContent = "Current path cost";
    $("metric-2-value").textContent = formatNumber(data.search?.current_cost);
    $("metric-3-label").textContent = "Expanded nodes";
    $("metric-3-value").textContent = String(data.stats?.expanded || 0);
    $("metric-4-label").textContent = "Queued nodes";
    $("metric-4-value").textContent = String(data.stats?.enqueued || 0);
    return;
  }
  if (isGraphUcs()) {
    $("metric-1-label").textContent = "Current path cost";
    $("metric-1-value").textContent = formatNumber(data.search?.current_cost);
    $("metric-2-label").textContent = "Best cost";
    $("metric-2-value").textContent = formatNumber(data.search?.best_cost);
    $("metric-3-label").textContent = "Expanded nodes";
    $("metric-3-value").textContent = String(data.stats?.expanded || 0);
    $("metric-4-label").textContent = "Relaxations";
    $("metric-4-value").textContent = String(data.stats?.relaxed || 0);
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

function cspColourValue(problem, colour) {
  return problem?.colour_values?.[colour] || "#d1c6b8";
}

function renderCspTree(container, data) {
  const nodes = data.tree?.nodes || [];
  if (!nodes.length) {
    container.textContent = "The search tree will appear here as assignments are tried.";
    return;
  }

  const svg = svgNode("svg", {
    class: "csp-tree-svg",
    viewBox: "0 0 1000 320",
    role: "img",
    "aria-label": "CSP search tree",
  });
  const nodeMap = new Map(nodes.map((node) => [node.tree_id, node]));
  const activePath = new Set(data.search?.active_tree_path || []);
  const finalPath = new Set(data.search?.final_tree_path || []);
  const links = svgNode("g");
  const cards = svgNode("g");

  nodes.forEach((node) => {
    if (!node.parent || !nodeMap.has(node.parent)) return;
    const parent = nodeMap.get(node.parent);
    const classes = ["csp-tree-link"];
    if (activePath.has(node.tree_id) && activePath.has(node.parent)) classes.push("active");
    if (finalPath.has(node.tree_id) && finalPath.has(node.parent)) classes.push("final");
    links.appendChild(
      svgNode("line", {
        class: classes.join(" "),
        x1: parent.x * 1000,
        y1: parent.y * 320,
        x2: node.x * 1000,
        y2: node.y * 320,
      })
    );
  });

  nodes.forEach((node) => {
    const group = svgNode("g", {
      class: `csp-tree-node ${node.status || ""}`,
      transform: `translate(${node.x * 1000}, ${node.y * 320})`,
    });
    group.appendChild(svgNode("rect", { class: "csp-tree-card", x: -78, y: -30, width: 156, height: 60, rx: 18 }));
    group.appendChild(svgNode("text", { class: "csp-tree-heading", y: -4 }, node.graph_node));
    group.appendChild(svgNode("text", { class: "csp-tree-subtext", y: 16 }, node.assignment_text || "No assignments"));
    cards.appendChild(group);
  });

  svg.append(links, cards);
  container.appendChild(svg);
}

function renderCspPanel(data) {
  const panel = $("csp-panel");
  panel.innerHTML = "";
  const csp = data.csp;
  const problem = data.csp_problem;
  if (!csp || !problem) return;

  const shell = document.createElement("div");
  shell.className = "csp-shell";

  const stateSection = document.createElement("section");
  stateSection.className = "csp-section";
  const stateHeading = document.createElement("h3");
  stateHeading.className = "csp-section-title";
  stateHeading.textContent = "Current CSP state";
  const stateCopy = document.createElement("p");
  stateCopy.className = "csp-copy";
  stateCopy.textContent = `Static replay of the variable table and the current focus region. Focus: ${csp.focus_variable || "none"}.`;
  stateSection.append(stateHeading, stateCopy);

  const table = document.createElement("table");
  table.className = "csp-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Variable</th>
        <th>Current domain</th>
        <th>Assigned</th>
        <th>Status</th>
      </tr>
    </thead>
  `;
  const body = document.createElement("tbody");
  (csp.variables || []).forEach((row) => {
    const tr = document.createElement("tr");
    tr.className = row.status || "unchanged";

    const variable = document.createElement("td");
    variable.textContent = row.variable;

    const domain = document.createElement("td");
    const domainList = document.createElement("div");
    domainList.className = "csp-domain-list";
    if ((row.domain || []).length) {
      row.domain.forEach((colour) => {
        const chip = document.createElement("span");
        chip.className = "csp-domain-chip";
        const dot = document.createElement("span");
        dot.className = "csp-colour-dot";
        dot.style.background = cspColourValue(problem, colour);
        chip.append(dot, document.createTextNode(colour));
        domainList.appendChild(chip);
      });
    } else {
      const chip = document.createElement("span");
      chip.className = "csp-domain-chip empty";
      chip.textContent = "empty";
      domainList.appendChild(chip);
    }
    domain.appendChild(domainList);

    const assigned = document.createElement("td");
    assigned.textContent = row.assigned_value || "—";

    const status = document.createElement("td");
    const pill = document.createElement("span");
    pill.className = `csp-status-pill ${row.status || "unchanged"}`;
    pill.textContent = row.status || "unchanged";
    status.appendChild(pill);

    tr.append(variable, domain, assigned, status);
    body.appendChild(tr);
  });
  table.appendChild(body);
  stateSection.appendChild(table);
  shell.appendChild(stateSection);

  const lowerSection = document.createElement("section");
  lowerSection.className = "csp-section";
  const lowerHeading = document.createElement("h3");
  lowerHeading.className = "csp-section-title";
  lowerHeading.textContent = state.view.cspViewMode === "tree" ? "Search tree" : "Decision trace";
  lowerSection.appendChild(lowerHeading);

  if (state.view.cspViewMode === "tree") {
    renderCspTree(lowerSection, data);
  } else {
    const traceList = document.createElement("div");
    traceList.className = "csp-trace-list";
    (csp.trace_entries || []).forEach((entry, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `csp-trace-row${index === csp.current_entry_index ? " current" : ""}`;
      button.dataset.stepIndex = String(index + 1);
      const meta = document.createElement("span");
      meta.className = "csp-trace-meta";
      meta.textContent = entry.action.replaceAll("_", " ");
      const text = document.createElement("span");
      text.className = "csp-trace-text";
      text.textContent = entry.text;
      button.append(meta, text);
      traceList.appendChild(button);
    });
    lowerSection.appendChild(traceList);
  }

  shell.appendChild(lowerSection);
  panel.appendChild(shell);
}

function renderDeliveryCspPanel(data) {
  const panel = $("csp-panel");
  panel.innerHTML = "";
  const csp = data.delivery_csp;
  const problem = data.delivery_problem;
  if (!csp || !problem) return;

  const valueLookup = new Map((problem.values || []).map((value) => [value.id, value]));
  const shell = document.createElement("div");
  shell.className = "csp-shell";

  const stateSection = document.createElement("section");
  stateSection.className = "csp-section";
  const stateHeading = document.createElement("h3");
  stateHeading.className = "csp-section-title";
  stateHeading.textContent = "Current CSP state";
  const stateCopy = document.createElement("p");
  stateCopy.className = "csp-copy";
  stateCopy.textContent = `Static replay of the delivery table and the current focus delivery. Focus: ${csp.focus_variable || "none"}.`;
  stateSection.append(stateHeading, stateCopy);

  const table = document.createElement("table");
  table.className = "csp-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Delivery</th>
        <th>Current domain</th>
        <th>Assigned</th>
        <th>Status</th>
      </tr>
    </thead>
  `;
  const body = document.createElement("tbody");
  (csp.variables || []).forEach((row) => {
    const tr = document.createElement("tr");
    tr.className = row.status || "unchanged";

    const variable = document.createElement("td");
    const label = document.createElement("div");
    label.className = "delivery-variable-label";
    label.textContent = row.label || row.variable;
    const meta = document.createElement("div");
    meta.className = "delivery-variable-meta";
    meta.textContent = `${row.short_label || row.variable.toUpperCase()} · ${row.variable}`;
    variable.append(label, meta);

    const domain = document.createElement("td");
    const domainList = document.createElement("div");
    domainList.className = "csp-domain-list";
    if ((row.domain || []).length) {
      row.domain.forEach((valueId) => {
        const value = valueLookup.get(valueId);
        const chip = document.createElement("span");
        chip.className = "csp-domain-chip delivery-domain-chip";
        chip.textContent = value?.label || valueId;
        domainList.appendChild(chip);
      });
    } else {
      const chip = document.createElement("span");
      chip.className = "csp-domain-chip empty";
      chip.textContent = "empty";
      domainList.appendChild(chip);
    }
    domain.appendChild(domainList);

    const assigned = document.createElement("td");
    assigned.textContent = row.assigned_label || "—";

    const status = document.createElement("td");
    const pill = document.createElement("span");
    pill.className = `csp-status-pill ${row.status || "unchanged"}`;
    pill.textContent = row.status || "unchanged";
    status.appendChild(pill);

    tr.append(variable, domain, assigned, status);
    body.appendChild(tr);
  });
  table.appendChild(body);
  stateSection.appendChild(table);
  shell.appendChild(stateSection);

  const lowerSection = document.createElement("section");
  lowerSection.className = "csp-section";
  const lowerHeading = document.createElement("h3");
  lowerHeading.className = "csp-section-title";
  lowerHeading.textContent = state.view.cspViewMode === "tree" ? "Search tree" : "Decision trace";
  lowerSection.appendChild(lowerHeading);

  if (state.view.cspViewMode === "tree") {
    renderCspTree(lowerSection, data);
  } else {
    const traceList = document.createElement("div");
    traceList.className = "csp-trace-list";
    (csp.trace_entries || []).forEach((entry, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `csp-trace-row${index === csp.current_entry_index ? " current" : ""}`;
      button.dataset.stepIndex = String(index + 1);
      const meta = document.createElement("span");
      meta.className = "csp-trace-meta";
      meta.textContent = entry.action.replaceAll("_", " ");
      const text = document.createElement("span");
      text.className = "csp-trace-text";
      text.textContent = entry.text;
      button.append(meta, text);
      traceList.appendChild(button);
    });
    lowerSection.appendChild(traceList);
  }

  shell.appendChild(lowerSection);
  panel.appendChild(shell);
}

function renderCspMap(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const problem = data.csp_problem;
  const csp = data.csp;
  if (!problem || !csp) return;

  const assignments = csp.assignments || {};
  const domains = csp.domains || {};
  const changed = new Set((csp.last_changes || []).map((change) => change.variable));
  const focus = csp.focus_variable;
  const failed = csp.failed_variable;
  const polygons = svgNode("g");
  const labels = svgNode("g");
  const markers = svgNode("g");

  (problem.regions || []).forEach((region) => {
    const geometry = problem.geometry?.[region];
    if (!geometry) return;
    const fill = assignments[region] ? cspColourValue(problem, assignments[region]) : "rgba(255, 252, 246, 0.92)";
    const classes = ["csp-region"];
    if (region === focus) classes.push("focus");
    if (changed.has(region)) classes.push("reduced");
    if (region === failed || !(domains[region] || []).length) classes.push("failed");
    polygons.appendChild(
      svgNode("polygon", {
        class: classes.join(" "),
        points: geometry.points.map(([x, y]) => `${x},${y}`).join(" "),
        style: `fill: ${fill};`,
      })
    );
    labels.appendChild(svgNode("text", { class: "csp-region-label", x: geometry.label[0], y: geometry.label[1] }, region.toUpperCase()));
    if (!state.view.showCspDomains || assignments[region]) return;
    const remaining = domains[region] || [];
    const anchor = geometry.domain_anchor || [geometry.label[0], geometry.label[1] + 30];
    if (!remaining.length) {
      markers.appendChild(svgNode("circle", { class: "csp-domain-empty", cx: anchor[0], cy: anchor[1], r: 12 }));
      markers.appendChild(svgNode("line", { class: "csp-domain-cross", x1: anchor[0] - 5, y1: anchor[1] - 5, x2: anchor[0] + 5, y2: anchor[1] + 5 }));
      markers.appendChild(svgNode("line", { class: "csp-domain-cross", x1: anchor[0] + 5, y1: anchor[1] - 5, x2: anchor[0] - 5, y2: anchor[1] + 5 }));
      return;
    }
    const width = (remaining.length - 1) * 22;
    remaining.forEach((colour, index) => {
      markers.appendChild(
        svgNode("circle", {
          class: "csp-domain-marker",
          cx: anchor[0] - width / 2 + index * 22,
          cy: anchor[1],
          r: 8,
          fill: cspColourValue(problem, colour),
        })
      );
    });
  });

  svg.append(polygons, labels, markers);
}

function renderDeliverySchedule(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  svg.setAttribute("viewBox", "0 0 1000 860");
  const problem = data.delivery_problem;
  const csp = data.delivery_csp;
  if (!problem || !csp) return;

  const deliveryMap = new Map((problem.deliveries || []).map((delivery) => [delivery.id, delivery]));
  const changed = new Set((csp.last_changes || []).map((change) => change.variable));
  const focus = csp.focus_variable;
  const failed = csp.failed_variable;
  const placementsByValue = new Map((csp.placements || []).map((placement) => [placement.value, placement]));
  const candidateMap = csp.candidate_map || {};

  const left = 118;
  const top = 92;
  const width = 808;
  const height = 538;
  const footerTop = top + height + 54;
  const rooms = problem.rooms || [];
  const slots = problem.slots || [];
  const cellWidth = width / Math.max(slots.length, 1);
  const cellHeight = height / Math.max(rooms.length, 1);

  const backdrop = svgNode("g");
  const labels = svgNode("g");
  const cells = svgNode("g");
  const overlays = svgNode("g");
  const footer = svgNode("g");

  backdrop.appendChild(
    svgNode("rect", {
      class: "delivery-board",
      x: left - 28,
      y: top - 42,
      width: width + 56,
      height: height + 84,
      rx: 32,
    })
  );

  slots.forEach((slot, slotIndex) => {
    const x = left + slotIndex * cellWidth;
    labels.appendChild(svgNode("text", { class: "delivery-slot-label", x: x + cellWidth / 2, y: top - 18 }, slot.label));
  });

  rooms.forEach((room, roomIndex) => {
    const y = top + roomIndex * cellHeight;
    labels.appendChild(svgNode("text", { class: "delivery-room-label", x: left - 24, y: y + cellHeight / 2 }, room.label));
  });

  rooms.forEach((room, roomIndex) => {
    slots.forEach((slot, slotIndex) => {
      const x = left + slotIndex * cellWidth;
      const y = top + roomIndex * cellHeight;
      const value = (problem.values || []).find((candidate) => candidate.slot === slot.id && candidate.room === room.id);
      if (!value) return;
      const placement = placementsByValue.get(value.id);
      const candidateDeliveries = (candidateMap[value.id] || []).map((deliveryId) => deliveryMap.get(deliveryId)).filter(Boolean);
      const cellFocus = placement?.delivery === focus || candidateDeliveries.some((delivery) => delivery.id === focus);
      const cellChanged = candidateDeliveries.some((delivery) => changed.has(delivery.id));
      const classes = ["delivery-slot-cell"];
      if (cellFocus) classes.push("focus");
      if (cellChanged) classes.push("reduced");
      cells.appendChild(
        svgNode("rect", {
          class: classes.join(" "),
          x,
          y,
          width: cellWidth - 14,
          height: cellHeight - 14,
          rx: 24,
        })
      );
      labels.appendChild(svgNode("text", { class: "delivery-cell-label", x: x + 26, y: y + 32 }, `${slot.label} · ${room.label}`));

      if (placement) {
        const fillColour = placement.colour || deliveryMap.get(placement.delivery)?.colour || "#d8c9b6";
        overlays.appendChild(
          svgNode("rect", {
            class: `delivery-placement-card${placement.delivery === focus ? " focus" : ""}`,
            x: x + 22,
            y: y + 52,
            width: cellWidth - 58,
            height: cellHeight - 84,
            rx: 22,
            style: `fill: ${fillColour};`,
          })
        );
        overlays.appendChild(svgNode("text", { class: "delivery-placement-short", x: x + cellWidth / 2 - 7, y: y + cellHeight / 2 + 2 }, placement.short_label));
        overlays.appendChild(svgNode("text", { class: "delivery-placement-name", x: x + cellWidth / 2 - 7, y: y + cellHeight / 2 + 34 }, placement.label));
      } else if (state.view.showCspDomains) {
        candidateDeliveries.slice(0, 4).forEach((delivery, index) => {
          overlays.appendChild(
            svgNode("rect", {
              class: `delivery-candidate-badge${delivery.id === focus ? " focus" : ""}${changed.has(delivery.id) ? " reduced" : ""}`,
              x: x + 22,
              y: y + 54 + index * 34,
              width: Math.min(cellWidth - 58, 176),
              height: 26,
              rx: 13,
              style: `fill: ${delivery.colour}22; stroke: ${delivery.colour};`,
            })
          );
          overlays.appendChild(svgNode("text", { class: "delivery-candidate-text", x: x + 36, y: y + 71 + index * 34 }, `${delivery.short_label}  ${delivery.label}`));
        });
        if (!candidateDeliveries.length) {
          overlays.appendChild(svgNode("text", { class: "delivery-empty-text", x: x + cellWidth / 2 - 7, y: y + cellHeight / 2 + 10 }, "No candidate"));
        }
      }
    });
  });

  footer.appendChild(svgNode("text", { class: "delivery-footer-heading", x: left - 28, y: footerTop }, "Active constraints"));
  (problem.constraints || []).slice(0, 4).forEach((constraint, index) => {
    footer.appendChild(svgNode("rect", { class: "delivery-constraint-pill", x: left - 28 + index * 188, y: footerTop + 18, width: 180, height: 38, rx: 19 }));
    footer.appendChild(svgNode("text", { class: "delivery-constraint-text", x: left - 10 + index * 188, y: footerTop + 42 }, constraint.label));
  });

  if (failed) {
    const failedLabel = deliveryMap.get(failed)?.label || failed;
    footer.appendChild(svgNode("rect", { class: "delivery-failure-banner", x: left - 28, y: footerTop + 68, width: 480, height: 44, rx: 22 }));
    footer.appendChild(svgNode("text", { class: "delivery-failure-text", x: left - 2, y: footerTop + 96 }, `${failedLabel} has no legal slot-room values left.`));
  }

  svg.append(backdrop, labels, cells, overlays, footer);
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
  const links = svgNode("g");
  const circles = svgNode("g");

  nodes.forEach((node) => {
    if (!node.parent || !nodeMap.has(node.parent)) return;
    const parent = nodeMap.get(node.parent);
    const classes = ["tree-link"];
    if (activePath.has(node.tree_id) && activePath.has(node.parent)) classes.push("active");
    if (bestPath.has(node.tree_id) && bestPath.has(node.parent)) classes.push("best");
    if (finalPath.has(node.tree_id) && finalPath.has(node.parent)) classes.push("final");
    if (node.status === "pruned") classes.push("pruned");
    links.appendChild(
      svgNode("line", {
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
    const group = svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    if (isLogic()) {
      group.appendChild(
        svgNode("rect", {
          class: "tree-node-card",
          x: -76,
          y: -30,
          width: 152,
          height: 60,
          rx: 18,
        })
      );
      group.appendChild(svgNode("text", { class: "tree-node-heading", y: -5 }, node.graph_node));
      group.appendChild(
        svgNode("text", { class: "tree-node-subtext", y: 14 }, node.assignment_text || "No assignments")
      );
      group.appendChild(svgNode("text", { class: "tree-node-reason", y: 28 }, node.reason || ""));
    } else {
      group.appendChild(svgNode("circle", { class: "tree-node-circle", r: isLabyrinth() ? 38 : 34 }));
      const label = isLabyrinth() ? String(node.graph_node).replace(", ", ",") : node.graph_node;
      group.appendChild(
        svgNode(
          "text",
          { class: isLabyrinth() ? "tree-node-label tree-node-label-labyrinth" : "tree-node-label", y: isLabyrinth() ? 4 : -6 },
          label
        )
      );
      if (isWeightedGraphSearch()) {
        group.appendChild(svgNode("text", { class: "tree-node-cost", y: 24 }, formatNumber(node.path_cost)));
      }
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

  const baselines = svgNode("g");
  const costs = svgNode("g");
  const overlays = svgNode("g");
  const nodes = svgNode("g");

  graph.edges.forEach((edge) => {
    const left = nodeMap.get(edge.u);
    const right = nodeMap.get(edge.v);
    const lineProps = {
      x1: left.x * 1000,
      y1: left.y * 700,
      x2: right.x * 1000,
      y2: right.y * 700,
    };
    baselines.appendChild(svgNode("line", { class: "graph-edge", ...lineProps }));
    costs.appendChild(
      svgNode(
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
      overlays.appendChild(svgNode("line", { class: "graph-overlay explored", ...lineProps }));
    }
    if (bestEdgeIds.has(id)) {
      overlays.appendChild(svgNode("line", { class: "graph-overlay best", ...lineProps }));
    }
    if (currentEdgeIds.has(id)) {
      overlays.appendChild(svgNode("line", { class: "graph-overlay current", ...lineProps }));
    }
    if (consideredEdgeId === id) {
      overlays.appendChild(svgNode("line", { class: "graph-overlay considered", ...lineProps }));
    }
    if (finalEdgeIds.has(id)) {
      overlays.appendChild(svgNode("line", { class: "graph-overlay final", ...lineProps }));
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
    const group = svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    group.appendChild(svgNode("circle", { class: "graph-node-circle", r: 30 }));
    group.appendChild(svgNode("text", { class: "graph-node-label" }, node.id));
    nodes.appendChild(group);
  });

  svg.appendChild(baselines);
  svg.appendChild(costs);
  svg.appendChild(overlays);
  svg.appendChild(nodes);
}

function renderGraphReachability(data) {
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

  const baselines = svgNode("g");
  const overlays = svgNode("g");
  const nodes = svgNode("g");

  graph.edges.forEach((edge) => {
    const left = nodeMap.get(edge.u);
    const right = nodeMap.get(edge.v);
    const lineProps = {
      x1: left.x * 1000,
      y1: left.y * 700,
      x2: right.x * 1000,
      y2: right.y * 700,
    };
    baselines.appendChild(svgNode("line", { class: "graph-edge", ...lineProps }));

    const id = edge.id || edgeId(edge.u, edge.v);
    if (exploredEdgeIds.has(id)) {
      overlays.appendChild(svgNode("line", { class: "graph-overlay explored", ...lineProps }));
    }
    if (currentEdgeIds.has(id)) {
      overlays.appendChild(svgNode("line", { class: "graph-overlay current", ...lineProps }));
    }
    if (finalEdgeIds.has(id)) {
      overlays.appendChild(svgNode("line", { class: "graph-overlay final", ...lineProps }));
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
    const group = svgNode("g", {
      class: classes.join(" "),
      transform: `translate(${node.x * 1000}, ${node.y * 700})`,
    });
    group.appendChild(svgNode("circle", { class: "graph-node-circle", r: 28 }));
    group.appendChild(svgNode("text", { class: "graph-node-label" }, node.id));
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
  const gridGroup = svgNode("g");
  const textGroup = svgNode("g");

  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const key = cellKey([row, col]);
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
        svgNode("rect", {
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
          svgNode(
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

function renderLogicProblem(data) {
  const panel = $("logic-problem-panel");
  panel.innerHTML = "";
  const logic = data.logic;
  if (!logic) return;

  const shell = document.createElement("div");
  shell.className = "logic-shell";

  if (logic.mode === "entailment") {
    const callout = document.createElement("div");
    callout.className = "logic-callout";
    callout.textContent =
      "To test entailment, the app checks whether the knowledge base together with not query is unsatisfiable.";
    shell.appendChild(callout);
  }

  const summaryGrid = document.createElement("div");
  summaryGrid.className = "logic-summary-grid";
  [
    ["Satisfied", logic.summary?.satisfied ?? 0],
    ["Unresolved", logic.summary?.unresolved ?? 0],
    ["Unit", logic.summary?.unit ?? 0],
    ["Contradicted", logic.summary?.contradicted ?? 0],
    ["Assigned", `${logic.summary?.assigned_variables ?? 0} / ${logic.summary?.total_variables ?? 0}`],
  ].forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "logic-summary-card";
    const title = document.createElement("span");
    title.className = "logic-summary-label";
    title.textContent = label;
    const body = document.createElement("strong");
    body.className = "logic-summary-value";
    body.textContent = String(value);
    card.append(title, body);
    summaryGrid.appendChild(card);
  });
  shell.appendChild(summaryGrid);

  if (logic.mode === "entailment") {
    const inputPanel = document.createElement("div");
    inputPanel.className = "logic-input-panel";
    const heading = document.createElement("h3");
    heading.className = "logic-section-title";
    heading.textContent = "Knowledge base";
    inputPanel.appendChild(heading);
    const list = document.createElement("div");
    list.className = "logic-input-list";
    (logic.kb_formulas || []).forEach((formula) => {
      const item = document.createElement("div");
      item.className = "logic-input-item";
      item.textContent = formula;
      list.appendChild(item);
    });
    const query = document.createElement("div");
    query.className = "logic-input-item";
    query.textContent = `query: ${logic.query || ""}`;
    list.appendChild(query);
    inputPanel.appendChild(list);
    shell.appendChild(inputPanel);
  }

  const assignmentPanel = document.createElement("div");
  assignmentPanel.className = "logic-assignment-panel";
  const assignmentHeading = document.createElement("h3");
  assignmentHeading.className = "logic-section-title";
  assignmentHeading.textContent = "Current assignment";
  assignmentPanel.appendChild(assignmentHeading);
  if (!logic.assignment?.length) {
    const empty = document.createElement("div");
    empty.className = "logic-assignment-empty";
    empty.textContent = "No variables have been assigned yet.";
    assignmentPanel.appendChild(empty);
  } else {
    const assignmentList = document.createElement("div");
    assignmentList.className = "logic-assignment-list";
    logic.assignment.forEach((entry) => {
      const row = document.createElement("div");
      row.className = "logic-assignment-item";
      const text = document.createElement("span");
      text.className = "logic-assignment-text";
      text.textContent = entry.text;
      const reason = document.createElement("span");
      reason.className = "logic-assignment-reason";
      reason.textContent =
        entry.reason === "decision"
          ? "decision"
          : entry.reason === "unit"
            ? `unit from C${(entry.clause_index ?? 0) + 1}`
            : "pure literal";
      row.append(text, reason);
      assignmentList.appendChild(row);
    });
    assignmentPanel.appendChild(assignmentList);
  }
  shell.appendChild(assignmentPanel);

  const clausePanel = document.createElement("div");
  const clauseHeading = document.createElement("h3");
  clauseHeading.className = "logic-section-title";
  clauseHeading.textContent = "CNF clauses";
  clausePanel.appendChild(clauseHeading);
  const clauseList = document.createElement("div");
  clauseList.className = "logic-clause-list";
  (logic.clauses || []).forEach((clause) => {
    const row = document.createElement("div");
    row.className = `logic-clause-row ${clause.status}`;
    const header = document.createElement("div");
    header.className = "logic-clause-header";
    const label = document.createElement("span");
    label.className = "logic-clause-label";
    label.textContent = `C${clause.index + 1} ${clause.text}`;
    const stateLabel = document.createElement("span");
    stateLabel.className = "logic-clause-state";
    stateLabel.textContent = clause.status;
    header.append(label, stateLabel);
    const literalRow = document.createElement("div");
    literalRow.className = "logic-literal-row";
    (clause.literals || []).forEach((literal) => {
      const chip = document.createElement("span");
      chip.className = `logic-literal-chip ${literal.state}`;
      chip.textContent = literal.text;
      literalRow.appendChild(chip);
    });
    row.append(header, literalRow);
    if (clause.status === "unit" && clause.unit_literal) {
      const footnote = document.createElement("div");
      footnote.className = "logic-clause-footnote";
      footnote.textContent = `Forced literal: ${formatLogicLiteral(clause.unit_literal)}`;
      row.appendChild(footnote);
    }
    clauseList.appendChild(row);
  });
  clausePanel.appendChild(clauseList);
  shell.appendChild(clausePanel);

  panel.appendChild(shell);
}

function planningActionBySignature(data, signature) {
  if (!signature) return null;
  const allActions = [
    ...(data.planning?.applicable_actions || []),
    ...(data.planning?.plan || []),
  ];
  return allActions.find((action) => action.signature === signature) || null;
}

function selectedPlanningAction(data) {
  const selectedFromView = planningActionBySignature(data, state.view.planningSelectedAction);
  if (selectedFromView) return selectedFromView;
  if (data.planning?.selected_action) return data.planning.selected_action;
  if (data.planning?.applicable_actions?.length) return data.planning.applicable_actions[0];
  if (data.planning?.plan?.length) return data.planning.plan[Math.min(data.planning.plan_index || 0, data.planning.plan.length - 1)];
  return null;
}

function planRowState(planIndex, actionIndex) {
  if (planIndex === 0) {
    return actionIndex === 0 ? "current" : "future";
  }
  if (actionIndex < planIndex - 1) return "completed";
  if (actionIndex === planIndex - 1) return "current";
  return "future";
}

function renderPlanningInternal(data) {
  const panel = $("planning-panel");
  panel.innerHTML = "";
  const planning = data.planning;
  if (!planning) return;

  const shell = document.createElement("div");
  shell.className = "planning-shell";

  const factsSection = document.createElement("section");
  factsSection.className = "planning-section";
  const factsHeading = document.createElement("h3");
  factsHeading.className = "planning-section-title";
  factsHeading.textContent = "Current state";
  factsSection.appendChild(factsHeading);
  const factGroups = new Map();
  (planning.facts || []).forEach((fact) => {
    if (!factGroups.has(fact.predicate)) factGroups.set(fact.predicate, []);
    factGroups.get(fact.predicate).push(fact);
  });
  const factGrid = document.createElement("div");
  factGrid.className = "planning-group-grid";
  Array.from(factGroups.entries()).forEach(([predicate, facts]) => {
    const group = document.createElement("div");
    group.className = "planning-group-card";
    const label = document.createElement("span");
    label.className = "planning-group-label";
    label.textContent = predicate;
    const chips = document.createElement("div");
    chips.className = "planning-chip-list";
    facts.forEach((fact) => {
      const chip = document.createElement("span");
      chip.className = "planning-chip";
      chip.textContent = fact.text;
      chips.appendChild(chip);
    });
    group.append(label, chips);
    factGrid.appendChild(group);
  });
  factsSection.appendChild(factGrid);
  shell.appendChild(factsSection);
  const chosenAction = selectedPlanningAction(data);

  const inspectorSection = document.createElement("section");
  inspectorSection.className = "planning-section";
  const inspectorHeading = document.createElement("h3");
  inspectorHeading.className = "planning-section-title";
  inspectorHeading.textContent = "Action schema inspector";
  inspectorSection.appendChild(inspectorHeading);
  const inspector = document.createElement("div");
  inspector.className = "planning-inspector-shell";
  if (chosenAction) {
    const heading = document.createElement("div");
    heading.className = "planning-inspector-heading";
    const signature = document.createElement("span");
    signature.className = "planning-inspector-signature";
    signature.textContent = chosenAction.signature;
    const args = document.createElement("span");
    args.className = "planning-inspector-args";
    args.textContent = chosenAction.args.join(", ");
    heading.append(signature, args);
    inspector.appendChild(heading);

    const effectGrid = document.createElement("div");
    effectGrid.className = "planning-effect-grid";
    [
      ["Preconditions", chosenAction.preconditions || []],
      ["Add effects", chosenAction.add_effects || []],
      ["Delete effects", chosenAction.delete_effects || []],
    ].forEach(([labelText, facts]) => {
      const card = document.createElement("div");
      card.className = "planning-effect-card";
      const label = document.createElement("span");
      label.className = "planning-effect-label";
      label.textContent = labelText;
      const chips = document.createElement("div");
      chips.className = "planning-chip-list";
      facts.forEach((fact) => {
        const chip = document.createElement("span");
        chip.className = "planning-chip";
        chip.textContent = fact.text;
        chips.appendChild(chip);
      });
      card.append(label, chips);
      effectGrid.appendChild(card);
    });
    inspector.appendChild(effectGrid);
  }
  inspectorSection.appendChild(inspector);
  shell.appendChild(inspectorSection);

  const planSection = document.createElement("section");
  planSection.className = "planning-section";
  const planHeading = document.createElement("h3");
  planHeading.className = "planning-section-title";
  planHeading.textContent = "Plan trace";
  planSection.appendChild(planHeading);
  const planList = document.createElement("div");
  planList.className = "planning-plan-list";
  (planning.plan || []).forEach((action, index) => {
    const rowState = planRowState(planning.plan_index || 0, index);
    const button = document.createElement("button");
    button.type = "button";
    button.className = `planning-plan-button ${rowState}`;
    button.dataset.stepIndex = String(index + 2);
    button.dataset.actionSignature = action.signature;
    const signature = document.createElement("span");
    signature.className = "planning-plan-signature";
    signature.textContent = action.signature;
    const meta = document.createElement("span");
    meta.className = "planning-plan-step";
    meta.textContent = `Step ${index + 1}`;
    button.append(signature, meta);
    planList.appendChild(button);
  });
  planSection.appendChild(planList);
  shell.appendChild(planSection);

  if (state.view.showPlannerTrace && (planning.search_trace || []).length) {
    const searchSection = document.createElement("section");
    searchSection.className = "planning-section";
    const searchHeading = document.createElement("h3");
    searchHeading.className = "planning-section-title";
    searchHeading.textContent = "Planner trace";
    searchSection.appendChild(searchHeading);
    const searchList = document.createElement("div");
    searchList.className = "planning-search-trace";
    (planning.search_trace || []).forEach((entry) => {
      const row = document.createElement("div");
      row.className = `planning-search-row${entry.goal_reached ? " goal" : ""}`;
      const meta = document.createElement("div");
      meta.className = "planning-search-meta";
      meta.textContent = `Expand S${entry.index} | depth ${entry.depth} | frontier ${entry.frontier_size}`;
      const plan = document.createElement("div");
      plan.className = "planning-search-plan";
      plan.textContent = entry.plan_prefix.length ? entry.plan_prefix.join(" -> ") : "initial state";
      const facts = document.createElement("div");
      facts.className = "planning-search-facts";
      facts.textContent = entry.state_facts.slice(0, 3).join(" • ");
      row.append(meta, plan, facts);
      searchList.appendChild(row);
    });
    searchSection.appendChild(searchList);
    shell.appendChild(searchSection);
  }

  panel.appendChild(shell);
}

function renderPlanningWorldPanel(data) {
  const panel = $("planning-world-panel");
  panel.innerHTML = "";
  const planning = data.planning;
  if (!planning) return;

  const shell = document.createElement("div");
  shell.className = "planning-world-shell";

  const summarySection = document.createElement("section");
  summarySection.className = "planning-section";
  const summaryHeading = document.createElement("h3");
  summaryHeading.className = "planning-section-title";
  summaryHeading.textContent = "Situation";
  summarySection.appendChild(summaryHeading);

  const world = planning.world || {};
  const summaryCopy = document.createElement("p");
  summaryCopy.className = "planning-world-copy";
  summaryCopy.textContent = [
    `Robot: ${world.robot_room || "unknown"}.`,
    world.parcel_carried
      ? "Parcel: carried by the robot."
      : `Parcel: ${world.parcel_room || "unknown"}.`,
    world.robot_has_keycard
      ? "Keycard: held by the robot."
      : `Keycard: ${world.keycard_room || "unknown"}.`,
    `Door: ${world.door_locked ? "locked" : "unlocked"}.`,
    "Goal: make at(parcel, lab) true.",
  ].join(" ");
  summarySection.appendChild(summaryCopy);

  const summaryGrid = document.createElement("div");
  summaryGrid.className = "planning-world-summary";
  [
    ["Robot", world.robot_room || "unknown"],
    ["Parcel", world.parcel_carried ? "carried" : world.parcel_room || "unknown"],
    ["Keycard", world.robot_has_keycard ? "held" : world.keycard_room || "unknown"],
    ["Door", world.door_locked ? "locked" : "unlocked"],
  ].forEach(([labelText, valueText]) => {
    const card = document.createElement("div");
    card.className = "planning-group-card";
    const label = document.createElement("span");
    label.className = "planning-group-label";
    label.textContent = labelText;
    const value = document.createElement("div");
    value.textContent = valueText;
    card.append(label, value);
    summaryGrid.appendChild(card);
  });
  summarySection.appendChild(summaryGrid);
  shell.appendChild(summarySection);

  const actionsSection = document.createElement("section");
  actionsSection.className = "planning-section";
  const actionsHeading = document.createElement("h3");
  actionsHeading.className = "planning-section-title";
  actionsHeading.textContent = "Available actions";
  actionsSection.appendChild(actionsHeading);
  const actionList = document.createElement("div");
  actionList.className = "planning-action-list";
  const chosenAction = selectedPlanningAction(data);
  (planning.applicable_actions || []).forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `planning-action-button${chosenAction?.signature === action.signature ? " selected" : ""}`;
    button.dataset.actionSignature = action.signature;
    const signature = document.createElement("span");
    signature.className = "planning-action-signature";
    signature.textContent = action.signature;
    const category = document.createElement("span");
    category.className = "planning-action-category";
    category.textContent = action.category;
    button.append(signature, category);
    actionList.appendChild(button);
  });
  actionsSection.appendChild(actionList);
  shell.appendChild(actionsSection);

  panel.appendChild(shell);
}

function renderFoundationInternal(data) {
  const panel = $("foundation-panel");
  panel.innerHTML = "";
  const foundation = data.foundation_models;
  if (!foundation) return;

  const shell = document.createElement("div");
  shell.className = "foundation-shell";

  const tokensSection = document.createElement("section");
  tokensSection.className = "foundation-section";
  const tokensHeading = document.createElement("h3");
  tokensHeading.className = "foundation-section-title";
  tokensHeading.textContent = "Token sequence";
  tokensSection.appendChild(tokensHeading);
  const tokenList = document.createElement("div");
  tokenList.className = "foundation-token-list";
  (foundation.tokens || []).forEach((token) => {
    const card = document.createElement("div");
    card.className = "foundation-token-card";
    const meta = document.createElement("span");
    meta.className = "foundation-token-meta";
    meta.textContent = `token ${token.index}  |  id ${token.token_id}`;
    const text = document.createElement("span");
    text.className = "foundation-token-text";
    text.textContent = token.text;
    card.append(meta, text);
    tokenList.appendChild(card);
  });
  tokensSection.appendChild(tokenList);
  shell.appendChild(tokensSection);

  const comparisonSection = document.createElement("section");
  comparisonSection.className = "foundation-section";
  const comparisonHeading = document.createElement("h3");
  comparisonHeading.className = "foundation-section-title";
  comparisonHeading.textContent = "Comparison";
  comparisonSection.appendChild(comparisonHeading);
  const comparisonGrid = document.createElement("div");
  comparisonGrid.className = "foundation-comparison-grid";
  (foundation.comparison || []).forEach((entry) => {
    const card = document.createElement("div");
    card.className = `foundation-comparison-card${entry.active ? " active" : ""}`;
    const label = document.createElement("span");
    label.className = "foundation-comparison-label";
    label.textContent = entry.label;
    const count = document.createElement("strong");
    count.textContent = `${entry.token_count} tokens`;
    const stats = document.createElement("div");
    stats.className = "foundation-comparison-subtext";
    stats.textContent = `avg ${entry.average_token_length} chars  |  context ${entry.context_usage}`;
    card.append(label, count, stats);
    comparisonGrid.appendChild(card);
  });
  comparisonSection.appendChild(comparisonGrid);
  shell.appendChild(comparisonSection);

  const bpeSection = document.createElement("section");
  bpeSection.className = "foundation-section";
  const bpeHeading = document.createElement("h3");
  bpeHeading.className = "foundation-section-title";
  bpeHeading.textContent = "BPE learning trace";
  bpeSection.appendChild(bpeHeading);
  const bpeGrid = document.createElement("div");
  bpeGrid.className = "foundation-bpe-grid";

  const summaryCard = document.createElement("div");
  summaryCard.className = "foundation-bpe-card";
  const summaryLabel = document.createElement("span");
  summaryLabel.className = "foundation-bpe-label";
  summaryLabel.textContent = "Current merge step";
  const summaryValue = document.createElement("strong");
  summaryValue.textContent = `${foundation.bpe?.merge_step || 0} / ${foundation.bpe?.requested_merges || 0}`;
  summaryCard.append(summaryLabel, summaryValue);
  if (foundation.bpe?.selected_pair) {
    const merge = document.createElement("div");
    merge.className = "foundation-bpe-merge";
    merge.textContent = `${foundation.bpe.selected_pair.left} + ${foundation.bpe.selected_pair.right} -> ${foundation.bpe.selected_pair.merged}`;
    summaryCard.appendChild(merge);
  }
  bpeGrid.appendChild(summaryCard);

  const pairsCard = document.createElement("div");
  pairsCard.className = "foundation-bpe-card";
  const pairsLabel = document.createElement("span");
  pairsLabel.className = "foundation-bpe-label";
  pairsLabel.textContent = "Most frequent pairs";
  pairsCard.appendChild(pairsLabel);
  const pairList = document.createElement("div");
  pairList.className = "foundation-pair-list";
  (foundation.bpe?.pair_counts || []).forEach((entry) => {
    const row = document.createElement("div");
    row.className = "foundation-pair-row";
    const pair = document.createElement("span");
    pair.className = "foundation-pair-text";
    pair.textContent = entry.pair;
    const count = document.createElement("span");
    count.className = "foundation-pair-count";
    count.textContent = `${entry.count}`;
    row.append(pair, count);
    pairList.appendChild(row);
  });
  pairsCard.appendChild(pairList);
  bpeGrid.appendChild(pairsCard);

  const corpusCard = document.createElement("div");
  corpusCard.className = "foundation-bpe-card";
  const corpusLabel = document.createElement("span");
  corpusLabel.className = "foundation-bpe-label";
  corpusLabel.textContent = "Segmented corpus";
  corpusCard.appendChild(corpusLabel);
  const corpusList = document.createElement("div");
  corpusList.className = "foundation-corpus-list";
  (foundation.bpe?.segmented_corpus || []).forEach((line) => {
    const row = document.createElement("div");
    row.className = "foundation-corpus-row";
    row.textContent = line;
    corpusList.appendChild(row);
  });
  corpusCard.appendChild(corpusList);
  bpeGrid.appendChild(corpusCard);

  const mergesCard = document.createElement("div");
  mergesCard.className = "foundation-bpe-card";
  const mergesLabel = document.createElement("span");
  mergesLabel.className = "foundation-bpe-label";
  mergesLabel.textContent = "Learned merges";
  mergesCard.appendChild(mergesLabel);
  const mergeList = document.createElement("div");
  mergeList.className = "foundation-merge-list";
  (foundation.bpe?.learned_merges || []).forEach((entry) => {
    const row = document.createElement("div");
    row.className = "foundation-merge-row";
    row.textContent = entry;
    mergeList.appendChild(row);
  });
  mergesCard.appendChild(mergeList);
  bpeGrid.appendChild(mergesCard);

  bpeSection.appendChild(bpeGrid);
  shell.appendChild(bpeSection);

  panel.appendChild(shell);
}

function renderFoundationTextPanel(data) {
  const panel = $("foundation-text-panel");
  panel.innerHTML = "";
  const foundation = data.foundation_models;
  if (!foundation) return;

  const shell = document.createElement("div");
  shell.className = "foundation-shell";

  const inputSection = document.createElement("section");
  inputSection.className = "foundation-section";
  const inputHeading = document.createElement("h3");
  inputHeading.className = "foundation-section-title";
  inputHeading.textContent = "Current text";
  const inputCopy = document.createElement("p");
  inputCopy.className = "foundation-copy";
  inputCopy.textContent =
    "This exported replay keeps the original text fixed while the merge steps and token boundaries change around it.";
  const textBlock = document.createElement("div");
  textBlock.className = "foundation-corpus-row";
  textBlock.textContent = foundation.text || "";
  inputSection.append(inputHeading, inputCopy, textBlock);
  shell.appendChild(inputSection);

  const overlaySection = document.createElement("section");
  overlaySection.className = "foundation-section";
  const overlayHeading = document.createElement("h3");
  overlayHeading.className = "foundation-section-title";
  overlayHeading.textContent = "Token boundary overlay";
  overlaySection.appendChild(overlayHeading);
  const stream = document.createElement("div");
  stream.className = "foundation-token-stream";
  (foundation.overlay_segments || []).forEach((segment) => {
    if (segment.kind === "whitespace") {
      const space = document.createElement("span");
      space.className = "foundation-space";
      space.textContent = segment.text;
      stream.appendChild(space);
      return;
    }
    const chip = document.createElement("span");
    chip.className = `foundation-token-chip${foundation.mode === "bpe" ? " active" : ""}`;
    chip.textContent = segment.text;
    stream.appendChild(chip);
  });
  overlaySection.appendChild(stream);
  shell.appendChild(overlaySection);

  panel.appendChild(shell);
}

function renderStripsWorld(data) {
  const svg = $("problem-svg");
  svg.innerHTML = "";
  const world = data.planning?.world;
  if (!world?.rooms?.length) return;

  const roomBoxes = {
    mail_room: { x: 90, y: 90, width: 220, height: 110 },
    office_a: { x: 690, y: 90, width: 220, height: 110 },
    corridor: { x: 390, y: 280, width: 220, height: 110 },
    office_b: { x: 90, y: 500, width: 220, height: 110 },
    lab: { x: 690, y: 500, width: 220, height: 110 },
  };
  const roomCenters = Object.fromEntries(
    Object.entries(roomBoxes).map(([room, box]) => [
      room,
      { x: box.x + box.width / 2, y: box.y + box.height / 2 },
    ])
  );

  const connectors = svgNode("g");
  const rooms = svgNode("g");
  const entities = svgNode("g");

  [
    ["corridor", "mail_room"],
    ["corridor", "office_a"],
    ["corridor", "office_b"],
    world.door_edge,
  ].forEach(([left, right]) => {
    const from = roomCenters[left];
    const to = roomCenters[right];
    connectors.appendChild(
      svgNode("line", {
        class: `planning-connector${left === world.door_edge[0] && right === world.door_edge[1] && world.door_locked ? " locked" : ""}`,
        x1: from.x,
        y1: from.y,
        x2: to.x,
        y2: to.y,
      })
    );
  });

  const [doorLeft, doorRight] = world.door_edge;
  const doorFrom = roomCenters[doorLeft];
  const doorTo = roomCenters[doorRight];
  const doorX = (doorFrom.x + doorTo.x) / 2;
  const doorY = (doorFrom.y + doorTo.y) / 2;
  connectors.appendChild(
    svgNode("rect", {
      class: `planning-door-body${world.door_locked ? " locked" : ""}`,
      x: doorX - 34,
      y: doorY - 18,
      width: 68,
      height: 36,
      rx: 12,
    })
  );
  connectors.appendChild(
    svgNode(
      "text",
      {
        class: "planning-door-label",
        x: doorX,
        y: doorY + 4,
      },
      world.door_locked ? "locked" : "open"
    )
  );

  world.rooms.forEach((room) => {
    const box = roomBoxes[room];
    rooms.appendChild(
      svgNode("rect", {
        class: `planning-room${world.robot_room === room ? " active" : ""}`,
        x: box.x,
        y: box.y,
        width: box.width,
        height: box.height,
        rx: 22,
      })
    );
    rooms.appendChild(
      svgNode(
        "text",
        {
          class: "planning-room-label",
          x: box.x + box.width / 2,
          y: box.y + 64,
        },
        room.replace("_", " ")
      )
    );
  });

  function appendEntity(room, label, cssClass, dx, dy) {
    const centre = roomCenters[room];
    const group = svgNode("g", {
      transform: `translate(${centre.x + dx}, ${centre.y + dy})`,
    });
    group.appendChild(svgNode("circle", { class: cssClass, r: 24 }));
    group.appendChild(svgNode("text", { class: "planning-entity-label" }, label));
    entities.appendChild(group);
  }

  if (world.parcel_room) appendEntity(world.parcel_room, "P", "planning-entity-parcel", -58, 26);
  if (world.keycard_room) appendEntity(world.keycard_room, "K", "planning-entity-keycard", 58, 26);
  if (world.robot_room) {
    appendEntity(world.robot_room, "R", "planning-entity-robot", 0, -12);
    const centre = roomCenters[world.robot_room];
    if (world.parcel_carried) {
      entities.appendChild(svgNode("circle", { class: "planning-badge", cx: centre.x + 28, cy: centre.y - 34, r: 12 }));
      entities.appendChild(svgNode("text", { class: "planning-badge-text", x: centre.x + 28, y: centre.y - 30 }, "P"));
    }
    if (world.robot_has_keycard) {
      entities.appendChild(svgNode("circle", { class: "planning-badge", cx: centre.x - 28, cy: centre.y - 34, r: 12 }));
      entities.appendChild(svgNode("text", { class: "planning-badge-text", x: centre.x - 28, y: centre.y - 30 }, "K"));
    }
  }

  svg.appendChild(connectors);
  svg.appendChild(rooms);
  svg.appendChild(entities);
}

function render() {
  const data = currentData();
  const step = currentStep();
  const max = state.trace.steps?.length || 0;
  renderPanelCopy();
  renderMetrics(data);
  $("step-readout").textContent = `${state.stepIndex} / ${max}`;
  $("step-event").textContent = step.event_type || "initialise";
  $("step-label").textContent = step.label;
  $("step-annotation").textContent = step.annotation || "";
  $("step-note").textContent = step.teaching_note || "";
  $("step-range").max = String(max);
  $("step-range").value = String(state.stepIndex);
  $("message-banner").classList.add("hidden");
  $("search-tree-svg").classList.toggle("hidden", isStrips() || isCspFamily() || isFoundationModels());
  $("csp-panel").classList.toggle("hidden", !isCspFamily());
  $("planning-panel").classList.toggle("hidden", !isStrips());
  $("planning-world-panel").classList.toggle("hidden", !isStrips());
  $("foundation-panel").classList.toggle("hidden", !isFoundationModels());
  if (isCsp()) {
    renderCspPanel(data);
  } else if (isDeliveryCsp()) {
    renderDeliveryCspPanel(data);
  } else if (isStrips()) {
    renderPlanningInternal(data);
    renderPlanningWorldPanel(data);
  } else if (isFoundationModels()) {
    renderFoundationInternal(data);
  } else {
    renderTree(data);
  }
  $("problem-svg").classList.toggle("hidden", isLogic() || isFoundationModels());
  $("problem-svg").classList.toggle("delivery-world-canvas", isDeliveryCsp());
  if (!isDeliveryCsp()) {
    $("problem-svg").setAttribute("viewBox", "0 0 1000 700");
  }
  $("logic-problem-panel").classList.toggle("hidden", !isLogic());
  $("foundation-text-panel").classList.toggle("hidden", !isFoundationModels());
  if (isLogic()) {
    renderLogicProblem(data);
  } else if (isFoundationModels()) {
    renderFoundationTextPanel(data);
  } else if (isCsp()) {
    renderCspMap(data);
  } else if (isDeliveryCsp()) {
    renderDeliverySchedule(data);
  } else if (isStrips()) {
    renderStripsWorld(data);
  } else if (isLabyrinth()) {
    renderLabyrinth(data);
  } else if (isGraphReachability()) {
    renderGraphReachability(data);
  } else {
    renderWeightedGraph(data);
  }
}

function stopPlay() {
  if (state.playTimer) {
    window.clearInterval(state.playTimer);
    state.playTimer = null;
  }
}

function startPlay() {
  stopPlay();
  state.playTimer = window.setInterval(() => {
    if (state.stepIndex >= state.trace.steps.length) {
      stopPlay();
      return;
    }
    state.stepIndex += 1;
    render();
  }, Math.round(850 / state.view.playbackSpeed));
}

window.addEventListener("DOMContentLoaded", async () => {
  await loadTrace();

  $("previous-button").addEventListener("click", () => {
    stopPlay();
    state.stepIndex = Math.max(state.stepIndex - 1, 0);
    render();
  });

  $("next-button").addEventListener("click", () => {
    stopPlay();
    state.stepIndex = Math.min(state.stepIndex + 1, state.trace.steps.length);
    render();
  });

  $("play-button").addEventListener("click", () => startPlay());

  $("pause-button").addEventListener("click", () => {
    stopPlay();
  });

  $("reset-button").addEventListener("click", () => {
    stopPlay();
    state.stepIndex = 0;
    render();
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

  $("show-planner-trace").addEventListener("change", (event) => {
    state.view.showPlannerTrace = event.target.checked;
    render();
  });

  $("show-csp-domains").addEventListener("change", (event) => {
    state.view.showCspDomains = event.target.checked;
    render();
  });

  $("csp-view-select").addEventListener("change", (event) => {
    state.view.cspViewMode = event.target.value;
    render();
  });

  $("step-range").addEventListener("input", (event) => {
    stopPlay();
    state.stepIndex = Math.max(0, Math.min(Number(event.target.value), state.trace.steps.length));
    render();
  });

  $("planning-panel").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { actionSignature, stepIndex } = target.dataset;
    if (actionSignature) {
      state.view.planningSelectedAction = actionSignature;
    }
    if (stepIndex) {
      stopPlay();
      state.stepIndex = Math.max(0, Math.min(Number(stepIndex), state.trace.steps.length));
    }
    render();
  });
  $("planning-world-panel").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { actionSignature } = target.dataset;
    if (actionSignature) {
      state.view.planningSelectedAction = actionSignature;
    }
    render();
  });

  $("csp-panel").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { stepIndex } = target.dataset;
    if (!stepIndex) return;
    stopPlay();
    state.stepIndex = Math.max(0, Math.min(Number(stepIndex), state.trace.steps.length));
    render();
  });
});
