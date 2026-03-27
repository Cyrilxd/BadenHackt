import subprocess
import logging

logger = logging.getLogger(__name__)

class FirewallManager:
    """Manages nftables rules for VLAN blocking"""
    
    @staticmethod
    def block_vlan(vlan_id: int, subnet: str) -> bool:
        """Block internet access for a VLAN"""
        try:
            # Add drop rule for subnet
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
        """Unblock internet access for a VLAN"""
        try:
            # Find and delete the drop rule for this subnet
            # First, list rules to find the handle
            list_cmd = ["nft", "-a", "list", "chain", "inet", "filter", "forward"]
            result = subprocess.run(list_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to list rules: {result.stderr}")
                return False
            
            # Parse output to find rule with our subnet
            for line in result.stdout.split('\n'):
                if subnet in line and 'drop' in line:
                    # Extract handle number
                    if '# handle' in line:
                        handle = line.split('# handle')[-1].strip()
                        # Delete rule by handle
                        del_cmd = ["nft", "delete", "rule", "inet", "filter", "forward", "handle", handle]
                        del_result = subprocess.run(del_cmd, capture_output=True, text=True)
                        
                        if del_result.returncode == 0:
                            logger.info(f"Unblocked VLAN {vlan_id} ({subnet})")
                            return True
            
            logger.warning(f"No blocking rule found for VLAN {vlan_id}")
            return True  # Not blocked, so technically unblocked
            
        except Exception as e:
            logger.error(f"Error unblocking VLAN {vlan_id}: {e}")
            return False
    
    @staticmethod
    def get_vlan_status(subnet: str) -> bool:
        """Check if VLAN is currently blocked"""
        try:
            list_cmd = ["nft", "list", "chain", "inet", "filter", "forward"]
            result = subprocess.run(list_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check if subnet is in drop rules
                is_blocked = subnet in result.stdout and 'drop' in result.stdout
                return not is_blocked  # Return True if internet is enabled (not blocked)
            
            return True  # Default to enabled if can't determine
        except Exception as e:
            logger.error(f"Error checking VLAN status: {e}")
            return True
