import subprocess
import shutil
import logging

logger = logging.getLogger(__name__)

NFT_AVAILABLE = shutil.which("nft") is not None

if not NFT_AVAILABLE:
    logger.warning("nft not found — running in simulation mode (no actual firewall changes)")

_blocked_subnets: set[str] = set()


class FirewallManager:
    """Manages nftables rules for VLAN blocking.
    Falls back to in-memory simulation when nft is unavailable (e.g. Windows/dev)."""

    @staticmethod
    def block_vlan(vlan_id: int, subnet: str) -> bool:
        if not NFT_AVAILABLE:
            _blocked_subnets.add(subnet)
            logger.info(f"[SIM] Blocked VLAN {vlan_id} ({subnet})")
            return True
        try:
            cmd = [
                "nft", "add", "rule", "inet", "filter", "forward",
                "ip", "saddr", subnet, "drop"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Blocked VLAN {vlan_id} ({subnet})")
                return True
            else:
                logger.error(f"Failed to block VLAN {vlan_id}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error blocking VLAN {vlan_id}: {e}")
            return False

    @staticmethod
    def unblock_vlan(vlan_id: int, subnet: str) -> bool:
        if not NFT_AVAILABLE:
            _blocked_subnets.discard(subnet)
            logger.info(f"[SIM] Unblocked VLAN {vlan_id} ({subnet})")
            return True
        try:
            list_cmd = ["nft", "-a", "list", "chain", "inet", "filter", "forward"]
            result = subprocess.run(list_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to list rules: {result.stderr}")
                return False
            for line in result.stdout.split('\n'):
                if subnet in line and 'drop' in line and '# handle' in line:
                    handle = line.split('# handle')[-1].strip()
                    del_cmd = ["nft", "delete", "rule", "inet", "filter", "forward", "handle", handle]
                    del_result = subprocess.run(del_cmd, capture_output=True, text=True)
                    if del_result.returncode == 0:
                        logger.info(f"Unblocked VLAN {vlan_id} ({subnet})")
                        return True
            logger.warning(f"No blocking rule found for VLAN {vlan_id}")
            return True
        except Exception as e:
            logger.error(f"Error unblocking VLAN {vlan_id}: {e}")
            return False

    @staticmethod
    def get_vlan_status(subnet: str) -> bool:
        """Returns True if internet is enabled (not blocked)."""
        if not NFT_AVAILABLE:
            return subnet not in _blocked_subnets
        try:
            list_cmd = ["nft", "list", "chain", "inet", "filter", "forward"]
            result = subprocess.run(list_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if subnet in line and 'drop' in line:
                        return False
                return True
            return True
        except Exception as e:
            logger.error(f"Error checking VLAN status: {e}")
            return True
