const stateUrl = "/state";
const actionUrl = "/action";
const resetUrl = "/reset";

const mapSvg = document.querySelector("#map-svg");
const missionName = document.querySelector("#mission-name");
const missionObjective = document.querySelector("#mission-objective");
const turnStatus = document.querySelector("#turn-status");
const phaseStatus = document.querySelector("#phase-status");
const decisionStatus = document.querySelector("#decision-status");
const seedInput = document.querySelector("#seed-input");
const resetButton = document.querySelector("#reset-button");
const terminalPanel = document.querySelector("#terminal-panel");
const activationDetails = document.querySelector("#activation-details");
const eventLog = document.querySelector("#event-log");
const actionList = document.querySelector("#action-list");
const messageLine = document.querySelector("#message-line");

let currentState = null;
let requestInFlight = false;

function titleCase(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function coordKey(coord) {
  return `${coord.q},${coord.r}`;
}

function hexCenter(coord, size) {
  return {
    x: size * 1.5 * coord.q,
    y: size * Math.sqrt(3) * (coord.r + coord.q / 2),
  };
}

function hexPoints(center, size) {
  const points = [];
  for (let index = 0; index < 6; index += 1) {
    const angle = (Math.PI / 180) * (60 * index);
    points.push(`${center.x + size * Math.cos(angle)},${center.y + size * Math.sin(angle)}`);
  }
  return points.join(" ");
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => {
    element.setAttribute(key, value);
  });
  return element;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    const error = payload.error || {};
    throw new Error(error.message || `Request failed with status ${response.status}`);
  }
  return payload;
}

async function loadState({clearMessage = true} = {}) {
  setBusy(true);
  try {
    const payload = await requestJson(stateUrl);
    setState(payload);
    if (clearMessage) {
      setMessage("");
    }
  } catch (error) {
    setMessage(error.message);
  } finally {
    setBusy(false);
  }
}

async function applyAction(actionId) {
  setBusy(true);
  try {
    const payload = await requestJson(actionUrl, {
      method: "POST",
      body: JSON.stringify({action_id: actionId}),
    });
    setState(payload);
    setMessage("");
  } catch (error) {
    setMessage(error.message);
    await loadState({clearMessage: false});
  } finally {
    setBusy(false);
  }
}

async function resetSession() {
  const seed = Number.parseInt(seedInput.value, 10);
  setBusy(true);
  try {
    const payload = await requestJson(resetUrl, {
      method: "POST",
      body: JSON.stringify({seed: Number.isNaN(seed) ? null : seed}),
    });
    setState(payload);
    setMessage("");
  } catch (error) {
    setMessage(error.message);
  } finally {
    setBusy(false);
  }
}

function setState(nextState) {
  currentState = nextState;
  seedInput.value = nextState.session.seed;
  render();
}

function setBusy(isBusy) {
  requestInFlight = isBusy;
  resetButton.disabled = isBusy;
  document.querySelectorAll(".action-button").forEach((button) => {
    button.disabled = isBusy;
  });
}

function setMessage(message) {
  messageLine.textContent = message;
}

function render() {
  if (!currentState) {
    return;
  }
  renderHeader(currentState);
  renderTerminal(currentState);
  renderActivation(currentState);
  renderEventLog(currentState);
  renderActions(currentState);
  renderMap(currentState);
}

function renderHeader(state) {
  missionName.textContent = state.mission.name;
  missionObjective.textContent = state.mission.objective;
  turnStatus.textContent = `Turn ${state.turn} / ${state.mission.turn_limit}`;
  phaseStatus.textContent = titleCase(state.phase);
  decisionStatus.textContent = state.pending_decision.label;
}

function renderTerminal(state) {
  if (!state.terminal_outcome) {
    terminalPanel.hidden = true;
    terminalPanel.textContent = "";
    terminalPanel.className = "terminal-panel";
    return;
  }
  terminalPanel.hidden = false;
  terminalPanel.className = `terminal-panel terminal-${state.terminal_outcome}`;
  terminalPanel.textContent = titleCase(state.terminal_outcome);
}

function renderActivation(state) {
  activationDetails.replaceChildren();
  const activation = state.current_activation;
  const rows = [
    ["Decision", state.pending_decision.label],
    ["Step", state.session.decision_step_count],
  ];

  if (activation) {
    rows.push(["Unit", activation.active_unit_label]);
    rows.push(["Morale", activation.active_unit_morale_label || "-"]);
    if (activation.restrictions.length) {
      rows.push([
        "Limit",
        activation.restrictions.map((restriction) => restriction.message).join(" "),
      ]);
    }
    rows.push(["Roll", activation.roll ? activation.roll.join(", ") : "-"]);
    if (activation.roll_options.length) {
      rows.push(["Roll options", formatRollOptions(activation.roll_options)]);
    }
    rows.push(["Selected die", activation.selected_die || "-"]);
    rows.push([
      "Orders",
      activation.planned_order_labels.length ? activation.planned_order_labels.join(", ") : "-",
    ]);
  }

  rows.forEach(([label, value]) => {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    activationDetails.append(term, description);
  });
}

