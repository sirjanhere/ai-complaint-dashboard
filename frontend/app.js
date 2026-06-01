const API_BASE = "http://127.0.0.1:8000";

const complaintForm = document.getElementById("complaint-form");
const complaintsBody = document.getElementById("complaints-body");
const totalCount = document.getElementById("total-count");
const highPriorityCount = document.getElementById("high-priority-count");
const resolvedCount = document.getElementById("resolved-count");
const categoryFilter = document.getElementById("category-filter");
const statusFilter = document.getElementById("status-filter");
const priorityFilter = document.getElementById("priority-filter");
const applyFiltersButton = document.getElementById("apply-filters");

function buildFilterParams() {
  const params = new URLSearchParams();
  if (categoryFilter.value) params.set("category", categoryFilter.value);
  if (statusFilter.value) params.set("status", statusFilter.value);
  if (priorityFilter.value) params.set("priority", priorityFilter.value);
  return params.toString();
}

async function loadAnalytics() {
  const response = await fetch(`${API_BASE}/api/analytics`);
  const payload = await response.json();
  totalCount.textContent = payload.total ?? 0;
  highPriorityCount.textContent = payload.high_priority ?? 0;
  resolvedCount.textContent = payload.resolved ?? 0;
}

async function loadComplaints() {
  const query = buildFilterParams();
  const url = query ? `${API_BASE}/api/complaints?${query}` : `${API_BASE}/api/complaints`;
  const response = await fetch(url);
  const complaints = await response.json();

  complaintsBody.innerHTML = "";
  complaints.forEach((complaint) => {
    const row = document.createElement("tr");
    const actionButton =
      complaint.status === "pending"
        ? `<button data-id="${complaint.id}" class="resolve-btn">Resolve</button>`
        : `<span>—</span>`;

    row.innerHTML = `
      <td>${complaint.id}</td>
      <td>${complaint.name}</td>
      <td>${complaint.text}</td>
      <td>${complaint.category ?? "-"}</td>
      <td>${complaint.priority ?? "-"}</td>
      <td>${complaint.status}</td>
      <td>${actionButton}</td>
    `;
    complaintsBody.appendChild(row);
  });
}

async function resolveComplaint(complaintId) {
  await fetch(`${API_BASE}/api/complaints/${complaintId}/resolve`, {
    method: "PATCH",
  });
  await Promise.all([loadComplaints(), loadAnalytics()]);
}

complaintForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(complaintForm);
  await fetch(`${API_BASE}/api/complaints`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: String(formData.get("name") || ""),
      text: String(formData.get("text") || ""),
    }),
  });

  complaintForm.reset();
  await Promise.all([loadComplaints(), loadAnalytics()]);
});

applyFiltersButton.addEventListener("click", loadComplaints);

complaintsBody.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  if (!target.classList.contains("resolve-btn")) return;
  const complaintId = target.getAttribute("data-id");
  if (!complaintId) return;
  await resolveComplaint(complaintId);
});

Promise.all([loadComplaints(), loadAnalytics()]);
