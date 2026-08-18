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
                hdl: "SystemVerilog"
            };


    return `

        <div class="design-page">

            <!-- =================================
                 DESIGN HEADER
            ================================== -->

            <div class="design-header">

                <div>

                    <div class="breadcrumb-small">
                        Projects / ${escapeHtml(project.name)}
                    </div>

                    <div class="design-title-row">

                        <h1>
                            ${escapeHtml(project.name)}
                        </h1>

                        <span class="design-status ready">
                            READY
                        </span>

                    </div>

                </div>


                <div class="design-actions">

                    <button
                        class="secondary-button"
                    >
                        Save
                    </button>

                    <button
                        class="primary-button"
                        onclick="generateAndVerify()"
                    >
                        Generate RTL + Verify
                    </button>

                </div>

            </div>


            <!-- =================================
                 DESIGN WORKSPACE
            ================================== -->

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
                        >Create a synchronous 4-bit up counter with:
- clk input
- active-low synchronous reset
- 4-bit count output
- increment every rising edge
- wrap around at 15</textarea>


                        <div class="specification-footer">

                            <span>
                                Natural-language specification
                            </span>

                            <span>
                                SystemVerilog
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

                            <span class="file-name">
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


            <!-- =================================
                 VERIFICATION BAR
            ================================== -->

            <section class="verification-bar">

                <div class="verification-summary">

                    <div class="verification-indicator neutral">
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


            <!-- =================================
                 TIMELINE
            ================================== -->

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


                <div class="timeline">

                    <div class="timeline-step">

                        <div class="timeline-marker">
                            01
                        </div>

                        <div class="timeline-info">

                            <strong>
                                RTL generated
                            </strong>

                            <span>
                                Waiting
                            </span>

                        </div>

                    </div>


                    <div class="timeline-line"></div>


                    <div class="timeline-step">

                        <div class="timeline-marker">
                            02
                        </div>

                        <div class="timeline-info">

                            <strong>
                                Testbench generated
                            </strong>

                            <span>
                                Waiting
                            </span>

                        </div>

                    </div>


                    <div class="timeline-line"></div>


                    <div class="timeline-step">

                        <div class="timeline-marker">
                            03
                        </div>

                        <div class="timeline-info">

                            <strong>
                                Compilation
                            </strong>

                            <span>
                                Waiting
                            </span>

                        </div>

                    </div>


                    <div class="timeline-line"></div>


                    <div class="timeline-step">

                        <div class="timeline-marker">
                            04
                        </div>

                        <div class="timeline-info">

                            <strong>
                                Simulation
                            </strong>

                            <span>
                                Waiting
                            </span>

                        </div>

                    </div>


                    <div class="timeline-line"></div>


                    <div class="timeline-step">

                        <div class="timeline-marker">
                            05
                        </div>

                        <div class="timeline-info">

                            <strong>
                                AI analysis
                            </strong>

                            <span>
                                Waiting
                            </span>

                        </div>

                    </div>

                </div>

            </section>

        </div>

    `;

}


/*
 * Temporary frontend action.
 *
 * Backend integration comes next.
 */

function generateAndVerify() {

    const message =
        document.getElementById(
            "verification-message"
        );

    const status =
        document.getElementById(
            "verification-status"
        );


    if (message) {
        message.textContent =
            "Generation and verification will connect to the backend next.";
    }


    if (status) {
        status.textContent =
            "READY";
    }

}


function copyRTL() {

    const editor =
        document.getElementById(
            "rtl-editor"
        );


    if (!editor) {
        return;
    }


    const code =
        editor.innerText;


    if (
        code &&
        code.trim()
    ) {

        navigator.clipboard.writeText(
            code
        );

    }

}