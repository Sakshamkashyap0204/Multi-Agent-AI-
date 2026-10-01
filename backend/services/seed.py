from datetime import datetime, timedelta
from models.db_models import (
    User, Agent, Task, Subtask, AgentExecution, Approval, GovernancePolicy,
    GovernanceEvent, AuditLog, TaskVersion, Notification,
    UserRole, AgentStatus, TaskStatus, TaskPriority, ExecutionStatus,
    ApprovalStatus, PolicyAction, PolicySeverity
)
from services.auth import hash_password
import uuid


def gen_id():
    return str(uuid.uuid4())


AGENT_CONFIGS = [
    {
        "name": "Planner Agent",
        "slug": "planner",
        "description": "Analyzes tasks, creates execution plans, and coordinates agent workflows.",
        "role": "Orchestration",
        "capabilities": ["Task decomposition", "Dependency mapping", "Agent selection", "Progress tracking"],
        "allowed_tools": ["task_analysis", "agent_registry", "dependency_graph"],
        "system_prompt": "You are the Planner Agent. Analyze tasks and create structured execution plans.",
    },
    {
        "name": "Research Agent",
        "slug": "research",
        "description": "Gathers and synthesizes information relevant to the task.",
        "role": "Research",
        "capabilities": ["Information gathering", "Source analysis", "Finding synthesis", "Gap identification"],
        "allowed_tools": ["web_search", "document_reader", "knowledge_base"],
        "system_prompt": "You are the Research Agent. Gather relevant information and return structured findings.",
    },
    {
        "name": "Data Analyst Agent",
        "slug": "data_analyst",
        "description": "Analyzes structured data, identifies trends, and produces metrics.",
        "role": "Analysis",
        "capabilities": ["Statistical analysis", "Trend identification", "Metric calculation", "Anomaly detection"],
        "allowed_tools": ["data_query", "statistics", "visualization"],
        "system_prompt": "You are the Data Analyst Agent. Analyze data and return structured metrics and trends.",
    },
    {
        "name": "Finance Agent",
        "slug": "finance",
        "description": "Evaluates financial implications, estimates costs, and compares scenarios.",
        "role": "Finance",
        "capabilities": ["Cost estimation", "ROI calculation", "Scenario modeling", "Risk quantification"],
        "allowed_tools": ["financial_calculator", "market_data", "scenario_modeler"],
        "requires_approval": True,
        "system_prompt": "You are the Finance Agent. Evaluate financial implications and return structured analysis.",
    },
    {
        "name": "Compliance Agent",
        "slug": "compliance",
        "description": "Checks outputs against governance policies and flags violations.",
        "role": "Compliance",
        "capabilities": ["Policy checking", "Risk assessment", "Violation detection", "Approval routing"],
        "allowed_tools": ["policy_engine", "risk_scorer", "approval_system"],
        "requires_approval": True,
        "system_prompt": "You are the Compliance Agent. Check outputs against governance policies.",
    },
    {
        "name": "Writer Agent",
        "slug": "writer",
        "description": "Converts research and analysis into clear, professional reports.",
        "role": "Content",
        "capabilities": ["Report writing", "Executive summaries", "Structured formatting", "Clarity review"],
        "allowed_tools": ["document_editor", "template_engine", "grammar_checker"],
        "system_prompt": "You are the Writer Agent. Convert analysis into professional reports.",
    },
    {
        "name": "Reviewer Agent",
        "slug": "reviewer",
        "description": "Reviews outputs from other agents for completeness and consistency.",
        "role": "Quality Assurance",
        "capabilities": ["Output validation", "Consistency checking", "Completeness review", "Revision routing"],
        "allowed_tools": ["output_validator", "consistency_checker"],
        "system_prompt": "You are the Reviewer Agent. Review all agent outputs for quality and completeness.",
    },
    {
        "name": "Final Synthesis Agent",
        "slug": "synthesis",
        "description": "Combines approved outputs into the final deliverable.",
        "role": "Synthesis",
        "capabilities": ["Output combination", "Report generation", "Assumption documentation", "Final delivery"],
        "allowed_tools": ["document_assembler", "report_generator"],
        "system_prompt": "You are the Final Synthesis Agent. Combine all approved outputs into the final deliverable.",
    },
]

