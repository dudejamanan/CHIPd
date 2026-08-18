/*
 * ============================================================
 * SILICA API CLIENT
 * ============================================================
 *
 * MOCK_MODE = true
 *     → Frontend works without Person 1's backend.
 *
 * MOCK_MODE = false
 *     → Frontend talks to http://localhost:8000.
 *
 * When Person 1's backend is ready, change ONLY this:
 *
 *     const MOCK_MODE = false;
 *
 * Do not change the rest of this file.
 * ============================================================
 */


const MOCK_MODE = true;

const API_BASE_URL = "http://localhost:8000";


/*
 * ============================================================
 * INTERNAL MOCK STORAGE
 * ============================================================
 */

const MOCK_STORAGE_KEY =
    "silica_mock_backend_state";


function loadMockState() {

    const stored =
        localStorage.getItem(
            MOCK_STORAGE_KEY
        );


    if (stored) {

        try {

            return JSON.parse(
                stored
            );

        } catch (error) {

            console.warn(
                "Invalid mock state. Resetting."
            );

        }

    }


    return {

        projects: [],

        designs: {},

        verifications: {},

        /*
         * Every verification run is retained here.
         *
         * verifications[designId] still contains the latest
         * verification result for backwards compatibility.
         */
        verification_history: [],

        analyses: {},

        counters: {

            project: 1000,

            design: 5000

        }

    };

}


function saveMockState(
    state
) {

    localStorage.setItem(

        MOCK_STORAGE_KEY,

        JSON.stringify(
            state
        )

    );

}


/*
 * ============================================================
 * GENERIC REQUEST
 * ============================================================
 */

async function request(
    method,
    endpoint,
    body = null
) {

    if (MOCK_MODE) {

        return mockRequest(
            method,
            endpoint,
            body
        );

    }


    const options = {

        method,

        headers: {

            "Content-Type":
                "application/json"

        }

    };


    if (body !== null) {

        options.body =
            JSON.stringify(
                body
            );

    }


    const response =
        await fetch(

            `${API_BASE_URL}${endpoint}`,

            options

        );


    let data = null;


    try {

        data =
            await response.json();

    } catch (error) {

        data = null;

    }


    if (!response.ok) {

        const message =
            data?.detail ||
            data?.message ||
            `Request failed with status ${response.status}`;


        throw new Error(
            message
        );

    }


    return data;

}


/*
 * ============================================================
 * PROJECT API
 * ============================================================
 */


/**
 * GET /projects
 *
 * Used by the Projects page.
 */
async function getProjects() {

    return request(

        "GET",

        "/projects"

    );

}


/**
 * POST /projects
 *
 * Creates a new project.
 */
async function createProject(
    project
) {

    return request(

        "POST",

        "/projects",

        {

            name:
                project.name,

            description:
                project.description || "",

            language:
                project.language ||
                "systemverilog"

        }

    );

}


/**
 * GET /projects/{project_id}
 */
async function getProject(
    projectId
) {

    return request(

        "GET",

        `/projects/${projectId}`

    );

}


/*
 * ============================================================
 * DESIGN API
 * ============================================================
 */


/**
 * POST /projects/{project_id}/designs
 *
 * Creates a design under a project.
 */
async function createDesign(
    projectId,
    design
) {

    return request(

        "POST",

        `/projects/${projectId}/designs`,

        {

            name:
                design.name ||
                "Untitled Design",

            specification:
                design.specification ||
                "",

            language:
                design.language ||
                "systemverilog"

        }

    );

}


/**
 * GET /designs/{design_id}
 */
async function getDesign(
    designId
) {

    return request(

        "GET",

        `/designs/${designId}`

    );

}


/*
 * ============================================================
 * RTL GENERATION
 * ============================================================
 */


/**
 * POST /designs/{design_id}/generate-rtl
 *
 * Expected backend response:
 *
 * {
 *   design_id,
 *   module_name,
 *   rtl_source
 * }
 */
