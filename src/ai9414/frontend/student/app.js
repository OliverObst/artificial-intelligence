const state = {
  manifest: null,
  session: null,
  trace: null,
  playTimer: null,
};

const $ = (id) => document.getElementById(id);

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

async function loadApp() {
  const [manifest, session, trace, examplesPayload] = await Promise.all([
    requestJson("/api/manifest"),
    requestJson("/api/state"),
    requestJson("/api/trace"),
    requestJson("/api/examples"),
  ]);

  state.manifest = manifest;
  state.session = session;
  state.trace = trace;
  populateExamples(examplesPayload.examples || []);
  syncPaceSelector();
  render();
}

function populateExamples(examples) {
  const select = $("example-select");
  select.innerHTML = "";
  examples.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    if (name === state.session.example_name) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function syncPaceSelector() {
  $("pace-select").value = state.session.options.pace || "normal";
}

function currentStep() {
  const currentIndex = state.session.view.current_step;
  if (!state.trace?.steps?.length || currentIndex === 0) {
    return {
      label: "Initial state",
      annotation: "The placeholder app is ready to demonstrate the infrastructure contracts.",
      teaching_note: "",
    };
  }
  return state.trace.steps[currentIndex - 1];
}

function render() {
  $("app-title").textContent = state.manifest.app_title;
  $("app-subtitle").textContent =
    state.session.config_name || state.session.example_name || "default";
  $("mode-badge").textContent = state.manifest.mode;
  $("execution-badge").textContent = state.manifest.execution_mode;
  $("counter-value").textContent = state.session.data.counter;
  $("status-value").textContent = state.session.data.status;
  $("history-view").textContent = JSON.stringify(state.session.data.history, null, 2);

  const step = currentStep();
  $("step-label").textContent = step.label;
  $("step-annotation").textContent = step.annotation || "";
  $("step-note").textContent = step.teaching_note || "";

  const max = state.trace?.steps?.length || 0;
  $("step-range").max = String(max);
  $("step-range").value = String(state.session.view.current_step);
  $("step-readout").textContent =
    `${state.session.view.current_step} / ${max}`;

  $("previous-button").disabled = state.session.view.current_step === 0;
  $("next-button").disabled =
    state.manifest.execution_mode === "precomputed"
      ? state.session.view.current_step >= max
      : Boolean(state.trace?.is_complete);
}

async function postAction(action, payload = {}) {
  const response = await requestJson("/api/action", {
    method: "POST",
    body: JSON.stringify({ action, payload }),
  });

  if (response.state) {
    state.session = response.state;
  }

  if (response.trace) {
    state.trace = response.trace;
  }

  if (response.new_step) {
    state.trace.steps.push(response.new_step);
    state.trace.summary.step_count = state.trace.steps.length;
  }

  if (response.trace_complete === true) {
    state.trace.is_complete = true;
  }

  render();
}

function stopPlay() {
  if (state.playTimer) {
    window.clearInterval(state.playTimer);
    state.playTimer = null;
  }
  $("play-button").textContent = "Play";
}

function playIntervalMs() {
  const pace = state.session.options.pace || "normal";
  if (pace === "slow") return 1000;
  if (pace === "fast") return 250;
  return 500;
}

function startPlay() {
  stopPlay();
  $("play-button").textContent = "Pause";
  state.playTimer = window.setInterval(async () => {
    const max = state.trace?.steps?.length || 0;
    const atEnd =
      state.manifest.execution_mode === "precomputed"
        ? state.session.view.current_step >= max
        : Boolean(state.trace?.is_complete);

    if (atEnd) {
      stopPlay();
      return;
    }

    try {
      await postAction("next_step");
    } catch (error) {
      stopPlay();
      window.alert(error.message);
    }
  }, playIntervalMs());
}

function bindEvents() {
  $("previous-button").addEventListener("click", () => postAction("previous_step"));
  $("next-button").addEventListener("click", () => postAction("next_step"));
  $("reset-button").addEventListener("click", () => {
    stopPlay();
    postAction("reset");
  });
  $("play-button").addEventListener("click", () => {
    if (state.playTimer) {
      stopPlay();
      return;
    }
    startPlay();
  });
  $("example-select").addEventListener("change", async (event) => {
    stopPlay();
    await postAction("load_example", { name: event.target.value });
    state.trace = await requestJson("/api/trace");
    render();
  });
  $("pace-select").addEventListener("change", (event) => {
    stopPlay();
    postAction("set_option", { pace: event.target.value });
  });
  $("step-range").addEventListener("input", (event) => {
    stopPlay();
    postAction("step_to", { index: Number(event.target.value) });
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  try {
    await loadApp();
  } catch (error) {
    window.alert(error.message);
  }
});

