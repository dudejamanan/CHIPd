function renderDesign() {

    const storedProject =
        localStorage.getItem(
            "chipd_current_project"
        );


    const project =
        storedProject
            ? JSON.parse(storedProject)
            : {
                name: "New Hardware Design",
                id: null,
                hdl: "systemverilog"
            };


    const savedSpecification =
        localStorage.getItem(
            `chipd_spec_${project.id || "draft"}`
        );


    const specification =
        savedSpecification ||
        `Create a synchronous 4-bit up counter with:
- clk input
- active-low synchronous reset
- 4-bit count output
- increment every rising edge
- wrap around at 15`;


    return `

        <div class="design-page">

            <!-- HEADER -->

            <div class="design-header">

                <div>

                    <div class="breadcrumb-small">
                        Projects /
                        ${escapeHtml(project.name)}
                    </div>


                    <div class="design-title-row">

                        <h1>
                            ${escapeHtml(project.name)}
                        </h1>

                        <span
                            class="design-status ready"
                            id="design-status-badge"
                        >
                            READY
                        </span>

                    </div>

                </div>


                <div class="design-actions">

                    <button
                        class="secondary-button"
                        onclick="saveDesignDraft()"
                    >
                        Save draft
                    </button>


                    <button
                        class="primary-button"
                        id="generate-verify-button"
                        onclick="generateAndVerify()"
                    >
                        Generate RTL + Verify
                    </button>

                </div>

            </div>


            <!-- MAIN WORKSPACE -->

            <section class="design-workspace">


                <!-- SPECIFICATION -->

                <div class="workspace-panel specification-panel">

                    <div class="workspace-panel-header">

                        <div>

                            <span class="panel-kicker">
                                01
                            </span>

                            <h2>
                                Specification
                            </h2>

                        </div>

                        <span class="panel-label">
                            NATURAL LANGUAGE
                        </span>

                    </div>


                    <div class="workspace-panel-body">

                        <label
                            class="editor-label"
                            for="specification"
                        >
                            Describe the hardware you want to build
                        </label>


                        <textarea
                            id="specification"
                            class="specification-editor"
                            placeholder="Describe the hardware you want to build..."
                        >${escapeHtml(specification)}</textarea>


                        <div class="specification-footer">

                            <span>
                                Natural-language specification
                            </span>

                            <span>
                                ${escapeHtml(
                                    String(
                                        project.hdl ||
                                        "systemverilog"
                                    ).toUpperCase()
                                )}
                            </span>

                        </div>

                    </div>

                </div>


                <!-- RTL -->

                <div class="workspace-panel rtl-panel">

                    <div class="workspace-panel-header">

                        <div>

                            <span class="panel-kicker">
                                02
                            </span>

                            <h2>
                                RTL
                            </h2>

                        </div>


                        <div class="rtl-header-actions">

                            <span
                                class="file-name"
                                id="rtl-file-name"
                            >
                                design.sv
                            </span>


                            <button
                                class="small-button"
                                onclick="copyRTL()"
                            >
                                Copy
                            </button>

                        </div>

                    </div>


                    <div
                        class="code-editor"
                        id="rtl-editor"
                    >

                        <div class="code-placeholder">

                            <div class="code-placeholder-icon">
                                ◇
                            </div>

                            <strong>
                                RTL not generated
                            </strong>

                            <span>
                                Generate RTL from the specification
                            </span>

                        </div>

                    </div>

                </div>


                <!-- AI COPILOT -->

                <div class="workspace-panel copilot-panel">

                    <div class="workspace-panel-header">

                        <div>

                            <span class="panel-kicker">
                                03
                            </span>

                            <h2>
                                AI Copilot
                            </h2>

                        </div>


                        <span class="ai-indicator">
                            AI
                        </span>

                    </div>


                    <div
                        class="copilot-content"
                        id="copilot-content"
                    >

                        <div class="copilot-empty">

                            <div class="copilot-icon">
                                ◈
                            </div>

                            <h3>
                                Awaiting verification
                            </h3>

                            <p>
                                AI analysis will appear here
                                when verification detects a problem.
                            </p>

                        </div>

                    </div>

                </div>


            </section>


            <!-- VERIFICATION -->

            <section
                class="verification-bar"
                id="verification-bar"
            >

                <div class="verification-summary">

                    <div
                        class="verification-indicator"
                        id="verification-indicator"
                    >
                    </div>


                    <div>

                        <div class="verification-title">
                            Verification
                        </div>


                        <div
                            class="verification-message"
                            id="verification-message"
                        >
                            Ready to compile and simulate
                        </div>

                    </div>

                </div>


                <div class="verification-metrics">

                    <div class="verification-metric">

                        <span>
                            TESTS
                        </span>

                        <strong id="test-count">
                            —
                        </strong>

                    </div>


                    <div class="verification-metric">

                        <span>
                            DURATION
                        </span>

                        <strong id="verification-duration">
                            —
                        </strong>

                    </div>


                    <div class="verification-metric">

                        <span>
                            STATUS
                        </span>

                        <strong id="verification-status">
                            READY
                        </strong>

                    </div>

                </div>

            </section>


            <!-- TIMELINE -->

            <section class="timeline-panel">

                <div class="timeline-header">

                    <div>

                        <h2>
                            Verification Timeline
                        </h2>

                        <p>
                            Track the hardware verification pipeline
                        </p>

                    </div>

                </div>


                <div
                    class="timeline"
                    id="design-timeline"
                >

                    ${renderDesignTimeline()}

                </div>

            </section>

        </div>

    `;
}