async function generateRTL(
    designId,
    data
) {

    return request(

        "POST",

        `/designs/${designId}/generate-rtl`,

        {

            specification:
                data.specification,

            language:
                data.language ||
                "systemverilog"

        }

    );

}


/*
 * ============================================================
 * TESTBENCH GENERATION
 * ============================================================
 */


/**
 * POST /designs/{design_id}/generate-testbench
 */
async function generateTestbench(
    designId
) {

    return request(

        "POST",

        `/designs/${designId}/generate-testbench`

    );

}


/*
 * ============================================================
 * VERIFICATION
 * ============================================================
 */


/**
 * POST /designs/{design_id}/verify
 *
 * Expected:
 *
 * {
 *   status,
 *   compile,
 *   simulation,
 *   tests,
 *   duration_ms
 * }
 */
async function verifyDesign(
    designId
) {

    return request(

        "POST",

        `/designs/${designId}/verify`

    );

}


/*
 * ============================================================
 * AI FAILURE ANALYSIS
 * ============================================================
 */


/**
 * POST /designs/{design_id}/analyze
 *
 * Expected:
 *
 * {
 *   root_cause,
 *   severity,
 *   explanation,
 *   suggested_fix,
 *   confidence
 * }
 */
async function analyzeDesign(
    designId
) {

    return request(

        "POST",

        `/designs/${designId}/analyze`

    );

}


/*
 * ============================================================
 * OPTIMIZATION
 * ============================================================
 */


/**
 * POST /designs/{design_id}/optimize
 */
async function optimizeDesign(
    designId,
    data = {}
) {

    return request(

        "POST",

        `/designs/${designId}/optimize`,

        data

    );

}


/*
 * ============================================================
 * MOCK BACKEND
 * ============================================================
 *
 * This simulates Person 1's API.
 *
 * It is intentionally deterministic so your UI can be developed
 * and demonstrated before the real backend exists.
 * ============================================================
 */