GOVERNANCE_POLICIES = [
    {
        "name": "External Communication Policy",
        "description": "Require approval before any external communication or publication.",
        "category": "Communication",
        "severity": PolicySeverity.high,
        "trigger": "Agent attempts external communication or publication",
        "action": PolicyAction.require_approval,
    },
    {
        "name": "Financial Actions Policy",
        "description": "Require approval for financial recommendations exceeding $1M threshold.",
        "category": "Finance",
        "severity": PolicySeverity.high,
        "trigger": "Financial recommendations exceed $1M threshold",
        "action": PolicyAction.require_approval,
        "config": {"threshold": 1000000},
    },
    {
        "name": "Sensitive Data Policy",
        "description": "Block agents from processing restricted data without explicit permission.",
        "category": "Data",
        "severity": PolicySeverity.critical,
        "trigger": "Agent accesses sensitive or restricted data",
        "action": PolicyAction.block,
    },
    {
        "name": "Data Export Policy",
        "description": "Require approval before exporting enterprise data externally.",
        "category": "Data",
        "severity": PolicySeverity.high,
        "trigger": "Agent attempts to export data outside the platform",
        "action": PolicyAction.require_approval,
    },
    {
        "name": "Maximum Execution Steps",
        "description": "Automatically stop agents that exceed maximum iteration limit.",
        "category": "Safety",
        "severity": PolicySeverity.medium,
        "trigger": "Agent exceeds 10 execution iterations",
        "action": PolicyAction.block,
        "config": {"max_iterations": 10},
    },
    {
        "name": "Compliance Review Gate",
        "description": "Require compliance review before final synthesis on all tasks.",
        "category": "Compliance",
        "severity": PolicySeverity.medium,
        "trigger": "Task reaches final synthesis stage",
        "action": PolicyAction.require_approval,
    },
    {
        "name": "Tool Access Control",
        "description": "Agents can only use explicitly permitted tools.",
        "category": "Security",
        "severity": PolicySeverity.high,
        "trigger": "Agent requests access to unauthorized tool",
        "action": PolicyAction.block,
    },
    {
        "name": "Runtime Limit Policy",
        "description": "Automatically stop tasks running longer than 2 hours.",
        "category": "Safety",
        "severity": PolicySeverity.medium,
        "trigger": "Task runtime exceeds 2 hours",
        "action": PolicyAction.warn,
        "config": {"max_runtime_minutes": 120},
    },
]


