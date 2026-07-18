function buildEmptyRow() {
    const row = document.createElement("tr");
    row.id = "empty-row";
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.textContent = "No documents uploaded yet.";
    row.appendChild(cell);
    return row;
}

function buildDocumentRow(doc) {
    const row = document.createElement("tr");
    row.dataset.id = doc.id;

    const nameCell = document.createElement("td");
    nameCell.textContent = doc.filename;

    const dateCell = document.createElement("td");
    dateCell.textContent = new Date(doc.created_at).toLocaleString();

    const statusCell = document.createElement("td");
    statusCell.textContent = doc.status;

    const actionCell = document.createElement("td");
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "delete-btn";
    deleteBtn.dataset.id = doc.id;
    deleteBtn.textContent = "Delete";
    actionCell.appendChild(deleteBtn);

    row.append(nameCell, dateCell, statusCell, actionCell);
    return row;
}

async function refreshDocuments() {
    const response = await fetch("/documents");
    if (!response.ok) return;

    const documents = await response.json();
    const tbody = document.getElementById("documents-body");
    tbody.innerHTML = "";

    if (documents.length === 0) {
        tbody.appendChild(buildEmptyRow());
        return;
    }

    for (const doc of documents) {
        tbody.appendChild(buildDocumentRow(doc));
    }
}

function setupUploadForm() {
    const form = document.getElementById("upload-form");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const errorEl = document.getElementById("upload-error");
        errorEl.hidden = true;

        const fileInput = document.getElementById("upload-file");
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/documents/upload", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            errorEl.textContent = body.detail || "Upload failed. Please try again.";
            errorEl.hidden = false;
            return;
        }

        form.reset();
        await refreshDocuments();
    });
}

function setupDeleteButtons() {
    const tbody = document.getElementById("documents-body");
    if (!tbody) return;

    tbody.addEventListener("click", async (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement) || !target.classList.contains("delete-btn")) {
            return;
        }

        const response = await fetch(`/documents/${target.dataset.id}`, { method: "DELETE" });
        if (response.ok) {
            await refreshDocuments();
        }
    });
}

function buildSourceItem(source) {
    // Built with textContent, not innerHTML — filename and text both come from
    // user-uploaded document content and must not be interpreted as HTML.
    const item = document.createElement("li");

    const doc = document.createElement("strong");
    doc.textContent = source.filename;

    const excerpt = document.createElement("p");
    excerpt.textContent = source.text;

    item.append(doc, excerpt);
    return item;
}

function setupQueryForm() {
    const form = document.getElementById("query-form");
    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const errorEl = document.getElementById("query-error");
        const resultEl = document.getElementById("query-result");
        errorEl.hidden = true;
        resultEl.hidden = true;

        const response = await fetch("/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: form.elements.question.value,
                use_web_search: form.elements.use_web_search.checked,
            }),
        });

        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            errorEl.textContent = body.detail || "Something went wrong. Please try again.";
            errorEl.hidden = false;
            return;
        }

        const data = await response.json();

        document.getElementById("query-answer").textContent = data.answer;

        const sourcesList = document.getElementById("query-sources");
        sourcesList.innerHTML = "";
        for (const source of data.sources) {
            sourcesList.appendChild(buildSourceItem(source));
        }

        resultEl.hidden = false;
    });
}

setupUploadForm();
setupDeleteButtons();
setupQueryForm();
