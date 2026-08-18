let backendProjects = [];


/*
 * ==========================================
 * PROJECTS PAGE
 * ==========================================
 */

function renderProjects() {

    return `

        <div class="page-header">

            <div>

                <div class="eyebrow">
                    HARDWARE PROJECTS
                </div>

                <h1>
                    Projects
                </h1>

                <p>
                    Create and manage your digital hardware projects.
                </p>

            </div>


            <button
                class="primary-button"
                onclick="openProjectModal()"
            >
                + New Project
            </button>

        </div>


        <section class="projects-toolbar">

            <div class="search-box">

                <span class="search-icon">
                    ⌕
                </span>

                <input
                    type="text"
                    id="project-search"
                    placeholder="Search projects..."
                    oninput="filterProjects(this.value)"
                >

            </div>


            <div class="project-filter">

                <button
                    class="filter-button active"
                    onclick="setProjectFilter(this, 'all')"
                >
                    All
                </button>

                <button
                    class="filter-button"
                    onclick="setProjectFilter(this, 'active')"
                >
                    Active
                </button>

                <button
                    class="filter-button"
                    onclick="setProjectFilter(this, 'archived')"
                >
                    Archived
                </button>

            </div>

        </section>


        <section
            class="projects-container"
            id="projects-container"
        >

            <div class="project-empty-state">

                <div class="large-empty-icon">
                    ◇
                </div>

                <h2>
                    Loading projects
                </h2>

                <p>
                    Connecting to the local hardware engine...
                </p>

            </div>

        </section>


        <div
            class="modal-overlay hidden"
            id="project-modal"
        >

            <div class="modal">

                <div class="modal-header">

                    <div>

                        <div class="eyebrow">
                            NEW PROJECT
                        </div>

                        <h2>
                            Create Hardware Project
                        </h2>

                    </div>


                    <button
                        class="modal-close"
                        onclick="closeProjectModal()"
                    >
                        ×
                    </button>

                </div>


                <div class="modal-body">

                    <div class="form-group">

                        <label for="project-name">
                            Project name
                        </label>

                        <input
                            id="project-name"
                            type="text"
                            placeholder="e.g. 4-bit Counter"
                        >

                    </div>


                    <div class="form-group">

                        <label for="project-description">
                            Description
                        </label>

                        <textarea
                            id="project-description"
                            rows="4"
                            placeholder="Describe what this project is for..."
                        ></textarea>

                    </div>


                    <div class="form-group">

                        <label for="project-hdl">
                            Hardware description language
                        </label>

                        <select id="project-hdl">

                            <option value="systemverilog">
                                SystemVerilog
                            </option>

                            <option value="verilog">
                                Verilog
                            </option>

                        </select>

                    </div>

                </div>


                <div class="modal-footer">

                    <button
                        class="secondary-button"
                        onclick="closeProjectModal()"
                    >
                        Cancel
                    </button>


                    <button
                        class="primary-button"
                        id="create-project-button"
                        onclick="createBackendProject()"
                    >
                        Create Project
                    </button>

                </div>

            </div>

        </div>

    `;
}


/*
 * ==========================================
 * PROJECT FILTER
 * ==========================================
 */

let currentProjectFilter = "all";


function setProjectFilter(button, filter) {

    document
        .querySelectorAll(".filter-button")
        .forEach(item => {
            item.classList.remove("active");
        });


    button.classList.add("active");

    currentProjectFilter = filter;

    const search =
        document.getElementById("project-search");


    renderProjectList(
        search ? search.value : ""
    );

}


/*
 * ==========================================
 * LOAD PROJECTS
 * ==========================================
 */

