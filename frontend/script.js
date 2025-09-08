// ---- CONFIG ----
const DEFAULT_CAPACITY = 20;   // capacity used when missing
const THRESHOLDS = {
  empty: 30,     // <30% occupancy → green
  moderate: 70   // <70% occupancy → yellow
  // ≥70% → red
};

let lastTrainId = null;
let autoRefreshTimer = null;

// wire search button
document.getElementById("searchBtn").addEventListener("click", searchTrains);

// refresh & auto controls
const refreshBtn = document.getElementById("refreshBtn");
const autoToggle = document.getElementById("autoRefreshToggle");
const intervalSelect = document.getElementById("autoInterval");

refreshBtn?.addEventListener("click", () => { if (lastTrainId) showCrowd(lastTrainId); });
autoToggle?.addEventListener("change", () => {
  setupAutoRefresh();
});

function setupAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
  if (autoToggle && autoToggle.checked && lastTrainId) {
    const ms = Number(intervalSelect.value) || 60000;
    autoRefreshTimer = setInterval(() => {
      showCrowd(lastTrainId);
    }, ms);
  }
}

async function searchTrains() {
  const src = document.getElementById("source").value.trim();
  const dst = document.getElementById("destination").value.trim();
  if (!src || !dst) { alert("Please enter both source and destination."); return; }

  const listEl = document.getElementById("trainList");
  listEl.innerHTML = "<div>Loading trains…</div>";

  try {
    const res = await fetch(`/trains?ts=${Date.now()}`);
    if (!res.ok) throw new Error("Network response not OK");
    const data = await res.json();

    let trains = [];
    if (Array.isArray(data)) {
      trains = data;
    } else if (data && typeof data === "object") {
      trains = Object.keys(data).map(k => {
        let code = k;
        let line = "";
        const v = data[k];
        if (v && typeof v === "object" && v.code) { code = v.code; line = v.line || ""; }
        return { train_id: k, code, line };
      });
    }

    if (!trains.length) {
      listEl.innerHTML = "<div>No trains found</div>";
      return;
    }

    listEl.innerHTML = "";
    trains.forEach(t => {
      const id = t.code || String(t.train_id);   // prefer code (98122), fallback to id
      const card = document.createElement("div");
      card.className = "train-item";

      // Show schedule style: Time — SRC → DST
      const title = `${t.time || ""} — ${t.src || ""} → ${t.dst || ""}`;
      card.innerHTML = `<strong>${title}</strong><div class="line">${t.line || ""}</div>`;

      card.onclick = () => {
        localStorage.setItem('lastSource', src);
        localStorage.setItem('lastDestination', dst);
        showCrowd(id);
      };
      listEl.appendChild(card);
    });

    const savedTrain = localStorage.getItem('lastTrainId');
    if (savedTrain) {
      const found = trains.find(tt => String(tt.train_id) === String(savedTrain) || String(tt.code) === String(savedTrain));
      if (found) {
        showCrowd(found.train_id ?? found.code);
      }
    }

  } catch (err) {
    console.error("Error fetching trains:", err);
    listEl.innerHTML = "<div style='color:red;'>Failed to load train data.</div>";
  }
}

async function showCrowd(trainId) {
  lastTrainId = trainId;
  localStorage.setItem('lastTrainId', trainId);

  document.getElementById("controls").style.display = "block";
  setupAutoRefresh();

  const display = document.getElementById("crowdDisplay");
  display.innerHTML = "<p>Loading coach data…</p>";

  try {
    const res = await fetch(`/train/${encodeURIComponent(trainId)}/status?ts=${Date.now()}`);
    if (!res.ok) {
      const body = await res.json().catch(()=>({error:"Train not found"}));
      display.innerHTML = `<p style="color:red;">${body.error || "Train not found"}</p>`;
      return;
    }
    const train = await res.json();

    if (Array.isArray(train.coaches)) {
      renderCoachesArray(train.code || train.train_id || trainId, train.coaches);
      return;
    }

    if (train.coaches && typeof train.coaches === "object") {
      renderCoachesMapping(train.code || train.train_id || trainId, train.coaches);
      return;
    }

    const keys = Object.keys(train).filter(k => /^coach/i.test(k));
    if (keys.length) {
      const mapping = {};
      keys.forEach(k => mapping[k] = train[k]);
      renderCoachesMapping(train.train_id || train.code || trainId, mapping);
      return;
    }

    if (train && typeof train === "object") {
      const hasCoachLike = Object.keys(train).some(k => /^coach/i.test(k) || (train[k] && (train[k].count !== undefined || train[k].status)));
      if (hasCoachLike) {
        renderCoachesMapping(trainId, train);
        return;
      }
    }

    display.innerHTML = "<p>No coach data available.</p>";

  } catch (err) {
    console.error("Error fetching train status:", err);
    display.innerHTML = "<p style='color:red;'>Failed to load train status.</p>";
  }
}

