import copy
import ipaddress
import json
import logging
import os
import shlex
import socket
import subprocess
from pathlib import Path
from threading import Lock

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATE_PATH = Path(os.environ.get("STATE_PATH", "/app/data/firewall-state.json"))
FIREWALL_DRIVER = os.environ.get("FIREWALL_DRIVER", "mock").strip().lower()
FIREWALL_API_TOKEN = os.environ.get("FIREWALL_API_TOKEN", "")
SHOREWALL_SOURCE_ZONE = os.environ.get("SHOREWALL_SOURCE_ZONE", "loc")
SHOREWALL_DEST_ZONE = os.environ.get("SHOREWALL_DEST_ZONE", "net")
SHOREWALL_RULES_FILE = Path(
    os.environ.get("SHOREWALL_RULES_FILE", "/etc/shorewall/rules")
)
SHOREWALL_MANAGED_RULES_FILE = Path(
    os.environ.get(
        "SHOREWALL_MANAGED_RULES_FILE", "/etc/shorewall/rules.d/badenhackt.rules"
    )
)
SHOREWALL_CHECK_COMMAND = shlex.split(
    os.environ.get("SHOREWALL_CHECK_COMMAND", "shorewall check")
)
SHOREWALL_REFRESH_COMMAND = shlex.split(
    os.environ.get("SHOREWALL_REFRESH_COMMAND", "shorewall refresh")
)
IPSET_COMMAND = shlex.split(os.environ.get("IPSET_COMMAND", "ipset"))
IPSET_PREFIX = os.environ.get("IPSET_PREFIX", "bh_room_")
MOCK_OUTPUT_DIR = Path(os.environ.get("MOCK_OUTPUT_DIR", "/app/data/mock"))


class RoomPolicy(BaseModel):
    vlan_id: int
    room_name: str | None = None
    subnet: str
    internet_enabled: bool = True
    whitelist_entries: list[str] = Field(default_factory=list)


class RoomPolicyBatch(BaseModel):
    rooms: list[RoomPolicy]


class RoomPolicyState(RoomPolicy):
    pass


class HealthResponse(BaseModel):
    status: str
    driver: str
    rooms: int


class BaseDriver:
    def apply(self, policies: dict[int, RoomPolicyState]) -> None:
        raise NotImplementedError

    def render_rules(self, policies: dict[int, RoomPolicyState]) -> str:
        lines = [
            "# Managed by BadenHackt firewall agent. Do not edit manually.",
        ]
        for policy in sorted(policies.values(), key=lambda item: item.vlan_id):
            source = f"{SHOREWALL_SOURCE_ZONE}:{policy.subnet}"
            if not policy.internet_enabled:
                lines.append(f"?COMMENT VLAN {policy.vlan_id} internet disabled")
                lines.append(f"DROP    {source}    {SHOREWALL_DEST_ZONE}")
                continue

            if not policy.whitelist_entries:
                continue

            lines.append(f"?COMMENT VLAN {policy.vlan_id} whitelist")
            lines.append(
                f"ACCEPT  {source}    {SHOREWALL_DEST_ZONE}:+{self.ipset_name(policy.vlan_id)}"
            )
            lines.append(f"DROP    {source}    {SHOREWALL_DEST_ZONE}")

        if len(lines) == 1:
            lines.append("# No managed rules are currently active.")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def ipset_name(vlan_id: int) -> str:
        return f"{IPSET_PREFIX}{vlan_id}_allow"