async function initializeProjectsPage() {

    const container =
        document.getElementById(
            "projects-container"
        );


    if (!container) {
        return;
    }


    container.innerHTML = `

        <div class="project-empty-state">

            <div class="large-empty-icon">
                ◇
            </div>

            <h2>
                Loading projects
            </h2>

            <p>
                Fetching projects from the local engine...
            </p>

        </div>

    `;


    try {

        const response =
            await getProjects();


        backendProjects =
            normalizeProjectsResponse(response);


        renderProjectList();

    } catch (error) {

        container.innerHTML = `

            <div class="project-empty-state">

                <div class="large-empty-icon">
                    !
                </div>

                <h2>
                    Unable to load projects
                </h2>

                <p>
                    ${escapeHtml(
                        error.message ||
                        "The backend could not be reached."
                    )}
                </p>

                <button
                    class="primary-button"
                    onclick="initializeProjectsPage()"
                >
                    Retry
                </button>

            </div>

        `;

    }

}


/*
 * ==========================================
 * NORMALIZE BACKEND RESPONSE
 * ==========================================
 */

function normalizeProjectsResponse(response) {

    const projects =
        Array.isArray(response)
            ? response
            : (
                response &&
                Array.isArray(response.projects)
                    ? response.projects
                    : []
            );


    return projects.map(project => {

        return {

            id:
                project.id ||
                project.project_id,

            name:
                project.name ||
                "Untitled Project",

            description:
                project.description ||
                "Hardware design project",

            hdl:
                project.language ||
                project.hdl ||
                "systemverilog",

            status:
                project.status ||
                "active",

            designs:
                project.designs ??
                project.design_count ??
                0,

            createdAt:
                project.created_at ||
                project.createdAt ||
                new Date().toISOString()

        };

    });

}


/*
 * ==========================================
 * RENDER PROJECT LIST
 * ==========================================
 */

function renderProjectList(searchValue = "") {

    const container =
        document.getElementById(
            "projects-container"
        );


    if (!container) {
        return;
    }


    const normalizedSearch =
        searchValue
            .trim()
            .toLowerCase();


    let filtered =
        backendProjects.filter(project => {

            const matchesSearch =
                !normalizedSearch ||
                project.name
                    .toLowerCase()
                    .includes(normalizedSearch) ||
                project.description
                    .toLowerCase()
                    .includes(normalizedSearch);


            const normalizedStatus =
                String(
                    project.status || "active"
                ).toLowerCase();


            const matchesFilter =
                currentProjectFilter === "all" ||
                normalizedStatus ===
                    currentProjectFilter;


            return (
                matchesSearch &&
                matchesFilter
            );

        });


    if (!filtered.length) {

        container.innerHTML = `

            <div class="project-empty-state">

                <div class="large-empty-icon">
                    ◇
                </div>

                <h2>
                    ${
                        normalizedSearch
                            ? "No matching projects"
                            : "No projects yet"
                    }
                </h2>

                <p>
                    ${
                        normalizedSearch
                            ? "Try a different search."
                            : "Start by creating a hardware project."
                    }
                </p>

                ${
                    normalizedSearch
                        ? ""
                        : `
                            <button
                                class="primary-button"
                                onclick="openProjectModal()"
                            >
                                Create your first project
                            </button>
                        `
                }

            </div>

        `;

        return;
    }


    container.innerHTML =
        filtered
            .map(project => {

                return `

                    <article
                        class="project-card-large"
                        onclick="openProject('${escapeHtml(project.id)}')"
                    >

                        <div class="project-card-main">

                            <div class="project-icon">
                                ◇
                            </div>


                            <div class="project-info">

                                <div class="project-title-row">

                                    <h2>
                                        ${escapeHtml(project.name)}
                                    </h2>

                                    <span class="project-status">
                                        ${escapeHtml(
                                            String(
                                                project.status ||
                                                "ACTIVE"
                                            ).toUpperCase()
                                        )}
                                    </span>

                                </div>


                                <p>
                                    ${escapeHtml(project.description)}
                                </p>


                                <div class="project-meta">

                                    <span>
                                        ${escapeHtml(
                                            formatLanguage(
                                                project.hdl
                                            )
                                        )}
                                    </span>

                                    <span>
                                        ${project.designs}
                                        ${
                                            project.designs === 1
                                                ? "design"
                                                : "designs"
                                        }
                                    </span>

                                    <span>
                                        Created
                                        ${formatProjectDate(
                                            project.createdAt
                                        )}
                                    </span>

                                </div>

                            </div>

                        </div>


                        <div class="project-open">
                            Open →
                        </div>

                    </article>

                `;

            })
            .join("");

}