/*
 * ==========================================
 * TIMELINE
 * ==========================================
 */

function renderDesignTimeline(
    state = {}
) {

    const steps = [

        [
            "01",
            "RTL generated",
            state.rtl || "Waiting"
        ],

        [
            "02",
            "Testbench generated",
            state.testbench || "Waiting"
        ],

        [
            "03",
            "Compilation",
            state.compile || "Waiting"
        ],

        [
            "04",
            "Simulation",
            state.simulation || "Waiting"
        ],

        [
            "05",
            "AI analysis",
            state.analysis || "Waiting"
        ]

    ];


    return steps
        .map(
            (step, index) => {

                return `

                    <div class="timeline-step">

                        <div class="timeline-marker">
                            ${step[0]}
                        </div>

                        <div class="timeline-info">

                            <strong>
                                ${step[1]}
                            </strong>

                            <span>
                                ${step[2]}
                            </span>

                        </div>

                    </div>

                    ${
                        index <
                        steps.length - 1
                            ? `
                                <div
                                    class="timeline-line"
                                ></div>
                            `
                            : ""
                    }

                `;

            }
        )
        .join("");

}


/*
 * ==========================================
 * SAVE DRAFT
 * ==========================================
 */

function saveDesignDraft() {

    const project =
        getCurrentProject();


    const specification =
        document.getElementById(
            "specification"
        );


    if (
        !specification
    ) {
        return;
    }


    localStorage.setItem(

        `chipd_spec_${
            project &&
            project.id
                ? project.id
                : "draft"
        }`,

        specification.value

    );


    setVerificationMessage(
        "Draft saved locally.",
        "running"
    );

}


/*
 * ==========================================
 * GENERATE + VERIFY
 * ==========================================
 */

