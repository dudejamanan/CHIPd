function renderVerification() {

    return `

        <div class="page-header">

            <div>

                <div class="eyebrow">
                    HARDWARE VERIFICATION
                </div>

                <h1>
                    Verification
                </h1>

                <p>
                    Compile, simulate and inspect hardware verification runs.
                </p>

            </div>

        </div>


        <section class="verification-overview-grid">

            <div class="verification-stat">

                <span>
                    TOTAL RUNS
                </span>

                <strong>
                    0
                </strong>

            </div>


            <div class="verification-stat">

                <span>
                    PASSED
                </span>

                <strong class="success-text">
                    0
                </strong>

            </div>


            <div class="verification-stat">

                <span>
                    FAILED
                </span>

                <strong class="danger-text">
                    0
                </strong>

            </div>


            <div class="verification-stat">

                <span>
                    PASS RATE
                </span>

                <strong>
                    —
                </strong>

            </div>

        </section>


        <section class="panel verification-history">

            <div class="panel-header">

                <div>

                    <h2>
                        Verification History
                    </h2>

                    <p>
                        Recent compiler and simulation results
                    </p>

                </div>

            </div>


            <div class="empty-state">

                <div class="empty-icon">
                    ✓
                </div>

                <h3>
                    No verification runs
                </h3>

                <p>
                    Verification runs will appear here after
                    you generate and verify a design.
                </p>

            </div>

        </section>

    `;

}