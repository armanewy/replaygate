const searchInput = document.getElementById("searchInput");
const workflowFilter = document.getElementById("workflowFilter");
const failureFilter = document.getElementById("failureFilter");
const failedOnly = document.getElementById("failedOnly");
const rows = Array.from(document.querySelectorAll("#resultsTable tbody tr"));
const visibleCount = document.getElementById("visibleCount");
const resultsEmpty = document.getElementById("resultsEmpty");

function applyFilters() {
  const search = searchInput.value.trim().toLowerCase();
  const workflow = workflowFilter.value;
  const failure = failureFilter.value;
  const onlyFailed = failedOnly.checked;
  let visible = 0;

  rows.forEach((row) => {
    const matchesSearch = row.dataset.search.includes(search);
    const matchesWorkflow = !workflow || row.dataset.workflow === workflow;
    const matchesFailure = !failure || row.dataset.kind === failure;
    const matchesFailed =
      !onlyFailed || row.dataset.status === "failed" || row.dataset.status === "error";
    const isVisible = matchesSearch && matchesWorkflow && matchesFailure && matchesFailed;
    row.hidden = !isVisible;
    if (isVisible) {
      visible += 1;
    }
  });

  visibleCount.textContent = String(visible);
  resultsEmpty.hidden = visible !== 0;
}

[searchInput, workflowFilter, failureFilter, failedOnly].forEach((node) => {
  node.addEventListener("input", applyFilters);
  node.addEventListener("change", applyFilters);
});

applyFilters();
