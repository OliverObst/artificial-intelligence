const state = {
  trace: null,
  stepIndex: 0,
  playTimer: null,
};

const $ = (id) => document.getElementById(id);

async function loadTrace() {
  const response = await fetch("./trace.json");
  state.trace = await response.json();
  $("solution-title").textContent = `${state.trace.app_type} solution replay`;
  render();
}

function currentStep() {
  if (!state.trace.steps.length || state.stepIndex === 0) {
    return {
      label: "Initial state",
      annotation: "Static replay is ready.",
    };
  }
  return state.trace.steps[state.stepIndex - 1];
}

function render() {
  const step = currentStep();
  $("step-readout").textContent = `${state.stepIndex} / ${state.trace.steps.length}`;
  $("step-label").textContent = step.label;
  $("step-annotation").textContent = step.annotation || "";
}

function stopPlay() {
  if (state.playTimer) {
    window.clearInterval(state.playTimer);
    state.playTimer = null;
    $("play-button").textContent = "Play";
  }
}

function startPlay() {
  stopPlay();
  $("play-button").textContent = "Pause";
  state.playTimer = window.setInterval(() => {
    if (state.stepIndex >= state.trace.steps.length) {
      stopPlay();
      return;
    }
    state.stepIndex += 1;
    render();
  }, 500);
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

  $("reset-button").addEventListener("click", () => {
    stopPlay();
    state.stepIndex = 0;
    render();
  });

  $("play-button").addEventListener("click", () => {
    if (state.playTimer) {
      stopPlay();
      return;
    }
    startPlay();
  });
});

