const API_BASE_URL = "http://localhost:8000";


async function request(
    path,
    options = {}
) {

    const response =
        await fetch(
            `${API_BASE_URL}${path}`,
            {
                ...options,

                headers: {
                    "Content-Type":
                        "application/json",

                    ...(options.headers || {})
                }
            }
        );


    if (!response.ok) {

        const text =
            await response.text();


        throw new Error(
            text ||
            `HTTP ${response.status}`
        );

    }


    return response.json();

}


/*
 * ==========================================
 * PROJECT API
 * ==========================================
 */

async function createProject(data) {

    return request(
        "/projects",
        {
            method: "POST",

            body:
                JSON.stringify(data)
        }
    );

}


async function getProjects() {

    return request(
        "/projects"
    );

}


/*
 * ==========================================
 * DESIGN API
 * ==========================================
 */

async function createDesign(
    projectId,
    data
) {

    return request(
        `/projects/${projectId}/designs`,
        {
            method: "POST",

            body:
                JSON.stringify(data)
        }
    );

}


async function generateRTL(
    designId,
    data
) {

    return request(
        `/designs/${designId}/generate-rtl`,
        {
            method: "POST",

            body:
                JSON.stringify(data)
        }
    );

}


async function generateTestbench(
    designId
) {

    return request(
        `/designs/${designId}/generate-testbench`,
        {
            method: "POST"
        }
    );

}


async function verifyDesign(
    designId
) {

    return request(
        `/designs/${designId}/verify`,
        {
            method: "POST"
        }
    );

}


async function analyzeDesign(
    designId
) {

    return request(
        `/designs/${designId}/analyze`,
        {
            method: "POST"
        }
    );

}


/*
 * ==========================================
 * HEALTH
 * ==========================================
 */

async function checkBackendHealth() {

    return request(
        "/health"
    );

}