/*
 * ============================================================
 * SILICA DASHBOARD
 * ============================================================
 *
 * Dashboard reads the same mock backend state used by
 * api-client.js.
 *
 * Important:
 *
 * verification_history contains EVERY verification run.
 *
 * Example:
 *
 *   FAILED
 *      ↓
 *   Apply AI Fix
 *      ↓
 *   PASSED
 *
 * Dashboard:
 *
 *   Verification Runs = 2
 *
 * ============================================================
 */


/*
 * ============================================================
 * MAIN DASHBOARD
 * ============================================================
 */

function renderDashboard() {

    const dashboardData =
        getDashboardData();


    setTimeout(
        refreshDashboardData,
        0
    );


    return `

        <div class="page-header">

            <div>

                <div class="eyebrow">
                    HARDWARE DESIGN AUTOMATION
                </div>

                <h1>
                    Overview
                </h1>

                <p>
                    Design, verify and debug digital hardware
                    with AI-assisted engineering.
                </p>

            </div>


            <button
                class="primary-button"
                onclick="navigate('projects')"
            >
                + New Project
            </button>

        </div>


        <!-- =====================================
             STATISTICS
        ====================================== -->

        <section class="stats-grid">

            <div class="stat-card">

                <div class="stat-label">
                    PROJECTS
                </div>

                <div
                    class="stat-value"
                    id="dashboard-project-count"
                >
                    ${dashboardData.projectCount}
                </div>

                <div class="stat-description">
                    Hardware projects
                </div>

            </div>


            <div class="stat-card">

                <div class="stat-label">
                    DESIGNS
                </div>

                <div
                    class="stat-value"
                    id="dashboard-design-count"
                >
                    ${dashboardData.designCount}
                </div>

                <div class="stat-description">
                    RTL designs
                </div>

            </div>


            <div class="stat-card">

                <div class="stat-label">
                    VERIFICATION RUNS
                </div>

                <div
                    class="stat-value"
                    id="dashboard-verification-count"
                >
                    ${dashboardData.verificationCount}
                </div>

                <div class="stat-description">
                    Simulation runs
                </div>

            </div>


            <div class="stat-card">

                <div class="stat-label">
                    PASS RATE
                </div>

                <div
                    class="stat-value"
                    id="dashboard-pass-rate"
                >
                    ${dashboardData.passRate}
                </div>

                <div
                    class="stat-description"
                    id="dashboard-pass-description"
                >
                    ${dashboardData.passDescription}
                </div>

            </div>

        </section>


        <!-- =====================================
             MAIN PANELS
        ====================================== -->

        <section class="content-grid">


            <!-- RECENT DESIGNS -->

            <div class="panel">

                <div class="panel-header">

                    <div>

                        <h2>
                            Recent Designs
                        </h2>

                        <p>
                            Your latest hardware designs
                        </p>

                    </div>

                    <button
                        class="text-button"
                        onclick="navigate('projects')"
                    >
                        View all →
                    </button>

                </div>


                <div
                    id="dashboard-recent-designs"
                >
                    ${renderRecentDesigns(
                        dashboardData.recentDesigns
                    )}
                </div>

            </div>


            <!-- VERIFICATION -->

            <div class="panel">

                <div class="panel-header">

                    <div>

                        <h2>
                            Verification
                        </h2>

                        <p>
                            Latest simulation activity
                        </p>

                    </div>

                </div>


                <div
                    id="dashboard-verification"
                >
                    ${renderDashboardVerification(
                        dashboardData.latestVerification
                    )}
                </div>

            </div>

        </section>


        <!-- =====================================
             WORKFLOW
        ====================================== -->

        <section class="workflow-panel">

            <div class="panel-header">

                <div>

                    <h2>
                        CHIPd Workflow
                    </h2>

                    <p>
                        From specification to verified RTL
                    </p>

                </div>

            </div>


            <div class="workflow">

                <div class="workflow-step">

                    <div class="workflow-number">
                        01
                    </div>

                    <div>

                        <strong>
                            Specification
                        </strong>

                        <span>
                            Describe the hardware
                        </span>

                    </div>

                </div>


                <div class="workflow-arrow">
                    →
                </div>


                <div class="workflow-step">

                    <div class="workflow-number">
                        02
                    </div>

                    <div>

                        <strong>
                            AI RTL
                        </strong>

                        <span>
                            Generate SystemVerilog
                        </span>

                    </div>

                </div>


                <div class="workflow-arrow">
                    →
                </div>


                <div class="workflow-step">

                    <div class="workflow-number">
                        03
                    </div>

                    <div>

                        <strong>
                            Verification
                        </strong>

                        <span>
                            Compile & simulate
                        </span>

                    </div>

                </div>


                <div class="workflow-arrow">
                    →
                </div>


                <div class="workflow-step">

                    <div class="workflow-number">
                        04
                    </div>

                    <div>

                        <strong>
                            AI Debug
                        </strong>

                        <span>
                            Analyze & fix failures
                        </span>

                    </div>

                </div>

            </div>

        </section>

    `;

}


