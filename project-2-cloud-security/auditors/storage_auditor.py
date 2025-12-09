from typing import List, Dict, Any
from botocore.exceptions import ClientError
from models.compliance import Control, ControlStatus, Severity, Finding, EvidenceArtifact
from auditors.base_auditor import BaseAuditor
import json

class StorageAuditor(BaseAuditor):
    """
    Storage Auditor (S3 + KMS) implementing 8 CIS Controls (v1.4.0)
    """

    def _setup_clients(self):
        self.s3 = self.session.client('s3')
        self.kms = self.session.client('kms')
        self.cloudtrail = self.session.client('cloudtrail')

    def audit_all(self):
        results = []
        # CIS-2.1.1: S3 Encryption
        results.append(self.audit_s3_encryption())
        # CIS-2.1.2: S3 Versioning
        results.append(self.audit_s3_versioning())
        # CIS-2.1.5: S3 Block Public Access
        results.append(self.audit_s3_block_public_access())
        # CIS-2.3: S3 Access Logging
        results.append(self.audit_s3_access_logging())
        # CIS-2.6: S3 Public Read via ACLs/Policies
        results.append(self.audit_s3_public_read())
        # CIS-2.8: KMS Key Rotation
        results.append(self.audit_kms_rotation())
        # CIS-2.10: S3 Object Logging
        results.append(self.audit_s3_object_logging())
        # CIS-2.11: SSL Enforcement
        results.append(self.audit_s3_ssl_enforcement())
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
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "Unencrypted Buckets", unencrypted_buckets)]
            
            if not unencrypted_buckets:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.HIGH, f"Unencrypted buckets: {', '.join(unencrypted_buckets)}", "Enable default encryption.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_s3_block_public_access(self):
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
            open_buckets = []
            
            for bucket in buckets:
                name = bucket['Name']
                try:
                    pab = self.s3.get_public_access_block(Bucket=name)
                    conf = pab['PublicAccessBlockConfiguration']
                    # Require all 4 settings to be True
                    if not (conf['BlockPublicAcls'] and conf['IgnorePublicAcls'] and 
                            conf['BlockPublicPolicy'] and conf['RestrictPublicBuckets']):
                        open_buckets.append(name)
                except ClientError:
                    open_buckets.append(name)

            evidence = [EvidenceArtifact(control.control_id, "api_output", "Open Buckets", open_buckets)]

            if not open_buckets:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.CRITICAL, f"Buckets without Block Public Access: {', '.join(open_buckets)}", "Enable Block Public Access.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_s3_versioning(self):
        control = Control(
            control_id="CIS-2.1.2",
            title="S3 Bucket Versioning",
            description="Ensure S3 bucket versioning is enabled.",
            severity=Severity.MEDIUM,
            category="Storage",
            cis_reference="2.1.2"
        )
        
        try:
            buckets = self.s3.list_buckets()['Buckets']
            unversioned = []
            
            for bucket in buckets:
                name = bucket['Name']
                ver = self.s3.get_bucket_versioning(Bucket=name)
                if ver.get('Status') != 'Enabled':
                    unversioned.append(name)
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "Unversioned Buckets", unversioned)]
            
            if not unversioned:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.MEDIUM, f"Unversioned buckets: {', '.join(unversioned)}", "Enable versioning.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_s3_access_logging(self):
        control = Control(
            control_id="CIS-2.3",
            title="S3 Access Logging",
            description="Ensure S3 buckets have server access logging enabled.",
            severity=Severity.MEDIUM,
            category="Storage",
            cis_reference="2.3"
        )
        try:
            buckets = self.s3.list_buckets()['Buckets']
            unlogged = []
            
            for bucket in buckets:
                name = bucket['Name']
                logging = self.s3.get_bucket_logging(Bucket=name)
                if 'LoggingEnabled' not in logging:
                    unlogged.append(name)
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "Unlogged Buckets", unlogged)]
            
            if not unlogged:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.MEDIUM, f"Buckets without access logging: {', '.join(unlogged)}", "Enable server access logging.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_s3_public_read(self):
        """Check ACLs and Policies for public read (redundant with Block Public Access but specific to READ)"""
        control = Control(
            control_id="CIS-2.6",
            title="S3 Public Read Disabled",
            description="Ensure no S3 buckets allow public read via ACLs or Policy.",
            severity=Severity.CRITICAL,
            category="Storage",
            cis_reference="2.6"
        )
        try:
            buckets = self.s3.list_buckets()['Buckets']
            public_buckets = []
            
            for bucket in buckets:
                name = bucket['Name']
                # Check ACL
                try:
                    acl = self.s3.get_bucket_acl(Bucket=name)
                    for grant in acl['Grants']:
                        uri = grant.get('Grantee', {}).get('URI', '')
                        if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                            public_buckets.append(name)
                            break
                except ClientError:
                    pass
                
                # Check Policy (Simplified: just checking if PolicyStatus says IsPublic if available, or manual parse)
                try:
                    pol_status = self.s3.get_bucket_policy_status(Bucket=name)
                    if pol_status.get('PolicyStatus', {}).get('IsPublic'):
                         if name not in public_buckets:
                             public_buckets.append(name)
                except ClientError:
                    pass
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "Public Read Buckets", public_buckets)]
            
            if not public_buckets:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.CRITICAL, f"Buckets with public read access: {', '.join(public_buckets)}", "Remove public read ACLs/Policies.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_kms_rotation(self):
        control = Control(
            control_id="CIS-2.8",
            title="KMS Key Rotation",
            description="Ensure rotation for customer created CMKs is enabled.",
            severity=Severity.HIGH,
            category="Storage",
            cis_reference="2.8"
        )
        try:
            keys = self.kms.list_keys()['Keys']
            bad_keys = []
            for k in keys:
                kid = k['KeyId']
                try:
                    meta = self.kms.describe_key(KeyId=kid)['KeyMetadata']
                    if meta['KeyManager'] == 'CUSTOMER' and meta['KeyState'] == 'Enabled':
                        rotation = self.kms.get_key_rotation_status(KeyId=kid)
                        if not rotation['KeyRotationEnabled']:
                            bad_keys.append(kid)
                except ClientError:
                    continue
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "Keys without Rotation", bad_keys)]
            
            if not bad_keys:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.HIGH, f"KMS Keys without rotation: {', '.join(bad_keys)}", "Enable key rotation.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_s3_object_logging(self):
        control = Control(
            control_id="CIS-2.10",
            title="S3 Object Logging",
            description="Ensure S3 object-level logging (write) is enabled in CloudTrail.",
            severity=Severity.MEDIUM,
            category="Storage",
            cis_reference="2.10"
        )
        try:
            # This requires iterating CloudTrail matching events selectors
            trails = self.cloudtrail.describe_trails()['trailList']
            buckets_logging = set()
            for trail in trails:
                try:
                    selectors = self.cloudtrail.get_event_selectors(TrailName=trail['Name']).get('EventSelectors', [])
                    for selector in selectors:
                        for resource in selector.get('DataResources', []):
                            if resource['Type'] == 'AWS::S3::Object':
                                # 'arn:aws:s3:::' means all buckets, or specific 'arn:aws:s3:::bucket/prefix'
                                for val in resource['Values']:
                                    if val.endswith('/'):
                                        buckets_logging.add(val.split(':')[-1].split('/')[0])
                                    else:
                                        # 'arn:aws:s3:::'
                                        buckets_logging.add('ALL')
                except ClientError:
                    continue
            
            if 'ALL' in buckets_logging:
                 return self.create_assessment(control, ControlStatus.PASS, evidence=[EvidenceArtifact(control.control_id, "api_output", "Logging", "All buckets logged")])
            
            # Check if all buckets are covered
            all_buckets = [b['Name'] for b in self.s3.list_buckets()['Buckets']]
            unlogged = [b for b in all_buckets if b not in buckets_logging]
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "Unlogged Buckets", unlogged)]
            
            if not unlogged:
                 return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                 # Often OK to fail if not critical, or user only logs sensitive. But for CIS strict:
                 return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.MEDIUM, f"Buckets without object logging: {', '.join(unlogged)}", "Enable object-level logging.")], evidence=evidence)

        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_s3_ssl_enforcement(self):
        control = Control(
            control_id="CIS-2.11",
            title="Enforce SSL in S3 Policies",
            description="Ensure S3 bucket policies deny HTTP checks.",
            severity=Severity.HIGH,
            category="Storage",
            cis_reference="2.11"
        )
        try:
            buckets = self.s3.list_buckets()['Buckets']
            no_ssl = []
            
            for bucket in buckets:
                name = bucket['Name']
                try:
                    pol_str = self.s3.get_bucket_policy(Bucket=name)['Policy']
                    policy = json.loads(pol_str)
                    # Simple check: Look for "aws:SecureTransport": "false" with "Effect": "Deny"
                    secure = False
                    for stmt in policy.get('Statement', []):
                        if stmt.get('Effect') == 'Deny':
                            cond = stmt.get('Condition', {})
                            # Check Bool: { "aws:SecureTransport": "false" } (can be string or bool)
                            bool_cond = cond.get('Bool', {})
                            secure_transport_val = bool_cond.get('aws:SecureTransport')
                            # Handle both string "false" and boolean False
                            if secure_transport_val in ('false', 'False', False):
                                secure = True
                                break
                    if not secure:
                        no_ssl.append(name)
                except ClientError:
                    # No policy = no SSL enforcement
                    no_ssl.append(name)
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "No SSL Enforcement", no_ssl)]
            
            if not no_ssl:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.HIGH, f"Buckets without SSL enforcement: {', '.join(no_ssl)}", "Add bucket policy to deny access without SSL.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)
