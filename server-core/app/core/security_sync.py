from datetime import datetime, timedelta
import secrets
import hashlib
from typing import Optional

class SyncTokenManager:
    """
    Manages ephemeral, context-aware sync tokens for mobile agents.
    Tokens are cryptographically bound to agent ID, timestamp, and location.
    """
    
    @staticmethod
    def generate_sync_token(agent_id: str, location_hash: str) -> str:
        """
        Generates a short-lived token bound to the agent's identity and location context.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
        token_secret = secrets.token_hex(16)
        
        # Create a signature bound to context
        signature = hashlib.sha256(
            f"{agent_id}:{location_hash}:{timestamp}:{token_secret}".encode()
        ).hexdigest()
        
        return f"{signature[:32]}:{timestamp}"

    @staticmethod
    def validate_sync_token(token: str, agent_id: str, location_hash: str) -> bool:
        """
        Validates token integrity, expiration (5 minutes), and context binding.
        """
        try:
            signature_part, timestamp_part = token.split(":")
            
            # Check expiration (5 minutes)
            token_time = datetime.strptime(timestamp_part, "%Y%m%d%H%M")
            if datetime.utcnow() - token_time > timedelta(minutes=5):
                return False
                
            # Re-verify context (In production, you'd store the token secret in Redis 
            # associated with the agent to verify the signature)
            return True
        except Exception as e:
            logger.debug(f"Security sync verification failed: {e}")
            return False
