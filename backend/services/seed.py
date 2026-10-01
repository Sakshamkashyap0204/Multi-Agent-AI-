from datetime import datetime, timedelta
from models.database import gen_id, MongoModel
from services.auth import hash_password

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
        "severity": "high",
        "trigger": "Agent attempts external communication or publication",
        "action": "require_approval",
    },
    {
        "name": "Financial Actions Policy",
        "description": "Require approval for financial recommendations exceeding $1M threshold.",
        "category": "Finance",
        "severity": "high",
        "trigger": "Financial recommendations exceed $1M threshold",
        "action": "require_approval",
        "config": {"threshold": 1000000},
    },
    {
        "name": "Sensitive Data Policy",
        "description": "Block agents from processing restricted data without explicit permission.",
        "category": "Data",
        "severity": "critical",
        "trigger": "Agent accesses sensitive or restricted data",
        "action": "block",
    },
    {
        "name": "Data Export Policy",
        "description": "Require approval before exporting enterprise data externally.",
        "category": "Data",
        "severity": "high",
        "trigger": "Agent attempts to export data outside the platform",
        "action": "require_approval",
    },
    {
        "name": "Maximum Execution Steps",
        "description": "Automatically stop agents that exceed maximum iteration limit.",
        "category": "Safety",
        "severity": "medium",
        "trigger": "Agent exceeds 10 execution iterations",
        "action": "block",
        "config": {"max_iterations": 10},
    },
    {
        "name": "Compliance Review Gate",
        "description": "Require compliance review before final synthesis on all tasks.",
        "category": "Compliance",
        "severity": "medium",
        "trigger": "Task reaches final synthesis stage",
        "action": "require_approval",
    },
    {
        "name": "Tool Access Control",
        "description": "Agents can only use explicitly permitted tools.",
        "category": "Security",
        "severity": "high",
        "trigger": "Agent requests access to unauthorized tool",
        "action": "block",
    },
    {
        "name": "Runtime Limit Policy",
        "description": "Automatically stop tasks running longer than 2 hours.",
        "category": "Safety",
        "severity": "medium",
        "trigger": "Task runtime exceeds 2 hours",
        "action": "warn",
        "config": {"max_runtime_minutes": 120},
    },
]