async function generateAndVerify() {

    const button =
        document.getElementById(
            "generate-verify-button"
        );


    const specificationElement =
        document.getElementById(
            "specification"
        );


    const project =
        getCurrentProject();


    if (
        !project ||
        !project.id
    ) {

        setVerificationMessage(
            "Open a backend-backed project before generating RTL.",
            "fail"
        );

        return;
    }


    const specification =
        specificationElement
            ? specificationElement.value.trim()
            : "";


    if (!specification) {

        setVerificationMessage(
            "Enter a hardware specification first.",
            "fail"
        );

        return;
    }


    setLoadingState(true);

    resetVerificationUI();


    try {

        /*
         * 1. Create design
         */

        setTimelineState({

            rtl:
                "Creating design",

            testbench:
                "Waiting",

            compile:
                "Waiting",

            simulation:
                "Waiting",

            analysis:
                "Waiting"

        });


        let design =
            getCurrentDesign();


        if (
            !design ||
            !(
                design.id ||
                design.design_id
            )
        ) {

            design =
                await createDesign(

                    project.id,

                    {

                        name:
                            project.name,

                        specification,

                        language:
                            project.hdl ||
                            "systemverilog"

                    }

                );


            localStorage.setItem(

                "chipd_current_design",

                JSON.stringify(design)

            );

        }


        const designId =
            design.id ||
            design.design_id;


        if (!designId) {

            throw new Error(
                "Backend did not return a design ID."
            );

        }


        /*
         * 2. Generate RTL
         */

        setTimelineState({

            rtl:
                "Generating",

            testbench:
                "Waiting",

            compile:
                "Waiting",

            simulation:
                "Waiting",

            analysis:
                "Waiting"

        });


        const rtlResult =
            await generateRTL(

                designId,

                {

                    specification,

                    language:
                        project.hdl ||
                        "systemverilog"

                }

            );


        const rtlSource =
            rtlResult.rtl_source ||
            "";


        if (!rtlSource) {

            throw new Error(
                "RTL generation returned no rtl_source."
            );

        }


        renderRTL(

            rtlSource,

            rtlResult.module_name

        );


        /*
         * 3. Generate testbench
         */

        setTimelineState({

            rtl:
                "Complete",

            testbench:
                "Generating",

            compile:
                "Waiting",

            simulation:
                "Waiting",

            analysis:
                "Waiting"

        });


        await generateTestbench(
            designId
        );


        /*
         * 4. Verify
         */

        setTimelineState({

            rtl:
                "Complete",

            testbench:
                "Complete",

            compile:
                "Running",

            simulation:
                "Waiting",

            analysis:
                "Waiting"

        });


        const verification =
            await verifyDesign(
                designId
            );


        renderVerificationResult(
            verification
        );


        /*
         * 5. AI analysis on failure
         */

        if (
            isVerificationFailure(
                verification
            )
        ) {

            setTimelineState({

                rtl:
                    "Complete",

                testbench:
                    "Complete",

                compile:
                    getCompileState(
                        verification
                    ),

                simulation:
                    getSimulationState(
                        verification
                    ),

                analysis:
                    "Analyzing"

            });


            try {

                const analysis =
                    await analyzeDesign(
                        designId
                    );


                renderAnalysis(
                    analysis
                );


                setTimelineState({

                    rtl:
                        "Complete",

                    testbench:
                        "Complete",

                    compile:
                        getCompileState(
                            verification
                        ),

                    simulation:
                        getSimulationState(
                            verification
                        ),

                    analysis:
                        "Complete"

                });

            } catch (error) {

                renderAnalysisError(
                    error
                );


                setTimelineState({

                    rtl:
                        "Complete",

                    testbench:
                        "Complete",

                    compile:
                        getCompileState(
                            verification
                        ),

                    simulation:
                        getSimulationState(
                            verification
                        ),

                    analysis:
                        "Failed"

                });

            }

        } else {

            setTimelineState({

                rtl:
                    "Complete",

                testbench:
                    "Complete",

                compile:
                    "Passed",

                simulation:
                    "Passed",

                analysis:
                    "Not required"

            });

        }


    } catch (error) {

        setVerificationMessage(

            error.message ||
            "The verification pipeline failed.",

            "fail"

        );


        setStatusText(
            "FAILED"
        );

    } finally {

        setLoadingState(
            false
        );

    }

}


/*
 * ==========================================
 * RTL VIEWER
 * ==========================================
 */

function renderRTL(
    source,
    moduleName
) {

    const editor =
        document.getElementById(
            "rtl-editor"
        );


    if (!editor) {
        return;
    }


    editor.innerHTML = `

        <pre
            class="rtl-source"
        ><code>${escapeHtml(source)}</code></pre>

    `;


    editor.dataset.rtl =
        source;


    const fileName =
        document.getElementById(
            "rtl-file-name"
        );


    if (fileName) {

        fileName.textContent =
            `${
                moduleName ||
                "design"
            }.sv`;

    }

}


/*
 * ==========================================
 * VERIFICATION RESULT
 * ==========================================
 */

function renderVerificationResult(
    result
) {

    const failed =
        isVerificationFailure(
            result
        );


    const tests =
        result &&
        result.tests
            ? result.tests
            : {};


    const passedCount =
        tests.passed ??
        tests.tests_passed ??
        null;


    const failedCount =
        tests.failed ??
        tests.tests_failed ??
        null;


    const total =
        tests.total ??
        (
            passedCount !== null &&
            failedCount !== null
                ? passedCount +
                  failedCount
                : null
        );


    const duration =
        result.duration_ms ??
        tests.duration_ms ??
        null;


    setStatusText(
        failed
            ? "FAILED"
            : "PASSED"
    );


    setVerificationMessage(

        failed
            ? "Verification failed. AI analysis is available."
            : "Verification completed successfully.",

        failed
            ? "fail"
            : "pass"

    );


    const testCount =
        document.getElementById(
            "test-count"
        );


    if (testCount) {

        testCount.textContent =
            total !== null
                ? `${
                    passedCount ??
                    "?"
                }/${total}`
                : "—";

    }


    const durationElement =
        document.getElementById(
            "verification-duration"
        );


    if (durationElement) {

        durationElement.textContent =
            duration !== null
                ? `${duration} ms`
                : "—";

    }

}


/*
 * ==========================================
 * AI ANALYSIS
 * ==========================================
 */

