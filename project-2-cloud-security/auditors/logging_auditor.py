from typing import List
from botocore.exceptions import ClientError
from models.compliance import Control, ControlStatus, Severity, Finding, EvidenceArtifact
from auditors.base_auditor import BaseAuditor

class LoggingAuditor(BaseAuditor):
    def _setup_clients(self):
        self.cloudtrail = self.session.client('cloudtrail')
        self.kms = self.session.client('kms')
        self.config = self.session.client('config')

    def audit_all(self):
        results = []
        results.append(self.audit_cloudtrail_enabled())
        results.append(self.audit_cloudtrail_encryption())
        results.append(self.audit_cloudtrail_log_validation())
        results.append(self.audit_aws_config_enabled())
        return results

    def audit_cloudtrail_enabled(self):
        control = Control(
            control_id="CIS-2.1",
            title="CloudTrail Enabled in All Regions",
            description="Ensure CloudTrail is enabled in all regions.",
            severity=Severity.CRITICAL,
            category="Logging",
            cis_reference="2.1"
        )
        
        try:
            trails = self.cloudtrail.describe_trails(includeShadowTrails=True)['trailList']
            
            multi_region_trails = [t for t in trails if t.get('IsMultiRegionTrail')]
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="CloudTrail Trails",
                    content=trails
                )
            ]
            
            if multi_region_trails:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.CRITICAL,
                        description="No multi-region CloudTrail found.",
                        remediation="Enable a multi-region CloudTrail."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_cloudtrail_log_validation(self):
        control = Control(
            control_id="CIS-2.2",
            title="CloudTrail Log File Validation",
            description="Ensure CloudTrail log file validation is enabled.",
            severity=Severity.MEDIUM,
            category="Logging",
            cis_reference="2.2"
        )

        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            valid_trails = [t['Name'] for t in trails if t.get('LogFileValidationEnabled')]
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Trails with Validation",
                    content=valid_trails
                )
            ]

            if valid_trails:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.MEDIUM,
                        description="No trails have log file validation enabled.",
                        remediation="Enable log file validation on CloudTrail."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_cloudtrail_encryption(self):
        control = Control(
            control_id="CIS-2.7",
            title="CloudTrail Logs Encrypted with KMS",
            description="Ensure CloudTrail logs are encrypted using KMS CMKs.",
            severity=Severity.HIGH,
            category="Logging",
            cis_reference="2.7"
        )

        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            encrypted_trails = [t['Name'] for t in trails if t.get('KmsKeyId')]
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Encrypted Trails",
                    content=encrypted_trails
                )
            ]

            if encrypted_trails:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description="No trails are encrypted with KMS.",
                        remediation="Enable KMS encryption for CloudTrail."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_aws_config_enabled(self):
        control = Control(
            control_id="CIS-2.5",
            title="AWS Config Enabled",
            description="Ensure AWS Config is enabled in all regions.",
            severity=Severity.HIGH,
            category="Logging",
            cis_reference="2.5"
        )
        
        try:
            recorders = self.config.describe_configuration_recorders()['ConfigurationRecorders']
            statuses = self.config.describe_configuration_recorder_status()['ConfigurationRecorderStatusList']
            
            valid_recorders = []
            for recorder in recorders:
                name = recorder['name']
                status = next((s for s in statuses if s['name'] == name), None)
                
                if status and status['recording']:
                    if recorder['recordingGroup'].get('allSupported', False) and recorder['recordingGroup'].get('includeGlobalResourceTypes', False):
                        valid_recorders.append(name)
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Active Configuration Recorders",
                    content=recorders
                )
            ]
            
            if valid_recorders:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description="No active AWS Config recorders found capturing all resources.",
                        remediation="Enable AWS Config to record all resources."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)