/*
 * ============================================================
 * GET DASHBOARD DATA
 * ============================================================
 */

function getDashboardData() {

    const state =
        loadDashboardMockState();


    const projects =
        Array.isArray(
            state.projects
        )
            ? state.projects
            : [];


    const designsObject =
        state.designs &&
        typeof state.designs === "object"
            ? state.designs
            : {};


    const designs =
        Object.values(
            designsObject
        );


    /*
     * IMPORTANT:
     *
     * Read verification_history rather than
     * state.verifications.
     *
     * state.verifications contains only the latest result
     * for each design.
     *
     * verification_history contains every run.
     */

    const verificationHistory =
        Array.isArray(
            state.verification_history
        )
            ? state.verification_history
            : [];


    const verificationCount =
        verificationHistory.length;


    const passedVerifications =
        verificationHistory.filter(
            verification => {

                return String(
                    verification?.status ||
                    ""
                ).toLowerCase() === "passed";

            }
        ).length;


    const passRate =
        verificationCount > 0
            ? `${Math.round(
                (
                    passedVerifications /
                    verificationCount
                ) * 100
            )}%`
            : "—";


    const passDescription =
        verificationCount > 0
            ? `${passedVerifications} of ${verificationCount} passed`
            : "No verification data";


    /*
     * Recent designs
     */

    const recentDesigns =
        designs
            .slice()
            .sort(
                (
                    a,
                    b
                ) => {

                    return (
                        new Date(
                            b.updated_at ||
                            b.created_at ||
                            0
                        ).getTime()
                        -
                        new Date(
                            a.updated_at ||
                            a.created_at ||
                            0
                        ).getTime()
                    );

                }
            )
            .slice(
                0,
                5
            );


    /*
     * Latest verification
     *
     * Use the actual latest verification-history record.
     */

    let latestVerification =
        null;


    if (
        verificationHistory.length > 0
    ) {

        const latest =
            verificationHistory
                .slice()
                .sort(
                    (
                        a,
                        b
                    ) => {

                        return (
                            new Date(
                                b.created_at ||
                                0
                            ).getTime()
                            -
                            new Date(
                                a.created_at ||
                                0
                            ).getTime()
                        );

                    }
                )[0];


        const design =
            designsObject[
                latest.design_id
            ];


        latestVerification = {

            designId:
                latest.design_id,

            verification:
                latest,

            design:
                design || null

        };

    }


    return {

        projectCount:
            projects.length,

        designCount:
            designs.length,

        verificationCount,

        passedVerifications,

        passRate,

        passDescription,

        recentDesigns,

        latestVerification

    };

}


/*
 * ============================================================
 * LOAD MOCK STATE
 * ============================================================
 */

