function renderDashboard() {

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

                <div class="stat-value">
                    0
                </div>

                <div class="stat-description">
                    Hardware projects
                </div>

            </div>


            <div class="stat-card">

                <div class="stat-label">
                    DESIGNS
                </div>

                <div class="stat-value">
                    0
                </div>

                <div class="stat-description">
                    RTL designs
                </div>

            </div>


            <div class="stat-card">

                <div class="stat-label">
                    VERIFICATION RUNS
                </div>

                <div class="stat-value">
                    0
                </div>

                <div class="stat-description">
                    Simulation runs
                </div>

            </div>


            <div class="stat-card">

                <div class="stat-label">
                    PASS RATE
                </div>

                <div class="stat-value">
                    —
                </div>

                <div class="stat-description">
                    No verification data
                </div>

            </div>

        </section>


        <!-- =====================================
             MAIN PANELS
        ====================================== -->

        <section class="content-grid">

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

            </div>


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