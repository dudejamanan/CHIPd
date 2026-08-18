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


        <!-- =====================================
             PROJECT AREA
        ====================================== -->

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

                <button class="filter-button active">
                    All
                </button>

                <button class="filter-button">
                    Active
                </button>

                <button class="filter-button">
                    Archived
                </button>

            </div>

        </section>


        <!-- =====================================
             EMPTY STATE
        ====================================== -->

        <section
            class="projects-container"
            id="projects-container"
        >

            <div class="project-empty-state">

                <div class="large-empty-icon">
                    ◇
                </div>

                <h2>
                    No projects yet
                </h2>

                <p>
                    Start by creating a hardware project.
                    You can then describe your design in natural language
                    and let CHIPd generate the RTL.
                </p>

                <button
                    class="primary-button"
                    onclick="openProjectModal()"
                >
                    Create your first project
                </button>

            </div>

        </section>


        <!-- =====================================
             CREATE PROJECT MODAL
        ====================================== -->

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
                        onclick="createLocalProject()"
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
 * TEMPORARY FRONTEND PROJECT STORAGE
 * ==========================================
 *
 * This is ONLY for frontend development.
 *
 * We will replace this with:
 *
 * POST /projects
 *
 * when Person 1's backend is ready.
 */

let localProjects =
    JSON.parse(
        localStorage.getItem("chipd_projects") || "[]"
    );


/*
 * ==========================================
 * MODAL
 * ==========================================
 */

function openProjectModal() {

    const modal =
        document.getElementById("project-modal");

    if (!modal) {
        return;
    }

    modal.classList.remove("hidden");

    const nameInput =
        document.getElementById("project-name");

    if (nameInput) {
        nameInput.focus();
    }

}


function closeProjectModal() {

    const modal =
        document.getElementById("project-modal");

    if (!modal) {
        return;
    }

    modal.classList.add("hidden");

}


/*
 * ==========================================
 * CREATE PROJECT
 * ==========================================
 */

function createLocalProject() {

    const name =
        document
            .getElementById("project-name")
            .value
            .trim();


    const description =
        document
            .getElementById("project-description")
            .value
            .trim();


    const hdl =
        document
            .getElementById("project-hdl")
            .value;


    if (!name) {

        alert(
            "Please enter a project name."
        );

        return;
    }


    const project = {

        id:
            Date.now().toString(),

        name,

        description:
            description ||
            "Hardware design project",

        hdl,

        status:
            "active",

        designs:
            0,

        createdAt:
            new Date().toISOString()

    };


    localProjects.push(project);


    localStorage.setItem(
        "chipd_projects",
        JSON.stringify(localProjects)
    );


    closeProjectModal();


    renderProjectList();

}


/*
 * ==========================================
 * RENDER PROJECTS
 * ==========================================
 */

function renderProjectList(
    searchTerm = ""
) {

    const container =
        document.getElementById(
            "projects-container"
        );


    if (!container) {
        return;
    }


    const normalizedSearch =
        searchTerm
            .trim()
            .toLowerCase();


    const filtered =
        localProjects.filter(project => {

            return (
                project.name
                    .toLowerCase()
                    .includes(normalizedSearch)
                ||
                project.description
                    .toLowerCase()
                    .includes(normalizedSearch)
            );

        });


    if (filtered.length === 0) {

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
                            ? "Try a different search term."
                            : "Create your first hardware project to begin."
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


    container.innerHTML = filtered
        .map(project => {

            return `

                <article
                    class="project-card-large"
                    onclick="openProject('${project.id}')"
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
                                    ACTIVE
                                </span>

                            </div>


                            <p>
                                ${escapeHtml(project.description)}
                            </p>


                            <div class="project-meta">

                                <span>
                                    ${project.hdl}
                                </span>

                                <span>
                                    ${project.designs} design
                                </span>

                                <span>
                                    Created ${formatProjectDate(project.createdAt)}
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
 * OPEN PROJECT
 * ==========================================
 */

function openProject(projectId) {

    const project =
        localProjects.find(
            item => item.id === projectId
        );


    if (!project) {
        return;
    }


    /*
     * Save selected project temporarily.
     *
     * Later this will become the real
     * backend project ID.
     */

    localStorage.setItem(
        "chipd_current_project",
        JSON.stringify(project)
    );


    navigate("design");

}


/*
 * ==========================================
 * HELPERS
 * ==========================================
 */

function formatProjectDate(date) {

    return new Date(date)
        .toLocaleDateString(
            undefined,
            {
                month: "short",
                day: "numeric"
            }
        );

}


function escapeHtml(value) {

    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


/*
 * ==========================================
 * PAGE INITIALIZATION
 * ==========================================
 */

function initializeProjectsPage() {

    renderProjectList();

}