function renderEventLog(state) {
  eventLog.replaceChildren();

  if (!state.event_log.length) {
    const empty = document.createElement("li");
    empty.className = "empty-log";
    empty.textContent = "No actions yet";
    eventLog.append(empty);
    return;
  }

  state.event_log.slice(-36).forEach((entry) => {
    const item = document.createElement("li");
    item.className = state.last_action_events.some((latest) => latest.id === entry.id)
      ? "event-entry event-entry-latest"
      : "event-entry";
    const step = document.createElement("span");
    step.className = "event-step";
    step.textContent = entry.step;
    const message = document.createElement("span");
    message.textContent = entry.message;
    item.append(step, message);
    eventLog.append(item);
  });
  eventLog.scrollTop = eventLog.scrollHeight;
}

function formatRollOptions(rollOptions) {
  return rollOptions
    .map((option) => {
      if (!option.order_labels || !option.order_labels.length) {
        return `Die ${option.die_value}`;
      }
      let label = `Die ${option.die_value}: ${option.order_labels.join(" + ")}`;
      if (option.restriction && option.restriction.short_message) {
        label += ` (${option.restriction.short_message})`;
      }
      return label;
    })
    .join("; ");
}

function renderActions(state) {
  actionList.replaceChildren();

  if (!state.legal_actions.length) {
    const empty = document.createElement("p");
    empty.className = "empty-actions";
    empty.textContent = state.terminal_outcome ? "No legal actions" : "Waiting for state";
    actionList.append(empty);
    return;
  }

  state.legal_actions.forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "action-button";
    button.textContent = action.label;
    button.disabled = requestInFlight;
    button.addEventListener("click", () => applyAction(action.id));
    actionList.append(button);
  });
}

function renderMap(state) {
  mapSvg.replaceChildren();
  const size = 42;
  const padding = 76;
  const centers = new Map();
  const affordances = buildAffordanceMaps(state.affordances);

  state.map.hexes.forEach((hex) => {
    centers.set(coordKey(hex.coord), hexCenter(hex.coord, size));
  });

  const centerValues = [...centers.values()];
  const minX = Math.min(...centerValues.map((center) => center.x)) - padding;
  const maxX = Math.max(...centerValues.map((center) => center.x)) + padding;
  const minY = Math.min(...centerValues.map((center) => center.y)) - padding;
  const maxY = Math.max(...centerValues.map((center) => center.y)) + padding;
  mapSvg.setAttribute("viewBox", `${minX} ${minY} ${maxX - minX} ${maxY - minY}`);

  state.map.hexes.forEach((hex) => {
    const center = centers.get(coordKey(hex.coord));
    const terrain = hex.terrain[0] || "clear";
    const advanceAffordance = affordances.advanceDestinations.get(coordKey(hex.coord));
    const polygon = svgElement("polygon", {
      points: hexPoints(center, size),
      class: [
        "hex",
        `hex-${terrain}`,
        hex.is_start ? "hex-start" : "",
        advanceAffordance ? "hex-advance-target" : "",
      ]
        .filter(Boolean)
        .join(" "),
    });
    attachShortcut(polygon, advanceAffordance);
    mapSvg.append(polygon);

    const label = svgElement("text", {
      x: center.x,
      y: center.y + size * 0.52,
      class: "hex-label",
      "text-anchor": "middle",
    });
    label.textContent = `${hex.coord.q},${hex.coord.r}`;
    mapSvg.append(label);
  });

  const slots = new Map();
  const nextOffset = (coord) => {
    const key = coordKey(coord);
    const slot = slots.get(key) || 0;
    slots.set(key, slot + 1);
    const offsets = [
      [0, -8],
      [-18, -20],
      [18, -20],
      [-18, 10],
      [18, 10],
    ];
    return offsets[slot] || [0, 18 + slot * 8];
  };

  state.units.unresolved_markers.forEach((marker) => {
    const center = centers.get(coordKey(marker.coord));
    if (!center) {
      return;
    }
    const [dx, dy] = nextOffset(marker.coord);
    drawMarker(
      center.x + dx,
      center.y + dy,
      marker,
      affordances.hiddenMarkers.get(marker.id),
    );
  });

  state.units.german.forEach((unit) => {
    const center = centers.get(coordKey(unit.coord));
    if (!center) {
      return;
    }
    const [dx, dy] = nextOffset(unit.coord);
    drawGermanCounter(center.x + dx, center.y + dy, unit, affordances.germanUnits.get(unit.id));
  });

  state.units.british.forEach((unit) => {
    const center = centers.get(coordKey(unit.coord));
    if (!center) {
      return;
    }
    const [dx, dy] = nextOffset(unit.coord);
    drawBritishCounter(center.x + dx, center.y + dy, unit, affordances.britishUnits.get(unit.id));
  });
}