// helper: numeric sort of coach keys
function sortCoachKeys(keys) {
  return keys.sort((a, b) => {
    const na = (a.match(/\d+/) || [])[0];
    const nb = (b.match(/\d+/) || [])[0];
    const ia = na ? parseInt(na, 10) : NaN;
    const ib = nb ? parseInt(nb, 10) : NaN;
    if (!isNaN(ia) && !isNaN(ib)) return ia - ib;
    if (!isNaN(ia)) return -1;
    if (!isNaN(ib)) return 1;
    return a.localeCompare(b);
  });
}

/* ----- rendering helpers with new UI layout ----- */

function renderCoachesArray(title, arr) {
  arr.sort((a,b) => (Number(a.index) || 0) - (Number(b.index) || 0));
  const display = document.getElementById("crowdDisplay");
  display.innerHTML = `<h2>${title} — Coaches</h2>`;

  const wrapper = document.createElement("div");
  wrapper.className = "train-visual";

  const row = document.createElement("div");
  row.className = "coach-row";

  // Engine block
  const engine = document.createElement("div");
  engine.className = "engine";
  engine.innerText = "ENGINE";
  row.appendChild(engine);

  arr.forEach((coach, idx) => {
    let occupancy = null;

    if (coach.count !== undefined) {
      occupancy = Math.round((coach.count / DEFAULT_CAPACITY) * 100);
    } else if (coach.status) {
      const s = coach.status.toLowerCase();
      occupancy = s.includes("empty") ? 5 : s.includes("moderate") ? 45 : s.includes("crowd") ? 85 : null;
    }

    const pctText = (occupancy === null || isNaN(occupancy)) ? "?" : `${Math.max(0,Math.min(100,occupancy))}%`;
    const cls = (occupancy === null) ? "status-unknown"
               : occupancy < THRESHOLDS.empty ? "status-empty"
               : occupancy < THRESHOLDS.moderate ? "status-moderate"
               : "status-crowded";

    const card = document.createElement("div");
    card.className = `coach ${cls}`;
    card.innerHTML = `
      <div class="bar"></div>
      <div class="body">
        <div class="badge">C-${coach.index || idx+1}</div>
        <div class="statusText">${cls === "status-empty" ? "Safe" : cls === "status-moderate" ? "Moderate" : cls === "status-crowded" ? "Overcrowded" : "?"}</div>
        <div class="label">Occupancy: ${pctText}</div>
      </div>
    `;
    row.appendChild(card);
  });

  wrapper.appendChild(row);
  display.appendChild(wrapper);
}

function renderCoachesMapping(title, mapping) {
  const display = document.getElementById("crowdDisplay");
  display.innerHTML = `<h2>${title} — Coaches</h2>`;

  const wrapper = document.createElement("div");
  wrapper.className = "train-visual";

  const row = document.createElement("div");
  row.className = "coach-row";

  // Engine block
  const engine = document.createElement("div");
  engine.className = "engine";
  engine.innerText = "ENGINE";
  row.appendChild(engine);

  const keys = sortCoachKeys(Object.keys(mapping));

  keys.forEach((coachName, idx) => {
    const details = mapping[coachName];
    let occupancy = null;

    if (details.count !== undefined) {
      occupancy = Math.round((details.count / DEFAULT_CAPACITY) * 100);
    } else if (details.status) {
      const s = details.status.toLowerCase();
      occupancy = s.includes("empty") ? 5 : s.includes("moderate") ? 45 : s.includes("crowd") ? 85 : null;
    }

    const pctText = (occupancy == null || isNaN(occupancy))
      ? "?" 
      : `${Math.max(0, Math.min(100, occupancy))}%`;

    const cls = (occupancy == null) ? "status-unknown"
               : occupancy < THRESHOLDS.empty ? "status-empty"
               : occupancy < THRESHOLDS.moderate ? "status-moderate"
               : "status-crowded";

    const card = document.createElement("div");
    card.className = `coach ${cls}`;
    card.innerHTML = `
      <div class="bar"></div>
      <div class="body">
        <div class="badge">${coachName}</div>
        <div class="statusText">${cls === "status-empty" ? "Safe" : cls === "status-moderate" ? "Moderate" : cls === "status-crowded" ? "Overcrowded" : "?"}</div>
        <div class="label">Occupancy: ${pctText}</div>
      </div>
    `;
    row.appendChild(card);
  });

  wrapper.appendChild(row);
  display.appendChild(wrapper);
}

// on page load
window.addEventListener('DOMContentLoaded', () => {
  const s = localStorage.getItem('lastSource'); if (s) document.getElementById('source').value = s;
  const d = localStorage.getItem('lastDestination'); if (d) document.getElementById('destination').value = d;
  const last = localStorage.getItem('lastTrainId');
  if (last) {
    showCrowd(last);
  }
});