async function mockRequest(
    method,
    endpoint,
    body
) {

    /*
     * Small delay so the UI behaves like a real application.
     */

    await mockDelay(
        500
    );


    const state =
        loadMockState();


    /*
     * Older mock states did not have verification_history.
     * Keep them valid without resetting existing data.
     */

    if (
        !Array.isArray(
            state.verification_history
        )
    ) {

        state.verification_history = [];

    }


    /*
     * --------------------------------------------------------
     * GET /projects
     * --------------------------------------------------------
     */

    if (
        method === "GET" &&
        endpoint === "/projects"
    ) {

        return {

            projects:
                state.projects

        };

    }


    /*
     * --------------------------------------------------------
     * POST /projects
     * --------------------------------------------------------
     */

    if (
        method === "POST" &&
        endpoint === "/projects"
    ) {

        state.counters.project += 1;


        const project = {

            id:
                String(
                    state.counters.project
                ),

            name:
                body?.name ||
                "Untitled Project",

            description:
                body?.description ||
                "Hardware design project",

            language:
                body?.language ||
                "systemverilog",

            status:
                "active",

            designs:
                0,

            created_at:
                new Date().toISOString(),

            updated_at:
                new Date().toISOString()

        };


        state.projects.unshift(
            project
        );


        saveMockState(
            state
        );


        return project;

    }


    /*
     * --------------------------------------------------------
     * GET /projects/{id}
     * --------------------------------------------------------
     */

    const projectMatch =
        endpoint.match(
            /^\/projects\/([^/]+)$/
        );


    if (
        method === "GET" &&
        projectMatch
    ) {

        const projectId =
            projectMatch[1];


        const project =
            state.projects.find(

                item =>
                    String(item.id) ===
                    String(projectId)

            );


        if (!project) {

            throw new Error(
                "Project not found."
            );

        }


        return project;

    }


    /*
     * --------------------------------------------------------
     * POST /projects/{id}/designs
     * --------------------------------------------------------
     */

    const createDesignMatch =
        endpoint.match(
            /^\/projects\/([^/]+)\/designs$/
        );


    if (
        method === "POST" &&
        createDesignMatch
    ) {

        const projectId =
            createDesignMatch[1];


        const project =
            state.projects.find(

                item =>
                    String(item.id) ===
                    String(projectId)

            );


        if (!project) {

            throw new Error(
                "Project not found."
            );

        }


        state.counters.design += 1;


        const designId =
            String(
                state.counters.design
            );


        const design = {

            id:
                designId,

            design_id:
                designId,

            project_id:
                projectId,

            name:
                body?.name ||
                "Untitled Design",

            specification:
                body?.specification ||
                "",

            language:
                body?.language ||
                "systemverilog",

            rtl_source:
                "",

            testbench_source:
                "",

            status:
                "created",

            created_at:
                new Date().toISOString(),

            updated_at:
                new Date().toISOString()

        };


        state.designs[designId] =
            design;


        project.designs =
            Number(
                project.designs || 0
            ) + 1;


        saveMockState(
            state
        );


        return design;

    }


    /*
     * --------------------------------------------------------
     * GET /designs/{id}
     * --------------------------------------------------------
     */

    const designMatch =
        endpoint.match(
            /^\/designs\/([^/]+)$/
        );


    if (
        method === "GET" &&
        designMatch
    ) {

        const designId =
            designMatch[1];


        const design =
            state.designs[designId];


        if (!design) {

            throw new Error(
                "Design not found."
            );

        }


        return design;

    }


    /*
     * --------------------------------------------------------
     * POST /designs/{id}/generate-rtl
     * --------------------------------------------------------
     */

    const rtlMatch =
        endpoint.match(
            /^\/designs\/([^/]+)\/generate-rtl$/
        );


    if (
        method === "POST" &&
        rtlMatch
    ) {

        const designId =
            rtlMatch[1];


        const design =
            state.designs[designId];


        if (!design) {

            throw new Error(
                "Design not found."
            );

        }


        const rtl =
            generateMockRTL(
                body?.specification ||
                design.specification
            );


        design.specification =
            body?.specification ||
            design.specification;


        design.rtl_source =
            rtl.rtl_source;


        design.module_name =
            rtl.module_name;


        design.status =
            "rtl_generated";


        design.updated_at =
            new Date().toISOString();


        saveMockState(
            state
        );


        return {

            design_id:
                designId,

            module_name:
                rtl.module_name,

            rtl_source:
                rtl.rtl_source

        };

    }


    /*
     * --------------------------------------------------------
     * POST /designs/{id}/generate-testbench
     * --------------------------------------------------------
     */

    const testbenchMatch =
        endpoint.match(
            /^\/designs\/([^/]+)\/generate-testbench$/
        );


    if (
        method === "POST" &&
        testbenchMatch
    ) {

        const designId =
            testbenchMatch[1];


        const design =
            state.designs[designId];


        if (!design) {

            throw new Error(
                "Design not found."
            );

        }


        design.testbench_source =
            generateMockTestbench(
                design.module_name ||
                "counter"
            );


        design.status =
            "testbench_generated";


        design.updated_at =
            new Date().toISOString();


        saveMockState(
            state
        );


        return {

            design_id:
                designId,

            testbench_source:
                design.testbench_source

        };

    }


    /*
     * --------------------------------------------------------
     * POST /designs/{id}/verify
     * --------------------------------------------------------
     */

    const verifyMatch =
        endpoint.match(
            /^\/designs\/([^/]+)\/verify$/
        );


    if (
        method === "POST" &&
        verifyMatch
    ) {

        const designId =
            verifyMatch[1];


        const design =
            state.designs[designId];


        if (!design) {

            throw new Error(
                "Design not found."
            );

        }


        const verification =
            generateMockVerification(
                design
            );


        /*
         * Keep the latest result available under the design ID.
         * Existing frontend code depends on this shape.
         */

        state.verifications[
            designId
        ] =
            verification;


        /*
         * Retain every verification run.
         *
         * Example:
         *
         *     FAILED
         *        ↓
         *     AI FIX
         *        ↓
         *     PASSED
         *
         * becomes two separate records in
         * verification_history.
         */

        if (
            !Array.isArray(
                state.verification_history
            )
        ) {

            state.verification_history = [];

        }


        state.verification_history.push({

            id:
                `verification_${Date.now()}_${Math.random()
                    .toString(36)
                    .slice(2, 8)}`,

            design_id:
                designId,

            status:
                verification.status,

            compile:
                verification.compile,

            simulation:
                verification.simulation,

            tests:
                verification.tests,

            duration_ms:
                verification.duration_ms,

            created_at:
                new Date().toISOString()

        });


        design.status =
            verification.status;


        design.updated_at =
            new Date().toISOString();


        saveMockState(
            state
        );


        return verification;

    }


    /*
     * --------------------------------------------------------
     * POST /designs/{id}/analyze
     * --------------------------------------------------------
     */

    const analyzeMatch =
        endpoint.match(
            /^\/designs\/([^/]+)\/analyze$/
        );


    if (
        method === "POST" &&
        analyzeMatch
    ) {

        const designId =
            analyzeMatch[1];


        const design =
            state.designs[designId];


        if (!design) {

            throw new Error(
                "Design not found."
            );

        }


        /*
         * Keep analysis using the latest verification result.
         * This preserves the existing AI Copilot behavior.
         */

        const verification =
            state.verifications[
                designId
            ];


        const analysis =
            generateMockAnalysis(
                design,
                verification
            );


        state.analyses[
            designId
        ] =
            analysis;


        saveMockState(
            state
        );


        return analysis;

    }


    /*
     * --------------------------------------------------------
     * POST /designs/{id}/optimize
     * --------------------------------------------------------
     */

    const optimizeMatch =
        endpoint.match(
            /^\/designs\/([^/]+)\/optimize$/
        );


    if (
        method === "POST" &&
        optimizeMatch
    ) {

        const designId =
            optimizeMatch[1];


        const design =
            state.designs[designId];


        if (!design) {

            throw new Error(
                "Design not found."
            );

        }


        return {

            design_id:
                designId,

            status:
                "completed",

            message:
                "Mock optimization completed.",

            changes: [

                "Reduced unnecessary combinational logic.",

                "Preserved functional behavior."

            ]

        };

    }


    throw new Error(

        `Mock endpoint not implemented: ${method} ${endpoint}`

    );

}


