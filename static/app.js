```javascript
let allLinks = [];

let currentCategory = "All";


async function loadLinks() {

    try {

        const response = await fetch("/api/links");

        allLinks = await response.json();

        displayLinks(allLinks);

    } catch (error) {

        console.error(error);

        document.getElementById("linksContainer").innerHTML =
            "<p>Unable to load links.</p>";
    }
}


function displayLinks(links) {

    const container =
        document.getElementById("linksContainer");

    container.innerHTML = "";

    if (links.length === 0) {

        container.innerHTML = `
            <p class="empty">
                No links found.
            </p>
        `;

        return;
    }


    links.forEach(link => {

        const card =
            document.createElement("div");

        card.className = "link-card";

        card.innerHTML = `

            <span class="category">
                ${escapeHTML(link.category)}
            </span>

            <h3>
                ${escapeHTML(link.title)}
            </h3>

            <p>
                ${escapeHTML(
                    link.description ||
                    "No description available."
                )}
            </p>

            <a
                href="${escapeHTML(link.url)}"
                target="_blank"
                rel="noopener noreferrer">
                ${escapeHTML(link.url)}
            </a>

            <button
                class="delete-button"
                onclick="deleteLink(${link.id})">
                Delete
            </button>

        `;

        container.appendChild(card);
    });
}


document
    .getElementById("linkForm")
    .addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const data = {

                title:
                    document.getElementById("title").value.trim(),

                url:
                    document.getElementById("url").value.trim(),

                category:
                    document.getElementById("category").value,

                description:
                    document
                        .getElementById("description")
                        .value
                        .trim()
            };


            try {

                const response =
                    await fetch("/api/links", {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(data)
                    });


                const result =
                    await response.json();


                const message =
                    document.getElementById("message");


                if (result.success) {

                    message.textContent =
                        "✓ Link saved successfully.";

                    message.style.color =
                        "#bbbbbb";


                    document
                        .getElementById("linkForm")
                        .reset();


                    loadLinks();

                } else {

                    message.textContent =
                        result.message ||
                        "Unable to save link.";

                    message.style.color =
                        "red";
                }

            } catch (error) {

                console.error(error);

                document
                    .getElementById("message")
                    .textContent =
                    "Something went wrong.";

            }
        }
    );


async function deleteLink(id) {

    const confirmed =
        confirm("Delete this link?");


    if (!confirmed) {

        return;
    }


    try {

        const response =
            await fetch(`/api/links/${id}`, {

                method: "DELETE"
            });


        const result =
            await response.json();


        if (result.success) {

            loadLinks();

        } else {

            alert(
                result.message ||
                "Unable to delete link."
            );
        }

    } catch (error) {

        console.error(error);

        alert("Something went wrong while deleting.");
    }
}


document
    .getElementById("searchInput")
    .addEventListener(
        "input",
        function () {

            const searchText =
                this.value
                    .toLowerCase()
                    .trim();


            let filtered =
                allLinks.filter(link => {

                    return (

                        (link.title || "")
                            .toLowerCase()
                            .includes(searchText)

                        ||

                        (link.url || "")
                            .toLowerCase()
                            .includes(searchText)

                        ||

                        (link.category || "")
                            .toLowerCase()
                            .includes(searchText)

                        ||

                        (link.description || "")
                            .toLowerCase()
                            .includes(searchText)

                    );
                });


            if (currentCategory !== "All") {

                filtered =
                    filtered.filter(link =>
                        link.category ===
                        currentCategory
                    );
            }


            displayLinks(filtered);
        }
    );


function filterCategory(category) {

    currentCategory =
        category;


    let filtered =
        allLinks;


    if (category !== "All") {

        filtered =
            allLinks.filter(link =>
                link.category === category
            );
    }


    displayLinks(filtered);
}


function escapeHTML(text) {

    if (text === null ||
        text === undefined) {

        return "";
    }


    const div =
        document.createElement("div");

    div.textContent =
        String(text);

    return div.innerHTML;
}


loadLinks();
```
