"""
Configuration Management for CSPM Auditor
Handles environment variable loading and validation.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Application configuration."""
    
    db_path: Path
    aws_profile: str = "default"
    aws_region: str = "us-east-1"
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Load configuration from environment variables.
        
        Returns:
            AppConfig instance with loaded or default values.
        """
        # Load .env file
        project_root = Path(__file__).parent.parent
        env_path = project_root / '.env'
        
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
        
        # Get values with defaults
        db_path = Path(os.getenv('DB_PATH', 'data/cspm.db'))
        
        # Make db_path absolute if relative
        if not db_path.is_absolute():
            db_path = project_root / db_path
        
        return cls(
            db_path=db_path,
            aws_profile=os.getenv('AWS_PROFILE', 'default'),
            aws_region=os.getenv('AWS_REGION', 'us-east-1')
        )


def validate_config() -> bool:
    """
    Validate configuration.
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    try:
        config = AppConfig.from_env()
        
        # Validate database exists
        if not config.db_path.exists():
            print(f"⚠️  Database not found: {config.db_path}")
            print(f"   Run: python cli.py audit")
            # Not returning False because it might be first run
        
        print("✅ Configuration loaded")
        print(f"   Database: {config.db_path}")
        print(f"   AWS Profile: {config.aws_profile}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


if __name__ == "__main__":
    """Test configuration loading."""
    print("Testing configuration loading...\n")
    validate_config()
