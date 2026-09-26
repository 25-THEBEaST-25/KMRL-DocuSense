const API_BASE = "http://localhost:8000";

// ---- Tab switching ----
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "dashboard") loadDashboard();
  });
});

// ---- Upload ----
document.getElementById("uploadBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) return alert("Choose a file first");

  const status = document.getElementById("uploadStatus");
  const resultBox = document.getElementById("uploadResult");
  status.textContent = "Processing (OCR + AI extraction)... this can take a few seconds";
  resultBox.textContent = "";

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const res = await fetch(`${API_BASE}/api/documents/upload`, { method: "POST", body: formData });
    const data = await res.json();
    status.textContent = res.ok ? "✅ Processed successfully" : "❌ Failed";
    resultBox.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    status.textContent = "❌ Error: " + e.message;
  }
});

// ---- Search ----
document.getElementById("searchBtn").addEventListener("click", async () => {
  const q = document.getElementById("searchInput").value.trim();
  if (!q) return;
  const box = document.getElementById("searchResults");
  box.innerHTML = "Searching...";

  const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(q)}`);
  const data = await res.json();

  box.innerHTML = "";
  if (!data.results.length) {
    box.innerHTML = "<p>No matching documents found.</p>";
    return;
  }
  data.results.forEach(r => {
    const div = document.createElement("div");
    div.className = "result-item";
    div.innerHTML = `
      <strong>${r.filename}</strong>
      <p>${r.text_snippet}...</p>
      <div class="meta">Category: ${r.category || "-"} | Station: ${r.station || "-"} | Relevance: ${r.relevance_score}</div>
    `;
    box.appendChild(div);
  });
});

// ---- Assistant ----
document.getElementById("askBtn").addEventListener("click", async () => {
  const question = document.getElementById("askInput").value.trim();
  if (!question) return;
  const box = document.getElementById("assistantAnswer");
  box.innerHTML = "Thinking...";

  const res = await fetch(`${API_BASE}/api/assistant/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const data = await res.json();

  box.innerHTML = `
    <div class="result-item">
      <p>${data.answer.replace(/\n/g, "<br>")}</p>
      <div class="meta">Sources: ${(data.sources || []).join(", ") || "none"}</div>
    </div>
  `;
});

// ---- Dashboard ----
async function loadDashboard() {
  const statsRes = await fetch(`${API_BASE}/api/dashboard/stats`);
  const stats = await statsRes.json();

  document.getElementById("statCards").innerHTML = `
    <div class="stat-card"><div class="num">${stats.total_documents}</div><div class="label">Total Documents</div></div>
    <div class="stat-card"><div class="num">${stats.today_uploads}</div><div class="label">Today's Uploads</div></div>
    <div class="stat-card"><div class="num">${stats.pending_reviews}</div><div class="label">Pending Reviews</div></div>
  `;

  renderChart("categoryChart", "bar", Object.keys(stats.department_wise), Object.values(stats.department_wise), "Documents");
  renderChart("faultChart", "bar",
    stats.most_common_faults.map(f => f[0]),
    stats.most_common_faults.map(f => f[1]),
    "Occurrences");

  const insightsRes = await fetch(`${API_BASE}/api/dashboard/incident-intelligence`);
  const insights = await insightsRes.json();
  const list = document.getElementById("insightsList");
  list.innerHTML = "";
  if (!insights.insights.length) {
    list.innerHTML = "<li>No significant trends detected yet — upload more documents.</li>";
  } else {
    insights.insights.forEach(i => {
      const li = document.createElement("li");
      li.textContent = i;
      list.appendChild(li);
    });
  }

  const expRes = await fetch(`${API_BASE}/api/dashboard/expiring-contracts`);
  const exp = await expRes.json();
  const tbody = document.querySelector("#expiryTable tbody");
  tbody.innerHTML = "";
  exp.expiring_contracts.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${c.filename}</td><td>${c.vendor || "-"}</td><td>${c.contract_expiry}</td><td>${c.days_remaining}</td>`;
    tbody.appendChild(tr);
  });
}

let chartInstances = {};
function renderChart(canvasId, type, labels, data, label) {
  if (chartInstances[canvasId]) chartInstances[canvasId].destroy();
  const ctx = document.getElementById(canvasId).getContext("2d");
  chartInstances[canvasId] = new Chart(ctx, {
    type,
    data: { labels, datasets: [{ label, data, backgroundColor: "#0a5c8a" }] },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

// initial load
loadDashboard();
