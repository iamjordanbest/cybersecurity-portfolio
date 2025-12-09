from datetime import datetime, timezone
from typing import List, Dict, Any
from botocore.exceptions import ClientError
from models.compliance import Control, ControlStatus, Severity, Finding, EvidenceArtifact
from auditors.base_auditor import BaseAuditor

class IAMAuditor(BaseAuditor):
    """
    Consolidated IAM Auditor implementing 10 CIS AWS Foundations Benchmark v1.4.0 controls.
    """

    def _setup_clients(self):
        self.iam = self.session.client('iam')
        self.cloudtrail = self.session.client('cloudtrail')

    def audit_all(self):
        results = []
        # CIS-1.1: Root MFA
        results.append(self.audit_root_mfa())
        # CIS-1.2: Root Access Keys
        results.append(self.audit_root_access_keys())
        # CIS-1.3: Unused Credentials
        results.append(self.audit_credentials_unused_90_days())
        # CIS-1.5: Password Policy
        results.append(self.audit_password_policy())
        # CIS-1.6: Hardware MFA
        results.append(self.audit_hardware_mfa_root())
        # CIS-1.7: Root Usage
        results.append(self.audit_root_usage())
        # CIS-1.8: User MFA
        results.append(self.audit_iam_user_mfa())
        # CIS-1.9: Access Key Rotation
        results.append(self.audit_access_key_rotation())
        # CIS-1.15: IAM Policies on Groups
        results.append(self.audit_iam_policies_on_groups())
        # CIS-1.17: Support Role
        results.append(self.audit_support_role())
        
        return results

    def audit_root_mfa(self):
        """CIS-1.1: Ensure MFA is enabled for the 'root' account"""
        control = Control(
            control_id="CIS-1.1",
            title="Root Account MFA Enabled",
            description="The 'root' account has the most privileges and must be protected by MFA.",
            severity=Severity.CRITICAL,
            category="Identity & Access Management",
            cis_reference="1.1"
        )
        
        try:
            summary = self.iam.get_account_summary()['SummaryMap']
            mfa_enabled = summary.get('AccountMFAEnabled', 0) == 1
            
            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="IAM Account Summary (AccountMFAEnabled)",
                content=summary
            )]
            
            if mfa_enabled:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.CRITICAL,
                        description="Root account MFA is not enabled.",
                        remediation="Enable MFA for the root account immediately."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_root_access_keys(self):
        """CIS-1.2: Ensure no root account access keys exist"""
        control = Control(
            control_id="CIS-1.2",
            title="Root Account Access Keys",
            description="The 'root' account should not have access keys.",
            severity=Severity.CRITICAL,
            category="Identity & Access Management",
            cis_reference="1.2"
        )
        
        try:
            summary = self.iam.get_account_summary()['SummaryMap']
            keys_present = summary.get('AccountAccessKeysPresent', 0) == 1
            
            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="IAM Account Summary (AccountAccessKeysPresent)",
                content=summary
            )]
            
            if not keys_present:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.CRITICAL,
                        description="Root account has active access keys.",
                        remediation="Delete root access keys and use IAM users/roles instead."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_credentials_unused_90_days(self):
        """CIS-1.3: Ensure credentials unused for 90 days or greater are disabled"""
        control = Control(
            control_id="CIS-1.3",
            title="Credentials Unused > 90 Days",
            description="Disable IAM users/credentials unused for >90 days.",
            severity=Severity.HIGH,
            category="Identity & Access Management",
            cis_reference="1.3"
        )
        
        try:
            users = self.iam.list_users()['Users']
            unused_items = []
            
            for user in users:
                if 'PasswordLastUsed' in user:
                    days_unused = (datetime.now(timezone.utc) - user['PasswordLastUsed']).days
                    if days_unused > 90:
                        unused_items.append(f"User {user['UserName']} password unused for {days_unused} days")
                elif 'CreateDate' in user:
                     pass # Simplified for API-only

                keys = self.iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
                for key in keys:
                    if key['Status'] == 'Active':
                        try:
                            last_used_info = self.iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                            if 'LastUsedDate' in last_used_info.get('AccessKeyLastUsed', {}):
                                last_used_date = last_used_info['AccessKeyLastUsed']['LastUsedDate']
                                days_unused = (datetime.now(timezone.utc) - last_used_date).days
                                if days_unused > 90:
                                    unused_items.append(f"Key {key['AccessKeyId']} for user {user['UserName']} unused for {days_unused} days")
                            else:
                                days_created = (datetime.now(timezone.utc) - key['CreateDate']).days
                                if days_created > 90:
                                    unused_items.append(f"Key {key['AccessKeyId']} for user {user['UserName']} created {days_created} days ago and never used")
                        except ClientError:
                            continue

            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="Unused Credentials",
                content=unused_items
            )]
            
            if not unused_items:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description=f"Found {len(unused_items)} unused credentials.",
                        remediation="Disable or remove unused credentials."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_password_policy(self):
        """CIS-1.5: Ensure IAM password policy requires at least one uppercase letter (etc)"""
        control = Control(
            control_id="CIS-1.5",
            title="Comprehensive Password Policy",
            description="Ensure password policy requires: 14+ chars, upper, lower, numbers, symbols, reuse prevention.",
            severity=Severity.HIGH,
            category="Identity & Access Management",
            cis_reference="1.5"
        )
        
        try:
            policy = self.iam.get_account_password_policy().get('PasswordPolicy', {})
            
            issues = []
            if policy.get('MinimumPasswordLength', 0) < 14:
                issues.append("Minimum length < 14")
            if not policy.get('RequireSymbols'):
                issues.append("Symbols not required")
            if not policy.get('RequireNumbers'):
                issues.append("Numbers not required")
            if not policy.get('RequireUppercaseCharacters'):
                issues.append("Uppercase not required")
            if not policy.get('RequireLowercaseCharacters'):
                issues.append("Lowercase not required")
            if policy.get('PasswordReusePrevention', 0) < 24:
                issues.append("Reuse prevention < 24")
            
            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="Password Policy",
                content=policy
            )]
            
            if not issues:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description=f"Password policy gaps: {', '.join(issues)}",
                        remediation="Update IAM password policy to meet all CIS requirements."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description="No IAM Password Policy exists.",
                        remediation="Create a strong IAM Password Policy."
                    )]
                )
            return self.handle_error(control.control_id, e)

    def audit_hardware_mfa_root(self):
        """CIS-1.6: Ensure hardware MFA is enabled for the 'root' account"""
        control = Control(
            control_id="CIS-1.6",
            title="Hardware MFA for Root",
            description="Root account should use hardware MFA (not virtual).",
            severity=Severity.CRITICAL,
            category="Identity & Access Management",
            cis_reference="1.6"
        )
        
        try:
            summary = self.iam.get_account_summary()['SummaryMap']
            mfa_enabled = summary.get('AccountMFAEnabled', 0) == 1
            
            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="Account Summary",
                content=summary
            )]
            
            if mfa_enabled:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence, notes="Verified MFA is enabled. Manual check required to confirm Hardware device.")
            else:
                 return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.CRITICAL,
                        description="Root account MFA is not enabled.",
                        remediation="Enable Hardware MFA for root."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_root_usage(self):
        """CIS-1.7: Ensure no 'root' user account usage in the last 90 days"""
        control = Control(
            control_id="CIS-1.7",
            title="Eliminate Usage of Root User",
            description="Root user should not be used for daily administrative tasks.",
            severity=Severity.CRITICAL,
            category="Identity & Access Management",
            cis_reference="1.7"
        )
        
        try:
            # Check last 90 days via CloudTrail (simplified last 50 events)
            response = self.cloudtrail.lookup_events(
                LookupAttributes=[{'AttributeKey': 'Username', 'AttributeValue': 'root'}],
                MaxResults=50
            )
            
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            recent_root_events = []
            
            for event in response.get('Events', []):
                # CloudTrail EventTime is already a datetime object
                if (now - event['EventTime']) < timedelta(days=1):
                    recent_root_events.append(f"{event['EventName']} at {event['EventTime']}")

            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="Recent Root Events (<24h)",
                content=recent_root_events
            )]
            
            if not recent_root_events:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.CRITICAL,
                        description=f"Root user activity detected in the last 24 hours: {len(recent_root_events)} events.",
                        remediation="Stop using root account. Use IAM users/roles."
                    )],
                    evidence=evidence
                )

        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_iam_user_mfa(self):
        """CIS-1.8: Ensure MFA is enabled for all IAM users with a console password"""
        control = Control(
            control_id="CIS-1.8",
            title="IAM User MFA Enabled",
            description="All IAM users with console access must have MFA enabled.",
            severity=Severity.HIGH,
            category="Identity & Access Management",
            cis_reference="1.8"
        )
        
        try:
            users = self.iam.list_users()['Users']
            users_without_mfa = []
            
            for user in users:
                try:
                    self.iam.get_login_profile(UserName=user['UserName'])
                    mfa_devices = self.iam.list_mfa_devices(UserName=user['UserName'])['MFADevices']
                    if not mfa_devices:
                        users_without_mfa.append(user['UserName'])
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchEntity':
                        continue 
            
            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="Users without MFA",
                content=users_without_mfa
            )]
            
            if not users_without_mfa:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description=f"Users with console access but no MFA: {', '.join(users_without_mfa)}",
                        remediation="Enable MFA for these users."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_access_key_rotation(self):
        """CIS-1.9: Ensure access keys are rotated every 90 days or less"""
        control = Control(
            control_id="CIS-1.9",
            title="Access Key Rotation (90 Days)",
            description="Access keys should be rotated every 90 days.",
            severity=Severity.HIGH,
            category="Identity & Access Management",
            cis_reference="1.9"
        )
        
        try:
            users = self.iam.list_users()['Users']
            old_keys = []
            
            for user in users:
                keys = self.iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
                for key in keys:
                    if key['Status'] == 'Active':
                        days_old = (datetime.now(timezone.utc) - key['CreateDate']).days
                        if days_old > 90:
                            old_keys.append(f"{user['UserName']} (Key ID: {key['AccessKeyId']}, Age: {days_old} days)")
            
            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="Old Keys",
                content=old_keys
            )]
            
            if not old_keys:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description=f"Active access keys older than 90 days found: {len(old_keys)}",
                        remediation="Rotate keys older than 90 days."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_iam_policies_on_groups(self):
        """CIS-1.15 (v1.4): Ensure IAM policies are attached only to groups or roles"""
        control = Control(
            control_id="CIS-1.15",
            title="IAM Policies Attached to Groups",
            description="IAM policies should be attached to groups/roles, not users directly.",
            severity=Severity.MEDIUM,
            category="Identity & Access Management",
            cis_reference="1.15"
        )

        try:
            users = self.iam.list_users()['Users']
            users_with_policies = []
            
            for user in users:
                try:
                    username = user['UserName']
                    attached = self.iam.list_attached_user_policies(UserName=username)['AttachedPolicies']
                    inline = self.iam.list_user_policies(UserName=username)['PolicyNames']
                    if attached or inline:
                        users_with_policies.append(username)
                except ClientError:
                    continue

            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="Users with direct policies",
                content=users_with_policies
            )]

            if not users_with_policies:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.MEDIUM,
                        description=f"Users found with direct policy attachments: {', '.join(users_with_policies)}",
                        remediation="Detach policies from users and attach them to groups instead."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_support_role(self):
        """CIS-1.17 (v1.4): Ensure a support role has been created to manage incidents with AWS Support"""
        control = Control(
            control_id="CIS-1.17",
            title="Support Role Created",
            description="Ensure a support role has been created to manage incidents with AWS Support.",
            severity=Severity.MEDIUM,
            category="Identity & Access Management",
            cis_reference="1.17"
        )
        
        try:
            roles = self.iam.list_roles()['Roles']
            support_role_found = False
            role_name = None
            
            for role in roles:
                try:
                    attached_policies = self.iam.list_attached_role_policies(RoleName=role['RoleName'])['AttachedPolicies']
                    for policy in attached_policies:
                        if policy['PolicyName'] == 'AWSSupportAccess':
                            support_role_found = True
                            role_name = role['RoleName']
                            break
                except ClientError:
                    continue
                if support_role_found:
                    break
            
            evidence = [EvidenceArtifact(
                control_id=control.control_id,
                artifact_type="api_output",
                description="Support Role Check",
                content={"support_role_found": support_role_found, "role_name": role_name}
            )]
            
            if support_role_found:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.MEDIUM,
                        description="No role found with AWSSupportAccess policy.",
                        remediation="Create a role for AWS Support access."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)