class MockDriver(BaseDriver):
    def apply(self, policies: dict[int, RoomPolicyState]) -> None:
        MOCK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        rules_path = MOCK_OUTPUT_DIR / "badenhackt.rules"
        state_path = MOCK_OUTPUT_DIR / "rendered-state.json"

        rules_path.write_text(self.render_rules(policies), encoding="utf-8")
        state_path.write_text(
            json.dumps(
                {
                    "rooms": [
                        policy.model_dump()
                        for policy in sorted(
                            policies.values(),
                            key=lambda item: item.vlan_id,
                        )
                    ]
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        logger.info("Mock firewall state rendered to %s", MOCK_OUTPUT_DIR)


class ShorewallDriver(BaseDriver):
    def apply(self, policies: dict[int, RoomPolicyState]) -> None:
        self._ensure_rules_include()
        self._sync_ipsets(policies)
        SHOREWALL_MANAGED_RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
        SHOREWALL_MANAGED_RULES_FILE.write_text(
            self.render_rules(policies),
            encoding="utf-8",
        )
        self._run(SHOREWALL_CHECK_COMMAND)
        self._run(SHOREWALL_REFRESH_COMMAND)
        logger.info("Applied %d room policies via Shorewall", len(policies))

    def _ensure_rules_include(self) -> None:
        include_line = f"?INCLUDE {SHOREWALL_MANAGED_RULES_FILE}"
        SHOREWALL_RULES_FILE.parent.mkdir(parents=True, exist_ok=True)

        if SHOREWALL_RULES_FILE.exists():
            lines = SHOREWALL_RULES_FILE.read_text(encoding="utf-8").splitlines()
        else:
            lines = []

        if include_line in lines:
            return

        insert_at = len(lines)
        for index, line in enumerate(lines):
            if line.strip().upper() == "?SECTION NEW":
                insert_at = index + 1
                break

        if not lines:
            lines = ["?SECTION NEW", include_line]
        else:
            lines.insert(insert_at, include_line)

        SHOREWALL_RULES_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _sync_ipsets(self, policies: dict[int, RoomPolicyState]) -> None:
        for policy in policies.values():
            set_name = self.ipset_name(policy.vlan_id)
            self._run(
                [
                    *IPSET_COMMAND,
                    "create",
                    set_name,
                    "hash:net",
                    "family",
                    "inet",
                    "-exist",
                ]
            )
            self._run([*IPSET_COMMAND, "flush", set_name])
            for target in self._resolve_targets(policy.whitelist_entries):
                self._run([*IPSET_COMMAND, "add", set_name, target, "-exist"])

    def _resolve_targets(self, entries: list[str]) -> list[str]:
        targets: set[str] = set()

        for entry in entries:
            candidate = entry.strip().lower()
            if not candidate:
                continue
            if candidate.startswith("*."):
                candidate = candidate[2:]

            try:
                network = ipaddress.ip_network(candidate, strict=False)
            except ValueError:
                network = None

            if network is not None:
                if network.version == 4:
                    targets.add(str(network))
                continue

            try:
                addresses = socket.getaddrinfo(
                    candidate,
                    None,
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM,
                )
            except socket.gaierror as exc:
                raise RuntimeError(
                    f"Could not resolve whitelist entry '{entry}': {exc}"
                ) from exc

            for address in addresses:
                targets.add(address[4][0])

        return sorted(targets)

    @staticmethod
    def _run(command: list[str]) -> None:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return

        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")


class FirewallService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._driver = self._build_driver()
        self._state = self._load_state()

    def _build_driver(self) -> BaseDriver:
        if FIREWALL_DRIVER == "shorewall":
            return ShorewallDriver()
        return MockDriver()

    def _load_state(self) -> dict[int, RoomPolicyState]:
        if not STATE_PATH.exists():
            return {}

        raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        rooms = raw.get("rooms", [])
        state = {int(room["vlan_id"]): RoomPolicyState(**room) for room in rooms}

        logger.info("Loaded %d persisted firewall room policies", len(state))
        return state

    def _persist_state(self) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "rooms": [
                policy.model_dump()
                for policy in sorted(
                    self._state.values(), key=lambda item: item.vlan_id
                )
            ]
        }
        STATE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def reconcile(self) -> None:
        if not self._state:
            return

        try:
            self._driver.apply(copy.deepcopy(self._state))
        except Exception as exc:
            logger.warning("Failed to reconcile persisted firewall state: %s", exc)
        else:
            logger.info("Reconciled persisted firewall state")

    def list_rooms(self) -> list[RoomPolicyState]:
        with self._lock:
            return [
                room.model_copy(deep=True)
                for room in sorted(self._state.values(), key=lambda item: item.vlan_id)
            ]

    def get_room(self, vlan_id: int) -> RoomPolicyState:
        with self._lock:
            room = self._state.get(vlan_id)
            if room is None:
                raise KeyError(vlan_id)
            return room.model_copy(deep=True)

    def upsert_rooms(self, policies: list[RoomPolicy]) -> list[RoomPolicyState]:
        with self._lock:
            candidate = copy.deepcopy(self._state)
            for policy in policies:
                candidate[policy.vlan_id] = RoomPolicyState(**policy.model_dump())

            self._driver.apply(candidate)
            self._state = candidate
            self._persist_state()

            updated = [
                self._state[policy.vlan_id].model_copy(deep=True) for policy in policies
            ]
            return updated


service = FirewallService()


def verify_token(x_firewall_token: str | None = Header(default=None)) -> None:
    if FIREWALL_API_TOKEN and x_firewall_token != FIREWALL_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid firewall token")


app = FastAPI(title="BadenHackt Firewall Agent", version="1.0.0")


@app.on_event("startup")
def startup_event() -> None:
    service.reconcile()


@app.get("/health", response_model=HealthResponse)
def health(_: None = Depends(verify_token)):
    return {
        "status": "ok",
        "driver": FIREWALL_DRIVER,
        "rooms": len(service.list_rooms()),
    }


@app.get("/rooms", response_model=list[RoomPolicyState])
def list_rooms(_: None = Depends(verify_token)):
    return service.list_rooms()


@app.get("/rooms/{vlan_id}", response_model=RoomPolicyState)
def get_room(vlan_id: int, _: None = Depends(verify_token)):
    try:
        return service.get_room(vlan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Room policy not found") from exc


@app.put("/rooms/policies", response_model=RoomPolicyBatch)
def put_room_policies(batch: RoomPolicyBatch, _: None = Depends(verify_token)):
    try:
        updated = service.upsert_rooms(batch.rooms)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"rooms": updated}
