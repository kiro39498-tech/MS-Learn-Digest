"""
Topic Repository — Hierarchy-aware database access layer.

Key concepts
────────────
resolve_descendant_ids(topic_ids)
    Given a set of subscribed topic IDs, returns those IDs PLUS every
    descendant topic ID.  This means subscribing to "Azure" automatically
    includes Azure → Networking, Azure → Security, etc. when building the
    catalog filter sets used by the digest generator.

seed_system_topics()
    Inserts the full hierarchical topic tree on first boot.
    Root topics (level 0) are inserted first so child FK references resolve.
    Idempotent — skips slugs that already exist.
"""

import logging
from typing import List, Optional, Set
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.topic import Topic, UserSubscription

logger = logging.getLogger(__name__)

# ── Full hierarchical topic seed data ─────────────────────────────────────────
# Each dict may contain a "children" list of subtopics.
# parent_slug is resolved to a UUID after the parent row is inserted.

SYSTEM_TOPICS = [
    {
        "name": "Azure",
        "slug": "azure",
        "description": "Microsoft Azure cloud platform — the complete ecosystem.",
        "icon": "cloud",
        "catalog_products": ["azure"],
        "catalog_subjects": ["azure"],
        "children": [
            {
                "name": "Azure Fundamentals",
                "slug": "azure-fundamentals",
                "description": "Core Azure concepts, cloud principles, and AZ-900 prep.",
                "icon": "cloud",
                "catalog_products": ["azure"],
                "catalog_subjects": ["azure", "fundamentals"],
            },
            {
                "name": "Azure Compute",
                "slug": "azure-compute",
                "description": "Virtual machines, App Service, Functions, and Container Instances.",
                "icon": "cpu",
                "catalog_products": ["azure", "azure-virtual-machines", "azure-app-service", "azure-functions"],
                "catalog_subjects": ["azure", "compute"],
            },
            {
                "name": "Azure Networking",
                "slug": "azure-networking",
                "description": "Virtual networks, load balancers, DNS, and VPN gateways.",
                "icon": "network",
                "catalog_products": ["azure", "azure-virtual-network", "azure-load-balancer"],
                "catalog_subjects": ["azure", "networking"],
            },
            {
                "name": "Azure Storage",
                "slug": "azure-storage",
                "description": "Blob storage, files, queues, tables, and data lake.",
                "icon": "database",
                "catalog_products": ["azure", "azure-storage", "azure-data-lake-storage"],
                "catalog_subjects": ["azure", "storage"],
            },
            {
                "name": "Azure Security",
                "slug": "azure-security",
                "description": "Azure Security Center, Key Vault, and cloud security practices.",
                "icon": "shield",
                "catalog_products": ["azure", "azure-key-vault", "microsoft-defender"],
                "catalog_subjects": ["azure", "security"],
            },
            {
                "name": "Azure Identity",
                "slug": "azure-identity",
                "description": "Entra ID, managed identities, and RBAC.",
                "icon": "key",
                "catalog_products": ["azure", "entra-id"],
                "catalog_subjects": ["azure", "identity", "security"],
            },
            {
                "name": "Azure Monitoring",
                "slug": "azure-monitoring",
                "description": "Azure Monitor, Log Analytics, Application Insights.",
                "icon": "activity",
                "catalog_products": ["azure", "azure-monitor"],
                "catalog_subjects": ["azure", "monitoring"],
            },
            {
                "name": "Azure DevOps",
                "slug": "azure-devops",
                "description": "Pipelines, boards, repos, and test plans on Azure DevOps.",
                "icon": "git-branch",
                "catalog_products": ["azure-devops"],
                "catalog_subjects": ["devops", "azure"],
            },
            {
                "name": "Azure Data Engineering",
                "slug": "azure-data-engineering",
                "description": "Azure Data Factory, Synapse Analytics, and Databricks.",
                "icon": "layers",
                "catalog_products": ["azure", "azure-data-factory", "azure-synapse-analytics", "azure-databricks"],
                "catalog_subjects": ["data-engineering", "analytics", "azure"],
            },
            {
                "name": "Azure AI",
                "slug": "azure-ai",
                "description": "Azure AI services, Cognitive Services, and Azure OpenAI.",
                "icon": "brain",
                "catalog_products": ["azure", "ai-services", "azure-openai-service"],
                "catalog_subjects": ["ai", "azure"],
            },
            {
                "name": "Azure AI Foundry",
                "slug": "azure-ai-foundry",
                "description": "Build, evaluate, and deploy AI applications on Azure AI Foundry.",
                "icon": "flask",
                "catalog_products": ["azure-ai-studio"],
                "catalog_subjects": ["ai", "genai", "azure"],
            },
            {
                "name": "Azure Kubernetes Service",
                "slug": "aks",
                "description": "Container orchestration, AKS, and cloud-native development.",
                "icon": "box",
                "catalog_products": ["azure-kubernetes-service", "azure"],
                "catalog_subjects": ["containers", "kubernetes", "azure"],
            },
            {
                "name": "Azure Architecture",
                "slug": "azure-architecture",
                "description": "Well-Architected Framework, landing zones, and solution design.",
                "icon": "layout",
                "catalog_products": ["azure"],
                "catalog_subjects": ["azure", "architecture"],
            },
            {
                "name": "Azure Integration Services",
                "slug": "azure-integration",
                "description": "Logic Apps, Service Bus, Event Grid, and API Management.",
                "icon": "share-2",
                "catalog_products": ["azure", "azure-logic-apps", "azure-service-bus", "azure-api-management"],
                "catalog_subjects": ["azure", "integration"],
            },
            {
                "name": "Azure IoT",
                "slug": "azure-iot",
                "description": "IoT Hub, IoT Central, and edge computing on Azure.",
                "icon": "radio",
                "catalog_products": ["azure", "azure-iot"],
                "catalog_subjects": ["azure", "iot"],
            },
        ],
    },
    {
        "name": "Microsoft Fabric",
        "slug": "fabric",
        "description": "Microsoft Fabric analytics platform — unified data and AI.",
        "icon": "database",
        "catalog_products": ["fabric"],
        "catalog_subjects": ["analytics", "data-engineering"],
        "children": [
            {
                "name": "Fabric Fundamentals",
                "slug": "fabric-fundamentals",
                "description": "Introduction to Microsoft Fabric and DP-600 prep.",
                "icon": "database",
                "catalog_products": ["fabric"],
                "catalog_subjects": ["analytics", "fundamentals"],
            },
            {
                "name": "Fabric Data Engineering",
                "slug": "fabric-data-engineering",
                "description": "Lakehouse, pipelines, and Spark notebooks in Fabric.",
                "icon": "layers",
                "catalog_products": ["fabric"],
                "catalog_subjects": ["data-engineering", "analytics"],
            },
            {
                "name": "Fabric Data Science",
                "slug": "fabric-data-science",
                "description": "ML experiments, notebooks, and AI in Microsoft Fabric.",
                "icon": "brain",
                "catalog_products": ["fabric"],
                "catalog_subjects": ["ai", "data-science", "analytics"],
            },
            {
                "name": "Fabric Data Warehouse",
                "slug": "fabric-data-warehouse",
                "description": "Synapse Data Warehouse in Microsoft Fabric.",
                "icon": "database",
                "catalog_products": ["fabric"],
                "catalog_subjects": ["analytics", "data-warehouse"],
            },
            {
                "name": "Fabric Real-Time Analytics",
                "slug": "fabric-real-time",
                "description": "KQL database, Event Streams, and real-time dashboards.",
                "icon": "zap",
                "catalog_products": ["fabric"],
                "catalog_subjects": ["analytics", "real-time"],
            },
            {
                "name": "Fabric Power BI",
                "slug": "fabric-power-bi",
                "description": "Reports, semantic models, and Direct Lake in Fabric.",
                "icon": "bar-chart-2",
                "catalog_products": ["fabric", "power-bi"],
                "catalog_subjects": ["analytics", "reporting"],
            },
            {
                "name": "Fabric Data Factory",
                "slug": "fabric-data-factory",
                "description": "Data integration, orchestration, and dataflows in Fabric.",
                "icon": "shuffle",
                "catalog_products": ["fabric"],
                "catalog_subjects": ["data-engineering", "integration"],
            },
            {
                "name": "Fabric Lakehouse",
                "slug": "fabric-lakehouse",
                "description": "OneLake, delta tables, and the medallion architecture.",
                "icon": "archive",
                "catalog_products": ["fabric"],
                "catalog_subjects": ["data-engineering", "analytics"],
            },
        ],
    },
    {
        "name": "Power Platform",
        "slug": "power-platform",
        "description": "Low-code platform — Power BI, Power Apps, Power Automate, and more.",
        "icon": "zap",
        "catalog_products": ["power-platform", "power-bi", "power-apps"],
        "catalog_subjects": ["analytics", "low-code"],
        "children": [
            {
                "name": "Power Apps",
                "slug": "power-apps",
                "description": "Build business apps without writing code.",
                "icon": "smartphone",
                "catalog_products": ["power-apps", "power-platform"],
                "catalog_subjects": ["low-code"],
            },
            {
                "name": "Power Automate",
                "slug": "power-automate",
                "description": "Automate workflows and business processes.",
                "icon": "repeat",
                "catalog_products": ["power-automate", "power-platform"],
                "catalog_subjects": ["automation", "low-code"],
            },
            {
                "name": "Power BI",
                "slug": "power-bi",
                "description": "Business intelligence, dashboards, and data visualisation.",
                "icon": "bar-chart-2",
                "catalog_products": ["power-bi", "power-platform"],
                "catalog_subjects": ["analytics", "reporting"],
            },
            {
                "name": "Power Pages",
                "slug": "power-pages",
                "description": "Build and publish secure business websites.",
                "icon": "globe",
                "catalog_products": ["power-pages", "power-platform"],
                "catalog_subjects": ["low-code"],
            },
            {
                "name": "Copilot Studio",
                "slug": "copilot-studio",
                "description": "Build AI-powered copilots and chatbots.",
                "icon": "sparkles",
                "catalog_products": ["copilot-studio", "power-platform"],
                "catalog_subjects": ["ai", "copilot"],
            },
        ],
    },
    {
        "name": "Microsoft 365",
        "slug": "m365",
        "description": "Microsoft 365 productivity, collaboration, and security.",
        "icon": "grid",
        "catalog_products": ["m365"],
        "catalog_subjects": ["m365", "productivity"],
        "children": [
            {
                "name": "Microsoft Teams",
                "slug": "m365-teams",
                "description": "Teams collaboration, meetings, and app extensibility.",
                "icon": "users",
                "catalog_products": ["m365", "teams"],
                "catalog_subjects": ["m365", "collaboration"],
            },
            {
                "name": "SharePoint",
                "slug": "m365-sharepoint",
                "description": "Intranet, document management, and SharePoint development.",
                "icon": "share",
                "catalog_products": ["m365", "sharepoint"],
                "catalog_subjects": ["m365"],
            },
            {
                "name": "Exchange",
                "slug": "m365-exchange",
                "description": "Exchange Online, email management, and hybrid scenarios.",
                "icon": "mail",
                "catalog_products": ["m365", "exchange"],
                "catalog_subjects": ["m365"],
            },
            {
                "name": "M365 Security & Compliance",
                "slug": "m365-security",
                "description": "Microsoft Defender for M365, Purview, and compliance.",
                "icon": "shield",
                "catalog_products": ["m365", "microsoft-defender"],
                "catalog_subjects": ["m365", "security", "compliance"],
            },
            {
                "name": "Microsoft Copilot",
                "slug": "copilot-m365",
                "description": "Microsoft 365 Copilot and AI-assisted productivity.",
                "icon": "sparkles",
                "catalog_products": ["m365", "copilot-studio"],
                "catalog_subjects": ["ai", "copilot", "m365"],
            },
        ],
    },
    {
        "name": "Security",
        "slug": "security",
        "description": "Microsoft Defender, Sentinel, and security best practices.",
        "icon": "shield",
        "catalog_products": ["microsoft-defender", "azure-sentinel"],
        "catalog_subjects": ["security"],
        "children": [
            {
                "name": "Microsoft Defender",
                "slug": "defender",
                "description": "Defender for Endpoint, Cloud, Identity, and Office.",
                "icon": "shield",
                "catalog_products": ["microsoft-defender"],
                "catalog_subjects": ["security"],
            },
            {
                "name": "Microsoft Sentinel",
                "slug": "sentinel",
                "description": "Cloud-native SIEM and SOAR on Azure.",
                "icon": "eye",
                "catalog_products": ["azure-sentinel"],
                "catalog_subjects": ["security", "siem"],
            },
            {
                "name": "Entra ID",
                "slug": "entra-id",
                "description": "Microsoft Entra ID — identity and access management.",
                "icon": "key",
                "catalog_products": ["entra-id"],
                "catalog_subjects": ["identity", "security"],
            },
            {
                "name": "Security Copilot",
                "slug": "security-copilot",
                "description": "AI-powered security analysis with Microsoft Security Copilot.",
                "icon": "sparkles",
                "catalog_products": ["microsoft-defender"],
                "catalog_subjects": ["security", "ai", "copilot"],
            },
        ],
    },
    {
        "name": "GitHub",
        "slug": "github",
        "description": "GitHub, GitHub Actions, and GitHub Copilot.",
        "icon": "github",
        "catalog_products": ["github"],
        "catalog_subjects": ["devops", "github"],
        "children": [
            {
                "name": "GitHub Actions",
                "slug": "github-actions",
                "description": "CI/CD workflows and automation with GitHub Actions.",
                "icon": "git-branch",
                "catalog_products": ["github"],
                "catalog_subjects": ["devops", "github"],
            },
            {
                "name": "GitHub Copilot",
                "slug": "github-copilot",
                "description": "AI pair programming with GitHub Copilot.",
                "icon": "sparkles",
                "catalog_products": ["github"],
                "catalog_subjects": ["ai", "copilot", "devops"],
            },
            {
                "name": "GitHub Advanced Security",
                "slug": "github-security",
                "description": "Code scanning, secret detection, and supply chain security.",
                "icon": "shield",
                "catalog_products": ["github"],
                "catalog_subjects": ["security", "devops", "github"],
            },
        ],
    },
    {
        "name": "AI Engineering",
        "slug": "ai-engineering",
        "description": "Building AI applications, LLMs, and generative AI solutions.",
        "icon": "cpu",
        "catalog_products": ["azure", "ai-services", "azure-openai-service"],
        "catalog_subjects": ["ai", "genai"],
        "children": [
            {
                "name": "Generative AI",
                "slug": "generative-ai",
                "description": "Prompt engineering, RAG, and building with LLMs.",
                "icon": "sparkles",
                "catalog_products": ["azure-openai-service", "ai-services"],
                "catalog_subjects": ["ai", "genai"],
            },
            {
                "name": "Responsible AI",
                "slug": "responsible-ai",
                "description": "Fairness, transparency, safety, and governance of AI systems.",
                "icon": "check-circle",
                "catalog_products": ["ai-services"],
                "catalog_subjects": ["ai", "responsible-ai"],
            },
        ],
    },
    {
        "name": "DevOps",
        "slug": "devops",
        "description": "Azure DevOps, GitHub Actions, and CI/CD pipelines.",
        "icon": "git-branch",
        "catalog_products": ["azure-devops", "github"],
        "catalog_subjects": ["devops"],
    },
    {
        "name": "Dynamics 365",
        "slug": "dynamics-365",
        "description": "CRM, ERP, and business applications on Dynamics 365.",
        "icon": "briefcase",
        "catalog_products": ["dynamics-365"],
        "catalog_subjects": ["dynamics"],
        "children": [
            {
                "name": "Dynamics 365 Sales",
                "slug": "d365-sales",
                "description": "Sales automation and CRM capabilities.",
                "icon": "trending-up",
                "catalog_products": ["dynamics-365"],
                "catalog_subjects": ["dynamics", "crm"],
            },
            {
                "name": "Dynamics 365 Finance",
                "slug": "d365-finance",
                "description": "Financial management and ERP capabilities.",
                "icon": "dollar-sign",
                "catalog_products": ["dynamics-365"],
                "catalog_subjects": ["dynamics", "erp"],
            },
            {
                "name": "Dynamics 365 Supply Chain",
                "slug": "d365-supply-chain",
                "description": "Supply chain management and operations.",
                "icon": "package",
                "catalog_products": ["dynamics-365"],
                "catalog_subjects": ["dynamics", "erp"],
            },
        ],
    },
]


class TopicRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Seeding ───────────────────────────────────────────────────────────

    def seed_system_topics(self) -> int:
        """
        Insert the full hierarchical topic tree and repair any stale hierarchy.
        Inserts root topics first, then children (so FK resolves).
        Idempotent — skips slugs that already exist but updates hierarchy columns.
        Returns count of newly inserted rows.
        """
        inserted = 0
        inserted += self._seed_list(SYSTEM_TOPICS, parent_id=None, level=0)
        self.db.commit()

        # Re-run a repair pass to catch any stale rows from the old flat seed
        # that may have been missed by _seed_list (e.g. if server restarted
        # between migration and seed).
        repaired = self._repair_hierarchy()
        if repaired:
            logger.info(f"seed_system_topics — repaired {repaired} stale hierarchy rows.")

        if inserted:
            logger.info(f"Seeded {inserted} new system topics.")
        else:
            logger.info("seed_system_topics — all topics already present.")
        return inserted

    def _repair_hierarchy(self) -> int:
        """
        Fix any topic rows that should have a parent but still have
        parent_topic_id = NULL (can happen when old flat-seed rows exist in
        the DB and the hierarchical seed updated them but the session wasn't
        flushed in the right order).

        Walks the SYSTEM_TOPICS tree and for every child slug whose DB row
        still has parent_topic_id = NULL, sets it to the correct parent.
        """
        repaired = 0

        def walk(topics_data, expected_parent_slug):
            nonlocal repaired
            for data in topics_data:
                slug = data["slug"]
                children = data.get("children", [])

                if expected_parent_slug is not None:
                    # This is a child — check its parent_topic_id
                    child_row = self.db.query(Topic).filter(Topic.slug == slug).first()
                    parent_row = self.db.query(Topic).filter(
                        Topic.slug == expected_parent_slug
                    ).first()
                    if child_row and parent_row and child_row.parent_topic_id != parent_row.id:
                        child_row.parent_topic_id = parent_row.id
                        child_row.level = parent_row.level + 1
                        repaired += 1

                if children:
                    walk(children, slug)

        for root in SYSTEM_TOPICS:
            walk(root.get("children", []), root["slug"])

        if repaired:
            self.db.commit()
        return repaired

    def _seed_list(self, topics_data: list, parent_id, level: int) -> int:
        inserted = 0
        for data in topics_data:
            # Extract children before inserting — don't mutate the original dict
            children = data.get("children", [])
            row_data = {k: v for k, v in data.items() if k != "children"}

            existing = self.db.query(Topic).filter(Topic.slug == row_data["slug"]).first()
            if not existing:
                topic = Topic(
                    **row_data,
                    is_system=True,
                    is_active=True,
                    parent_topic_id=parent_id,
                    level=level,
                )
                self.db.add(topic)
                self.db.flush()   # get the id before inserting children
                inserted += 1
                parent_id_for_children = topic.id
            else:
                # Ensure hierarchy columns are set even for pre-existing rows
                if existing.parent_topic_id is None and parent_id is not None:
                    existing.parent_topic_id = parent_id
                if existing.level != level:
                    existing.level = level
                parent_id_for_children = existing.id

            if children:
                inserted += self._seed_list(children, parent_id=parent_id_for_children, level=level + 1)

        return inserted

    # ── Basic queries ─────────────────────────────────────────────────────

    def get_all(self) -> List[Topic]:
        """All active topics, ordered by level then name."""
        return (
            self.db.query(Topic)
            .filter(Topic.is_active == True)  # noqa: E712
            .order_by(Topic.level, Topic.name)
            .all()
        )

    def get_roots(self) -> List[Topic]:
        """Root topics only (level 0)."""
        return (
            self.db.query(Topic)
            .filter(Topic.parent_topic_id == None, Topic.is_active == True)  # noqa: E711, E712
            .order_by(Topic.name)
            .all()
        )

    def get_tree(self) -> List[Topic]:
        """
        Returns all active topics.  The caller can build the tree from
        parent_topic_id relationships.  SQLAlchemy lazy-loads children
        so this is equivalent to a single SELECT + lazy selects on access.
        """
        return self.get_all()

    def get_by_id(self, topic_id: UUID) -> Optional[Topic]:
        return self.db.query(Topic).filter(Topic.id == topic_id).first()

    def get_by_slug(self, slug: str) -> Optional[Topic]:
        return self.db.query(Topic).filter(Topic.slug == slug).first()

    def get_children(self, parent_id: UUID) -> List[Topic]:
        return (
            self.db.query(Topic)
            .filter(Topic.parent_topic_id == parent_id, Topic.is_active == True)  # noqa: E712
            .order_by(Topic.name)
            .all()
        )

    # ── Hierarchy resolution ──────────────────────────────────────────────

    def resolve_descendant_ids(self, topic_ids: List[UUID]) -> Set[UUID]:
        """
        Given a list of subscribed topic IDs, return those IDs PLUS every
        descendant topic ID.

        Example: if user subscribes to "Azure", this returns Azure's id
        PLUS all Azure subtopic ids (Networking, Compute, Storage, …).

        The resolution is done with a CTE recursive query so it handles
        arbitrary tree depth without N+1 queries.
        """
        if not topic_ids:
            return set()

        # Use a recursive CTE via raw SQL for efficiency
        from sqlalchemy import text
        uuid_list = ", ".join(f"'{tid}'" for tid in topic_ids)
        sql = text(f"""
            WITH RECURSIVE descendants AS (
                -- Anchor: the subscribed topics themselves
                SELECT id
                FROM   topics
                WHERE  id IN ({uuid_list})
                UNION ALL
                -- Recursive: one level deeper each iteration
                SELECT t.id
                FROM   topics t
                JOIN   descendants d ON t.parent_topic_id = d.id
                WHERE  t.is_active = true
            )
            SELECT id FROM descendants
        """)
        rows = self.db.execute(sql).fetchall()
        return {row[0] for row in rows}

    # ── Subscription management ───────────────────────────────────────────

    def get_user_subscriptions(self, user_id: UUID) -> List[UserSubscription]:
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .all()
        )

    def get_subscribed_topic_ids(self, user_id: UUID) -> List[UUID]:
        rows = (
            self.db.query(UserSubscription.topic_id)
            .filter(UserSubscription.user_id == user_id)
            .all()
        )
        return [r.topic_id for r in rows]

    def replace_user_subscriptions(
        self, user_id: UUID, topic_ids: List[UUID]
    ) -> List[UserSubscription]:
        """Atomically replace all subscriptions for a user."""
        self.db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id
        ).delete()
        subs = []
        for tid in topic_ids:
            topic = self.get_by_id(tid)
            if topic:
                sub = UserSubscription(user_id=user_id, topic_id=tid)
                self.db.add(sub)
                subs.append(sub)
        self.db.commit()
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .all()
        )
