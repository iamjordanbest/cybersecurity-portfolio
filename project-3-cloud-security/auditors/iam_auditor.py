from typing import List
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from models.compliance import Control, ControlStatus, Severity, Finding, EvidenceArtifact
from auditors.base_auditor import BaseAuditor

class IAMAuditor(BaseAuditor):
    def _setup_clients(self):
        self.iam = self.session.client('iam')

    def audit_all(self):
        results = []
        results.append(self.audit_root_mfa())
        results.append(self.audit_password_policy())
        results.append(self.audit_iam_policies_on_groups())
        results.append(self.audit_access_key_rotation())
        results.append(self.audit_unused_iam_users())
        return results

    def audit_root_mfa(self):
        control = Control(
            control_id="CIS-1.4",
            title="Root Account MFA Enabled",
            description="The 'root' account has the most privileges and must be protected by MFA.",
            severity=Severity.CRITICAL,
            category="Identity & Access Management",
            cis_reference="1.4"
        )
        
        try:
            response = self.iam.get_account_summary()
            summary = response.get('SummaryMap', {})
            mfa_enabled = summary.get('AccountMFAEnabled', 0) == 1
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="IAM Account Summary",
                    content=summary
                )
            ]
            
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

    def audit_password_policy(self):
        control = Control(
            control_id="CIS-1.12",
            title="Strong Password Policy",
            description="Ensure IAM password policy requires at least 14 characters.",
            severity=Severity.HIGH,
            category="Identity & Access Management",
            cis_reference="1.12"
        )

        try:
            response = self.iam.get_account_password_policy()
            policy = response.get('PasswordPolicy', {})
            
            min_length = policy.get('MinimumPasswordLength', 0)
            required_length = 14
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="IAM Password Policy",
                    content=policy
                )
            ]

            if min_length >= required_length:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description=f"Password minimum length is {min_length}, required {required_length}.",
                        remediation="Update IAM password policy to require 14+ characters."
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
                        description="No IAM password policy exists.",
                        remediation="Create an IAM password policy."
                    )]
                )
            return self.handle_error(control.control_id, e)

    def audit_iam_policies_on_groups(self):
        control = Control(
            control_id="CIS-1.16",
            title="IAM Policies Attached to Groups",
            description="IAM policies should be attached to groups/roles, not users directly.",
            severity=Severity.MEDIUM,
            category="Identity & Access Management",
            cis_reference="1.16"
        )

        try:
            users = self.iam.list_users()['Users']
            users_with_policies = []
            
            for user in users:
                username = user['UserName']
                # Check attached managed policies
                attached = self.iam.list_attached_user_policies(UserName=username)['AttachedPolicies']
                # Check inline policies
                inline = self.iam.list_user_policies(UserName=username)['PolicyNames']
                
                if attached or inline:
                    users_with_policies.append(username)

            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Users with direct policies",
                    content=users_with_policies
                )
            ]

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

    def audit_access_key_rotation(self):
        control = Control(
            control_id="CIS-1.14",
            title="Ensure Access Keys Rotated Every 90 Days",
            description="Access keys should be rotated every 90 days or less.",
            severity=Severity.MEDIUM,
            category="IAM",
            cis_reference="1.14"
        )

        try:
            users = self.iam.list_users()['Users']
            old_keys = []
            
            for user in users:
                keys = self.iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
                
                for key in keys:
                    if key['Status'] == 'Active':
                        age = (datetime.now(timezone.utc) - key['CreateDate']).days
                        if age > 90:
                            old_keys.append(f"{user['UserName']} (Key: {key['AccessKeyId']}, Age: {age} days)")

            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Old Access Keys",
                    content=old_keys
                )
            ]

            if not old_keys:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.MEDIUM,
                        description=f"Found active access keys older than 90 days: {', '.join(old_keys)}",
                        remediation="Rotate access keys every 90 days."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_unused_iam_users(self):
        control = Control(
            control_id="CIS-1.12",
            title="Ensure Unused IAM Users Are Disabled",
            description="IAM users with no activity for >90 days should be disabled.",
            severity=Severity.MEDIUM,
            category="IAM",
            cis_reference="1.12"
        )

        try:
            users = self.iam.list_users()['Users']
            unused_users = []
            
            for user in users:
                # Check PasswordLastUsed
                last_used = user.get('PasswordLastUsed')
                if last_used:
                    age = (datetime.now(timezone.utc) - last_used).days
                    if age > 90:
                        unused_users.append(f"{user['UserName']} (Last Used: {age} days ago)")
                else:
                    # If never used, check creation date
                    age = (datetime.now(timezone.utc) - user['CreateDate']).days
                    if age > 90:
                        unused_users.append(f"{user['UserName']} (Never used, Created: {age} days ago)")

            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Unused IAM Users",
                    content=unused_users
                )
            ]

            if not unused_users:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.MEDIUM,
                        description=f"Found unused IAM users (>90 days): {', '.join(unused_users)}",
                        remediation="Disable or delete unused IAM users."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)
