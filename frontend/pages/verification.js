function renderVerification() {

    const state =
        typeof getSilicaMockState === "function"
            ? getSilicaMockState()
            : null;

    const history =
        state &&
        Array.isArray(state.verification_history)
            ? state.verification_history
            : [];

    const runs = [...history].reverse();

    const totalRuns = history.length;

    const passedRuns =
        history.filter(
            run =>
                String(run.status).toLowerCase() ===
                "passed"
        ).length;

    const failedRuns =
        history.filter(
            run =>
                String(run.status).toLowerCase() ===
                "failed"
        ).length;

    const passRate =
        totalRuns > 0
            ? Math.round(
                  (passedRuns / totalRuns) * 100
              )
            : 0;


    function formatDate(value) {

        if (!value) {
            return "—";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return "—";
        }

        return date.toLocaleString([], {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }


    function renderRun(run, index) {

        const status =
            String(
                run.status || "unknown"
            ).toLowerCase();

        const passed =
            status === "passed";

        const tests =
            run.tests || {};

        const passedTests =
            Number(
                tests.passed || 0
            );

        const totalTests =
            Number(
                tests.total || 0
            );

        const duration =
            run.duration_ms !== undefined
                ? `${run.duration_ms} ms`
                : "—";

        const runNumber =
            history.length - index;


        return `
            <div class="verification-history-item">

                <div class="verification-history-main">

                    <div class="verification-run-number">

                        <span>
                            Verification Run
                        </span>

                        <strong>
                            #${runNumber}
                        </strong>

                    </div>


                    <div
                        class="verification-run-status ${
                            passed
                                ? "passed"
                                : "failed"
                        }"
                    >

                        <span
                            class="verification-status-dot"
                        ></span>

                        <strong>
                            ${
                                passed
                                    ? "PASSED"
                                    : "FAILED"
                            }
                        </strong>

                    </div>

                </div>


                <div class="verification-history-details">

                    <div class="verification-history-detail">

                        <span>
                            TESTS
                        </span>

                        <strong>
                            ${passedTests}/${totalTests}
                        </strong>

                    </div>


                    <div class="verification-history-detail">

                        <span>
                            DURATION
                        </span>

                        <strong>
                            ${duration}
                        </strong>

                    </div>


                    <div class="verification-history-detail">

                        <span>
                            STATUS
                        </span>

                        <strong
                            class="${
                                passed
                                    ? "success-text"
                                    : "danger-text"
                            }"
                        >
                            ${
                                passed
                                    ? "Passed"
                                    : "Failed"
                            }
                        </strong>

                    </div>


                    <div class="verification-history-detail">

                        <span>
                            TIME
                        </span>

                        <strong>
                            ${formatDate(
                                run.created_at
                            )}
                        </strong>

                    </div>

                </div>

            </div>
        `;
    }


    const historyHTML =
        runs.length > 0

            ? runs
                  .map(
                      (run, index) =>
                          renderRun(
                              run,
                              index
                          )
                  )
                  .join("")

            : `
                <div class="empty-state">

                    <div class="empty-icon">
                        ✓
                    </div>

                    <h3>
                        No verification runs
                    </h3>

                    <p>
                        Verification runs will appear here
                        after you verify a design.
                    </p>

                </div>
            `;


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
                    Review all verification runs across your designs.
                </p>

            </div>

        </div>


        <section class="verification-overview-grid">


            <div class="verification-stat">

                <span>
                    TOTAL RUNS
                </span>

                <strong>
                    ${totalRuns}
                </strong>

            </div>


            <div class="verification-stat">

                <span>
                    PASSED
                </span>

                <strong class="success-text">
                    ${passedRuns}
                </strong>

            </div>


            <div class="verification-stat">

                <span>
                    FAILED
                </span>

                <strong class="danger-text">
                    ${failedRuns}
                </strong>

            </div>


            <div class="verification-stat">

                <span>
                    PASS RATE
                </span>

                <strong>
                    ${
                        totalRuns > 0
                            ? `${passRate}%`
                            : "—"
                    }
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
                        Recent verification runs
                    </p>

                </div>

            </div>


            <div class="verification-history-list">

                ${historyHTML}

            </div>


        </section>

    `;
}