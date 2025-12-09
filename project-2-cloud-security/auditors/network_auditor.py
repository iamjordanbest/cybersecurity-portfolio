from typing import List
from botocore.exceptions import ClientError
from models.compliance import Control, ControlStatus, Severity, Finding, EvidenceArtifact
from auditors.base_auditor import BaseAuditor

class NetworkAuditor(BaseAuditor):
    """
    Network Auditor implementing 4 CIS Controls (v1.4.0)
    """

    def _setup_clients(self):
        self.ec2 = self.session.client('ec2')

    def audit_all(self):
        results = []
        # CIS-5.1: No Inbound SSH/RDP (was 4.1)
        results.append(self.audit_security_groups_ingress())
        # CIS-5.2: No Unrestricted Egress
        results.append(self.audit_security_groups_egress())
        # CIS-5.3: Default SG Closed (was 4.3)
        results.append(self.audit_default_security_group())
        # CIS-2.9: VPC Flow Logs (retained ID)
        results.append(self.audit_vpc_flow_logs())
        return results

    def audit_security_groups_ingress(self):
        control = Control(
            control_id="CIS-5.1",
            title="No Unrestricted SSH/RDP Access",
            description="Ensure no security groups allow ingress from 0.0.0.0/0 to port 22 or 3389.",
            severity=Severity.CRITICAL,
            category="Networking",
            cis_reference="5.1"
        )
        
        try:
            sgs = self.ec2.describe_security_groups()['SecurityGroups']
            open_sgs = []
            
            for sg in sgs:
                for perm in sg['IpPermissions']:
                    is_open = any(r.get('CidrIp') == '0.0.0.0/0' for r in perm.get('IpRanges', []))
                    if is_open:
                        from_port = perm.get('FromPort')
                        to_port = perm.get('ToPort')
                        # Check logic: if port range includes 22 or 3389
                        # Port -1 means all.
                        if (from_port is None) or \
                           (from_port == -1) or \
                           (from_port <= 22 and to_port >= 22) or \
                           (from_port <= 3389 and to_port >= 3389):
                                open_sgs.append(f"{sg['GroupName']} ({sg['GroupId']})")
            
            # Deduplicate
            open_sgs = list(set(open_sgs))

            evidence = [EvidenceArtifact(control.control_id, "api_output", "Open Security Groups", open_sgs)]
            
            if not open_sgs:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.CRITICAL, f"Open security groups: {', '.join(open_sgs)}", "Restrict SSH/RDP access.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_security_groups_egress(self):
        """CIS-5.2: Ensure no security groups allow unrestricted egress to 0.0.0.0/0"""
        control = Control(
            control_id="CIS-5.2",
            title="No Unrestricted Egress",
            description="Ensure no security groups allow unrestricted egress to 0.0.0.0/0.",
            severity=Severity.MEDIUM,
            category="Networking",
            cis_reference="5.2"
        )
        
        try:
            sgs = self.ec2.describe_security_groups()['SecurityGroups']
            open_egress_sgs = []
            
            for sg in sgs:
                for perm in sg['IpPermissionsEgress']:
                    is_open = any(r.get('CidrIp') == '0.0.0.0/0' for r in perm.get('IpRanges', []))
                    if is_open:
                        # CIS recommends only allowing specific ports needed. 
                        # If Egress is ALL Ports to 0.0.0.0/0, flag it?
                        # Or checking for specific risky ports? 
                        # Usually "Restricted Egress" means don't use -1 (All) to 0.0.0.0/0.
                        if perm.get('IpProtocol') == '-1':
                             open_egress_sgs.append(f"{sg['GroupName']} ({sg['GroupId']})")
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "Unrestricted Egress SGs", open_egress_sgs)]
            
            if not open_egress_sgs:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                # Severity Medium because it's common but bad practice
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.MEDIUM, f"SGs with unrestricted egress: {', '.join(open_egress_sgs)}", "Restrict egress traffic.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_default_security_group(self):
        control = Control(
            control_id="CIS-5.3",
            title="Default Security Group Closed",
            description="Ensure the default security group of every VPC restricts all traffic.",
            severity=Severity.HIGH,
            category="Networking",
            cis_reference="5.3"
        )

        try:
            sgs = self.ec2.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['default']}])['SecurityGroups']
            non_compliant_sgs = []
            
            for sg in sgs:
                if sg.get('IpPermissions') or sg.get('IpPermissionsEgress'):
                    non_compliant_sgs.append(sg['GroupId'])
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "Non-compliant Default SGs", non_compliant_sgs)]

            if not non_compliant_sgs:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.HIGH, f"Default SGs with rules: {', '.join(non_compliant_sgs)}", "Remove all rules from default SGs.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)

    def audit_vpc_flow_logs(self):
        control = Control(
            control_id="CIS-2.9",
            title="VPC Flow Logs Enabled",
            description="Ensure VPC Flow Logs are enabled for all VPCs.",
            severity=Severity.HIGH,
            category="Networking",
            cis_reference="2.9"
        )
        
        try:
            vpcs = self.ec2.describe_vpcs()['Vpcs']
            flow_logs = self.ec2.describe_flow_logs()['FlowLogs']
            vpcs_with_logs = set(fl['ResourceId'] for fl in flow_logs)
            
            vpcs_without_logs = [v['VpcId'] for v in vpcs if v['VpcId'] not in vpcs_with_logs]
            
            evidence = [EvidenceArtifact(control.control_id, "api_output", "VPCs without Flow Logs", vpcs_without_logs)]
            
            if not vpcs_without_logs:
                return self.create_assessment(control, ControlStatus.PASS, evidence=evidence)
            else:
                return self.create_assessment(control, ControlStatus.FAIL, findings=[Finding(control.control_id, Severity.HIGH, f"VPCs without Flow Logs: {', '.join(vpcs_without_logs)}", "Enable Flow Logs.")], evidence=evidence)
        except ClientError as e:
            return self.handle_error(control.control_id, e)
