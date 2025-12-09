from typing import List
from botocore.exceptions import ClientError
from models.compliance import Control, ControlStatus, Severity, Finding, EvidenceArtifact
from auditors.base_auditor import BaseAuditor

class MonitoringAuditor(BaseAuditor):
    """
    Monitoring Auditor implementing 5 CIS Controls (v1.4.0, Section 3)
    Focus: Log Metric Filters and Alarms
    """

    def _setup_clients(self):
        self.cloudwatch = self.session.client('cloudwatch')
        self.logs = self.session.client('logs')

    def audit_all(self):
        # We need to return a LIST of results, not just one.
        return self.audit_log_metric_filters()

    def audit_log_metric_filters(self):
        controls_to_check = [
            ("CIS-3.1", "Unauthorized API Calls", "{($.errorCode = \"*UnauthorizedOperation\") || ($.errorCode = \"AccessDenied*\")}"),
            ("CIS-3.2", "Console Sign-in w/o MFA", "{($.eventName = \"ConsoleLogin\") && ($.additionalEventData.MFAUsed != \"Yes\")}"),
            ("CIS-3.4", "IAM Policy Changes", "{($.eventName=DeleteGroupPolicy)||($.eventName=DeleteRolePolicy)||($.eventName=DeleteUserPolicy)||($.eventName=PutGroupPolicy)||($.eventName=PutRolePolicy)||($.eventName=PutUserPolicy)||($.eventName=CreatePolicy)||($.eventName=DeletePolicy)||($.eventName=CreatePolicyVersion)||($.eventName=DeletePolicyVersion)||($.eventName=AttachRolePolicy)||($.eventName=DetachRolePolicy)||($.eventName=AttachUserPolicy)||($.eventName=DetachUserPolicy)||($.eventName=AttachGroupPolicy)||($.eventName=DetachGroupPolicy)}"),
            ("CIS-3.5", "CloudTrail Config Changes", "{($.eventName=CreateTrail)||($.eventName=UpdateTrail)||($.eventName=DeleteTrail)||($.eventName=StartLogging)||($.eventName=StopLogging)}"),
            ("CIS-3.9", "AWS Config Changes", "{($.eventSource=config.amazonaws.com) && (($.eventName=StopConfigurationRecorder)||($.eventName=DeleteDeliveryChannel)||($.eventName=PutDeliveryChannel)||($.eventName=PutConfigurationRecorder))}")
        ]

        results = []
        try:
            # Get all metric filters (paginate)
            filters = []
            paginator = self.logs.get_paginator('describe_metric_filters')
            for page in paginator.paginate():
                filters.extend(page['metricFilters'])
                
            evidence_content = [{"filterName": f['filterName'], "pattern": f['filterPattern']} for f in filters]

            for cis_id, title, pattern in controls_to_check:
                control = Control(
                    control_id=cis_id,
                    title=f"Metric Filter: {title}",
                    description=f"Ensure a log metric filter exists for {title}.",
                    severity=Severity.MEDIUM,
                    category="Monitoring",
                    cis_reference=cis_id
                )

                # Loose matching: check if the key parts of pattern exist (exact string match is brittle due to spacing)
                # We'll strip spaces for comparison
                clean_pattern = pattern.replace(" ", "")
                matching_filter = next((f for f in filters if clean_pattern in f.get('filterPattern', '').replace(" ", "")), None)
                
                # Also try partial match if complex
                if not matching_filter and "errorCode" in pattern:
                     # Fallback: look for simplified check
                     pass

                evidence = [EvidenceArtifact(control.control_id, "api_output", "Metric Filters", evidence_content)]

                if matching_filter:
                    # Check for Alarm
                    metric_name = matching_filter['metricTransformations'][0]['metricName']
                    metric_ns = matching_filter['metricTransformations'][0]['metricNamespace']
                    
                    alarms = self.cloudwatch.describe_alarms_for_metric(
                        MetricName=metric_name,
                        Namespace=metric_ns
                    )['MetricAlarms']

                    if alarms:
                        results.append(self.create_assessment(control, ControlStatus.PASS, evidence=evidence))
                    else:
                        results.append(self.create_assessment(
                            control,
                            ControlStatus.FAIL,
                            findings=[Finding(control.control_id, Severity.MEDIUM, f"Filter exists but no alarm for {title}.", "Create CloudWatch Alarm.")],
                            evidence=evidence
                        ))
                else:
                    results.append(self.create_assessment(
                        control,
                        ControlStatus.FAIL,
                        findings=[Finding(control.control_id, Severity.MEDIUM, f"No metric filter found for {title}.", f"Create filter with pattern: {pattern}")],
                        evidence=evidence
                    ))
            
            return results

        except ClientError as e:
            # If error, fail all
            err_results = []
            for cis_id, _, _ in controls_to_check:
                 err_results.append(self.handle_error(cis_id, e))
            return err_results