function loadDashboardMockState() {

    const storageKey =
        "silica_mock_backend_state";


    const stored =
        localStorage.getItem(
            storageKey
        );


    if (!stored) {

        return {

            projects: [],

            designs: {},

            verifications: {},

            verification_history: [],

            analyses: {},

            counters: {}

        };

    }


    try {

        const state =
            JSON.parse(
                stored
            );


        return {

            projects:
                Array.isArray(
                    state.projects
                )
                    ? state.projects
                    : [],

            designs:
                state.designs &&
                typeof state.designs === "object"
                    ? state.designs
                    : {},

            verifications:
                state.verifications &&
                typeof state.verifications === "object"
                    ? state.verifications
                    : {},

            verification_history:
                Array.isArray(
                    state.verification_history
                )
                    ? state.verification_history
                    : [],

            analyses:
                state.analyses &&
                typeof state.analyses === "object"
                    ? state.analyses
                    : {},

            counters:
                state.counters || {}

        };

    } catch (error) {

        console.warn(
            "Unable to read Silica dashboard mock state.",
            error
        );


        return {

            projects: [],

            designs: {},

            verifications: {},

            verification_history: [],

            analyses: {},

            counters: {}

        };

    }

}


/*
 * ============================================================
 * REFRESH DASHBOARD
 * ============================================================
 */

function refreshDashboardData() {

    const dashboard =
        getDashboardData();


    const projectCount =
        document.getElementById(
            "dashboard-project-count"
        );


    const designCount =
        document.getElementById(
            "dashboard-design-count"
        );


    const verificationCount =
        document.getElementById(
            "dashboard-verification-count"
        );


    const passRate =
        document.getElementById(
            "dashboard-pass-rate"
        );


    /*
     * Dashboard is not currently mounted.
     */

    if (
        !projectCount ||
        !designCount ||
        !verificationCount ||
        !passRate
    ) {

        return;

    }


    projectCount.textContent =
        dashboard.projectCount;


    designCount.textContent =
        dashboard.designCount;


    verificationCount.textContent =
        dashboard.verificationCount;


    passRate.textContent =
        dashboard.passRate;


    const passDescription =
        document.getElementById(
            "dashboard-pass-description"
        );


    if (passDescription) {

        passDescription.textContent =
            dashboard.passDescription;

    }


    const recentDesigns =
        document.getElementById(
            "dashboard-recent-designs"
        );


    if (recentDesigns) {

        recentDesigns.innerHTML =
            renderRecentDesigns(
                dashboard.recentDesigns
            );

    }


    const verification =
        document.getElementById(
            "dashboard-verification"
        );


    if (verification) {

        verification.innerHTML =
            renderDashboardVerification(
                dashboard.latestVerification
            );

    }

}


/*
 * ============================================================
 * RECENT DESIGNS
 * ============================================================
 */

function renderRecentDesigns(
    designs
) {

    if (
        !designs ||
        designs.length === 0
    ) {

        return `

            <div class="empty-state">

                <div class="empty-icon">
                    ◇
                </div>

                <h3>
                    No designs yet
                </h3>

                <p>
                    Create your first hardware design
                    from a natural-language specification.
                </p>

                <button
                    class="secondary-button"
                    onclick="navigate('projects')"
                >
                    Create Design
                </button>

            </div>

        `;

    }


    return `

        <div
            class="dashboard-design-list"
            style="
                display:flex;
                flex-direction:column;
                gap:12px;
            "
        >

            ${designs
                .map(
                    design => {

                        const status =
                            String(
                                design.status ||
                                "created"
                            ).toLowerCase();


                        const statusLabel =
                            status === "passed"
                                ? "PASSED"
                                : status === "failed"
                                    ? "FAILED"
                                    : "CREATED";


                        const statusClass =
                            status === "passed"
                                ? "pass"
                                : status === "failed"
                                    ? "fail"
                                    : "ready";


                        return `

                            <div
                                class="dashboard-design-item"
                                style="
                                    display:flex;
                                    align-items:center;
                                    justify-content:space-between;
                                    gap:16px;
                                    padding:14px 0;
                                    border-bottom:1px solid var(--border-color, #e5e7eb);
                                    cursor:pointer;
                                "
                                onclick="openDashboardDesign('${escapeDashboardValue(
                                    design.id ||
                                    design.design_id
                                )}')"
                            >

                                <div
                                    style="
                                        min-width:0;
                                    "
                                >

                                    <strong
                                        style="
                                            display:block;
                                            margin-bottom:4px;
                                        "
                                    >
                                        ${escapeHtml(
                                            design.name ||
                                            "Untitled Design"
                                        )}
                                    </strong>


                                    <span
                                        style="
                                            display:block;
                                            overflow:hidden;
                                            text-overflow:ellipsis;
                                            white-space:nowrap;
                                            max-width:360px;
                                        "
                                    >
                                        ${escapeHtml(
                                            design.language ||
                                            "systemverilog"
                                        )}
                                    </span>

                                </div>


                                <span
                                    class="design-status ${statusClass}"
                                >
                                    ${statusLabel}
                                </span>

                            </div>

                        `;

                    }
                )
                .join("")}

        </div>

    `;

}


