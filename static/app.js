let currentEditId = null;

document.addEventListener("DOMContentLoaded", () => {
    loadLinks();
    loadStats();

    const searchInput = document.getElementById("searchInput");

    if (searchInput) {
        searchInput.addEventListener("input", () => {
            searchLinks(searchInput.value);
        });
    }
});


async function loadLinks() {
    try {
        const response = await fetch("/links");
        const links = await response.json();
        displayLinks(links);
    } catch (error) {
        console.error("Error loading links:", error);
    }
}


async function loadStats() {
    try {
        const response = await fetch("/stats");
        const stats = await response.json();

        const totalElement = document.getElementById("totalLinks");
        const pinnedElement = document.getElementById("pinnedLinks");

        if (totalElement) {
            totalElement.textContent = stats.total;
        }

        if (pinnedElement) {
            pinnedElement.textContent = stats.pinned;
        }
    } catch (error) {
        console.error("Error loading statistics:", error);
    }
}


function displayLinks(links) {
    const container = document.getElementById("linksContainer");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (links.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No links found</h3>
                <p>Save your first link to get started.</p>
            </div>
        `;
        return;
    }

    links.forEach(link => {
        const card = document.createElement("div");

        card.className = "link-card";

        card.innerHTML = `
            <div class="link-header">
                <div>
                    <h3>${escapeHTML(link.title || "Untitled Link")}</h3>

                    <a href="${escapeHTML(link.url)}"
                       target="_blank"
                       rel="noopener noreferrer">
                        ${escapeHTML(link.url)}
                    </a>
                </div>

                <button
                    class="pin-button"
                    onclick="togglePin(${link.id})">
                    ${link.pinned ? "📌" : "📍"}
                </button>
            </div>

            <div class="link-details">

                <span class="category">
                    ${escapeHTML(link.category || "Other")}
                </span>

                ${
                    link.notes
                    ? `<p>${escapeHTML(link.notes)}</p>`
                    : ""
                }

            </div>

            <div class="link-actions">

                <button onclick="editLink(${link.id})">
                    Edit
                </button>

                <button onclick="checkLink(${link.id})">
                    Check Link
                </button>

                <button onclick="deleteLink(${link.id})">
                    Delete
                </button>

            </div>

            <div class="link-status"
                 id="status-${link.id}">
            </div>
        `;

        container.appendChild(card);
    });
}


async function addLink() {
    const urlInput = document.getElementById("urlInput");
    const titleInput = document.getElementById("titleInput");
    const categoryInput = document.getElementById("categoryInput");
    const notesInput = document.getElementById("notesInput");

    if (!urlInput) {
        return;
    }

    const url = urlInput.value.trim();
    const title = titleInput ? titleInput.value.trim() : "";
    const category = categoryInput ? categoryInput.value : "Other";
    const notes = notesInput ? notesInput.value.trim() : "";

    if (!url) {
        alert("Please enter a URL.");
        return;
    }

    try {
        const response = await fetch("/add", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: url,
                title: title,
                category: category,
                notes: notes
            })
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error);
            return;
        }

        clearForm();
        loadLinks();
        loadStats();

        alert("Link saved successfully.");

    } catch (error) {
        alert("Could not save the link.");
    }
}


async function editLink(id) {
    try {
        const response = await fetch("/links");
        const links = await response.json();

        const link = links.find(item => item.id === id);

        if (!link) {
            alert("Link not found.");
            return;
        }

        const urlInput = document.getElementById("urlInput");
        const titleInput = document.getElementById("titleInput");
        const categoryInput = document.getElementById("categoryInput");
        const notesInput = document.getElementById("notesInput");
        const submitButton = document.getElementById("saveButton");

        if (urlInput) {
            urlInput.value = link.url;
        }

        if (titleInput) {
            titleInput.value = link.title;
        }

        if (categoryInput) {
            categoryInput.value = link.category;
        }

        if (notesInput) {
            notesInput.value = link.notes;
        }

        currentEditId = id;

        if (submitButton) {
            submitButton.textContent = "Update Link";
            submitButton.onclick = updateLink;
        }

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    } catch (error) {
        alert("Could not load the link.");
    }
}


async function updateLink() {
    const urlInput = document.getElementById("urlInput");
    const titleInput = document.getElementById("titleInput");
    const categoryInput = document.getElementById("categoryInput");
    const notesInput = document.getElementById("notesInput");

    if (!currentEditId) {
        return;
    }

    const url = urlInput.value.trim();
    const title = titleInput ? titleInput.value.trim() : "";
    const category = categoryInput ? categoryInput.value : "Other";
    const notes = notesInput ? notesInput.value.trim() : "";

    if (!url) {
        alert("Please enter a URL.");
        return;
    }

    try {
        const response = await fetch(`/edit/${currentEditId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: url,
                title: title,
                category: category,
                notes: notes
            })
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error);
            return;
        }

        alert("Link updated successfully.");

        currentEditId = null;

        clearForm();

        const submitButton = document.getElementById("saveButton");

        if (submitButton) {
            submitButton.textContent = "Save Link";
            submitButton.onclick = addLink;
        }

        loadLinks();
        loadStats();

    } catch (error) {
        alert("Could not update the link.");
    }
}