function buildAffordanceMaps(affordances = {}) {
  return {
    advanceDestinations: new Map(
      (affordances.advance_destinations || []).map((entry) => [coordKey(entry.coord), entry]),
    ),
    britishUnits: new Map(
      (affordances.british_units || []).map((entry) => [entry.unit_id, entry]),
    ),
    germanUnits: new Map((affordances.german_units || []).map((entry) => [entry.unit_id, entry])),
    hiddenMarkers: new Map(
      (affordances.hidden_markers || []).map((entry) => [entry.marker_id, entry]),
    ),
  };
}

function attachShortcut(element, affordance) {
  if (!affordance || !affordance.shortcut_action_id) {
    return;
  }

  const actionId = affordance.shortcut_action_id;
  element.classList.add("map-clickable");
  element.setAttribute("role", "button");
  element.setAttribute("tabindex", "0");
  element.addEventListener("click", () => {
    if (!requestInFlight) {
      applyAction(actionId);
    }
  });
  element.addEventListener("keydown", (event) => {
    if ((event.key === "Enter" || event.key === " ") && !requestInFlight) {
      event.preventDefault();
      applyAction(actionId);
    }
  });
}

function drawBritishCounter(x, y, unit, affordance) {
  const group = svgElement("g", {
    class: [
      "counter",
      "british-counter",
      `british-morale-${unit.morale}`,
      unit.active ? "counter-active" : "",
      affordance ? "counter-activatable" : "",
    ]
      .filter(Boolean)
      .join(" "),
  });
  attachShortcut(group, affordance);
  group.append(svgElement("rect", {x: x - 17, y: y - 13, width: 34, height: 26, rx: 4}));
  const text = svgElement("text", {x, y: y + 4, "text-anchor": "middle"});
  text.textContent = unit.counter_label || unit.id;
  group.append(text);
  drawMoraleMarker(group, x, y, unit);
  if (unit.cover > 0) {
    const cover = svgElement("text", {x: x + 18, y: y - 14, class: "counter-note"});
    cover.textContent = `+${unit.cover}`;
    group.append(cover);
  }
  mapSvg.append(group);
}

function drawGermanCounter(x, y, unit, affordance) {
  const group = svgElement("g", {
    class: [
      "counter",
      "german-counter",
      `german-${unit.status}`,
      affordance ? "counter-targetable" : "",
    ]
      .filter(Boolean)
      .join(" "),
  });
  attachShortcut(group, affordance);
  group.append(svgElement("rect", {x: x - 22, y: y - 14, width: 44, height: 28, rx: 4}));
  const text = svgElement("text", {x, y: y + 4, "text-anchor": "middle"});
  text.textContent = unit.counter_label || unit.unit_class;
  group.append(text);
  const angle = facingAngle(unit.facing);
  const arrow = svgElement("polygon", {
    points: `${x},${y - 26} ${x - 6},${y - 15} ${x + 6},${y - 15}`,
    class: "facing-arrow",
    transform: `rotate(${angle + 90} ${x} ${y})`,
  });
  group.append(arrow);
  mapSvg.append(group);
}

function drawMoraleMarker(group, x, y, unit) {
  if (unit.morale === "normal") {
    group.append(svgElement("circle", {cx: x + 13, cy: y - 9, r: 3.2, class: "morale-dot"}));
    return;
  }

  const badgeText = unit.morale === "low" ? "LOW" : "OUT";
  group.append(
    svgElement("rect", {
      x: x - 16,
      y: y + 10,
      width: 32,
      height: 12,
      rx: 3,
      class: `morale-badge morale-badge-${unit.morale}`,
    }),
  );
  const badge = svgElement("text", {
    x,
    y: y + 20,
    class: "morale-badge-text",
    "text-anchor": "middle",
  });
  badge.textContent = badgeText;
  group.append(badge);
}

function facingAngle(facing) {
  const angles = {
    up_left: -150,
    up: -90,
    up_right: -30,
    down_right: 30,
    down: 90,
    down_left: 150,
  };
  return angles[facing] ?? -90;
}

function drawMarker(x, y, marker, affordance) {
  const group = svgElement("g", {
    class: ["hidden-marker", affordance ? "hidden-marker-targetable" : ""]
      .filter(Boolean)
      .join(" "),
  });
  attachShortcut(group, affordance);
  group.append(
    svgElement("polygon", {
      points: `${x},${y - 17} ${x + 17},${y} ${x},${y + 17} ${x - 17},${y}`,
    }),
  );
  const text = svgElement("text", {x, y: y + 5, "text-anchor": "middle"});
  text.textContent = marker.counter_label || "?";
  group.append(text);
  mapSvg.append(group);
}

resetButton.addEventListener("click", resetSession);
loadState();
