/*
 * ============================================================
 * CHIPd / Silica
 * CHIP ARCHITECTURE VISUALIZER
 *
 * This component renders the visual RTL architecture for the
 * current hardware design.
 *
 * Current first-class visual design:
 *   4-bit synchronous up counter
 *
 * The visualization is intentionally schematic-like rather
 * than a collection of descriptive cards.
 * ============================================================
 */


(function () {

    "use strict";


    /*
     * ----------------------------------------------------------
     * HTML ESCAPING
     * ----------------------------------------------------------
     */

    function escapeHtml(value) {

        return String(
            value === null ||
            value === undefined
                ? ""
                : value
        )
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    /*
     * ----------------------------------------------------------
     * DETECT CURRENT DESIGN TYPE
     * ----------------------------------------------------------
     *
     * For now CHIPd has a detailed visual architecture for the
     * counter specification being used in the demo.
     *
     * We deliberately do not pretend to understand arbitrary
     * RTL without a real RTL parser/backend.
     * ----------------------------------------------------------
     */

    function isCounterDesign(
        specification,
        rtlSource
    ) {

        const text = (

            String(
                specification || ""
            ) +

            " " +

            String(
                rtlSource || ""
            )

        ).toLowerCase();


        return (

            text.includes("counter") &&

            (
                text.includes("4-bit") ||
                text.includes("4 bit") ||
                text.includes("[3:0]")
            )

        );

    }


    /*
     * ----------------------------------------------------------
     * MAIN RENDER FUNCTION
     * ----------------------------------------------------------
     */

    window.renderChipDesign = function (
        specification,
        rtlSource,
        moduleName
    ) {

        const container =
            document.getElementById(
                "chip-design-visualizer"
            );


        if (!container) {
            return;
        }


        /*
         * Restrict architectural rendering until RTL has been generated.
         */

        if (!rtlSource) {

            container.innerHTML = `

                <div class="code-placeholder">

                    <div class="code-placeholder-icon">
                        ◇
                    </div>

                    <strong>
                        Architecture preview
                    </strong>

                    <span>
                        Visual hardware architecture will appear here
                    </span>

                </div>

            `;

            return;

        }


        /*
         * Current detailed architecture.
         */

        if (
            isCounterDesign(
                specification,
                rtlSource
            )
        ) {

            renderCounterArchitecture(
                container,
                specification,
                rtlSource,
                moduleName
            );

            return;
        }


        /*
         * If the current design is not one of the
         * architectures we can confidently visualize,
         * do not invent hardware structure.
         */

        renderUnsupportedArchitecture(
            container,
            specification,
            rtlSource,
            moduleName
        );

    };


    /*
     * ----------------------------------------------------------
     * COUNTER ARCHITECTURE
     * ----------------------------------------------------------
     */

    function renderCounterArchitecture(
        container,
        specification,
        rtlSource,
        moduleName
    ) {

        const safeModuleName =
            escapeHtml(
                moduleName ||
                "counter_4bit"
            );


        const hasRTL =
            Boolean(
                rtlSource
            );


        container.innerHTML = `

            <div class="chip-viewer-shell">

                <!-- TOOLBAR -->

                <div class="chip-viewer-toolbar">

                    <div class="chip-viewer-title">

                        <span class="chip-live-dot"></span>

                        <div>

                            <strong>
                                4-BIT SYNCHRONOUS UP COUNTER
                            </strong>

                            <span>
                                RTL architecture
                            </span>

                        </div>

                    </div>


                    <div class="chip-viewer-actions">

                        <button
                            type="button"
                            class="chip-view-button active"
                            data-chip-view="architecture"
                        >
                            Architecture
                        </button>


                        <button
                            type="button"
                            class="chip-view-button"
                            data-chip-view="signals"
                        >
                            Signals
                        </button>


                        <button
                            type="button"
                            class="chip-view-button"
                            id="chip-fit-view"
                        >
                            Fit View
                        </button>

                    </div>

                </div>


                <!-- SCHEMATIC -->

                <div
                    class="chip-canvas"
                    id="chip-canvas"
                >

                    <div class="chip-grid"></div>


                    <svg
                        class="chip-svg"
                        id="chip-svg"
                        viewBox="0 0 1200 700"
                        preserveAspectRatio="xMidYMid meet"
                        role="img"
                        aria-label="4-bit synchronous counter RTL schematic"
                    >

                        <defs>

                            <marker
                                id="chip-arrow"
                                markerWidth="8"
                                markerHeight="8"
                                refX="7"
                                refY="4"
                                orient="auto"
                            >
                                <path
                                    d="M0,0 L8,4 L0,8 Z"
                                    fill="currentColor"
                                ></path>
                            </marker>


                            <filter
                                id="chip-glow"
                                x="-30%"
                                y="-30%"
                                width="160%"
                                height="160%"
                            >

                                <feGaussianBlur
                                    stdDeviation="3"
                                    result="blur"
                                />

                                <feMerge>

                                    <feMergeNode
                                        in="blur"
                                    />

                                    <feMergeNode
                                        in="SourceGraphic"
                                    />

                                </feMerge>

                            </filter>

                        </defs>


                        <!-- =================================================
                             SIGNAL WIRES
                        ================================================== -->

                        <!-- CLOCK -->

                        <path
                            class="chip-wire chip-wire-clock"
                            d="M80 120 H170 V315 H245"
                            fill="none"
                            stroke="#60a5fa"
                            style="fill:none; stroke:#60a5fa; stroke-width:4;"
                            marker-end="url(#chip-arrow)"
                        ></path>


                        <!-- RESET -->

                        <path
                            class="chip-wire chip-wire-reset"
                            d="M80 235 H150 V390 H245"
                            fill="none"
                            stroke="#f59e0b"
                            style="fill:none; stroke:#f59e0b; stroke-width:4;"
                            marker-end="url(#chip-arrow)"
                        ></path>


                        <!-- Q -> INCREMENTER -->

                        <path
                            class="chip-wire chip-wire-data"
                            d="M595 320 H665"
                            fill="none"
                            stroke="#a78bfa"
                            style="fill:none; stroke:#a78bfa; stroke-width:4;"
                            marker-end="url(#chip-arrow)"
                        ></path>


                        <!-- INCREMENTER -> MUX -->

                        <path
                            class="chip-wire chip-wire-data"
                            d="M810 320 H850 V400 H875"
                            marker-end="url(#chip-arrow)"
                        ></path>


                        <!-- RESET -> MUX -->

                        <path
                            class="chip-wire chip-wire-reset"
                            d="M150 390 H790 V455 H875"
                            marker-end="url(#chip-arrow)"
                        ></path>


                        <!-- MUX -> REGISTER -->

                        <path
                            class="chip-wire chip-wire-data"
                            d="M1015 400 H1060 V320 H595"
                            marker-end="url(#chip-arrow)"
                        ></path>


                        <!-- REGISTER -> OUTPUT -->

                        <path
                            class="chip-wire chip-wire-output"
                            d="M595 250 H1080 V180 H1135"
                            marker-end="url(#chip-arrow)"
                        ></path>


                        <!-- =================================================
                             INPUT PORTS
                        ================================================== -->

                        <g
                            class="chip-node chip-port-node"
                            data-chip-node="clock"
                        >

                            <rect
                                x="35"
                                y="90"
                                width="110"
                                height="60"
                                rx="6"
                                class="chip-port"
                                fill="#171f2b"
                                stroke="#607796"
                                style="fill:#171f2b; stroke:#607796; stroke-width:2;"
                            ></rect>

                            <text
                                x="55"
                                y="116"
                                class="chip-port-label"
                                style="fill:#65758d; font-size:10px; font-weight:700; letter-spacing:.08em;"
                            >
                                INPUT
                            </text>

                            <text
                                x="55"
                                y="137"
                                class="chip-port-name"
                                style="fill:#e6edf7; font-size:15px; font-weight:700;"
                            >
                                clk
                            </text>

                        </g>


                        <g
                            class="chip-node chip-port-node"
                            data-chip-node="reset"
                        >

                            <rect
                                x="35"
                                y="205"
                                width="110"
                                height="60"
                                rx="6"
                                class="chip-port chip-port-reset"
                            ></rect>

                            <text
                                x="55"
                                y="231"
                                class="chip-port-label"
                            >
                                INPUT
                            </text>

                            <text
                                x="55"
                                y="252"
                                class="chip-port-name"
                            >
                                reset_n
                            </text>

                        </g>


                        <!-- =================================================
                             CLOCK CONTROL
                        ================================================== -->

                        <g
                            class="chip-node"
                            data-chip-node="clock-control"
                        >

                            <rect
                                x="170"
                                y="280"
                                width="75"
                                height="70"
                                rx="6"
                                class="chip-logic-block chip-clock-block"
                            ></rect>

                            <text
                                x="207"
                                y="307"
                                text-anchor="middle"
                                class="chip-block-kicker"
                            >
                                CLOCK
                            </text>

                            <text
                                x="207"
                                y="328"
                                text-anchor="middle"
                                class="chip-block-name"
                            >
                                EDGE
                            </text>

                            <text
                                x="207"
                                y="344"
                                text-anchor="middle"
                                class="chip-block-small"
                            >
                                ↑ RISING
                            </text>

                        </g>


                        <!-- =================================================
                             REGISTER
                        ================================================== -->

                        <g
                            class="chip-node"
                            data-chip-node="register"
                        >

                            <rect
                                x="245"
                                y="205"
                                width="350"
                                height="230"
                                rx="8"
                                class="chip-main-register"
                                fill="#1a2432"
                                stroke="#6e91c7"
                                style="fill:#1a2432; stroke:#6e91c7; stroke-width:2;"
                            ></rect>


                            <rect
                                x="265"
                                y="225"
                                width="310"
                                height="42"
                                rx="4"
                                class="chip-block-header"
                            ></rect>


                            <text
                                x="285"
                                y="251"
                                class="chip-block-kicker"
                            >
                                SEQUENTIAL LOGIC
                            </text>


                            <text
                                x="285"
                                y="294"
                                class="chip-register-title"
                            >
                                4-BIT STATE REGISTER
                            </text>


                            <text
                                x="285"
                                y="319"
                                class="chip-register-subtitle"
                            >
                                Q[3:0] / D[3:0]
                            </text>


                            <!-- register bits -->

                            <g class="chip-register-bits">

                                <rect
                                    x="275"
                                    y="345"
                                    width="62"
                                    height="52"
                                    rx="4"
                                ></rect>

                                <rect
                                    x="347"
                                    y="345"
                                    width="62"
                                    height="52"
                                    rx="4"
                                ></rect>

                                <rect
                                    x="419"
                                    y="345"
                                    width="62"
                                    height="52"
                                    rx="4"
                                ></rect>

                                <rect
                                    x="491"
                                    y="345"
                                    width="62"
                                    height="52"
                                    rx="4"
                                ></rect>


                                <text
                                    x="306"
                                    y="366"
                                    text-anchor="middle"
                                >
                                    Q3
                                </text>

                                <text
                                    x="378"
                                    y="366"
                                    text-anchor="middle"
                                >
                                    Q2
                                </text>

                                <text
                                    x="450"
                                    y="366"
                                    text-anchor="middle"
                                >
                                    Q1
                                </text>

                                <text
                                    x="522"
                                    y="366"
                                    text-anchor="middle"
                                >
                                    Q0
                                </text>


                                <text
                                    x="306"
                                    y="387"
                                    text-anchor="middle"
                                >
                                    1 BIT
                                </text>

                                <text
                                    x="378"
                                    y="387"
                                    text-anchor="middle"
                                >
                                    1 BIT
                                </text>

                                <text
                                    x="450"
                                    y="387"
                                    text-anchor="middle"
                                >
                                    1 BIT
                                </text>

                                <text
                                    x="522"
                                    y="387"
                                    text-anchor="middle"
                                >
                                    1 BIT
                                </text>

                            </g>


                            <text
                                x="285"
                                y="418"
                                class="chip-block-small"
                            >
                                SYNCHRONOUS ACTIVE-LOW RESET
                            </text>

                        </g>


                        <!-- =================================================
                             INCREMENTER
                        ================================================== -->

                        <g
                            class="chip-node"
                            data-chip-node="incrementer"
                        >

                            <rect
                                x="665"
                                y="270"
                                width="145"
                                height="100"
                                rx="7"
                                class="chip-logic-block"
                                fill="#1b2330"
                                stroke="#7d8ca3"
                                style="fill:#1b2330; stroke:#7d8ca3; stroke-width:2;"
                            ></rect>


                            <text
                                x="737"
                                y="295"
                                text-anchor="middle"
                                class="chip-block-kicker"
                            >
                                COMBINATIONAL
                            </text>


                            <text
                                x="737"
                                y="321"
                                text-anchor="middle"
                                class="chip-block-name"
                            >
                                +1
                            </text>


                            <text
                                x="737"
                                y="344"
                                text-anchor="middle"
                                class="chip-block-small"
                            >
                                4-BIT ADDER
                            </text>


                            <text
                                x="737"
                                y="360"
                                text-anchor="middle"
                                class="chip-block-small"
                            >
                                Q + 4'b0001
                            </text>

                        </g>


                        <!-- =================================================
                             RESET MUX
                        ================================================== -->

                        <g
                            class="chip-node"
                            data-chip-node="reset-mux"
                        >

                            <path
                                d="
                                    M875 355
                                    L1015 400
                                    L875 445
                                    Z
                                "
                                class="chip-mux"
                                fill="#1d1f2b"
                                stroke="#b48d4c"
                                style="fill:#1d1f2b; stroke:#b48d4c; stroke-width:2;"
                            ></path>


                            <text
                                x="925"
                                y="397"
                                text-anchor="middle"
                                class="chip-block-name"
                            >
                                MUX
                            </text>


                            <text
                                x="925"
                                y="416"
                                text-anchor="middle"
                                class="chip-block-small"
                            >
                                RESET SELECT
                            </text>


                            <text
                                x="890"
                                y="350"
                                class="chip-mux-label"
                            >
                                1
                            </text>


                            <text
                                x="890"
                                y="454"
                                class="chip-mux-label"
                            >
                                0
                            </text>

                        </g>


                        <!-- =================================================
                             OUTPUT PORT
                        ================================================== -->

                        <g
                            class="chip-node chip-port-node"
                            data-chip-node="output"
                        >

                            <rect
                                x="1135"
                                y="150"
                                width="50"
                                height="60"
                                rx="6"
                                class="chip-port chip-port-output"
                            ></rect>


                            <text
                                x="1160"
                                y="176"
                                text-anchor="middle"
                                class="chip-port-label"
                            >
                                OUT
                            </text>


                            <text
                                x="1160"
                                y="195"
                                text-anchor="middle"
                                class="chip-port-name"
                            >
                                Q
                            </text>

                        </g>


                        <!-- =================================================
                             SIGNAL LABELS
                        ================================================== -->

                        <g class="chip-signal-label">

                            <rect
                                x="158"
                                y="105"
                                width="66"
                                height="24"
                                rx="3"
                            ></rect>

                            <text
                                x="191"
                                y="122"
                                text-anchor="middle"
                            >
                                clk
                            </text>

                        </g>


                        <g class="chip-signal-label">

                            <rect
                                x="158"
                                y="216"
                                width="78"
                                height="24"
                                rx="3"
                            ></rect>

                            <text
                                x="197"
                                y="233"
                                text-anchor="middle"
                            >
                                reset_n
                            </text>

                        </g>


                        <g class="chip-signal-label">

                            <rect
                                x="612"
                                y="294"
                                width="55"
                                height="24"
                                rx="3"
                            ></rect>

                            <text
                                x="639"
                                y="311"
                                text-anchor="middle"
                            >
                                Q[3:0]
                            </text>

                        </g>


                        <g class="chip-signal-label">

                            <rect
                                x="815"
                                y="328"
                                width="105"
                                height="24"
                                rx="3"
                            ></rect>

                            <text
                                x="867"
                                y="345"
                                text-anchor="middle"
                            >
                                next_count[3:0]
                            </text>

                        </g>


                        <g class="chip-signal-label">

                            <rect
                                x="1020"
                                y="370"
                                width="65"
                                height="24"
                                rx="3"
                            ></rect>

                            <text
                                x="1052"
                                y="387"
                                text-anchor="middle"
                            >
                                D[3:0]
                            </text>

                        </g>


                        <g class="chip-signal-label">

                            <rect
                                x="1060"
                                y="145"
                                width="75"
                                height="24"
                                rx="3"
                            ></rect>

                            <text
                                x="1097"
                                y="162"
                                text-anchor="middle"
                            >
                                count[3:0]
                            </text>

                        </g>


                        <!-- =================================================
                             RESET BEHAVIOR LABEL
                        ================================================== -->

                        <g class="chip-behavior-callout">

                            <rect
                                x="650"
                                y="500"
                                width="400"
                                height="92"
                                rx="7"
                            ></rect>


                            <text
                                x="675"
                                y="528"
                                class="chip-callout-title"
                            >
                                RESET BEHAVIOR
                            </text>


                            <text
                                x="675"
                                y="550"
                                class="chip-callout-text"
                            >
                                reset_n = 0
                            </text>


                            <text
                                x="805"
                                y="550"
                                class="chip-callout-arrow"
                            >
                                →
                            </text>


                            <text
                                x="830"
                                y="550"
                                class="chip-callout-text"
                            >
                                Q = 4'b0000
                            </text>


                            <text
                                x="675"
                                y="574"
                                class="chip-callout-text"
                            >
                                reset_n = 1
                            </text>


                            <text
                                x="805"
                                y="574"
                                class="chip-callout-arrow"
                            >
                                →
                            </text>


                            <text
                                x="830"
                                y="574"
                                class="chip-callout-text"
                            >
                                Q increments on ↑clk
                            </text>

                        </g>

                    </svg>


                    <!-- ZOOM CONTROLS -->

                    <div class="chip-canvas-controls">

                        <button
                            type="button"
                            id="chip-zoom-out"
                            title="Zoom out"
                        >
                            −
                        </button>

                        <button
                            type="button"
                            id="chip-zoom-reset"
                            title="Reset zoom"
                        >
                            100%
                        </button>

                        <button
                            type="button"
                            id="chip-zoom-in"
                            title="Zoom in"
                        >
                            +
                        </button>

                    </div>

                </div>


                <!-- LEGEND -->

                <div class="chip-viewer-footer">

                    <div class="chip-legend">

                        <span>
                            <i class="chip-legend-line clock"></i>
                            Clock
                        </span>

                        <span>
                            <i class="chip-legend-line reset"></i>
                            Reset
                        </span>

                        <span>
                            <i class="chip-legend-line data"></i>
                            Data
                        </span>

                        <span>
                            <i class="chip-legend-line output"></i>
                            Output
                        </span>

                    </div>


                    <div class="chip-viewer-meta">

                        <span>
                            ${safeModuleName}
                        </span>

                        <span>
                            4-bit state
                        </span>

                        <span>
                            ${hasRTL ? "RTL GENERATED" : "ARCHITECTURE PREVIEW"}
                        </span>

                    </div>

                </div>


                <!-- NODE INSPECTOR -->

                <div
                    class="chip-node-inspector"
                    id="chip-node-inspector"
                >

                    <div>

                        <span class="chip-inspector-kicker">
                            SELECT A BLOCK
                        </span>

                        <strong>
                            Click any hardware block to inspect it
                        </strong>

                    </div>

                    <span class="chip-inspector-hint">
                        Architecture viewer
                    </span>

                </div>

            </div>

        `;


        applySchematicColors(
            container
        );

        installCounterInteractions(
            container
        );

    }


    /*
     * ----------------------------------------------------------
     * SVG COLOR OVERRIDES
     * ----------------------------------------------------------
     *
     * Some browsers keep SVG primitives in their default black
     * fill/stroke state unless the applied color is set directly
     * on the element after insertion into the DOM.
     * ----------------------------------------------------------
     */

    function applySchematicColors(
        container
    ) {

        if (!container) {
            return;
        }

        const primitives = [
            ".chip-wire",
            ".chip-port",
            ".chip-main-register",
            ".chip-logic-block",
            ".chip-mux",
            ".chip-signal-label rect",
            ".chip-register-bits rect",
            ".chip-behavior-callout rect",
            ".chip-port-label",
            ".chip-port-name",
            ".chip-register-title",
            ".chip-register-subtitle",
            ".chip-register-bits text",
            ".chip-block-kicker",
            ".chip-block-name",
            ".chip-block-small",
            ".chip-mux-label",
            ".chip-callout-title",
            ".chip-callout-text",
            ".chip-callout-arrow"
        ];

        primitives.forEach(
            selector => {

                container.querySelectorAll(
                    selector
                ).forEach(
                    element => {

                        if (
                            element.tagName ===
                            "path" ||
                            element.tagName ===
                            "rect" ||
                            element.tagName ===
                            "polygon"
                        ) {

                            if (
                                element.classList.contains(
                                    "chip-wire"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "none"
                                );

                                const color =
                                    element.classList.contains(
                                        "chip-wire-reset"
                                    )
                                        ? "#f59e0b"
                                        : element.classList.contains(
                                            "chip-wire-output"
                                        )
                                            ? "#4ade80"
                                            : element.classList.contains(
                                                "chip-wire-clock"
                                            )
                                                ? "#60a5fa"
                                                : "#a78bfa";

                                element.setAttribute(
                                    "stroke",
                                    color
                                );
                                element.setAttribute(
                                    "style",
                                    `fill:none; stroke:${color}; stroke-width:4; stroke-linecap:round; stroke-linejoin:round;`
                                );

                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-port"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#171f2b"
                                );
                                element.setAttribute(
                                    "stroke",
                                    "#607796"
                                );
                                element.setAttribute(
                                    "style",
                                    "fill:#171f2b; stroke:#607796; stroke-width:2;"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-main-register"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#1a2432"
                                );
                                element.setAttribute(
                                    "stroke",
                                    "#6e91c7"
                                );
                                element.setAttribute(
                                    "style",
                                    "fill:#1a2432; stroke:#6e91c7; stroke-width:2;"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-logic-block"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#1b2330"
                                );
                                element.setAttribute(
                                    "stroke",
                                    "#7d8ca3"
                                );
                                element.setAttribute(
                                    "style",
                                    "fill:#1b2330; stroke:#7d8ca3; stroke-width:2;"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-mux"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#1d1f2b"
                                );
                                element.setAttribute(
                                    "stroke",
                                    "#b48d4c"
                                );
                                element.setAttribute(
                                    "style",
                                    "fill:#1d1f2b; stroke:#b48d4c; stroke-width:2;"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-signal-label"
                                ) ||
                                element.classList.contains(
                                    "chip-register-bits"
                                ) ||
                                element.classList.contains(
                                    "chip-behavior-callout"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "rgba(17, 24, 34, 0.9)"
                                );
                                element.setAttribute(
                                    "stroke",
                                    "#2f3d4f"
                                );
                            }
                        }

                        if (
                            element.tagName ===
                            "text"
                        ) {
                            if (
                                element.classList.contains(
                                    "chip-port-label"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#65758d"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-port-name"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#e6edf7"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-register-title"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#edf3fb"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-register-subtitle"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#71839b"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-register-bits"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#dfeafc"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-block-kicker"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#73849b"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-block-name"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#dfe8f5"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-block-small"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#7e8ea4"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-mux-label"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#cbd5e1"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-callout-title"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#dfe8f5"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-callout-text"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#75849a"
                                );
                                return;
                            }

                            if (
                                element.classList.contains(
                                    "chip-callout-arrow"
                                )
                            ) {
                                element.setAttribute(
                                    "fill",
                                    "#6e8fbd"
                                );
                            }
                        }

                    }
                );

            }
        );

    }


    /*
     * ----------------------------------------------------------
     * NODE INTERACTIONS
     * ----------------------------------------------------------
     */

    function installCounterInteractions(
        container
    ) {

        const nodes =
            container.querySelectorAll(
                "[data-chip-node]"
            );


        const inspector =
            container.querySelector(
                "#chip-node-inspector"
            );


        const descriptions = {

            clock: {

                title:
                    "Clock Input",

                kicker:
                    "INPUT PORT",

                body:
                    "Rising-edge clock used by the sequential state register.",

                metadata:
                    "clk • 1 bit • posedge"

            },


            reset: {

                title:
                    "Active-Low Reset",

                kicker:
                    "INPUT PORT",

                body:
                    "Synchronous reset control. When reset_n is low at the rising clock edge, the counter state is loaded with zero.",

                metadata:
                    "reset_n • 1 bit • active-low"

            },


            "clock-control": {

                title:
                    "Clock Edge Control",

                kicker:
                    "SEQUENTIAL CONTROL",

                body:
                    "The counter updates its state on every rising edge of clk.",

                metadata:
                    "posedge clk"

            },


            register: {

                title:
                    "4-Bit State Register",

                kicker:
                    "SEQUENTIAL LOGIC",

                body:
                    "Stores the current counter state. The register contains four one-bit state elements representing Q[3:0].",

                metadata:
                    "Q[3:0] • D[3:0] • synchronous reset"

            },


            incrementer: {

                title:
                    "4-Bit Incrementer",

                kicker:
                    "COMBINATIONAL LOGIC",

                body:
                    "Adds 4'b0001 to the current register value to produce the next counter state.",

                metadata:
                    "Q[3:0] + 4'b0001"

            },


            "reset-mux": {

                title:
                    "Reset Select Logic",

                kicker:
                    "CONTROL LOGIC",

                body:
                    "Selects zero during synchronous reset and otherwise forwards the incremented next-state value into the register.",

                metadata:
                    "reset_n • 0 → 0000"

            },


            output: {

                title:
                    "Counter Output",

                kicker:
                    "OUTPUT PORT",

                body:
                    "The current register state is exposed as the 4-bit count output.",

                metadata:
                    "count[3:0] • 4 bits"

            }

        };


        nodes.forEach(
            node => {

                node.addEventListener(
                    "click",
                    event => {

                        event.stopPropagation();


                        nodes.forEach(
                            item => {

                                item.classList.remove(
                                    "selected"
                                );

                            }
                        );


                        node.classList.add(
                            "selected"
                        );


                        const key =
                            node.dataset.chipNode;


                        const info =
                            descriptions[key];


                        if (
                            !inspector ||
                            !info
                        ) {
                            return;
                        }


                        inspector.innerHTML = `

                            <div class="chip-inspector-content">

                                <span class="chip-inspector-kicker">
                                    ${escapeHtml(info.kicker)}
                                </span>

                                <strong>
                                    ${escapeHtml(info.title)}
                                </strong>

                                <p>
                                    ${escapeHtml(info.body)}
                                </p>

                                <code>
                                    ${escapeHtml(info.metadata)}
                                </code>

                            </div>

                        `;

                    }
                );

            }
        );


        /*
         * View buttons
         */

        const viewButtons =
            container.querySelectorAll(
                "[data-chip-view]"
            );


        viewButtons.forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        viewButtons.forEach(
                            item => {

                                item.classList.remove(
                                    "active"
                                );

                            }
                        );


                        button.classList.add(
                            "active"
                        );


                        const view =
                            button.dataset.chipView;


                        if (
                            view ===
                            "signals"
                        ) {

                            highlightSignals(
                                container
                            );

                        } else {

                            clearSignalHighlight(
                                container
                            );

                        }

                    }
                );

            }
        );


        /*
         * Fit view
         */

        const fitButton =
            container.querySelector(
                "#chip-fit-view"
            );


        if (fitButton) {

            fitButton.addEventListener(
                "click",
                () => {

                    resetZoom(
                        container
                    );

                }
            );

        }


        /*
         * Zoom
         */

        const zoomIn =
            container.querySelector(
                "#chip-zoom-in"
            );


        const zoomOut =
            container.querySelector(
                "#chip-zoom-out"
            );


        const zoomReset =
            container.querySelector(
                "#chip-zoom-reset"
            );


        let scale = 1;


        function applyZoom() {

            const svg =
                container.querySelector(
                    "#chip-svg"
                );


            if (!svg) {
                return;
            }


            svg.style.transform =
                `scale(${scale})`;


            svg.style.transformOrigin =
                "center center";


            if (zoomReset) {

                zoomReset.textContent =
                    `${Math.round(
                        scale * 100
                    )}%`;

            }

        }


        if (zoomIn) {

            zoomIn.addEventListener(
                "click",
                () => {

                    scale =
                        Math.min(
                            1.5,
                            scale + 0.1
                        );

                    applyZoom();

                }
            );

        }


        if (zoomOut) {

            zoomOut.addEventListener(
                "click",
                () => {

                    scale =
                        Math.max(
                            0.7,
                            scale - 0.1
                        );

                    applyZoom();

                }
            );

        }


        if (zoomReset) {

            zoomReset.addEventListener(
                "click",
                () => {

                    scale = 1;

                    applyZoom();

                }
            );

        }

    }


    /*
     * ----------------------------------------------------------
     * SIGNAL VIEW
     * ----------------------------------------------------------
     */

    function highlightSignals(
        container
    ) {

        const wires =
            container.querySelectorAll(
                ".chip-wire"
            );


        wires.forEach(
            wire => {

                wire.classList.add(
                    "signal-highlight"
                );

            }
        );

    }


    function clearSignalHighlight(
        container
    ) {

        const wires =
            container.querySelectorAll(
                ".chip-wire"
            );


        wires.forEach(
            wire => {

                wire.classList.remove(
                    "signal-highlight"
                );

            }
        );

    }


    /*
     * ----------------------------------------------------------
     * RESET ZOOM
     * ----------------------------------------------------------
     */

    function resetZoom(
        container
    ) {

        const svg =
            container.querySelector(
                "#chip-svg"
            );


        const button =
            container.querySelector(
                "#chip-zoom-reset"
            );


        if (svg) {

            svg.style.transform =
                "scale(1)";

        }


        if (button) {

            button.textContent =
                "100%";

        }

    }


    /*
     * ----------------------------------------------------------
     * UNSUPPORTED ARCHITECTURE
     * ----------------------------------------------------------
     *
     * Important: we do not invent a hardware diagram when the
     * frontend cannot confidently infer the architecture.
     * ----------------------------------------------------------
     */

    function renderUnsupportedArchitecture(
        container,
        specification,
        rtlSource,
        moduleName
    ) {

        container.innerHTML = `

            <div class="chip-unsupported">

                <div class="chip-unsupported-icon">
                    ◇
                </div>


                <div>

                    <span>
                        ARCHITECTURE PREVIEW
                    </span>

                    <h3>
                        RTL generated
                    </h3>

                    <p>
                        A detailed schematic visualization
                        will be generated when the RTL architecture
                        is supported by the visual design engine.
                    </p>

                    ${
                        rtlSource
                            ? `
                                <div class="chip-unsupported-status">
                                    RTL source available
                                </div>
                              `
                            : `
                                <div class="chip-unsupported-status">
                                    Generate RTL to populate architecture
                                </div>
                              `
                    }

                </div>

            </div>

        `;

    }


})();