/*
 * ============================================================
 * MOCK RTL
 * ============================================================
 */

function generateMockRTL(
    specification
) {

    const text =
        String(
            specification || ""
        ).toLowerCase();


    /*
     * 2:1 MUX
     */

    if (
        text.includes("mux") ||
        text.includes("multiplexer")
    ) {

        return {

            module_name:
                "mux_2to1",

            rtl_source:
`module mux_2to1 (
    input  logic a,
    input  logic b,
    input  logic sel,
    output logic y
);

    always_comb begin
        if (sel)
            y = b;
        else
            y = a;
    end

endmodule`

        };

    }


    /*
     * D FLIP-FLOP
     */

    if (
        text.includes("flip-flop") ||
        text.includes("flip flop") ||
        text.includes("d flip")
    ) {

        return {

            module_name:
                "d_flip_flop",

            rtl_source:
`module d_flip_flop (
    input  logic clk,
    input  logic rst_n,
    input  logic d,
    output logic q
);

    always_ff @(posedge clk) begin
        if (!rst_n)
            q <= 1'b0;
        else
            q <= d;
    end

endmodule`

        };

    }


    /*
     * ALU
     */

    if (
        text.includes("alu") ||
        text.includes("arithmetic logic")
    ) {

        return {

            module_name:
                "alu_4bit",

            rtl_source:
`module alu_4bit (
    input  logic [3:0] a,
    input  logic [3:0] b,
    input  logic [1:0] op,
    output logic [3:0] result
);

    always_comb begin
        case (op)
            2'b00: result = a + b;
            2'b01: result = a - b;
            2'b10: result = a & b;
            2'b11: result = a | b;
            default: result = 4'b0000;
        endcase
    end

endmodule`

        };

    }


    /*
     * DEFAULT → COUNTER
     */

    return {

        module_name:
            "counter",

        rtl_source:
`module counter (
    input  logic clk,
    input  logic rst_n,
    output logic [3:0] count
);

    always_ff @(posedge clk) begin
        if (!rst_n)
            count <= 4'b0000;
        else
            count <= count + 4'b0001;
    end

endmodule`

    };

}