/*
 * ==========================================
 * SEARCH
 * ==========================================
 */

function filterProjects(value) {

    renderProjectList(value);

}


/*
 * ==========================================
 * CREATE PROJECT MODAL
 * ==========================================
 */

function openProjectModal() {

    const modal =
        document.getElementById(
            "project-modal"
        );


    if (!modal) {
        return;
    }


    modal.classList.remove("hidden");


    const nameInput =
        document.getElementById(
            "project-name"
        );


    if (nameInput) {
        nameInput.focus();
    }

}


function closeProjectModal() {

    const modal =
        document.getElementById(
            "project-modal"
        );


    if (!modal) {
        return;
    }


    modal.classList.add("hidden");

}


/*
 * ==========================================
 * CREATE BACKEND PROJECT
 * ==========================================
 */

async function createBackendProject() {

    const nameInput =
        document.getElementById(
            "project-name"
        );


    const descriptionInput =
        document.getElementById(
            "project-description"
        );


    const hdlInput =
        document.getElementById(
            "project-hdl"
        );


    const button =
        document.getElementById(
            "create-project-button"
        );


    const name =
        nameInput
            ? nameInput.value.trim()
            : "";


    const description =
        descriptionInput
            ? descriptionInput.value.trim()
            : "";


    const language =
        hdlInput
            ? hdlInput.value
            : "systemverilog";


    if (!name) {

        alert(
            "Please enter a project name."
        );

        return;
    }


    if (button) {

        button.disabled = true;

        button.textContent =
            "Creating...";

    }


    try {

        const response =
            await createProject({

                name,

                description:
                    description ||
                    "Hardware design project",

                language

            });


        const project =
            normalizeProjectsResponse([
                response
            ])[0];


        if (!project || !project.id) {

            throw new Error(
                "Backend did not return a project ID."
            );

        }


        backendProjects.unshift(
            project
        );


        localStorage.setItem(
            "chipd_current_project",
            JSON.stringify(project)
        );


        localStorage.removeItem(
            "chipd_current_design"
        );


        closeProjectModal();

        renderProjectList();


        navigate("design");

    } catch (error) {

        alert(
            error.message ||
            "Unable to create project."
        );

    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "Create Project";

        }

    }

}


/*
 * ==========================================
 * OPEN PROJECT
 * ==========================================
 */

function openProject(projectId) {

    const project =
        backendProjects.find(
            item =>
                String(item.id) ===
                String(projectId)
        );


    if (!project) {
        return;
    }


    localStorage.setItem(
        "chipd_current_project",
        JSON.stringify(project)
    );


    localStorage.removeItem(
        "chipd_current_design"
    );


    navigate("design");

}


/*
 * ==========================================
 * HELPERS
 * ==========================================
 */

function formatProjectDate(date) {

    if (!date) {
        return "—";
    }


    const parsed =
        new Date(date);


    if (
        Number.isNaN(
            parsed.getTime()
        )
    ) {
        return "—";
    }


    return parsed.toLocaleDateString(
        undefined,
        {
            month: "short",
            day: "numeric"
        }
    );

}


function formatLanguage(language) {

    if (
        String(language).toLowerCase() ===
        "systemverilog"
    ) {
        return "SystemVerilog";
    }


    if (
        String(language).toLowerCase() ===
        "verilog"
    ) {
        return "Verilog";
    }


    return language || "SystemVerilog";

}


function escapeHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}