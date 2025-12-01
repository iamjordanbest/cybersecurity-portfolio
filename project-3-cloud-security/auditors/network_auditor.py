from typing import List
from botocore.exceptions import ClientError
from models.compliance import Control, ControlStatus, Severity, Finding, EvidenceArtifact
from auditors.base_auditor import BaseAuditor

class NetworkAuditor(BaseAuditor):
    def _setup_clients(self):
        self.ec2 = self.session.client('ec2')

    def audit_all(self):
        results = []
        results.append(self.audit_security_groups_ingress())
        results.append(self.audit_default_security_group())
        results.append(self.audit_vpc_flow_logs())
        return results

    def audit_security_groups_ingress(self):
        control = Control(
            control_id="CIS-4.1",
            title="No Unrestricted SSH/RDP Access",
            description="Ensure no security groups allow ingress from 0.0.0.0/0 to port 22 or 3389.",
            severity=Severity.CRITICAL,
            category="Networking",
            cis_reference="4.1"
        )
        
        try:
            sgs = self.ec2.describe_security_groups()['SecurityGroups']
            open_sgs = []
            
            for sg in sgs:
                for perm in sg['IpPermissions']:
                    # Check for 0.0.0.0/0
                    is_open = any(r.get('CidrIp') == '0.0.0.0/0' for r in perm.get('IpRanges', []))
                    
                    if is_open:
                        from_port = perm.get('FromPort')
                        to_port = perm.get('ToPort')
                        
                        # Check specific ports (22, 3389) or all ports (-1)
                        if from_port is None or (from_port <= 22 <= to_port) or (from_port <= 3389 <= to_port):
                            open_sgs.append(f"{sg['GroupName']} ({sg['GroupId']})")

            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Open Security Groups",
                    content=open_sgs
                )
            ]
            
            if not open_sgs:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.CRITICAL,
                        description=f"Found security groups with open SSH/RDP: {', '.join(open_sgs)}",
                        remediation="Remove 0.0.0.0/0 inbound rules for ports 22 and 3389."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_default_security_group(self):
        control = Control(
            control_id="CIS-4.3",
            title="Default Security Group Restricts All Traffic",
            description="Ensure the default security group of every VPC restricts all traffic.",
            severity=Severity.HIGH,
            category="Networking",
            cis_reference="4.3"
        )

        try:
            sgs = self.ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['default']}])['SecurityGroups']
            non_compliant_sgs = []
            
            for sg in sgs:
                # Default SG should have no inbound or outbound rules (or restricted ones)
                # CIS recommends deleting all rules
                if sg['IpPermissions'] or sg['IpPermissionsEgress']:
                    non_compliant_sgs.append(sg['GroupId'])

            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="Non-compliant Default SGs",
                    content=non_compliant_sgs
                )
            ]

            if not non_compliant_sgs:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control,
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.HIGH,
                        description=f"Default security groups have active rules: {', '.join(non_compliant_sgs)}",
                        remediation="Remove all rules from default security groups."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_vpc_flow_logs(self):
        control = Control(
            control_id="CIS-2.9",
            title="VPC Flow Logs Enabled",
            description="Ensure VPC Flow Logs is enabled in all VPCs.",
            severity=Severity.MEDIUM,
            category="Networking",
            cis_reference="2.9"
        )
        
        try:
            vpcs = self.ec2.describe_vpcs()['Vpcs']
            flow_logs = self.ec2.describe_flow_logs()['FlowLogs']
            
            # Map VPC ID to flow log existence
            vpcs_with_logs = set(fl['ResourceId'] for fl in flow_logs)
            
            vpcs_without_logs = []
            for vpc in vpcs:
                vpc_id = vpc['VpcId']
                if vpc_id not in vpcs_with_logs:
                    vpcs_without_logs.append(vpc_id)
            
            evidence = [
                EvidenceArtifact(
                    control_id=control.control_id,
                    artifact_type="api_output",
                    description="VPCs without Flow Logs",
                    content=vpcs_without_logs
                )
            ]
            
            if not vpcs_without_logs:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(
                    control, 
                    ControlStatus.FAIL,
                    findings=[Finding(
                        control_id=control.control_id,
                        severity=Severity.MEDIUM,
                        description=f"Found VPCs without flow logs: {', '.join(vpcs_without_logs)}",
                        remediation="Enable Flow Logs for all VPCs."
                    )],
                    evidence=evidence
                )
        except ClientError as e:
            return self.handle_error(control.control_id, e)
