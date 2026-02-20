// ======================================
// Global State (Frontend Topology Model)
// ======================================

let routers = [];
let links = [];


// ======================================
// Refresh UI After Any Change
// ======================================

function refreshUI() {

    // ----- Update Router List (with delete button) -----
    document.getElementById("routerList").innerHTML =
        routers.map(r =>
            `<div>
                ${r}
                <button onclick="deleteRouter('${r}')">🗑</button>
             </div>`
        ).join("");

    // ----- Update Dropdowns -----
    const routerA = document.getElementById("routerA");
    const routerB = document.getElementById("routerB");

    routerA.innerHTML = "";
    routerB.innerHTML = "";

    routers.forEach(r => {
        routerA.innerHTML += `<option value="${r}">${r}</option>`;
        routerB.innerHTML += `<option value="${r}">${r}</option>`;
    });

    // ----- Update Link List (with delete button) -----
    document.getElementById("linkList").innerHTML =
        links.map((l, index) =>
            `<div>
                ${l[0]} ↔ ${l[1]}
                <button onclick="deleteLink(${index})">🗑</button>
             </div>`
        ).join("");

    updateJSONPreview();
    renderTopologyDiagram();
}


// ======================================
// JSON Preview
// ======================================

function updateJSONPreview() {

    const payload = {
        name: "sdn-lab",
        mgmt_subnet: "172.20.20.0/24",
        routers: routers,
        links: links,
        ceos_image: "ceos:4.35.1F"
    };

    document.getElementById("jsonPreview").textContent =
        JSON.stringify(payload, null, 2);
}


// ======================================
// Add Router
// ======================================

function addRouter() {

    const name = document.getElementById("routerName").value.trim();

    if (!name) return;

    if (routers.length >= 8) {
        alert("Maximum 8 routers allowed.");
        return;
    }

    if (routers.includes(name)) {
        alert("Router already exists.");
        return;
    }

    routers.push(name);

    document.getElementById("routerName").value = "";

    refreshUI();
}


// ======================================
// Delete Router
// ======================================

function deleteRouter(name) {

    // Remove router
    routers = routers.filter(r => r !== name);

    // Remove all links involving that router
    links = links.filter(l => l[0] !== name && l[1] !== name);

    refreshUI();
}


// ======================================
// Add Link
// ======================================

function addLink() {

    const a = document.getElementById("routerA").value;
    const b = document.getElementById("routerB").value;

    if (!a || !b || a === b) {
        alert("Invalid link.");
        return;
    }

    // Prevent duplicate link
    if (links.some(l =>
        (l[0] === a && l[1] === b) ||
        (l[0] === b && l[1] === a)
    )) {
        alert("Link already exists.");
        return;
    }

    links.push([a, b]);

    refreshUI();
}


// ======================================
// Delete Link
// ======================================

function deleteLink(index) {

    links.splice(index, 1);

    refreshUI();
}


// ======================================
// Deploy
// ======================================

async function deploy() {

    const payload = {
        name: "sdn-lab",
        mgmt_subnet: "172.20.20.0/24",
        routers: routers,
        links: links,
        ceos_image: "ceos:4.35.1F"
    };

    setDeployStatus("running", "Deploying topology... this may take a few minutes.");

    // 10 minute timeout — deploy pipeline takes several minutes
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000);

    try {
        const response = await fetch("http://localhost:5000/deploy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const data = await response.json();

        if (response.ok) {
            const routers = data.controller_result?.topology_nodes?.join(", ") || "";
            setDeployStatus("success",
                `Routes installed successfully on ${data.router_count} routers (${routers}).`
            );
        } else {
            setDeployStatus("error", "Deploy failed: " + (data.detail || JSON.stringify(data)));
        }

    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === "AbortError") {
            setDeployStatus("error", "Deploy timed out after 10 minutes.");
        } else {
            setDeployStatus("error", "Backend error: " + error);
        }
    }
}


function setDeployStatus(state, message) {
    const box = document.getElementById("deployStatus");
    box.textContent = message;
    box.className = "status-box status-" + state;
    box.style.display = "block";
}


// ======================================
// Render Topology Diagram (SVG)
// ======================================

function renderTopologyDiagram() {

    const container = document.getElementById("diagram");

    if (!container) return;

    if (routers.length === 0) {
        container.innerHTML = "<div>Add routers to visualize topology.</div>";
        return;
    }

    const width = 860;
    const height = 420;
    const cx = width / 2;
    const cy = height / 2;
    const radius = Math.min(width, height) * 0.33;

    const positions = {};

    routers.forEach((r, i) => {
        const angle = (2 * Math.PI * i) / routers.length;
        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);
        positions[r] = { x, y };
    });

    let svg = `
        <svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
            <g class="links">
    `;

    links.forEach(([a, b]) => {

        if (!positions[a] || !positions[b]) return;

        svg += `
            <line 
                x1="${positions[a].x}" 
                y1="${positions[a].y}" 
                x2="${positions[b].x}" 
                y2="${positions[b].y}" 
                stroke="#444" 
                stroke-width="2"
            />
        `;
    });

    svg += `
            </g>
            <g class="nodes">
    `;

    routers.forEach(r => {

        const { x, y } = positions[r];

        svg += `
            <g class="node">
                <circle 
                    cx="${x}" 
                    cy="${y}" 
                    r="22" 
                    fill="#e8f0ff" 
                    stroke="#2b5cff" 
                    stroke-width="2">
                </circle>
                <text 
                    x="${x}" 
                    y="${y + 4}" 
                    text-anchor="middle" 
                    fill="#111">
                    ${r}
                </text>
            </g>
        `;
    });

    svg += `
            </g>
        </svg>
    `;

    container.innerHTML = svg;
}