/*
 * ============================================================
 * LATEST VERIFICATION
 * ============================================================
 */

function renderDashboardVerification(
    latest
) {

    if (!latest) {

        return `

            <div class="empty-state compact">

                <div class="empty-icon">
                    ✓
                </div>

                <h3>
                    No verification runs
                </h3>

                <p>
                    Verification results will appear here.
                </p>

            </div>

        `;

    }


    const verification =
        latest.verification ||
        {};


    const design =
        latest.design ||
        {};


    const status =
        String(
            verification.status ||
            "unknown"
        ).toLowerCase();


    const passed =
        status === "passed";


    const tests =
        verification.tests ||
        {};


    const passedTests =
        tests.passed ??
        0;


    const totalTests =
        tests.total ??
        0;


    const duration =
        verification.duration_ms ??
        null;


    return `

        <div
            class="dashboard-verification-result"
            style="
                padding:8px 0;
            "
        >

            <div
                style="
                    display:flex;
                    align-items:center;
                    justify-content:space-between;
                    gap:12px;
                    margin-bottom:20px;
                "
            >

                <div>

                    <strong
                        style="
                            display:block;
                            margin-bottom:5px;
                        "
                    >
                        ${escapeHtml(
                            design.name ||
                            "Latest design"
                        )}
                    </strong>

                    <span>
                        Latest verification result
                    </span>

                </div>


                <span
                    class="design-status ${
                        passed
                            ? "pass"
                            : "fail"
                    }"
                >
                    ${
                        passed
                            ? "PASSED"
                            : "FAILED"
                    }
                </span>

            </div>


            <div
                style="
                    display:grid;
                    grid-template-columns:repeat(3, 1fr);
                    gap:12px;
                "
            >

                <div>

                    <div
                        style="
                            font-size:11px;
                            letter-spacing:.08em;
                            margin-bottom:4px;
                        "
                    >
                        TESTS
                    </div>

                    <strong>
                        ${passedTests}/${totalTests}
                    </strong>

                </div>


                <div>

                    <div
                        style="
                            font-size:11px;
                            letter-spacing:.08em;
                            margin-bottom:4px;
                        "
                    >
                        DURATION
                    </div>

                    <strong>
                        ${
                            duration !== null
                                ? `${duration} ms`
                                : "—"
                        }
                    </strong>

                </div>


                <div>

                    <div
                        style="
                            font-size:11px;
                            letter-spacing:.08em;
                            margin-bottom:4px;
                        "
                    >
                        STATUS
                    </div>

                    <strong>
                        ${
                            passed
                                ? "PASS"
                                : "FAIL"
                        }
                    </strong>

                </div>

            </div>

        </div>

    `;

}


/*
 * ============================================================
 * OPEN DESIGN FROM DASHBOARD
 * ============================================================
 */

function openDashboardDesign(
    designId
) {

    const state =
        loadDashboardMockState();


    const design =
        state.designs &&
        state.designs[
            designId
        ];


    if (!design) {
        return;
    }


    const project =
        state.projects.find(
            item =>
                String(
                    item.id
                ) ===
                String(
                    design.project_id
                )
        );


    if (project) {

        localStorage.setItem(

            "chipd_current_project",

            JSON.stringify(
                project
            )

        );

    }


    localStorage.setItem(

        "chipd_current_design",

        JSON.stringify(
            design
        )

    );


    navigate(
        "design"
    );

}


/*
 * ============================================================
 * HTML HELPERS
 * ============================================================
 */

function escapeDashboardValue(
    value
) {

    return String(
        value ?? ""
    )
        .replace(
            /\\/g,
            "\\\\"
        )
        .replace(
            /'/g,
            "\\'"
        )
        .replace(
            /"/g,
            "&quot;"
        );

}


function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}