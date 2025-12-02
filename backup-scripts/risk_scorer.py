import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Default Configuration Constants
DEFAULT_WEIGHTS = {'control_weight': 1.0}
DEFAULT_MULTIPLIERS = {
    'fail': 3.0,
    'warn': 1.5,
    'pass': 0.1,
    'not_tested': 2.0
}
DEFAULT_STALENESS = {'max_days': 365, 'factor': 1.0}
IMPACT_MAP = {
    'critical': 2.0,
    'high': 1.5,
    'medium': 1.0,
    'low': 0.5
}

class RiskScorer:
    """
    Calculates risk scores for compliance controls based on configuration.
    """

    def __init__(self, config_path: str = "config/scoring.yaml"):
        """
        Initialize RiskScorer with configuration.
        
        Args:
            config_path: Path to scoring configuration YAML
        """
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            path = Path(config_path)
            if not path.exists():
                # Try finding it relative to project root if we are in src
                project_root = Path(__file__).parent.parent.parent
                path = project_root / config_path
                
            if not path.exists():
                logger.warning(f"Config not found at {path}, using defaults")
                return {
                    'weights': DEFAULT_WEIGHTS,
                    'multipliers': DEFAULT_MULTIPLIERS,
                    'staleness': DEFAULT_STALENESS
                }
                
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def calculate_risk_score(self, control: Dict[str, Any]) -> float:
        """
        Calculate risk score for a single control.
        
        Formula: Risk = Weight * Status_Multiplier * Staleness_Factor * Impact_Factor
        """
        # 1. Base Weight
        weight = float(control.get('control_weight', 1.0))
        
        # 2. Status Multiplier
        status = control.get('status', 'not_tested').lower()
        multipliers = self.config.get('multipliers', DEFAULT_MULTIPLIERS)
        status_mult = multipliers.get(status, multipliers.get('not_tested', 2.0))
        
        # 3. Staleness Factor (Placeholder for future implementation)
        staleness_factor = 1.0
        
        # 4. Business Impact
        impact = control.get('business_impact', 'medium').lower()
        impact_factor = IMPACT_MAP.get(impact, 1.0)
        
        risk_score = weight * status_mult * staleness_factor * impact_factor
        return round(risk_score, 2)

    def calculate_portfolio_risk(self, controls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate risk metrics for a list of controls."""
        if not controls:
            return {
                'total_risk_score': 0.0,
                'average_risk': 0.0,
                'high_risk_controls': 0
            }

        total_risk = 0.0
        high_risk_count = 0
        
        for c in controls:
            score = self.calculate_risk_score(c)
            c['risk_score'] = score
            total_risk += score
            if score > 10.0: # Threshold
                high_risk_count += 1
                
        return {
            'total_risk_score': round(total_risk, 2),
            'average_risk': round(total_risk / len(controls), 2),
            'high_risk_controls': high_risk_count
        }