function renderAnalysis(
    analysis
) {

    const container =
        document.getElementById(
            "copilot-content"
        );


    if (!container) {
        return;
    }


    const confidence =
        analysis &&
        analysis.confidence !== undefined
            ? Math.round(
                Number(
                    analysis.confidence
                ) * 100
            )
            : null;


    container.innerHTML = `

        <div
            class="copilot-empty"
            style="
                justify-content:flex-start;
                text-align:left;
                padding:20px;
                gap:12px;
            "
        >

            <div
                class="copilot-icon"
                style="align-self:center;"
            >
                ◈
            </div>


            <h3
                style="
                    align-self:center;
                    margin:0;
                "
            >
                Root cause identified
            </h3>


            <div
                style="
                    width:100%;
                    margin-top:4px;
                "
            >

                <p
                    style="
                        margin-bottom:10px;
                    "
                >
                    <strong>
                        ${escapeHtml(
                            analysis?.root_cause ||
                            "Verification failure detected"
                        )}
                    </strong>
                </p>


                <p
                    style="
                        margin-bottom:14px;
                    "
                >
                    ${escapeHtml(
                        analysis?.explanation ||
                        "No explanation returned."
                    )}
                </p>


                <p
                    style="
                        margin-bottom:6px;
                    "
                >
                    <strong>
                        Suggested fix
                    </strong>
                </p>


                <p
                    style="
                        margin-bottom:14px;
                    "
                >
                    ${escapeHtml(
                        analysis?.suggested_fix ||
                        "No suggested fix returned."
                    )}
                </p>


                ${
                    confidence !== null
                        ? `
                            <span
                                class="ai-indicator"
                                style="
                                    display:inline-block;
                                    margin-bottom:14px;
                                "
                            >
                                Confidence ${confidence}%
                            </span>
                        `
                        : ""
                }


                <button
                    type="button"
                    class="primary-button"
                    id="apply-ai-fix-button"
                    onclick="applyAIFix()"
                    style="
                        width:100%;
                        margin-top:4px;
                    "
                >
                    Apply AI Fix + Re-verify
                </button>

            </div>

        </div>

    `;
}


/*
 * ==========================================
 * APPLY AI FIX + RE-VERIFY
 * ==========================================
 */

async function applyAIFix() {

    const button =
        document.getElementById(
            "apply-ai-fix-button"
        );


    const specificationElement =
        document.getElementById(
            "specification"
        );


    if (!specificationElement) {
        return;
    }


    /*
     * Prevent double clicks.
     */

    if (button) {

        button.disabled =
            true;

        button.textContent =
            "Applying fix…";

    }


    try {

        /*
         * --------------------------------------------------
         * MOCK MODE
         * --------------------------------------------------
         *
         * Our current mock backend intentionally creates
         * a failure whenever the specification contains:
         *
         *     intentional bug
         *
         * Removing that marker makes the mock verification
         * pass again.
         *
         * When Person 1's real backend is connected, this
         * frontend can later be changed to apply the actual
         * RTL fix returned by the backend.
         * --------------------------------------------------
         */

        let specification =
            specificationElement.value;


        specification =
            specification.replace(
                /\s*intentional bug\s*/gi,
                "\n"
            ).trim();


        specificationElement.value =
            specification;


        /*
         * Save the corrected specification.
         */

        const project =
            getCurrentProject();


        if (project && project.id) {

            localStorage.setItem(

                `chipd_spec_${project.id}`,

                specification

            );

        }


        /*
         * Clear the current design so the next run
         * creates a fresh design using the corrected
         * specification.
         */

        localStorage.removeItem(
            "chipd_current_design"
        );


        /*
         * Reset the AI panel while re-running.
         */

        const container =
            document.getElementById(
                "copilot-content"
            );


        if (container) {

            container.innerHTML = `

                <div
                    class="copilot-empty"
                >

                    <div
                        class="copilot-icon"
                    >
                        ◇
                    </div>

                    <h3>
                        Re-verifying design
                    </h3>

                    <p>
                        The corrected RTL is being
                        generated and verified again.
                    </p>

                </div>

            `;

        }


        /*
         * Run the complete pipeline again.
         *
         * This calls:
         *
         * createDesign
         *      ↓
         * generateRTL
         *      ↓
         * generateTestbench
         *      ↓
         * verifyDesign
         */

        await generateAndVerify();


    } catch (error) {

        console.error(
            "AI fix failed:",
            error
        );


        setVerificationMessage(

            error.message ||
            "Unable to apply the AI fix.",

            "fail"

        );


    } finally {

        /*
         * generateAndVerify() controls the main
         * loading state, so only restore this button
         * if it still exists.
         */

        const currentButton =
            document.getElementById(
                "apply-ai-fix-button"
            );


        if (currentButton) {

            currentButton.disabled =
                false;

            currentButton.textContent =
                "Apply AI Fix + Re-verify";

        }

    }

}


