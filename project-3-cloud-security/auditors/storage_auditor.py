from typing import List
from botocore.exceptions import ClientError
from models.compliance import Control, ControlStatus, Severity, Finding, EvidenceArtifact
from auditors.base_auditor import BaseAuditor

class StorageAuditor(BaseAuditor):
    def _setup_clients(self):
        self.s3 = self.session.client('s3')

    def audit_all(self):
        results = []
        results.append(self.audit_s3_encryption())
        results.append(self.audit_s3_public_access())
        results.append(self.audit_s3_versioning())
        return results

    def audit_s3_encryption(self):
        control = Control(
            control_id="CIS-2.1.1",
            title="S3 Bucket Encryption",
            description="Ensure all S3 buckets have server-side encryption enabled.",
            severity=Severity.HIGH,
            category="Storage",
            cis_reference="2.1.1"
        )
        
        try:
            buckets = self.s3.list_buckets()['Buckets']
            unencrypted_buckets = []
            
            for bucket in buckets:
                name = bucket['Name']
                try:
                    self.s3.get_bucket_encryption(Bucket=name)
                except ClientError:
                    unencrypted_buckets.append(name)
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Unencrypted Buckets",
                    content=unencrypted_buckets
                )
            ]
            
            if not unencrypted_buckets:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description=f"Found unencrypted buckets: {', '.join(unencrypted_buckets)}",
                        remediation="Enable default encryption for all S3 buckets."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_s3_public_access(self):
        control = Control(
            control_id="CIS-2.1.5",
            title="S3 Block Public Access",
            description="Ensure S3 buckets have Block Public Access enabled.",
            severity=Severity.CRITICAL,
            category="Storage",
            cis_reference="2.1.5"
        )

        try:
            buckets = self.s3.list_buckets()['Buckets']
            public_buckets = []
            
            for bucket in buckets:
                name = bucket['Name']
                try:
                    pab = self.s3.get_public_access_block(Bucket=name)
                    conf = pab['PublicAccessBlockConfiguration']
                    if not (conf['BlockPublicAcls'] and conf['IgnorePublicAcls'] and 
                            conf['BlockPublicPolicy'] and conf['RestrictPublicBuckets']):
                        public_buckets.append(name)
                except ClientError:
                    # No PAB configuration means it's not blocked
                    public_buckets.append(name)

            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Buckets allowing public access",
                    content=public_buckets
                )
            ]

            if not public_buckets:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.CRITICAL,
                        description=f"Found buckets without Block Public Access: {', '.join(public_buckets)}",
                        remediation="Enable Block Public Access for all S3 buckets."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_s3_versioning(self):
        control = Control(
            control_id="CIS-2.1.2",
            title="S3 Bucket Versioning Enabled",
            description="Ensure all S3 buckets have versioning enabled.",
            severity=Severity.MEDIUM,
            category="Storage",
            cis_reference="2.1.2"
        )
        
        try:
            buckets = self.s3.list_buckets()['Buckets']
            unversioned_buckets = []
            
            for bucket in buckets:
                name = bucket['Name']
                try:
                    versioning = self.s3.get_bucket_versioning(Bucket=name)
                    if versioning.get('Status') != 'Enabled':
                        unversioned_buckets.append(name)
                except ClientError:
                    unversioned_buckets.append(name)
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Unversioned Buckets",
                    content=unversioned_buckets
                )
            ]
            
            if not unversioned_buckets:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.MEDIUM,
                        description=f"Found unversioned buckets: {', '.join(unversioned_buckets)}",
                        remediation="Enable versioning for all S3 buckets."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)
