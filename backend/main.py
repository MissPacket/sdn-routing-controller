import os
import json
import subprocess
import time
import shutil
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.addressing import generate_interface_map
from backend.fabric_config import configure_fabric
from backend.topology_gen import build_containerlab_yaml, dump_yaml
from backend.controller import run_controller


app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GENERATED_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "generated")
)
os.makedirs(GENERATED_DIR, exist_ok=True)

MAX_ROUTERS = 8
MIN_ROUTERS = 2


class DeployRequest(BaseModel):
    name: str = "sdn-lab"
    mgmt_subnet: str = "172.20.20.0/24"
    routers: list[str] = Field(min_length=MIN_ROUTERS)
    links: list[list[str]] = Field(min_length=1)
    ceos_image: str = "ceos:4.35.1F"


def validate_request(req: DeployRequest):
    routers = req.routers
    links = req.links

    if len(routers) > MAX_ROUTERS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_ROUTERS} routers allowed."
        )

    if len(set(routers)) != len(routers):
        raise HTTPException(
            status_code=400,
            detail="Duplicate router names not allowed."
        )

    router_set = set(routers)

    for pair in links:
        if len(pair) != 2:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid link format: {pair}"
            )

        a, b = pair

        if a not in router_set or b not in router_set:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid router in link: {a}-{b}"
            )

        if a == b:
            raise HTTPException(
                status_code=400,
                detail="Self-links not allowed."
            )


def _run_deploy_blocking(req: DeployRequest):
    topo, mgmt_ips = build_containerlab_yaml(req.model_dump())

    topo_path = os.path.join(GENERATED_DIR, "topology.clab.yaml")
    inv_path = os.path.join(GENERATED_DIR, "inventory.json")

    dump_yaml(topo, topo_path)

    with open(inv_path, "w") as f:
        json.dump(mgmt_ips, f, indent=2)

    subprocess.run(
        ["containerlab", "destroy", "-t", topo_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    subprocess.run(
        "docker rm -f $(docker ps -aq --filter name=clab-sdn-lab) || true",
        shell=True
    )

    time.sleep(2)

    generated_path = os.path.join("generated", "clab-sdn-lab")
    if os.path.exists(generated_path):
        shutil.rmtree(generated_path, ignore_errors=True)

    result = subprocess.run(
        ["sudo", "containerlab", "deploy", "-t", topo_path, "--reconfigure"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr)

    print("Waiting for containers to initialise...")
    time.sleep(40)

    generated_interface_map = generate_interface_map(req.routers, req.links)
    print("Generated Interface Map:")
    print(generated_interface_map)

    time.sleep(40)

    print("Configuring fabric interfaces....")
    configure_fabric(mgmt_ips, generated_interface_map)

    print("Waiting for routers to fully boot...")
    time.sleep(20)

    controller_result = run_controller(inv_path)

    return {
        "status": "deployed_and_configured",
        "router_count": len(req.routers),
        "controller_result": controller_result
    }


@app.post("/deploy")
async def deploy(req: DeployRequest):
    validate_request(req)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_deploy_blocking, req)
    return result


@app.get("/health")
def health():
    return {"status": "ok"}