/*
 * ==========================================
 * AI ANALYSIS ERROR
 * ==========================================
 */

function renderAnalysisError(
    error
) {

    const container =
        document.getElementById(
            "copilot-content"
        );


    if (!container) {
        return;
    }


    container.innerHTML = `

        <div
            class="copilot-empty"
        >

            <div
                class="copilot-icon"
            >
                !
            </div>


            <h3>
                Analysis unavailable
            </h3>


            <p>
                ${escapeHtml(
                    error?.message ||
                    "The AI analysis request failed."
                )}
            </p>

        </div>

    `;

}


/*
 * ==========================================
 * COPY RTL
 * ==========================================
 */

function copyRTL() {

    const editor =
        document.getElementById(
            "rtl-editor"
        );


    const code =
        editor
            ? editor.dataset.rtl
            : "";


    if (!code) {
        return;
    }


    navigator
        .clipboard
        .writeText(code)
        .then(() => {

            const button =
                document.querySelector(
                    ".rtl-header-actions .small-button"
                );


            if (!button) {
                return;
            }


            const original =
                button.textContent;


            button.textContent =
                "Copied";


            setTimeout(
                () => {

                    button.textContent =
                        original;

                },

                1200

            );

        });

}


/*
 * ==========================================
 * STATE HELPERS
 * ==========================================
 */

function getCurrentProject() {

    const value =
        localStorage.getItem(
            "chipd_current_project"
        );


    return value
        ? JSON.parse(value)
        : null;

}


function getCurrentDesign() {

    const value =
        localStorage.getItem(
            "chipd_current_design"
        );


    return value
        ? JSON.parse(value)
        : null;

}


function setLoadingState(
    loading
) {

    const button =
        document.getElementById(
            "generate-verify-button"
        );


    const badge =
        document.getElementById(
            "design-status-badge"
        );


    if (button) {

        button.disabled =
            loading;


        button.textContent =
            loading
                ? "Generating…"
                : "Generate RTL + Verify";

    }


    if (badge) {

        badge.textContent =
            loading
                ? "RUNNING"
                : "READY";


        badge.className =
            `design-status ${
                loading
                    ? "running"
                    : "ready"
            }`;

    }


    if (loading) {

        setVerificationMessage(
            "Running RTL generation and verification…",
            "running"
        );

    }

}


function resetVerificationUI() {

    const testCount =
        document.getElementById(
            "test-count"
        );


    const duration =
        document.getElementById(
            "verification-duration"
        );


    if (testCount) {
        testCount.textContent = "—";
    }


    if (duration) {
        duration.textContent = "—";
    }


    setStatusText(
        "RUNNING"
    );

}


/*
 * ==========================================
 * VERIFICATION HELPERS
 * ==========================================
 */

function setStatusText(
    status
) {

    const element =
        document.getElementById(
            "verification-status"
        );


    if (element) {
        element.textContent =
            status;
    }

}


function setVerificationMessage(
    message,
    state = "running"
) {

    const messageElement =
        document.getElementById(
            "verification-message"
        );


    const indicator =
        document.getElementById(
            "verification-indicator"
        );


    if (messageElement) {

        messageElement.textContent =
            message;

    }


    if (indicator) {

        indicator.className =
            `verification-indicator ${state}`;

    }

}


function setTimelineState(
    state
) {

    const timeline =
        document.getElementById(
            "design-timeline"
        );


    if (timeline) {

        timeline.innerHTML =
            renderDesignTimeline(
                state
            );

    }

}


function isVerificationFailure(
    result
) {

    const status =
        String(
            result?.status || ""
        ).toLowerCase();


    if (
        status === "failed" ||
        status === "failure"
    ) {
        return true;
    }


    const failedTests =
        Number(
            result?.tests?.failed ??
            result?.tests?.tests_failed ??
            0
        );


    if (failedTests > 0) {
        return true;
    }


    const compileStatus =
        String(
            result?.compile?.status || ""
        ).toLowerCase();


    if (
        compileStatus ===
        "failed"
    ) {
        return true;
    }


    const simulationStatus =
        String(
            result?.simulation?.status || ""
        ).toLowerCase();


    return (
        simulationStatus ===
        "failed"
    );

}


function getCompileState(
    result
) {

    return (
        result?.compile?.status ||
        "Complete"
    );

}


function getSimulationState(
    result
) {

    return (
        result?.simulation?.status ||
        "Complete"
    );

}