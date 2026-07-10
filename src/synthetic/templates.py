"""Templates for generating synthetic test tickets across multiple departments and categories."""

SCENARIO_TEMPLATES = [
    {
        "category": "billing",
        "title": "Refund request for CloudSync Pro subscription",
        "content_template": "I would like to request a refund for my CloudSync Pro monthly subscription. The transaction occurred on {date_ref} which is {days_diff} days ago. I haven't been using the service active.",
        "priority": "high",
        "department": "Billing",
        "metadata_template": {
            "tier": "enterprise",
            "purchase_date": "{date_ref}",
            "amount_usd": 49.99
        }
    },
    {
        "category": "account_access",
        "title": "API Gateway access keys provision request",
        "content_template": "Our engineering team requires production write keys for the core API Gateway. We completed our security clearance checks on {date_ref}.",
        "priority": "medium",
        "department": "Security",
        "metadata_template": {
            "tier": "partner",
            "security_clearance": "passed"
        }
    },
    {
        "category": "technical_support",
        "title": "SLA breach notification on support ticket",
        "content_template": "This is a follow-up on ticket #{ticket_num}. It has been open for {hours} hours without a response from your engineering team. This is a direct SLA breach.",
        "priority": "high",
        "department": "Operations",
        "metadata_template": {
            "sla_tier": "gold",
            "hours_open": "{hours}"
        }
    },
    {
        "category": "general_inquiry",
        "title": "Product catalog compatibility list request",
        "content_template": "Can you provide the integration specifications list and product compatibility matrices for CloudSync Pro version {version}?",
        "priority": "low",
        "department": "Product Management",
        "metadata_template": {
            "product_version": "{version}"
        }
    }
]