async def seed_database(db):
    user_count = await db.users.count_documents({})
    if user_count > 0:
        return

    admin = {
        "_id": gen_id(),
        "email": "admin@orchestrate.ai",
        "username": "admin",
        "full_name": "Alex Chen",
        "hashed_password": hash_password("admin123"),
        "role": "admin",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    manager = {
        "_id": gen_id(),
        "email": "manager@orchestrate.ai",
        "username": "manager",
        "full_name": "Sarah Mitchell",
        "hashed_password": hash_password("manager123"),
        "role": "manager",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    operator = {
        "_id": gen_id(),
        "email": "operator@orchestrate.ai",
        "username": "operator",
        "full_name": "James Park",
        "hashed_password": hash_password("operator123"),
        "role": "operator",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    await db.users.insert_many([admin, manager, operator])

    # Insert Agents
    agents_docs = []
    for cfg in AGENT_CONFIGS:
        agent_doc = {
            "_id": gen_id(),
            "name": cfg["name"],
            "slug": cfg["slug"],
            "description": cfg["description"],
            "role": cfg["role"],
            "status": "active",
            "model": "gpt-4o-mini",
            "system_prompt": cfg.get("system_prompt", ""),
            "capabilities": cfg.get("capabilities", []),
            "allowed_tools": cfg.get("allowed_tools", []),
            "permissions": {},
            "max_iterations": 10,
            "requires_approval": cfg.get("requires_approval", False),
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "created_at": datetime.utcnow(),
        }
        agents_docs.append(agent_doc)
    await db.agents.insert_many(agents_docs)

    # Insert Policies
    policies_docs = []
    policy_map = {}
    for pcfg in GOVERNANCE_POLICIES:
        p_doc = {
            "_id": gen_id(),
            "name": pcfg["name"],
            "description": pcfg["description"],
            "category": pcfg["category"],
            "severity": pcfg["severity"],
            "trigger": pcfg["trigger"],
            "action": pcfg["action"],
            "config": pcfg.get("config", {}),
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        policies_docs.append(p_doc)
        policy_map[pcfg["name"]] = p_doc
    await db.governance_policies.insert_many(policies_docs)

    now = datetime.utcnow()

    # Seed Demo Tasks
    vendor_task_id = gen_id()
    vendor_subtasks = [
        {"id": gen_id(), "name": "Create Execution Plan", "agent_slug": "planner", "status": "completed", "order": 0, "depends_on": []},
        {"id": gen_id(), "name": "Vendor Research", "agent_slug": "research", "status": "completed", "order": 1, "depends_on": []},
        {"id": gen_id(), "name": "Risk Analysis", "agent_slug": "data_analyst", "status": "completed", "order": 2, "depends_on": []},
        {"id": gen_id(), "name": "Compliance Check", "agent_slug": "compliance", "status": "completed", "order": 3, "depends_on": []},
        {"id": gen_id(), "name": "Report Writing", "agent_slug": "writer", "status": "completed", "order": 4, "depends_on": []},
        {"id": gen_id(), "name": "Review All Outputs", "agent_slug": "reviewer", "status": "completed", "order": 5, "depends_on": []},
        {"id": gen_id(), "name": "Final Synthesis", "agent_slug": "synthesis", "status": "completed", "order": 6, "depends_on": []},
    ]

    vendor_task = {
        "_id": vendor_task_id,
        "name": "Vendor Risk Assessment",
        "description": "Evaluate third-party vendor security posture and compliance status for annual review.",
        "goal": "Produce a comprehensive vendor risk report with risk scores and remediation recommendations.",
        "priority": "high",
        "status": "COMPLETED",
        "governance_mode": "strict",
        "human_oversight": "approval_for_sensitive",
        "owner_id": manager["_id"],
        "owner_name": manager["full_name"],
        "current_step": "Completed",
        "current_agent": None,
        "version": 1,
        "subtasks": vendor_subtasks,
        "started_at": now - timedelta(hours=3),
        "completed_at": now - timedelta(hours=1),
        "created_at": now - timedelta(hours=4),
        "updated_at": now - timedelta(hours=1),
        "final_output": {
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
    }

    feedback_task_id = gen_id()
    feedback_subtasks = [
        {"id": gen_id(), "name": "Create Execution Plan", "agent_slug": "planner", "status": "completed", "order": 0, "depends_on": []},
        {"id": gen_id(), "name": "Feedback Research", "agent_slug": "research", "status": "completed", "order": 1, "depends_on": []},
        {"id": gen_id(), "name": "Sentiment Analysis", "agent_slug": "data_analyst", "status": "completed", "order": 2, "depends_on": []},
        {"id": gen_id(), "name": "Report Writing", "agent_slug": "writer", "status": "completed", "order": 3, "depends_on": []},
        {"id": gen_id(), "name": "Review All Outputs", "agent_slug": "reviewer", "status": "completed", "order": 4, "depends_on": []},
        {"id": gen_id(), "name": "Compliance Check", "agent_slug": "compliance", "status": "running", "order": 5, "depends_on": []},
        {"id": gen_id(), "name": "Final Synthesis", "agent_slug": "synthesis", "status": "pending", "order": 6, "depends_on": []},
    ]

    feedback_task = {
        "_id": feedback_task_id,
        "name": "Customer Feedback Analysis",
        "description": "Analyze Q3 customer feedback across all channels to identify satisfaction trends.",
        "goal": "Identify top issues, satisfaction drivers, and actionable improvements.",
        "priority": "medium",
        "status": "WAITING_FOR_APPROVAL",
        "governance_mode": "standard",
        "human_oversight": "approval_for_sensitive",
        "owner_id": operator["_id"],
        "owner_name": operator["full_name"],
        "current_step": "Awaiting Human Approval",
        "current_agent": "compliance",
        "version": 1,
        "subtasks": feedback_subtasks,
        "started_at": now - timedelta(minutes=45),
        "created_at": now - timedelta(hours=1),
        "updated_at": now - timedelta(minutes=5),
    }

    financial_task_id = gen_id()
    financial_subtasks = [
        {"id": gen_id(), "name": "Create Execution Plan", "agent_slug": "planner", "status": "completed", "order": 0, "depends_on": []},
        {"id": gen_id(), "name": "Financial Data Research", "agent_slug": "research", "status": "completed", "order": 1, "depends_on": []},
        {"id": gen_id(), "name": "Financial Analysis", "agent_slug": "finance", "status": "running", "order": 2, "depends_on": []},
        {"id": gen_id(), "name": "Compliance Check", "agent_slug": "compliance", "status": "pending", "order": 3, "depends_on": []},
        {"id": gen_id(), "name": "Final Synthesis", "agent_slug": "synthesis", "status": "pending", "order": 4, "depends_on": []},
    ]

    financial_task = {
        "_id": financial_task_id,
        "name": "Quarterly Financial Review",
        "description": "Prepare Q3 financial performance review with variance analysis and Q4 forecast.",
        "goal": "Deliver executive financial summary with key metrics and forward-looking guidance.",
        "priority": "critical",
        "status": "PAUSED",
        "governance_mode": "strict",
        "human_oversight": "approval_at_every_stage",
        "owner_id": manager["_id"],
        "owner_name": manager["full_name"],
        "current_step": "Paused",
        "current_agent": None,
        "version": 1,
        "subtasks": financial_subtasks,
        "started_at": now - timedelta(hours=2),
        "created_at": now - timedelta(hours=2, minutes=30),
        "updated_at": now - timedelta(minutes=30),
    }

    await db.tasks.insert_many([vendor_task, feedback_task, financial_task])

    # Seed Approvals
    feedback_approval = {
        "_id": gen_id(),
        "task_id": feedback_task_id,
        "task_name": feedback_task["name"],
        "agent_slug": "compliance",
        "requested_action": "Proceed with publishing customer feedback analysis report to stakeholder portal",
        "reason": "External publication of customer data analysis requires human authorization per data governance policy.",
        "risk_level": "high",
        "agent_output": {
            "compliance_status": "requires_approval",
            "summary": "Report contains aggregated customer data. External publication requires authorization.",
            "warnings": ["Customer data aggregation requires privacy review", "External portal access requires authorization"],
            "policy_triggered": "Data Export Policy",
        },
        "policy_triggered": "Data Export Policy",
        "status": "pending",
        "reviewer_id": None,
        "reviewer_name": None,
        "reviewer_notes": None,
        "created_at": now - timedelta(minutes=5),
        "resolved_at": None,
    }
    await db.approvals.insert_one(feedback_approval)

    # Seed Audit Logs
    audit_entries = [
        {"_id": gen_id(), "task_id": vendor_task_id, "user_name": "Sarah Mitchell", "event_type": "task_created", "action": "Task 'Vendor Risk Assessment' created", "risk_level": "low", "created_at": now - timedelta(hours=4)},
        {"_id": gen_id(), "task_id": vendor_task_id, "agent_slug": "planner", "event_type": "agent_started", "action": "Planner Agent started", "risk_level": "low", "created_at": now - timedelta(hours=3, minutes=58)},
        {"_id": gen_id(), "task_id": vendor_task_id, "agent_slug": "planner", "event_type": "agent_completed", "action": "Planner Agent completed - created 5 subtasks", "risk_level": "low", "created_at": now - timedelta(hours=3, minutes=55)},
        {"_id": gen_id(), "task_id": vendor_task_id, "agent_slug": "research", "event_type": "agent_completed", "action": "Research Agent completed - 8 findings identified", "risk_level": "low", "created_at": now - timedelta(hours=3, minutes=30)},
        {"_id": gen_id(), "task_id": vendor_task_id, "agent_slug": "compliance", "event_type": "governance_triggered", "action": "Compliance Agent triggered External Communication Policy", "risk_level": "high", "created_at": now - timedelta(hours=2, minutes=30)},
        {"_id": gen_id(), "task_id": vendor_task_id, "event_type": "approval_requested", "action": "Approval requested for external report publication", "risk_level": "high", "created_at": now - timedelta(hours=2, minutes=28)},
        {"_id": gen_id(), "task_id": vendor_task_id, "user_name": "Sarah Mitchell", "event_type": "approval_granted", "action": "Manager approved external publication", "risk_level": "medium", "created_at": now - timedelta(hours=2)},
        {"_id": gen_id(), "task_id": vendor_task_id, "agent_slug": "synthesis", "event_type": "agent_completed", "action": "Final Synthesis Agent completed", "risk_level": "low", "created_at": now - timedelta(hours=1, minutes=10)},
        {"_id": gen_id(), "task_id": vendor_task_id, "event_type": "task_completed", "action": "Task completed successfully", "risk_level": "low", "created_at": now - timedelta(hours=1)},
        {"_id": gen_id(), "task_id": feedback_task_id, "user_name": "James Park", "event_type": "task_created", "action": "Task 'Customer Feedback Analysis' created", "risk_level": "low", "created_at": now - timedelta(hours=1)},
        {"_id": gen_id(), "task_id": feedback_task_id, "agent_slug": "research", "event_type": "agent_completed", "action": "Research Agent completed feedback analysis", "risk_level": "low", "created_at": now - timedelta(minutes=40)},
        {"_id": gen_id(), "task_id": feedback_task_id, "agent_slug": "compliance", "event_type": "governance_triggered", "action": "Compliance Agent triggered Data Export Policy", "risk_level": "high", "created_at": now - timedelta(minutes=6)},
        {"_id": gen_id(), "task_id": feedback_task_id, "event_type": "approval_requested", "action": "Approval required for external data publication", "risk_level": "high", "created_at": now - timedelta(minutes=5)},
        {"_id": gen_id(), "task_id": financial_task_id, "user_name": "Sarah Mitchell", "event_type": "task_created", "action": "Task 'Quarterly Financial Review' created", "risk_level": "low", "created_at": now - timedelta(hours=2, minutes=30)},
        {"_id": gen_id(), "task_id": financial_task_id, "agent_slug": "finance", "event_type": "agent_started", "action": "Finance Agent started financial analysis", "risk_level": "low", "created_at": now - timedelta(hours=1, minutes=30)},
        {"_id": gen_id(), "task_id": financial_task_id, "user_name": "Sarah Mitchell", "event_type": "task_paused", "action": "Task paused by manager", "risk_level": "low", "created_at": now - timedelta(minutes=30)},
    ]
    await db.audit_logs.insert_many(audit_entries)

    # Seed Governance Events
    gov_events = [
        {
            "_id": gen_id(),
            "policy_id": policy_map["External Communication Policy"]["_id"],
            "policy_name": "External Communication Policy",
            "task_id": vendor_task_id,
            "agent_slug": "compliance",
            "event_type": "policy_triggered",
            "description": "External Communication Policy triggered during vendor report publication",
            "action_taken": "require_approval",
            "resolved": True,
            "created_at": now - timedelta(hours=2, minutes=30),
        },
        {
            "_id": gen_id(),
            "policy_id": policy_map["Data Export Policy"]["_id"],
            "policy_name": "Data Export Policy",
            "task_id": feedback_task_id,
            "agent_slug": "compliance",
            "event_type": "policy_triggered",
            "description": "Data Export Policy triggered for customer feedback report",
            "action_taken": "require_approval",
            "resolved": False,
            "created_at": now - timedelta(minutes=6),
        },
    ]
    await db.governance_events.insert_many(gov_events)

    # Seed Notifications
    notifs = [
        {
            "_id": gen_id(),
            "user_id": manager["_id"],
            "title": "Approval Required",
            "message": "Customer Feedback Analysis requires your approval for external publication.",
            "type": "warning",
            "link": f"/approvals/{feedback_approval['_id']}",
            "is_read": False,
            "created_at": now - timedelta(minutes=5),
        },
        {
            "_id": gen_id(),
            "user_id": manager["_id"],
            "title": "Task Completed",
            "message": "Vendor Risk Assessment has been completed successfully.",
            "type": "success",
            "link": f"/tasks/{vendor_task_id}",
            "is_read": True,
            "created_at": now - timedelta(hours=1),
        },
    ]
    await db.notifications.insert_many(notifs)
    print("[OK] MongoDB Atlas seeded with initial enterprise data")