/*
 * ============================================================
 * MOCK TESTBENCH
 * ============================================================
 */

function generateMockTestbench(
    moduleName
) {

    return `module ${moduleName}_tb;

    logic clk;
    logic rst_n;

    logic [3:0] count;

    ${moduleName} dut (
        .clk(clk),
        .rst_n(rst_n),
        .count(count)
    );

    initial begin

        $display("SILICA_TEST_START");

        clk = 1'b0;
        rst_n = 1'b0;

        #10;

        rst_n = 1'b1;

        #10;

        if (count !== 4'b0001)
            $display("SILICA_TEST_FAIL");

        #10;

        if (count !== 4'b0010)
            $display("SILICA_TEST_FAIL");

        $display("SILICA_TEST_PASS");
        $display("SILICA_TEST_END");

        $finish;

    end

    always #5 clk = ~clk;

endmodule`;

}


/*
 * ============================================================
 * MOCK VERIFICATION
 * ============================================================
 */

function generateMockVerification(
    design
) {

    const intentionallyBroken =
        String(
            design.specification || ""
        ).toLowerCase()
        .includes(
            "intentional bug"
        );


    if (intentionallyBroken) {

        return {

            status:
                "failed",

            compile: {

                status:
                    "passed",

                stdout:
                    "Compilation successful.",

                stderr:
                    ""

            },

            simulation: {

                status:
                    "failed",

                stdout:
                    "SILICA_TEST_START\nSILICA_TEST_FAIL\nSILICA_TEST_END",

                stderr:
                    ""

            },

            tests: {

                passed:
                    5,

                failed:
                    3,

                total:
                    8

            },

            duration_ms:
                428

        };

    }


    return {

        status:
            "passed",

        compile: {

            status:
                "passed",

            stdout:
                "SystemVerilog compilation successful.",

            stderr:
                ""

        },

        simulation: {

            status:
                "passed",

            stdout:
                "SILICA_TEST_START\nSILICA_TEST_PASS\nSILICA_TEST_END",

            stderr:
                ""

        },

        tests: {

            passed:
                8,

            failed:
                0,

            total:
                8

        },

        duration_ms:
            431

    };

}


/*
 * ============================================================
 * MOCK AI ANALYSIS
 * ============================================================
 */

function generateMockAnalysis(
    design,
    verification
) {

    return {

        root_cause:
            "The RTL output does not match the expected counter behavior.",

        severity:
            "high",

        explanation:
            "The verification failure indicates that the generated design is not producing the expected value at the required clock edge. The reset and sequential update behavior should be checked against the specification.",

        suggested_fix:
            "Use a synchronous active-low reset inside the posedge clocked block and increment the 4-bit counter only when rst_n is high.",

        confidence:
            0.91

    };

}


/*
 * ============================================================
 * MOCK DELAY
 * ============================================================
 */

function mockDelay(
    milliseconds
) {

    return new Promise(
        resolve =>
            setTimeout(
                resolve,
                milliseconds
            )
    );

}


/*
 * ============================================================
 * DEVELOPMENT UTILITIES
 * ============================================================
 *
 * These are useful while developing the frontend.
 *
 * Browser console:
 *
 *     resetSilicaMock()
 *
 * clears all mock projects/designs.
 *
 *     getSilicaMockState()
 *
 * shows the current mock backend state.
 * ============================================================
 */

function resetSilicaMock() {

    localStorage.removeItem(
        MOCK_STORAGE_KEY
    );


    localStorage.removeItem(
        "chipd_current_project"
    );


    localStorage.removeItem(
        "chipd_current_design"
    );


    console.log(
        "Silica mock backend reset."
    );


    location.reload();

}


function getSilicaMockState() {

    const state =
        loadMockState();


    console.log(
        state
    );


    return state;

}