async function deleteLink(id) {
    const confirmed = confirm(
        "Are you sure you want to delete this link?"
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/delete/${id}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error);
            return;
        }

        loadLinks();
        loadStats();

    } catch (error) {
        alert("Could not delete the link.");
    }
}


async function togglePin(id) {
    try {
        const response = await fetch(`/pin/${id}`, {
            method: "PUT"
        });

        const result = await response.json();

        if (!response.ok) {
            alert(result.error);
            return;
        }

        loadLinks();
        loadStats();

    } catch (error) {
        alert("Could not change pin status.");
    }
}


async function searchLinks(query) {
    try {
        const response = await fetch(
            `/search?q=${encodeURIComponent(query)}`
        );

        const links = await response.json();

        displayLinks(links);

    } catch (error) {
        console.error("Search error:", error);
    }
}


async function filterCategory(category) {
    try {
        const response = await fetch(
            `/category/${encodeURIComponent(category)}`
        );

        const links = await response.json();

        displayLinks(links);

    } catch (error) {
        console.error("Category filter error:", error);
    }
}


async function checkLink(id) {
    const statusElement = document.getElementById(`status-${id}`);

    if (statusElement) {
        statusElement.textContent = "Checking link...";
    }

    try {
        const response = await fetch(`/check-link/${id}`);

        const result = await response.json();

        if (statusElement) {
            if (result.status === "working") {
                statusElement.textContent =
                    `Working ✓ (${result.code})`;
            } else {
                statusElement.textContent =
                    `Broken ✕ (${result.code || "No response"})`;
            }
        }

    } catch (error) {
        if (statusElement) {
            statusElement.textContent =
                "Could not check this link.";
        }
    }
}


async function checkAllLinks() {
    try {
        const response = await fetch("/check-all-links");

        const results = await response.json();

        results.forEach(result => {
            const statusElement =
                document.getElementById(`status-${result.id}`);

            if (statusElement) {
                if (result.status === "working") {
                    statusElement.textContent =
                        `Working ✓ (${result.code})`;
                } else {
                    statusElement.textContent =
                        `Broken ✕ (${result.code || "No response"})`;
                }
            }
        });

    } catch (error) {
        alert("Could not check the links.");
    }
}


function clearForm() {
    const urlInput = document.getElementById("urlInput");
    const titleInput = document.getElementById("titleInput");
    const categoryInput = document.getElementById("categoryInput");
    const notesInput = document.getElementById("notesInput");

    if (urlInput) {
        urlInput.value = "";
    }

    if (titleInput) {
        titleInput.value = "";
    }

    if (categoryInput) {
        categoryInput.value = "Other";
    }

    if (notesInput) {
        notesInput.value = "";
    }
}


function escapeHTML(value) {
    const div = document.createElement("div");
    div.textContent = value;
    return div.innerHTML;
}