async def seed_database(db):
    from sqlalchemy import select

    existing = await db.execute(select(User).limit(1))
    if existing.scalar_one_or_none():
        return

    admin = User(
        id=gen_id(),
        email="admin@orchestrate.ai",
        username="admin",
        full_name="Alex Chen",
        hashed_password=hash_password("admin123"),
        role=UserRole.admin,
    )
    manager = User(
        id=gen_id(),
        email="manager@orchestrate.ai",
        username="manager",
        full_name="Sarah Mitchell",
        hashed_password=hash_password("manager123"),
        role=UserRole.manager,
    )
    operator = User(
        id=gen_id(),
        email="operator@orchestrate.ai",
        username="operator",
        full_name="James Park",
        hashed_password=hash_password("operator123"),
        role=UserRole.operator,
    )
    db.add_all([admin, manager, operator])
    await db.flush()

    agents = {}
    for cfg in AGENT_CONFIGS:
        agent = Agent(
            id=gen_id(),
            name=cfg["name"],
            slug=cfg["slug"],
            description=cfg["description"],
            role=cfg["role"],
            status=AgentStatus.active,
            model="gpt-4o-mini",
            system_prompt=cfg.get("system_prompt", ""),
            capabilities=cfg.get("capabilities", []),
            allowed_tools=cfg.get("allowed_tools", []),
            permissions={},
            max_iterations=10,
            requires_approval=cfg.get("requires_approval", False),
            tasks_completed=0,
            tasks_failed=0,
            total_execution_time=0.0,
        )
        db.add(agent)
        agents[cfg["slug"]] = agent
    await db.flush()

    policies = {}
    for pcfg in GOVERNANCE_POLICIES:
        policy = GovernancePolicy(
            id=gen_id(),
            name=pcfg["name"],
            description=pcfg["description"],
            category=pcfg["category"],
            severity=pcfg["severity"],
            trigger=pcfg["trigger"],
            action=pcfg["action"],
            config=pcfg.get("config", {}),
            is_active=True,
        )
        db.add(policy)
        policies[pcfg["name"]] = policy
    await db.flush()

    now = datetime.utcnow()

    vendor_task = Task(
        id=gen_id(),
        name="Vendor Risk Assessment",
        description="Evaluate third-party vendor security posture and compliance status for annual review.",
        goal="Produce a comprehensive vendor risk report with risk scores and remediation recommendations.",
        priority=TaskPriority.high,
        status=TaskStatus.completed,
        governance_mode="strict",
        human_oversight="approval_for_sensitive",
        owner_id=manager.id,
        current_step="Completed",
        version=1,
        started_at=now - timedelta(hours=3),
        completed_at=now - timedelta(hours=1),
        created_at=now - timedelta(hours=4),
        updated_at=now - timedelta(hours=1),
        final_output={
            "status": "completed",
            "executive_summary": "Vendor risk assessment completed. 3 of 12 vendors flagged for remediation.",
            "key_findings": [
                "3 vendors have critical security gaps requiring immediate attention",
                "7 vendors are compliant with current standards",
                "2 vendors require additional documentation"
            ],
            "recommendations": [
                "Terminate contract with Vendor C pending security remediation",
                "Schedule quarterly reviews for all Tier 1 vendors",
                "Implement automated compliance monitoring"
            ],
            "risks": ["Supply chain exposure through Vendor A", "Data handling gaps in Vendor B"],
            "assumptions": ["Assessment based on Q3 documentation"],
            "governance_notes": "All compliance checkpoints passed. Human approval obtained.",
            "contributing_agents": ["planner", "research", "compliance", "writer", "reviewer", "synthesis"],
            "human_reviewed": True,
        }
    )

    feedback_task = Task(
        id=gen_id(),
        name="Customer Feedback Analysis",
        description="Analyze Q3 customer feedback across all channels to identify satisfaction trends.",
        goal="Identify top issues, satisfaction drivers, and actionable improvements.",
        priority=TaskPriority.medium,
        status=TaskStatus.waiting_for_approval,
        governance_mode="standard",
        human_oversight="approval_for_sensitive",
        owner_id=operator.id,
        current_step="Awaiting Human Approval",
        current_agent="compliance",
        version=1,
        started_at=now - timedelta(minutes=45),
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(minutes=5),
    )

    financial_task = Task(
        id=gen_id(),
        name="Quarterly Financial Review",
        description="Prepare Q3 financial performance review with variance analysis and Q4 forecast.",
        goal="Deliver executive financial summary with key metrics and forward-looking guidance.",
        priority=TaskPriority.critical,
        status=TaskStatus.paused,
        governance_mode="strict",
        human_oversight="approval_at_every_stage",
        owner_id=manager.id,
        current_step="Paused",
        version=1,
        started_at=now - timedelta(hours=2),
        created_at=now - timedelta(hours=2, minutes=30),
        updated_at=now - timedelta(minutes=30),
    )

    db.add_all([vendor_task, feedback_task, financial_task])
    await db.flush()

    vendor_subtasks = [
        Subtask(id=gen_id(), task_id=vendor_task.id, name="Create Execution Plan", agent_slug="planner", status=ExecutionStatus.completed, order=0),
        Subtask(id=gen_id(), task_id=vendor_task.id, name="Vendor Research", agent_slug="research", status=ExecutionStatus.completed, order=1),
        Subtask(id=gen_id(), task_id=vendor_task.id, name="Risk Analysis", agent_slug="data_analyst", status=ExecutionStatus.completed, order=2),
        Subtask(id=gen_id(), task_id=vendor_task.id, name="Compliance Check", agent_slug="compliance", status=ExecutionStatus.completed, order=3),
        Subtask(id=gen_id(), task_id=vendor_task.id, name="Report Writing", agent_slug="writer", status=ExecutionStatus.completed, order=4),
        Subtask(id=gen_id(), task_id=vendor_task.id, name="Review All Outputs", agent_slug="reviewer", status=ExecutionStatus.completed, order=5),
        Subtask(id=gen_id(), task_id=vendor_task.id, name="Final Synthesis", agent_slug="synthesis", status=ExecutionStatus.completed, order=6),
    ]

    feedback_subtasks = [
        Subtask(id=gen_id(), task_id=feedback_task.id, name="Create Execution Plan", agent_slug="planner", status=ExecutionStatus.completed, order=0),
        Subtask(id=gen_id(), task_id=feedback_task.id, name="Feedback Research", agent_slug="research", status=ExecutionStatus.completed, order=1),
        Subtask(id=gen_id(), task_id=feedback_task.id, name="Sentiment Analysis", agent_slug="data_analyst", status=ExecutionStatus.completed, order=2),
        Subtask(id=gen_id(), task_id=feedback_task.id, name="Report Writing", agent_slug="writer", status=ExecutionStatus.completed, order=3),
        Subtask(id=gen_id(), task_id=feedback_task.id, name="Review All Outputs", agent_slug="reviewer", status=ExecutionStatus.completed, order=4),
        Subtask(id=gen_id(), task_id=feedback_task.id, name="Compliance Check", agent_slug="compliance", status=ExecutionStatus.running, order=5),
        Subtask(id=gen_id(), task_id=feedback_task.id, name="Final Synthesis", agent_slug="synthesis", status=ExecutionStatus.pending, order=6),
    ]

    financial_subtasks = [
        Subtask(id=gen_id(), task_id=financial_task.id, name="Create Execution Plan", agent_slug="planner", status=ExecutionStatus.completed, order=0),
        Subtask(id=gen_id(), task_id=financial_task.id, name="Financial Data Research", agent_slug="research", status=ExecutionStatus.completed, order=1),
        Subtask(id=gen_id(), task_id=financial_task.id, name="Financial Analysis", agent_slug="finance", status=ExecutionStatus.running, order=2),
        Subtask(id=gen_id(), task_id=financial_task.id, name="Compliance Check", agent_slug="compliance", status=ExecutionStatus.pending, order=3),
        Subtask(id=gen_id(), task_id=financial_task.id, name="Final Synthesis", agent_slug="synthesis", status=ExecutionStatus.pending, order=4),
    ]

    for st in vendor_subtasks + feedback_subtasks + financial_subtasks:
        db.add(st)
    await db.flush()

    feedback_approval = Approval(
        id=gen_id(),
        task_id=feedback_task.id,
        agent_slug="compliance",
        requested_action="Proceed with publishing customer feedback analysis report to stakeholder portal",
        reason="External publication of customer data analysis requires human authorization per data governance policy.",
        risk_level="high",
        agent_output={
            "compliance_status": "requires_approval",
            "summary": "Report contains aggregated customer data. External publication requires authorization.",
            "warnings": ["Customer data aggregation requires privacy review", "External portal access requires authorization"],
            "policy_triggered": "Data Export Policy",
        },
        policy_triggered="Data Export Policy",
        status=ApprovalStatus.pending,
        created_at=now - timedelta(minutes=5),
    )
    db.add(feedback_approval)

    audit_entries = [
        AuditLog(id=gen_id(), task_id=vendor_task.id, user_name="Sarah Mitchell", event_type="task_created", action="Task 'Vendor Risk Assessment' created", risk_level="low", created_at=now - timedelta(hours=4)),
        AuditLog(id=gen_id(), task_id=vendor_task.id, agent_slug="planner", event_type="agent_started", action="Planner Agent started", risk_level="low", created_at=now - timedelta(hours=3, minutes=58)),
        AuditLog(id=gen_id(), task_id=vendor_task.id, agent_slug="planner", event_type="agent_completed", action="Planner Agent completed - created 5 subtasks", risk_level="low", created_at=now - timedelta(hours=3, minutes=55)),
        AuditLog(id=gen_id(), task_id=vendor_task.id, agent_slug="research", event_type="agent_completed", action="Research Agent completed - 8 findings identified", risk_level="low", created_at=now - timedelta(hours=3, minutes=30)),
        AuditLog(id=gen_id(), task_id=vendor_task.id, agent_slug="compliance", event_type="governance_triggered", action="Compliance Agent triggered External Communication Policy", risk_level="high", created_at=now - timedelta(hours=2, minutes=30)),
        AuditLog(id=gen_id(), task_id=vendor_task.id, event_type="approval_requested", action="Approval requested for external report publication", risk_level="high", created_at=now - timedelta(hours=2, minutes=28)),
        AuditLog(id=gen_id(), task_id=vendor_task.id, user_name="Sarah Mitchell", event_type="approval_granted", action="Manager approved external publication", risk_level="medium", created_at=now - timedelta(hours=2)),
        AuditLog(id=gen_id(), task_id=vendor_task.id, agent_slug="synthesis", event_type="agent_completed", action="Final Synthesis Agent completed", risk_level="low", created_at=now - timedelta(hours=1, minutes=10)),
        AuditLog(id=gen_id(), task_id=vendor_task.id, event_type="task_completed", action="Task completed successfully", risk_level="low", created_at=now - timedelta(hours=1)),
        AuditLog(id=gen_id(), task_id=feedback_task.id, user_name="James Park", event_type="task_created", action="Task 'Customer Feedback Analysis' created", risk_level="low", created_at=now - timedelta(hours=1)),
        AuditLog(id=gen_id(), task_id=feedback_task.id, agent_slug="research", event_type="agent_completed", action="Research Agent completed feedback analysis", risk_level="low", created_at=now - timedelta(minutes=40)),
        AuditLog(id=gen_id(), task_id=feedback_task.id, agent_slug="compliance", event_type="governance_triggered", action="Compliance Agent triggered Data Export Policy", risk_level="high", created_at=now - timedelta(minutes=6)),
        AuditLog(id=gen_id(), task_id=feedback_task.id, event_type="approval_requested", action="Approval required for external data publication", risk_level="high", created_at=now - timedelta(minutes=5)),
        AuditLog(id=gen_id(), task_id=financial_task.id, user_name="Sarah Mitchell", event_type="task_created", action="Task 'Quarterly Financial Review' created", risk_level="low", created_at=now - timedelta(hours=2, minutes=30)),
        AuditLog(id=gen_id(), task_id=financial_task.id, agent_slug="finance", event_type="agent_started", action="Finance Agent started financial analysis", risk_level="low", created_at=now - timedelta(hours=1, minutes=30)),
        AuditLog(id=gen_id(), task_id=financial_task.id, user_name="Sarah Mitchell", event_type="task_paused", action="Task paused by manager", risk_level="low", created_at=now - timedelta(minutes=30)),
    ]
    for entry in audit_entries:
        db.add(entry)

    gov_events = [
        GovernanceEvent(
            id=gen_id(),
            policy_id=policies["External Communication Policy"].id,
            task_id=vendor_task.id,
            agent_slug="compliance",
            event_type="policy_triggered",
            description="External Communication Policy triggered during vendor report publication",
            action_taken="require_approval",
            resolved=True,
            created_at=now - timedelta(hours=2, minutes=30),
        ),
        GovernanceEvent(
            id=gen_id(),
            policy_id=policies["Data Export Policy"].id,
            task_id=feedback_task.id,
            agent_slug="compliance",
            event_type="policy_triggered",
            description="Data Export Policy triggered for customer feedback report",
            action_taken="require_approval",
            resolved=False,
            created_at=now - timedelta(minutes=6),
        ),
    ]
    for ge in gov_events:
        db.add(ge)

    notifs = [
        Notification(
            id=gen_id(),
            user_id=manager.id,
            title="Approval Required",
            message="Customer Feedback Analysis requires your approval for external publication.",
            type="warning",
            link=f"/approvals/{feedback_approval.id}",
            is_read=False,
            created_at=now - timedelta(minutes=5),
        ),
        Notification(
            id=gen_id(),
            user_id=manager.id,
            title="Task Completed",
            message="Vendor Risk Assessment has been completed successfully.",
            type="success",
            link=f"/tasks/{vendor_task.id}",
            is_read=True,
            created_at=now - timedelta(hours=1),
        ),
    ]
    for n in notifs:
        db.add(n)

    await db.commit()
    print("[OK] Database seeded with demo data")
