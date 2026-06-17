"""
Learning Curriculum — Professional Platform Edition

400+ modules across 7 tracks, structured as phased learning paths.
Each module includes: phase, skill_level, objectives, keywords, duration.

skill_level: beginner | intermediate | advanced | expert
is_milestone: True = capstone / hands-on project
"""

# ── Helper ─────────────────────────────────────────────────────────────────────

def m(seq, title, skill, duration, phase_num, phase_name, objectives, keywords,
      milestone=False, description=""):
    """Compact module definition builder."""
    return {
        "seq": seq, "title": title, "difficulty": skill, "skill_level": skill,
        "duration": duration, "phase_number": phase_num, "phase_name": phase_name,
        "objectives": objectives, "keywords": keywords,
        "is_milestone": milestone, "description": description,
    }


# ── Azure Track — 52 modules ───────────────────────────────────────────────────

_AZURE = [
    # Phase 1: Cloud & Azure Fundamentals (beginner)
    m(1,  "Cloud Computing Concepts",           "beginner", 25, 1, "Phase 1: Cloud Fundamentals",       ["Understand IaaS/PaaS/SaaS", "Explain cloud benefits"],          ["cloud computing", "IaaS", "PaaS", "SaaS", "shared responsibility"]),
    m(2,  "Azure Global Infrastructure",        "beginner", 25, 1, "Phase 1: Cloud Fundamentals",       ["Explain Azure regions", "Understand availability zones"],         ["azure regions", "availability zones", "geographies", "datacenters"]),
    m(3,  "Azure Portal and CLI",               "beginner", 20, 1, "Phase 1: Cloud Fundamentals",       ["Navigate Azure Portal", "Run basic CLI commands"],                ["azure portal", "azure CLI", "cloud shell", "azure PowerShell"]),
    m(4,  "Subscriptions and Resource Groups",  "beginner", 20, 1, "Phase 1: Cloud Fundamentals",       ["Create resource groups", "Understand subscription hierarchy"],     ["resource groups", "subscriptions", "management groups", "azure hierarchy"]),
    m(5,  "Azure Resource Manager (ARM)",       "beginner", 25, 1, "Phase 1: Cloud Fundamentals",       ["Understand ARM templates", "Deploy via ARM"],                      ["ARM", "resource manager", "templates", "infrastructure as code"]),
    m(6,  "Azure Pricing and Cost Management",  "beginner", 20, 1, "Phase 1: Cloud Fundamentals",       ["Estimate costs", "Use Azure Cost Management"],                     ["azure pricing", "cost management", "TCO calculator", "reserved instances"]),
    m(7,  "AZ-900 Exam Prep — Capstone",        "beginner", 45, 1, "Phase 1: Cloud Fundamentals",       ["Review AZ-900 topics", "Practice exam questions"],                 ["AZ-900", "azure fundamentals exam", "certification prep"], milestone=True),

    # Phase 2: Compute (beginner → intermediate)
    m(8,  "Azure Virtual Machines",             "beginner",      40, 2, "Phase 2: Compute",              ["Deploy Windows/Linux VMs", "Configure VM sizes"],                  ["virtual machines", "VM sizes", "IaaS", "compute"]),
    m(9,  "VM Availability & Scale Sets",       "intermediate",  35, 2, "Phase 2: Compute",              ["Configure availability sets", "Deploy VMSS"],                      ["availability sets", "VMSS", "scale sets", "HA"]),
    m(10, "Azure App Service",                  "intermediate",  35, 2, "Phase 2: Compute",              ["Deploy web apps", "Configure App Service plans"],                  ["app service", "web apps", "deployment slots", "PaaS"]),
    m(11, "Azure Functions",                    "intermediate",  30, 2, "Phase 2: Compute",              ["Build serverless functions", "Use triggers and bindings"],         ["azure functions", "serverless", "triggers", "event-driven"]),
    m(12, "Azure Container Instances",          "intermediate",  30, 2, "Phase 2: Compute",              ["Run containers without orchestration", "Use ACI"],                 ["container instances", "ACI", "Docker", "containers"]),
    m(13, "Azure Kubernetes Service",           "advanced",      55, 2, "Phase 2: Compute",              ["Deploy AKS clusters", "Manage pods and services"],                 ["AKS", "kubernetes", "pods", "deployments", "services"]),
    m(14, "Compute Architecture Project",       "advanced",      60, 2, "Phase 2: Compute",              ["Design a multi-tier compute architecture"],                        ["compute design", "architecture", "scalability"], milestone=True),

    # Phase 3: Networking
    m(15, "Azure Virtual Networks",             "beginner",      35, 3, "Phase 3: Networking",           ["Create VNets", "Configure subnets"],                               ["VNet", "subnets", "IP addressing", "CIDR"]),
    m(16, "Network Security Groups",            "beginner",      30, 3, "Phase 3: Networking",           ["Configure NSG rules", "Understand traffic filtering"],             ["NSG", "network security", "inbound rules", "outbound rules"]),
    m(17, "Azure Load Balancer",                "intermediate",  35, 3, "Phase 3: Networking",           ["Deploy Azure Load Balancer", "Configure health probes"],           ["load balancer", "layer 4", "health probes", "backend pool"]),
    m(18, "Azure Application Gateway",          "intermediate",  35, 3, "Phase 3: Networking",           ["Configure WAF", "Use URL-based routing"],                         ["application gateway", "WAF", "SSL termination", "layer 7"]),
    m(19, "VNet Peering and VPN Gateway",       "intermediate",  40, 3, "Phase 3: Networking",           ["Peer VNets", "Configure site-to-site VPN"],                       ["VNet peering", "VPN gateway", "site-to-site", "hub-spoke"]),
    m(20, "Azure DNS",                          "intermediate",  25, 3, "Phase 3: Networking",           ["Configure Azure DNS zones", "Understand private DNS"],            ["azure DNS", "DNS zones", "name resolution", "private DNS"]),
    m(21, "Private Endpoints and Service Endpoints","advanced",  40, 3, "Phase 3: Networking",           ["Use private endpoints", "Restrict service access"],               ["private endpoint", "service endpoint", "private link"]),
    m(22, "ExpressRoute",                       "advanced",      45, 3, "Phase 3: Networking",           ["Understand ExpressRoute circuits", "Plan hybrid connectivity"],   ["ExpressRoute", "dedicated connectivity", "BGP", "peering"]),
    m(23, "Networking Architecture Project",    "advanced",      60, 3, "Phase 3: Networking",           ["Design hub-spoke network topology"],                              ["hub-spoke", "network design", "enterprise networking"], milestone=True),

    # Phase 4: Storage
    m(24, "Azure Storage Account",              "beginner",      30, 4, "Phase 4: Storage",              ["Create storage accounts", "Understand redundancy options"],        ["storage account", "LRS", "GRS", "ZRS", "redundancy"]),
    m(25, "Azure Blob Storage",                 "beginner",      35, 4, "Phase 4: Storage",              ["Upload blobs", "Configure access tiers"],                         ["blob storage", "hot tier", "cool tier", "archive tier"]),
    m(26, "Azure Files and File Sync",          "intermediate",  30, 4, "Phase 4: Storage",              ["Create file shares", "Configure Azure File Sync"],               ["azure files", "SMB", "file sync", "hybrid storage"]),
    m(27, "Azure Data Lake Storage Gen2",       "intermediate",  35, 4, "Phase 4: Storage",              ["Set up ADLS Gen2", "Manage ACLs"],                               ["ADLS Gen2", "hierarchical namespace", "data lake", "ACL"]),
    m(28, "Storage Security and SAS",           "intermediate",  30, 4, "Phase 4: Storage",              ["Generate SAS tokens", "Configure encryption"],                   ["SAS token", "shared access signature", "encryption", "RBAC"]),

    # Phase 5: Identity & Security
    m(29, "Microsoft Entra ID (Azure AD)",      "beginner",      35, 5, "Phase 5: Identity & Security",  ["Manage users and groups", "Understand directory roles"],          ["entra id", "azure AD", "users", "groups", "directory"]),
    m(30, "Role-Based Access Control (RBAC)",   "intermediate",  35, 5, "Phase 5: Identity & Security",  ["Assign roles", "Create custom roles"],                            ["RBAC", "role assignment", "custom roles", "scope"]),
    m(31, "Managed Identities",                 "intermediate",  30, 5, "Phase 5: Identity & Security",  ["Use system-assigned managed identities", "Access Key Vault"],    ["managed identity", "system-assigned", "user-assigned", "MSI"]),
    m(32, "Azure Key Vault",                    "intermediate",  35, 5, "Phase 5: Identity & Security",  ["Store secrets and keys", "Configure access policies"],            ["key vault", "secrets", "certificates", "encryption keys"]),
    m(33, "Microsoft Defender for Cloud",       "intermediate",  40, 5, "Phase 5: Identity & Security",  ["Assess security posture", "Configure security policies"],        ["defender for cloud", "security score", "recommendations", "CSPM"]),
    m(34, "Azure Policy and Blueprints",        "advanced",      35, 5, "Phase 5: Identity & Security",  ["Create policies", "Enforce governance"],                          ["azure policy", "blueprints", "governance", "compliance"]),
    m(35, "Zero Trust Architecture",            "advanced",      40, 5, "Phase 5: Identity & Security",  ["Apply Zero Trust principles", "Implement conditional access"],   ["zero trust", "conditional access", "MFA", "identity protection"]),
    m(36, "Security Architecture Project",      "advanced",      60, 5, "Phase 5: Identity & Security",  ["Design end-to-end security for a workload"],                      ["security design", "defence in depth", "enterprise security"], milestone=True),

    # Phase 6: Monitoring & Operations
    m(37, "Azure Monitor",                      "intermediate",  35, 6, "Phase 6: Monitoring",           ["Configure metrics and logs", "Create dashboards"],               ["azure monitor", "metrics", "logs", "workbooks"]),
    m(38, "Log Analytics Workspace",            "intermediate",  35, 6, "Phase 6: Monitoring",           ["Query logs with KQL", "Configure data collection"],              ["log analytics", "KQL", "workspace", "queries"]),
    m(39, "Application Insights",               "intermediate",  35, 6, "Phase 6: Monitoring",           ["Instrument applications", "Analyse telemetry"],                  ["application insights", "APM", "telemetry", "distributed tracing"]),
    m(40, "Azure Alerts and Action Groups",     "intermediate",  25, 6, "Phase 6: Monitoring",           ["Create metric alerts", "Configure action groups"],               ["alerts", "action groups", "notification", "automation"]),
    m(41, "Azure Automation and Update Mgmt",   "advanced",      30, 6, "Phase 6: Monitoring",           ["Automate operational tasks", "Manage VM updates"],               ["azure automation", "update management", "runbooks", "PowerShell"]),

    # Phase 7: Architecture & Expert Topics
    m(42, "Well-Architected Framework",         "advanced",      40, 7, "Phase 7: Architecture",         ["Apply 5 pillars", "Conduct workload reviews"],                   ["well-architected", "reliability", "security", "cost", "operational excellence"]),
    m(43, "Landing Zones and Cloud Adoption",   "advanced",      45, 7, "Phase 7: Architecture",         ["Design landing zones", "Understand CAF"],                       ["landing zone", "CAF", "cloud adoption framework", "governance"]),
    m(44, "Azure DevOps Pipelines",             "advanced",      45, 7, "Phase 7: Architecture",         ["Build CI/CD pipelines", "Use YAML pipelines"],                  ["azure devops", "CI/CD", "YAML pipeline", "release gates"]),
    m(45, "Infrastructure as Code with Bicep",  "advanced",      40, 7, "Phase 7: Architecture",         ["Write Bicep templates", "Deploy to Azure"],                     ["bicep", "IaC", "ARM templates", "infrastructure as code"]),
    m(46, "Multi-Region Architecture",          "expert",        50, 7, "Phase 7: Architecture",         ["Design active-active patterns", "Configure Traffic Manager"],   ["multi-region", "active-active", "traffic manager", "disaster recovery"]),
    m(47, "Azure Cost Optimisation Strategies", "expert",        40, 7, "Phase 7: Architecture",         ["Apply FinOps practices", "Rightsize resources"],                ["finops", "cost optimisation", "reserved instances", "spot VMs"]),
    m(48, "Event-Driven Architectures",         "expert",        45, 7, "Phase 7: Architecture",         ["Use Event Grid and Service Bus", "Design async patterns"],      ["event grid", "service bus", "event hub", "messaging patterns"]),
    m(49, "Azure API Management",               "expert",        40, 7, "Phase 7: Architecture",         ["Publish and secure APIs", "Configure policies"],                ["APIM", "API gateway", "policies", "developer portal"]),
    m(50, "Enterprise Architecture Capstone",   "expert",        90, 7, "Phase 7: Architecture",         ["Design a complete enterprise Azure solution"],                  ["enterprise architecture", "design review", "capstone"], milestone=True),

    # Phase 8: Certifications
    m(51, "AZ-104 Administrator Exam Prep",     "advanced",      50, 8, "Phase 8: Certification",        ["Review AZ-104 objectives", "Practice questions"],               ["AZ-104", "azure administrator", "certification", "exam prep"]),
    m(52, "AZ-305 Solutions Architect Prep",    "expert",        50, 8, "Phase 8: Certification",        ["Review AZ-305 objectives", "Practice case studies"],            ["AZ-305", "solutions architect", "certification", "expert"]),
]


# ── Microsoft Fabric Track — 55 modules ───────────────────────────────────────

_FABRIC = [
    # Phase 1: Foundations
    m(1,  "Microsoft Fabric Overview",          "beginner",      25, 1, "Phase 1: Foundations",          ["Understand Fabric architecture", "Navigate the portal"],         ["microsoft fabric", "unified analytics", "SaaS", "workspaces"]),
    m(2,  "Fabric Licensing and Capacity",      "beginner",      20, 1, "Phase 1: Foundations",          ["Understand F-SKUs", "Configure capacity pools"],                  ["fabric capacity", "F-SKU", "licensing", "cost management"]),
    m(3,  "OneLake Architecture",               "beginner",      30, 1, "Phase 1: Foundations",          ["Understand OneLake", "Manage shortcuts and mounts"],              ["OneLake", "delta parquet", "shortcuts", "data lake"]),
    m(4,  "Fabric Workspaces",                  "beginner",      25, 1, "Phase 1: Foundations",          ["Create and manage workspaces", "Configure roles"],                ["workspaces", "roles", "access control", "items"]),
    m(5,  "Fabric Security Model",              "intermediate",  30, 1, "Phase 1: Foundations",          ["Understand row-level security", "Configure sensitivity labels"],  ["security", "RLS", "sensitivity labels", "data governance"]),

    # Phase 2: Lakehouse
    m(6,  "Lakehouse Concepts",                 "beginner",      30, 2, "Phase 2: Lakehouse",            ["Understand lakehouse architecture", "Compare to warehouse"],      ["lakehouse", "delta lake", "bronze silver gold", "medallion"]),
    m(7,  "Creating and Loading Lakehouses",    "beginner",      35, 2, "Phase 2: Lakehouse",            ["Create lakehouses", "Load data with pipelines and notebooks"],   ["lakehouse creation", "data loading", "files section", "tables section"]),
    m(8,  "Delta Tables and ACID Transactions", "intermediate",  40, 2, "Phase 2: Lakehouse",            ["Use Delta format", "Run MERGE and UPDATE"],                      ["delta lake", "ACID", "MERGE", "time travel", "versioning"]),
    m(9,  "Medallion Architecture in Fabric",   "intermediate",  45, 2, "Phase 2: Lakehouse",            ["Implement Bronze/Silver/Gold layers", "Apply data quality"],     ["medallion", "bronze", "silver", "gold", "data quality"]),
    m(10, "Lakehouse with SQL Analytics",       "intermediate",  35, 2, "Phase 2: Lakehouse",            ["Use SQL endpoint", "Query delta tables with T-SQL"],             ["SQL endpoint", "T-SQL", "lakehouse queries", "automatic schema"]),
    m(11, "Lakehouse Architecture Project",     "intermediate",  75, 2, "Phase 2: Lakehouse",            ["Build a complete medallion lakehouse solution"],                  ["lakehouse design", "capstone", "data engineering"], milestone=True),

    # Phase 3: Data Engineering
    m(12, "Fabric Data Factory Pipelines",      "beginner",      35, 3, "Phase 3: Data Engineering",     ["Create pipelines", "Use Copy Data activity"],                    ["data factory", "pipelines", "Copy Data", "activities"]),
    m(13, "Dataflows Gen2",                     "intermediate",  35, 3, "Phase 3: Data Engineering",     ["Build Dataflows Gen2", "Use Power Query transformations"],       ["dataflow gen2", "power query", "M language", "transformations"]),
    m(14, "Spark Notebooks",                    "intermediate",  45, 3, "Phase 3: Data Engineering",     ["Write PySpark code", "Use Fabric notebooks"],                    ["spark", "pyspark", "notebooks", "magic commands"]),
    m(15, "Spark Pools and Configuration",      "intermediate",  30, 3, "Phase 3: Data Engineering",     ["Configure Spark pools", "Optimise Spark jobs"],                  ["spark pools", "node types", "autoscale", "configuration"]),
    m(16, "Data Wrangler",                      "intermediate",  25, 3, "Phase 3: Data Engineering",     ["Use Data Wrangler for EDA", "Generate PySpark code"],            ["data wrangler", "EDA", "pandas", "code generation"]),
    m(17, "Fabric Pipelines — Advanced",        "advanced",      45, 3, "Phase 3: Data Engineering",     ["Use ForEach and conditional activities", "Handle errors"],        ["pipeline orchestration", "foreach", "error handling", "variables"]),
    m(18, "Data Engineering Capstone",          "advanced",      90, 3, "Phase 3: Data Engineering",     ["Build end-to-end pipeline from source to Gold layer"],           ["data pipeline", "capstone", "end-to-end"], milestone=True),

    # Phase 4: Data Warehouse
    m(19, "Fabric Warehouse Concepts",          "beginner",      30, 4, "Phase 4: Data Warehouse",       ["Understand Fabric Warehouse vs Lakehouse"],                      ["warehouse", "lakehouse", "comparison", "synapse"]),
    m(20, "Creating and Loading Warehouse",     "intermediate",  35, 4, "Phase 4: Data Warehouse",       ["Create warehouse", "Load with COPY INTO"],                       ["warehouse creation", "COPY INTO", "T-SQL loading"]),
    m(21, "T-SQL in Fabric Warehouse",          "intermediate",  40, 4, "Phase 4: Data Warehouse",       ["Write complex T-SQL", "Use stored procedures"],                  ["T-SQL", "stored procedures", "views", "functions"]),
    m(22, "Star Schema Design",                 "intermediate",  40, 4, "Phase 4: Data Warehouse",       ["Design fact and dimension tables", "Implement slowly changing dims"],["star schema", "fact tables", "dimensions", "SCD"]),
    m(23, "Warehouse Performance Tuning",       "advanced",      40, 4, "Phase 4: Data Warehouse",       ["Analyse query performance", "Optimise with statistics"],        ["query performance", "statistics", "distribution", "indexes"]),
    m(24, "Cross-Database Queries",             "advanced",      30, 4, "Phase 4: Data Warehouse",       ["Query across warehouse and lakehouse", "Use shortcuts"],         ["cross-database", "shortcuts", "three-part naming"]),

    # Phase 5: Real-Time Intelligence
    m(25, "Eventstream Fundamentals",           "beginner",      30, 5, "Phase 5: Real-Time Intelligence", ["Create Eventstreams", "Connect streaming sources"],             ["eventstream", "kafka", "event hub", "streaming sources"]),
    m(26, "KQL Database",                       "intermediate",  35, 5, "Phase 5: Real-Time Intelligence", ["Create KQL databases", "Ingest streaming data"],               ["KQL database", "kusto", "ingestion", "real-time"]),
    m(27, "KQL Query Language",                 "intermediate",  45, 5, "Phase 5: Real-Time Intelligence", ["Write KQL queries", "Use aggregations and joins"],             ["KQL", "kusto query language", "where", "summarize", "join"]),
    m(28, "Real-Time Dashboards",               "intermediate",  35, 5, "Phase 5: Real-Time Intelligence", ["Build real-time dashboards", "Configure auto-refresh"],        ["real-time dashboard", "KQL visuals", "auto-refresh", "tiles"]),
    m(29, "Activator (Data Activator)",         "advanced",      35, 5, "Phase 5: Real-Time Intelligence", ["Create triggers on streaming data", "Automate actions"],       ["data activator", "reflex", "triggers", "automation"]),
    m(30, "Streaming Architecture Project",     "advanced",      90, 5, "Phase 5: Real-Time Intelligence", ["Build an IoT streaming analytics solution"],                   ["streaming architecture", "IoT", "real-time analytics"], milestone=True),

    # Phase 6: Power BI in Fabric
    m(31, "Semantic Models in Fabric",          "intermediate",  40, 6, "Phase 6: Power BI in Fabric",   ["Create semantic models", "Define relationships and measures"],   ["semantic model", "dataset", "relationships", "DAX"]),
    m(32, "Direct Lake Mode",                   "intermediate",  35, 6, "Phase 6: Power BI in Fabric",   ["Understand Direct Lake", "Compare to DirectQuery and Import"],  ["direct lake", "framing", "fallback", "performance"]),
    m(33, "Power BI Reports and Dashboards",    "intermediate",  35, 6, "Phase 6: Power BI in Fabric",   ["Build reports in Fabric", "Create pinned dashboards"],           ["power bi reports", "dashboards", "visuals", "slicers"]),
    m(34, "Deployment Pipelines",               "advanced",      30, 6, "Phase 6: Power BI in Fabric",   ["Manage dev/test/prod deployment", "Configure rules"],            ["deployment pipelines", "ALM", "CI/CD", "environment rules"]),

    # Phase 7: Data Science
    m(35, "Data Science in Fabric Overview",    "intermediate",  30, 7, "Phase 7: Data Science",         ["Understand data science tools in Fabric"],                       ["data science", "ML", "notebooks", "experiments"]),
    m(36, "ML Experiments with MLflow",         "intermediate",  45, 7, "Phase 7: Data Science",         ["Track experiments", "Log metrics and parameters"],              ["MLflow", "experiments", "tracking", "runs"]),
    m(37, "Model Training in Fabric",           "advanced",      50, 7, "Phase 7: Data Science",         ["Train scikit-learn and Spark models", "Register models"],        ["model training", "scikit-learn", "spark ML", "model registry"]),
    m(38, "Fabric Copilot for Data Science",    "advanced",      30, 7, "Phase 7: Data Science",         ["Use AI-assisted notebook features", "Generate ML code"],         ["copilot", "AI assistance", "code generation", "Fabric AI"]),

    # Phase 8: Administration & Governance
    m(39, "Fabric Administration",              "advanced",      35, 8, "Phase 8: Administration",       ["Manage tenant settings", "Configure capacity"],                  ["fabric admin", "tenant settings", "capacity management"]),
    m(40, "Microsoft Purview Integration",      "advanced",      35, 8, "Phase 8: Administration",       ["Catalog Fabric assets", "Apply data classification"],           ["purview", "data catalog", "lineage", "governance"]),
    m(41, "Fabric Monitoring Hub",              "advanced",      25, 8, "Phase 8: Administration",       ["Monitor activity and capacity", "Analyse usage"],               ["monitoring hub", "capacity usage", "activity tracking"]),
    m(42, "Fabric Certification Prep (DP-600)", "advanced",      55, 8, "Phase 8: Administration",       ["Review DP-600 objectives", "Practice exam questions"],           ["DP-600", "fabric analytics engineer", "certification"], milestone=True),

    # Phase 9: Advanced Integration
    m(43, "Fabric REST APIs",                   "expert",        40, 9, "Phase 9: Advanced Integration", ["Automate Fabric with APIs", "Build CI/CD for Fabric"],           ["fabric API", "REST", "automation", "CI/CD"]),
    m(44, "Git Integration in Fabric",          "expert",        35, 9, "Phase 9: Advanced Integration", ["Connect workspaces to Git", "Manage branches and PRs"],         ["git integration", "version control", "branching", "DevOps"]),
    m(45, "Fabric + Azure Synapse Integration", "expert",        40, 9, "Phase 9: Advanced Integration", ["Move between Fabric and Synapse", "Migrate Synapse workloads"],  ["synapse migration", "interoperability", "hybrid analytics"]),
    m(46, "Multi-Workspace Architecture",       "expert",        45, 9, "Phase 9: Advanced Integration", ["Design enterprise workspace strategy", "Govern at scale"],       ["enterprise architecture", "workspace design", "governance at scale"]),
    m(47, "Fabric Enterprise Architecture",     "expert",        90, 9, "Phase 9: Advanced Integration", ["Design complete enterprise Fabric solution"],                    ["enterprise Fabric", "architecture", "capstone"], milestone=True),

    # Phase 10: Expert Scenarios
    m(48, "Cost Optimisation in Fabric",        "expert",        35, 10, "Phase 10: Expert Scenarios",   ["Analyse Fabric costs", "Optimise capacity consumption"],        ["cost optimisation", "capacity units", "billing", "efficiency"]),
    m(49, "High Availability Patterns",         "expert",        40, 10, "Phase 10: Expert Scenarios",   ["Design for resilience", "Handle failures in pipelines"],        ["high availability", "resilience", "fault tolerance", "retry"]),
    m(50, "Fabric for Large Enterprises",       "expert",        45, 10, "Phase 10: Expert Scenarios",   ["Scale Fabric for enterprise", "Multi-geography considerations"],["enterprise scale", "multi-geo", "large-scale analytics"]),
    m(51, "Performance Engineering in Fabric",  "expert",        50, 10, "Phase 10: Expert Scenarios",   ["Profile and tune Spark jobs", "Optimise lakehouse queries"],    ["performance tuning", "spark optimisation", "query profiling"]),
    m(52, "Fabric Security Deep Dive",          "expert",        45, 10, "Phase 10: Expert Scenarios",   ["Implement end-to-end data security", "Audit and compliance"],   ["data security", "encryption", "compliance", "audit logs"]),
    m(53, "AI-Powered Analytics in Fabric",     "expert",        50, 10, "Phase 10: Expert Scenarios",   ["Integrate Copilot and AI functions", "Build AI-enriched reports"],["Fabric Copilot", "AI insights", "AI functions", "Azure OpenAI"]),
    m(54, "Fabric Migration from Legacy DW",    "expert",        55, 10, "Phase 10: Expert Scenarios",   ["Migrate from SQL Server/SSAS", "Validate migrated workloads"],  ["migration", "legacy DW", "SSAS", "SQL Server migration"]),
    m(55, "Master Architect Challenge",         "expert",        120, 10, "Phase 10: Expert Scenarios",  ["Complete end-to-end Fabric analytics platform design"],          ["master architect", "final capstone", "enterprise design"], milestone=True),
]


# ── Azure Data Engineering Track — 60 modules ─────────────────────────────────

_DATA_ENG = [
    m(1,  "Data Engineering Fundamentals",      "beginner",     25, 1, "Phase 1: Foundations",           ["Understand data engineer role", "Map Azure data services"],      ["data engineering", "DP-203", "azure data", "roles"]),
    m(2,  "Data Storage Concepts",              "beginner",     25, 1, "Phase 1: Foundations",           ["Compare structured vs unstructured", "Choose storage type"],      ["storage types", "structured", "unstructured", "semi-structured"]),
    m(3,  "ADLS Gen2 Setup",                    "beginner",     30, 1, "Phase 1: Foundations",           ["Create ADLS Gen2", "Configure hierarchical namespace"],           ["ADLS Gen2", "hierarchical namespace", "ACLs", "data lake"]),
    m(4,  "ADLS Gen2 Security",                 "intermediate", 35, 1, "Phase 1: Foundations",           ["Configure POSIX ACLs", "Use managed identities with ADLS"],      ["ACL", "RBAC", "managed identity", "data lake security"]),
    m(5,  "Azure Data Factory — Basics",        "beginner",     35, 2, "Phase 2: Data Factory",          ["Create ADF pipelines", "Use Copy Data activity"],                ["ADF", "pipelines", "copy data", "linked services"]),
    m(6,  "ADF Linked Services and Datasets",   "beginner",     30, 2, "Phase 2: Data Factory",          ["Configure linked services", "Define datasets"],                  ["linked services", "datasets", "connectors", "connection strings"]),
    m(7,  "ADF Control Flow Activities",        "intermediate", 40, 2, "Phase 2: Data Factory",          ["Use ForEach, If, Until", "Chain activities with dependencies"],  ["ForEach", "If Condition", "pipeline control flow", "chaining"]),
    m(8,  "ADF Data Flows",                     "intermediate", 45, 2, "Phase 2: Data Factory",          ["Build mapping data flows", "Apply transformations visually"],    ["mapping data flow", "data transformations", "no-code ETL"]),
    m(9,  "ADF Triggers and Scheduling",        "intermediate", 30, 2, "Phase 2: Data Factory",          ["Schedule pipelines", "Use event-based triggers"],                ["schedule trigger", "tumbling window", "event trigger"]),
    m(10, "ADF Monitoring and Debugging",       "intermediate", 30, 2, "Phase 2: Data Factory",          ["Debug pipeline runs", "Analyse activity failures"],              ["pipeline monitoring", "debug mode", "activity runs", "error handling"]),
    m(11, "ADF Integration Runtime",            "advanced",     35, 2, "Phase 2: Data Factory",          ["Configure self-hosted IR", "Use Azure IR"],                      ["integration runtime", "self-hosted IR", "SHIR", "on-premises"]),
    m(12, "ADF Capstone",                       "advanced",     75, 2, "Phase 2: Data Factory",          ["Build complete ETL pipeline with ADF"],                          ["ADF ETL", "capstone", "pipeline design"], milestone=True),
    m(13, "Apache Spark Architecture",          "beginner",     35, 3, "Phase 3: Apache Spark",          ["Understand RDD vs DataFrame", "Explain lazy evaluation"],        ["spark", "RDD", "DataFrame", "lazy evaluation", "DAG"]),
    m(14, "PySpark DataFrames",                 "intermediate", 45, 3, "Phase 3: Apache Spark",          ["Transform data with PySpark", "Use filter, select, groupBy"],    ["pyspark", "DataFrame API", "filter", "groupby", "aggregation"]),
    m(15, "Spark SQL",                          "intermediate", 40, 3, "Phase 3: Apache Spark",          ["Write Spark SQL queries", "Register temp views"],                ["spark SQL", "temp views", "SQL on DataFrames", "catalog"]),
    m(16, "Spark Streaming",                    "intermediate", 45, 3, "Phase 3: Apache Spark",          ["Read from Kafka with Spark", "Apply windowed aggregations"],     ["spark streaming", "structured streaming", "Kafka", "watermarks"]),
    m(17, "Spark Performance Tuning",           "advanced",     50, 3, "Phase 3: Apache Spark",          ["Partition data correctly", "Use caching and broadcast joins"],  ["partitioning", "caching", "broadcast join", "skew", "AQE"]),
    m(18, "Delta Lake Deep Dive",               "intermediate", 45, 4, "Phase 4: Delta Lake",            ["Use MERGE", "Time travel queries", "Vacuum and optimize"],       ["delta lake", "MERGE", "time travel", "vacuum", "Z-ordering"]),
    m(19, "Delta Live Tables (DLT)",            "advanced",     50, 4, "Phase 4: Delta Lake",            ["Declare DLT pipelines", "Use expectations for quality"],        ["DLT", "delta live tables", "expectations", "streaming tables"]),
    m(20, "Unity Catalog",                      "advanced",     45, 4, "Phase 4: Delta Lake",            ["Set up Unity Catalog", "Manage data governance"],               ["unity catalog", "metastore", "governance", "fine-grained access"]),
    m(21, "Synapse Analytics Workspace",        "beginner",     35, 5, "Phase 5: Azure Synapse",         ["Navigate Synapse workspace", "Understand components"],           ["synapse analytics", "workspace", "linked services", "integration"]),
    m(22, "Synapse Dedicated SQL Pool",         "intermediate", 45, 5, "Phase 5: Azure Synapse",         ["Create dedicated SQL pool", "Load data with COPY INTO"],        ["dedicated SQL pool", "DW units", "distributions", "COPY INTO"]),
    m(23, "Synapse Serverless SQL Pool",        "intermediate", 35, 5, "Phase 5: Azure Synapse",         ["Query files with serverless SQL", "Create external tables"],     ["serverless SQL", "OPENROWSET", "external tables", "Delta"]),
    m(24, "Synapse Spark Pool",                 "intermediate", 40, 5, "Phase 5: Azure Synapse",         ["Run PySpark notebooks in Synapse", "Connect to ADLS"],          ["synapse spark", "notebooks", "linked services", "ADLS"]),
    m(25, "Azure Databricks Setup",             "beginner",     30, 6, "Phase 6: Databricks",            ["Create Databricks workspace", "Launch clusters"],               ["databricks", "workspace", "clusters", "compute"]),
    m(26, "Databricks Notebooks",               "beginner",     30, 6, "Phase 6: Databricks",            ["Write Python/SQL notebooks", "Collaborate with teammates"],     ["notebooks", "Python", "SQL", "collaboration"]),
    m(27, "Databricks Delta Lake",              "intermediate", 45, 6, "Phase 6: Databricks",            ["Use Delta on Databricks", "Apply MERGE and CDC patterns"],      ["delta lake", "CDC", "MERGE", "streaming"]),
    m(28, "Databricks Workflows",               "advanced",     40, 6, "Phase 6: Databricks",            ["Orchestrate notebooks with Workflows", "Handle retries"],       ["databricks workflows", "job orchestration", "retries", "DLT"]),
    m(29, "Event Hubs and Kafka",               "intermediate", 35, 7, "Phase 7: Streaming",             ["Ingest events with Event Hubs", "Use Kafka protocol"],          ["event hubs", "kafka", "partitions", "consumer groups"]),
    m(30, "Azure Stream Analytics",             "intermediate", 40, 7, "Phase 7: Streaming",             ["Write SAQL queries", "Handle tumbling windows"],                ["stream analytics", "SAQL", "tumbling window", "hopping window"]),
    m(31, "Streaming Architecture Patterns",    "advanced",     45, 7, "Phase 7: Streaming",             ["Choose Lambda vs Kappa", "Design streaming pipelines"],         ["lambda architecture", "kappa architecture", "streaming design"]),
    m(32, "IoT Hub and Streaming Pipeline",     "advanced",     50, 7, "Phase 7: Streaming",             ["Ingest IoT telemetry", "Route to storage and analytics"],       ["IoT hub", "device telemetry", "message routing", "time series"]),
    m(33, "Streaming Capstone",                 "advanced",     90, 7, "Phase 7: Streaming",             ["Build end-to-end streaming pipeline from IoT to dashboard"],    ["streaming capstone", "IoT analytics", "real-time"], milestone=True),
    m(34, "Data Quality Fundamentals",          "intermediate", 30, 8, "Phase 8: Data Quality",          ["Understand data quality dimensions", "Profile data"],           ["data quality", "completeness", "accuracy", "profiling"]),
    m(35, "Great Expectations",                 "advanced",     40, 8, "Phase 8: Data Quality",          ["Write data expectations", "Validate pipeline outputs"],         ["great expectations", "data validation", "expectations", "checkpoints"]),
    m(36, "Data Contracts",                     "advanced",     35, 8, "Phase 8: Data Quality",          ["Define data contracts", "Enforce schema agreements"],           ["data contracts", "schema enforcement", "producer-consumer", "SLA"]),
    m(37, "Microsoft Purview for Data Eng",     "advanced",     35, 8, "Phase 8: Data Quality",          ["Catalog data assets", "Track lineage"],                         ["purview", "data catalog", "lineage", "classification"]),
    m(38, "dbt (Data Build Tool) Basics",       "advanced",     45, 9, "Phase 9: Modern Stack",          ["Write dbt models", "Use Jinja templating"],                     ["dbt", "data build tool", "models", "tests", "sources"]),
    m(39, "dbt Advanced Patterns",              "expert",       50, 9, "Phase 9: Modern Stack",          ["Use incremental models", "Apply macros and packages"],          ["dbt incremental", "macros", "packages", "advanced dbt"]),
    m(40, "Medallion Architecture Design",      "advanced",     50, 9, "Phase 9: Modern Stack",          ["Design Bronze/Silver/Gold layers", "Apply best practices"],     ["medallion", "bronze", "silver", "gold", "lakehouse design"]),
    m(41, "Data Mesh Architecture",             "expert",       50, 9, "Phase 9: Modern Stack",          ["Apply data mesh principles", "Domain-oriented ownership"],      ["data mesh", "domain ownership", "data products", "self-serve"]),
    m(42, "Data Governance Framework",          "expert",       45, 10, "Phase 10: Enterprise",          ["Design enterprise governance", "Align with regulatory needs"],  ["governance framework", "data stewardship", "GDPR", "compliance"]),
    m(43, "DataOps and CI/CD for Data",         "expert",       50, 10, "Phase 10: Enterprise",          ["Apply DevOps to data pipelines", "Automate testing and deploy"], ["DataOps", "CI/CD", "automated testing", "git workflows"]),
    m(44, "Cost Optimisation for Data Platforms","expert",      40, 10, "Phase 10: Enterprise",          ["Rightsize Databricks clusters", "Optimise ADF costs"],          ["cost optimisation", "spark tuning", "ADF cost", "efficiency"]),
    m(45, "Multi-Cloud Data Architecture",      "expert",       50, 10, "Phase 10: Enterprise",          ["Design cloud-agnostic pipelines", "Portability patterns"],      ["multi-cloud", "cloud-agnostic", "Iceberg", "Apache Arrow"]),
    m(46, "DP-203 Exam Prep",                   "advanced",     55, 10, "Phase 10: Enterprise",          ["Review DP-203 objectives", "Practice exam scenarios"],           ["DP-203", "data engineer associate", "certification"], milestone=True),
    m(47, "Real-World ETL Case Study — Retail", "advanced",     60, 11, "Phase 11: Case Studies",        ["Analyse retail analytics pipeline", "Apply best practices"],    ["retail analytics", "case study", "ETL patterns"]),
    m(48, "Real-World Case Study — Finance",    "expert",       60, 11, "Phase 11: Case Studies",        ["Design compliant financial data platform", "Handle PII"],       ["financial data", "PII", "compliance", "BCBS 239"]),
    m(49, "Real-World Case Study — IoT",        "expert",       60, 11, "Phase 11: Case Studies",        ["Process 100M+ IoT events per day", "Design for scale"],         ["IoT scale", "high throughput", "time series", "edge computing"]),
    m(50, "Senior Data Engineer Interview Prep","expert",       55, 11, "Phase 11: Case Studies",        ["System design questions", "Coding challenges", "Trade-offs"],   ["interview prep", "system design", "data engineering interviews"]),
    m(51, "Pipeline Observability",             "expert",       40, 12, "Phase 12: Expert Topics",       ["Add observability to pipelines", "Track SLAs"],                  ["observability", "SLA tracking", "alerting", "pipeline health"]),
    m(52, "Schema Evolution Strategies",        "expert",       40, 12, "Phase 12: Expert Topics",       ["Handle schema changes safely", "Backward/forward compatibility"],["schema evolution", "backward compatibility", "Delta schema", "Avro"]),
    m(53, "Late Arriving Data Patterns",        "expert",       40, 12, "Phase 12: Expert Topics",       ["Handle late data in batch and stream", "Reprocess partitions"],  ["late data", "watermarking", "reprocessing", "backfill"]),
    m(54, "Data Platform Modernisation",        "expert",       50, 12, "Phase 12: Expert Topics",       ["Migrate legacy data warehouse to modern lakehouse"],             ["DW modernisation", "migration", "legacy systems", "lift and shift"]),
    m(55, "Data Engineering Master Project",    "expert",       120, 12, "Phase 12: Expert Topics",      ["Build production-grade, end-to-end data platform from scratch"], ["master project", "capstone", "full-stack data engineering"], milestone=True),
    m(56, "Incident Management for Data",       "expert",       35, 12, "Phase 12: Expert Topics",       ["Respond to data pipeline incidents", "RCA process"],            ["incident management", "RCA", "on-call", "SRE for data"]),
    m(57, "Change Data Capture (CDC)",          "advanced",     40, 12, "Phase 12: Expert Topics",       ["Use Debezium and ADF CDC", "Apply CDC with Delta Lake"],         ["CDC", "change data capture", "Debezium", "incremental load"]),
    m(58, "Slowly Changing Dimensions",         "intermediate", 35, 12, "Phase 12: Expert Topics",       ["Implement SCD Types 1,2,3", "Handle historisation"],             ["SCD", "type 1", "type 2", "type 3", "historisation"]),
    m(59, "Performance Benchmarking",           "expert",       45, 12, "Phase 12: Expert Topics",       ["Benchmark pipeline performance", "Compare compute options"],    ["benchmarking", "TPC-DS", "performance comparison"]),
    m(60, "Expert Capstone: Enterprise Data Platform","expert", 120, 12, "Phase 12: Expert Topics",      ["Design and present an enterprise data platform architecture"],   ["enterprise data platform", "architecture design", "capstone"], milestone=True),
]


# ── Power BI Track — 52 modules ───────────────────────────────────────────────

_POWER_BI = [
    m(1,  "Power BI Ecosystem Overview",        "beginner",     20, 1, "Phase 1: Foundations",           ["Understand Power BI components", "Desktop vs Service vs Mobile"],["power bi", "ecosystem", "desktop", "service", "mobile"]),
    m(2,  "Power BI Desktop Basics",            "beginner",     30, 1, "Phase 1: Foundations",           ["Navigate the interface", "Connect to Excel and CSV"],           ["power bi desktop", "interface", "Excel connection", "CSV"]),
    m(3,  "Connecting to Data Sources",         "beginner",     35, 1, "Phase 1: Foundations",           ["Connect to SQL, SharePoint, web sources"],                       ["data sources", "SQL Server", "SharePoint", "web connector"]),
    m(4,  "Power Query Fundamentals",           "beginner",     40, 2, "Phase 2: Power Query",           ["Remove columns", "Filter rows", "Change data types"],           ["power query", "M language", "applied steps", "query editor"]),
    m(5,  "Data Transformation Techniques",     "intermediate", 45, 2, "Phase 2: Power Query",           ["Pivot/unpivot", "Merge and append queries"],                    ["pivot", "unpivot", "merge queries", "append queries"]),
    m(6,  "M Language Deep Dive",               "intermediate", 50, 2, "Phase 2: Power Query",           ["Write custom M functions", "Use conditional expressions"],      ["M language", "custom functions", "List.Generate", "Table.AddColumn"]),
    m(7,  "Query Folding",                      "advanced",     35, 2, "Phase 2: Power Query",           ["Understand and optimise query folding"],                         ["query folding", "performance", "SQL pushdown", "native query"]),
    m(8,  "Data Modelling Concepts",            "beginner",     35, 3, "Phase 3: Data Modelling",        ["Understand star schema", "Avoid snowflake models"],              ["star schema", "fact table", "dimension", "data model"]),
    m(9,  "Relationships in Power BI",          "intermediate", 40, 3, "Phase 3: Data Modelling",        ["Configure cardinality", "Use bi-directional filters wisely"],    ["relationships", "cardinality", "cross-filter direction", "model"]),
    m(10, "Calculated Columns vs Measures",     "intermediate", 35, 3, "Phase 3: Data Modelling",        ["Understand computed context", "When to use each"],              ["calculated columns", "measures", "storage", "context"]),
    m(11, "Role-Playing Dimensions",            "advanced",     35, 3, "Phase 3: Data Modelling",        ["Use multiple date relationships", "USERELATIONSHIP"],           ["role-playing dimensions", "USERELATIONSHIP", "inactive relationship"]),
    m(12, "Many-to-Many Relationships",         "advanced",     40, 3, "Phase 3: Data Modelling",        ["Handle M:N relationships", "Bridge tables"],                    ["many-to-many", "bridge table", "M:N", "composite models"]),
    m(13, "DAX Fundamentals",                   "beginner",     45, 4, "Phase 4: DAX",                   ["Write SUM, COUNT, AVERAGE", "Basic CALCULATE usage"],           ["DAX", "SUM", "COUNT", "CALCULATE", "measures"]),
    m(14, "Filter Context and Row Context",     "intermediate", 50, 4, "Phase 4: DAX",                   ["Understand context transition", "Explain CALCULATE mechanism"],["filter context", "row context", "context transition", "CALCULATE"]),
    m(15, "Time Intelligence Functions",        "intermediate", 50, 4, "Phase 4: DAX",                   ["TOTALYTD, DATESYTD, SAMEPERIODLASTYEAR"],                       ["time intelligence", "YTD", "MTD", "SAMEPERIODLASTYEAR", "DATEADD"]),
    m(16, "CALCULATE and FILTER",               "intermediate", 45, 4, "Phase 4: DAX",                   ["Master CALCULATE", "Use ALL and REMOVEFILTERS"],                ["CALCULATE", "FILTER", "ALL", "REMOVEFILTERS", "ALLEXCEPT"]),
    m(17, "ITERATOR Functions",                 "advanced",     45, 4, "Phase 4: DAX",                   ["Use SUMX, AVERAGEX, RANKX"],                                    ["iterator functions", "SUMX", "AVERAGEX", "RANKX", "row context"]),
    m(18, "VARIABLES and RETURN",               "intermediate", 30, 4, "Phase 4: DAX",                   ["Use VAR for readability", "Debug with variables"],              ["VAR", "RETURN", "variables", "code readability"]),
    m(19, "Advanced DAX Patterns",              "advanced",     55, 4, "Phase 4: DAX",                   ["Implement ABC analysis", "Basket analysis", "Pareto"],          ["DAX patterns", "ABC analysis", "basket analysis", "Pareto"]),
    m(20, "DAX Optimisation",                   "advanced",     45, 4, "Phase 4: DAX",                   ["Use DAX Studio", "Analyse query plans"],                         ["DAX Studio", "query plan", "VertiPaq analyser", "optimisation"]),
    m(21, "DAX Capstone",                       "advanced",     60, 4, "Phase 4: DAX",                   ["Build complex KPI dashboard with advanced DAX"],                ["DAX capstone", "KPIs", "business metrics"], milestone=True),
    m(22, "Visual Design Principles",           "beginner",     30, 5, "Phase 5: Visualisations",        ["Choose the right chart", "Apply design best practices"],        ["chart selection", "UX design", "colour theory", "accessibility"]),
    m(23, "Report Layout and Navigation",       "intermediate", 35, 5, "Phase 5: Visualisations",        ["Design report pages", "Add buttons and bookmarks"],             ["report layout", "bookmarks", "drill-through", "navigation"]),
    m(24, "Custom Visuals",                     "intermediate", 35, 5, "Phase 5: Visualisations",        ["Use AppSource visuals", "Evaluate custom visual quality"],      ["custom visuals", "AppSource", "charticulator", "Deneb"]),
    m(25, "Advanced Interactivity",             "advanced",     40, 5, "Phase 5: Visualisations",        ["Cross-filtering, drill-through, Q&A"],                          ["cross-filter", "drill-through", "Q&A", "decomposition tree"]),
    m(26, "Accessibility in Power BI",          "intermediate", 25, 5, "Phase 5: Visualisations",        ["Apply WCAG to reports", "Configure alt text"],                  ["accessibility", "WCAG", "screen reader", "alt text", "tab order"]),
    m(27, "Power BI Service",                   "beginner",     30, 6, "Phase 6: Service & Sharing",     ["Publish reports", "Share dashboards"],                          ["power bi service", "publish", "workspace", "share"]),
    m(28, "Row-Level Security",                 "intermediate", 40, 6, "Phase 6: Service & Sharing",     ["Define static and dynamic RLS", "Test roles"],                  ["RLS", "row-level security", "USERPRINCIPALNAME", "roles"]),
    m(29, "Scheduled Refresh",                  "intermediate", 30, 6, "Phase 6: Service & Sharing",     ["Configure data gateway", "Schedule dataset refresh"],           ["scheduled refresh", "data gateway", "on-premises gateway", "incremental refresh"]),
    m(30, "Apps and Distribution",              "intermediate", 30, 6, "Phase 6: Service & Sharing",     ["Create Power BI Apps", "Manage audiences"],                     ["Power BI apps", "distribution", "audience", "publish app"]),
    m(31, "Deployment Pipelines",               "advanced",     35, 6, "Phase 6: Service & Sharing",     ["Manage dev/test/prod", "Configure deployment rules"],           ["deployment pipelines", "ALM", "environment rules", "CI/CD"]),
    m(32, "Power BI Admin Portal",              "advanced",     35, 6, "Phase 6: Service & Sharing",     ["Manage tenant settings", "Monitor usage metrics"],              ["admin portal", "tenant settings", "usage metrics", "governance"]),
    m(33, "Direct Query vs Import",             "intermediate", 35, 7, "Phase 7: Performance",           ["Choose the right connectivity mode", "Trade-offs"],             ["DirectQuery", "Import mode", "Live connection", "composite models"]),
    m(34, "Composite Models",                   "advanced",     40, 7, "Phase 7: Performance",           ["Combine Import and DirectQuery", "Aggregation tables"],         ["composite models", "aggregations", "import + DirectQuery", "hybrid tables"]),
    m(35, "Aggregation Tables",                 "advanced",     40, 7, "Phase 7: Performance",           ["Configure aggregations", "Boost query performance"],            ["aggregation tables", "pre-aggregation", "VertiPaq", "performance"]),
    m(36, "Incremental Refresh",                "advanced",     35, 7, "Phase 7: Performance",           ["Configure incremental refresh", "Range and detect parameters"],["incremental refresh", "RangeStart", "RangeEnd", "partitions"]),
    m(37, "VertiPaq Optimisation",              "expert",       50, 7, "Phase 7: Performance",           ["Analyse model size", "Reduce cardinality"],                     ["VertiPaq", "column store", "cardinality", "model size"]),
    m(38, "Power BI Embedded",                  "advanced",     45, 8, "Phase 8: Developer",             ["Embed reports in web apps", "Use embed tokens"],                ["power bi embedded", "embed API", "embed token", "ISV"]),
    m(39, "Power BI REST API",                  "advanced",     40, 8, "Phase 8: Developer",             ["Automate with REST API", "Refresh datasets programmatically"],  ["REST API", "refresh dataset", "programmatic access", "service principal"]),
    m(40, "Paginated Reports",                  "intermediate", 40, 8, "Phase 8: Developer",             ["Build pixel-perfect reports", "Use Report Builder"],            ["paginated reports", "Report Builder", "SSRS", "RDL"]),
    m(41, "Datamart",                           "intermediate", 30, 8, "Phase 8: Developer",             ["Create Power BI Datamarts", "Build self-service analytics"],    ["datamart", "self-service analytics", "Azure SQL", "built-in"]),
    m(42, "Power BI with Azure Services",       "advanced",     40, 9, "Phase 9: Integration",           ["Connect to Synapse, ADLS, Fabric"],                             ["Azure integration", "Synapse", "ADLS", "Fabric", "Direct Lake"]),
    m(43, "Power BI + Python/R",                "advanced",     40, 9, "Phase 9: Integration",           ["Use Python visuals", "Run R in Power BI"],                     ["python", "R", "custom visuals", "script visual"]),
    m(44, "Power BI + Microsoft 365",           "intermediate", 30, 9, "Phase 9: Integration",           ["Embed in Teams and SharePoint", "Use Power Automate"],          ["teams", "SharePoint", "Power Automate", "export to Excel"]),
    m(45, "PL-300 Exam Prep",                   "advanced",     55, 9, "Phase 9: Integration",           ["Review PL-300 objectives", "Practice scenario questions"],      ["PL-300", "power bi analyst", "certification"], milestone=True),
    m(46, "Semantic Model Architecture",        "expert",       50, 10, "Phase 10: Expert",              ["Design enterprise semantic layer", "Shared datasets"],          ["enterprise semantic model", "shared dataset", "XMLA endpoint"]),
    m(47, "Power BI Governance",                "expert",       40, 10, "Phase 10: Expert",              ["Design governance framework", "Manage certified datasets"],     ["governance", "certified datasets", "endorsed content", "lineage"]),
    m(48, "Large Model Storage",                "expert",       40, 10, "Phase 10: Expert",              ["Enable large model storage", "Partition strategies"],           ["large models", "storage format", "Premium", "partitions"]),
    m(49, "XMLA Endpoint and External Tools",   "expert",       45, 10, "Phase 10: Expert",              ["Use XMLA for advanced management", "Tabular Editor, DAX Studio"],["XMLA endpoint", "Tabular Editor", "DAX Studio", "ALM Toolkit"]),
    m(50, "Report Performance Profiler",        "expert",       40, 10, "Phase 10: Expert",              ["Profile slow reports", "Fix bottlenecks"],                      ["performance analyser", "report profiling", "query times"]),
    m(51, "Executive Dashboard Project",        "advanced",     90, 10, "Phase 10: Expert",              ["Build a complete executive KPI dashboard"],                     ["executive dashboard", "KPIs", "project"], milestone=True),
    m(52, "Power BI Architecture Master",       "expert",       90, 10, "Phase 10: Expert",              ["Design enterprise-grade Power BI platform"],                    ["enterprise Power BI", "architecture", "capstone"], milestone=True),
]


# ── Azure AI Track — 50 modules ───────────────────────────────────────────────

_AZURE_AI = [
    m(1,  "AI and ML Fundamentals",             "beginner",     25, 1, "Phase 1: Foundations",           ["Distinguish AI/ML/DL", "Identify Azure AI services"],           ["AI fundamentals", "machine learning", "deep learning", "AI-900"]),
    m(2,  "Azure Cognitive Services Overview",  "beginner",     30, 1, "Phase 1: Foundations",           ["Use Computer Vision API", "Call Text Analytics"],               ["cognitive services", "computer vision", "text analytics", "language"]),
    m(3,  "Azure Language Services",            "beginner",     35, 1, "Phase 1: Foundations",           ["Use sentiment analysis", "Key phrase extraction", "NER"],       ["language service", "sentiment", "NER", "key phrase"]),
    m(4,  "Azure Vision Services",              "beginner",     35, 1, "Phase 1: Foundations",           ["Analyse images", "Use Custom Vision"],                          ["computer vision", "custom vision", "OCR", "object detection"]),
    m(5,  "Azure Speech Services",              "beginner",     30, 1, "Phase 1: Foundations",           ["Transcribe speech", "Use text-to-speech"],                     ["speech to text", "text to speech", "speech SDK", "voice"]),
    m(6,  "Azure OpenAI Fundamentals",          "intermediate", 35, 2, "Phase 2: Azure OpenAI",         ["Deploy GPT models", "Call Completions API"],                    ["azure openai", "GPT-4", "ChatGPT", "API endpoint"]),
    m(7,  "Prompt Engineering Basics",          "intermediate", 35, 2, "Phase 2: Azure OpenAI",         ["Write system prompts", "Zero/few-shot prompting"],              ["prompt engineering", "system prompt", "few-shot", "zero-shot"]),
    m(8,  "Advanced Prompt Techniques",         "intermediate", 40, 2, "Phase 2: Azure OpenAI",         ["Chain-of-thought", "ReAct pattern", "Prompt compression"],      ["chain-of-thought", "ReAct", "prompt chaining", "temperature"]),
    m(9,  "Embeddings and Vector Search",       "intermediate", 45, 2, "Phase 2: Azure OpenAI",         ["Generate embeddings", "Implement cosine similarity search"],    ["embeddings", "vector search", "cosine similarity", "text-embedding"]),
    m(10, "Azure AI Search",                    "intermediate", 40, 2, "Phase 2: Azure OpenAI",         ["Create indexes", "Configure semantic search"],                  ["AI search", "cognitive search", "index", "semantic ranking"]),
    m(11, "RAG Architecture",                   "intermediate", 50, 3, "Phase 3: RAG & Agents",         ["Build retrieval-augmented generation pipeline", "Chunking"],    ["RAG", "retrieval augmented generation", "chunking", "grounding"]),
    m(12, "RAG Optimisation",                   "advanced",     50, 3, "Phase 3: RAG & Agents",         ["Improve retrieval quality", "Re-ranking", "Hybrid search"],     ["RAG optimisation", "re-ranking", "hybrid search", "quality"]),
    m(13, "Function Calling",                   "advanced",     40, 3, "Phase 3: RAG & Agents",         ["Define functions for GPT", "Build tool-augmented LLMs"],        ["function calling", "tool use", "structured outputs", "JSON schema"]),
    m(14, "Semantic Kernel Basics",             "advanced",     45, 3, "Phase 3: RAG & Agents",         ["Use Semantic Kernel SDK", "Create plugins and planners"],       ["semantic kernel", "plugins", "planners", "AI orchestration"]),
    m(15, "AI Agents",                          "advanced",     55, 3, "Phase 3: RAG & Agents",         ["Build autonomous AI agents", "Multi-agent coordination"],      ["AI agents", "autonomous", "multi-agent", "tool calling"]),
    m(16, "Azure AI Foundry Portal",            "intermediate", 35, 4, "Phase 4: AI Foundry",           ["Navigate AI Foundry", "Deploy and test models"],               ["AI foundry", "AI studio", "model catalog", "deployments"]),
    m(17, "Model Evaluation",                   "intermediate", 40, 4, "Phase 4: AI Foundry",           ["Evaluate model quality", "Compare models"],                    ["model evaluation", "benchmarks", "RAGAS", "groundedness"]),
    m(18, "Content Safety",                     "intermediate", 30, 4, "Phase 4: AI Foundry",           ["Configure content filters", "Block harmful outputs"],          ["content safety", "content filters", "harm categories", "jailbreak"]),
    m(19, "Prompt Flow",                        "advanced",     50, 4, "Phase 4: AI Foundry",           ["Build and evaluate LLM flows", "CI/CD for prompts"],           ["prompt flow", "flow authoring", "evaluation flow", "CI/CD"]),
    m(20, "Fine-Tuning GPT Models",             "advanced",     55, 4, "Phase 4: AI Foundry",           ["Prepare fine-tuning data", "Train and evaluate custom model"],  ["fine-tuning", "JSONL", "training data", "custom model"]),
    m(21, "Responsible AI Principles",          "intermediate", 30, 5, "Phase 5: Responsible AI",       ["Apply 6 Microsoft AI principles", "Assess harms"],             ["responsible AI", "fairness", "transparency", "accountability"]),
    m(22, "AI Safety and Red Teaming",          "advanced",     40, 5, "Phase 5: Responsible AI",       ["Red team AI systems", "Test for adversarial inputs"],          ["red teaming", "AI safety", "adversarial prompts", "bias"]),
    m(23, "Explainable AI",                     "advanced",     40, 5, "Phase 5: Responsible AI",       ["Interpret ML model predictions", "Use SHAP/LIME"],             ["explainability", "SHAP", "LIME", "interpretability"]),
    m(24, "AI Governance and Compliance",       "expert",       40, 5, "Phase 5: Responsible AI",       ["Design AI governance framework", "Regulatory compliance"],     ["AI governance", "EU AI Act", "compliance", "audit"]),
    m(25, "Azure Machine Learning Workspace",   "intermediate", 35, 6, "Phase 6: Azure ML",             ["Navigate AML workspace", "Understand compute resources"],      ["azure ML", "workspace", "compute cluster", "environment"]),
    m(26, "Training ML Models in AML",          "intermediate", 50, 6, "Phase 6: Azure ML",             ["Submit training runs", "Track with MLflow"],                   ["AML training", "scripts", "MLflow", "run tracking"]),
    m(27, "AutoML in Azure",                    "intermediate", 40, 6, "Phase 6: Azure ML",             ["Configure AutoML runs", "Interpret the best model"],           ["AutoML", "automated ML", "best model", "featurisation"]),
    m(28, "Model Deployment in AML",            "advanced",     45, 6, "Phase 6: Azure ML",             ["Deploy to online endpoint", "Batch scoring"],                  ["model deployment", "online endpoint", "batch endpoint", "scoring"]),
    m(29, "ML Pipelines",                       "advanced",     50, 6, "Phase 6: Azure ML",             ["Build ML pipelines", "Reuse components"],                      ["ML pipelines", "components", "pipeline YAML", "orchestration"]),
    m(30, "Copilot Studio Overview",            "beginner",     30, 7, "Phase 7: Copilot & Integration",["Create a Copilot in Copilot Studio", "Add topics"],            ["copilot studio", "Power Virtual Agents", "topics", "bot"]),
    m(31, "Generative AI Plugins",              "advanced",     40, 7, "Phase 7: Copilot & Integration",["Build Copilot plugins", "Connect to external APIs"],           ["copilot plugins", "connector", "API integration", "manifest"]),
    m(32, "Azure AI Search Advanced",           "advanced",     45, 7, "Phase 7: Copilot & Integration",["Skillsets and enrichment", "Custom skills"],                   ["AI search advanced", "skillset", "enrichment pipeline", "OCR"]),
    m(33, "LLMOps Fundamentals",                "expert",       55, 8, "Phase 8: LLMOps",               ["Apply MLOps to LLMs", "Version prompts and models"],           ["LLMOps", "MLOps", "prompt versioning", "model registry"]),
    m(34, "Monitoring AI Applications",         "expert",       45, 8, "Phase 8: LLMOps",               ["Monitor inference quality", "Detect drift and hallucinations"],["AI monitoring", "drift detection", "hallucination", "quality"]),
    m(35, "Cost Optimisation for AI",           "expert",       40, 8, "Phase 8: LLMOps",               ["Reduce OpenAI token costs", "Caching and batching strategies"],["token cost", "caching", "batching", "cost optimisation"]),
    m(36, "Multimodal AI",                      "advanced",     45, 8, "Phase 8: LLMOps",               ["Process images with GPT-4V", "Use DALL-E 3"],                  ["multimodal", "GPT-4V", "vision", "DALL-E", "image generation"]),
    m(37, "AI for Enterprise Search",           "expert",       50, 9, "Phase 9: Enterprise AI",        ["Build enterprise knowledge base", "Federated search"],         ["enterprise search", "knowledge base", "federated", "SharePoint"]),
    m(38, "AI Document Intelligence",           "advanced",     40, 9, "Phase 9: Enterprise AI",        ["Extract from PDFs and forms", "Custom models"],                ["document intelligence", "form recogniser", "custom model", "OCR"]),
    m(39, "AI Translation and Localisation",    "intermediate", 30, 9, "Phase 9: Enterprise AI",        ["Use Azure Translator", "Custom translation models"],           ["translator", "language detection", "custom translator", "localisation"]),
    m(40, "Enterprise AI Architecture",         "expert",       55, 9, "Phase 9: Enterprise AI",        ["Design enterprise AI platform", "Select right AI service"],    ["AI architecture", "service selection", "design patterns"]),
    m(41, "AI Ethics Case Studies",             "expert",       40, 10, "Phase 10: Expert",              ["Analyse real-world AI failures", "Apply ethical frameworks"],  ["AI ethics", "case studies", "harms", "bias in production"]),
    m(42, "AI Security and Adversarial ML",     "expert",       50, 10, "Phase 10: Expert",              ["Defend against prompt injection", "Secure AI workloads"],      ["prompt injection", "adversarial ML", "AI security", "OWASP LLM"]),
    m(43, "Building AI Products",               "expert",       55, 10, "Phase 10: Expert",              ["Product thinking for AI", "Evaluate AI features"],             ["AI product", "product management", "evaluation", "user research"]),
    m(44, "AI-102 Exam Prep",                   "advanced",     55, 10, "Phase 10: Expert",              ["Review AI-102 objectives", "Practice exam questions"],         ["AI-102", "azure AI engineer", "certification"], milestone=True),
    m(45, "AI Engineer Capstone",               "expert",       120, 10, "Phase 10: Expert",             ["Build and deploy an enterprise AI application end-to-end"],    ["capstone", "enterprise AI app", "full-stack AI"], milestone=True),
    m(46, "Future of AI — Trends",              "expert",       30, 10, "Phase 10: Expert",              ["Survey AI research frontiers", "Prepare for AI evolution"],    ["AI trends", "GPT-5", "multimodal", "AGI considerations"]),
    m(47, "AI in Healthcare Use Cases",         "expert",       40, 11, "Phase 11: Industry AI",         ["Analyse AI in diagnostics and drug discovery"],                ["healthcare AI", "diagnostics", "drug discovery", "compliance"]),
    m(48, "AI in Finance Use Cases",            "expert",       40, 11, "Phase 11: Industry AI",         ["Fraud detection, risk models, regulatory AI"],                 ["finance AI", "fraud detection", "credit risk", "regulatory"]),
    m(49, "AI in Retail and Supply Chain",      "expert",       40, 11, "Phase 11: Industry AI",         ["Demand forecasting, personalisation, inventory AI"],           ["retail AI", "demand forecasting", "personalisation", "supply chain"]),
    m(50, "Real-World AI System Design",        "expert",       90, 11, "Phase 11: Industry AI",         ["Design a production AI system with proper guardrails"],        ["AI system design", "production", "guardrails", "architecture"], milestone=True),
]


# ── SQL Track — 50 modules ────────────────────────────────────────────────────

_SQL = [
    m(1,  "What Is SQL and Why It Matters",     "beginner",     20, 1, "Phase 1: Foundations",           ["Understand relational databases", "Explain SQL use cases"],     ["SQL", "RDBMS", "relational database", "use cases"]),
    m(2,  "SELECT Basics",                      "beginner",     25, 1, "Phase 1: Foundations",           ["Write SELECT statements", "Use DISTINCT and aliases"],         ["SELECT", "FROM", "DISTINCT", "aliases", "column selection"]),
    m(3,  "Filtering with WHERE",               "beginner",     25, 1, "Phase 1: Foundations",           ["Use comparison operators", "Combine AND, OR, NOT"],            ["WHERE", "AND", "OR", "NOT", "BETWEEN", "IN"]),
    m(4,  "Sorting and Limiting Results",       "beginner",     20, 1, "Phase 1: Foundations",           ["ORDER BY", "TOP / LIMIT", "FETCH NEXT"],                       ["ORDER BY", "LIMIT", "TOP", "ASC", "DESC"]),
    m(5,  "NULL Handling",                      "beginner",     25, 1, "Phase 1: Foundations",           ["Handle NULLs correctly", "IS NULL, COALESCE, ISNULL"],         ["NULL", "IS NULL", "COALESCE", "ISNULL", "NULLIF"]),
    m(6,  "String Functions",                   "beginner",     30, 2, "Phase 2: Core SQL",              ["Use UPPER, LOWER, TRIM, SUBSTRING", "Pattern matching LIKE"],  ["string functions", "CONCAT", "SUBSTRING", "TRIM", "LIKE"]),
    m(7,  "Date and Time Functions",            "beginner",     30, 2, "Phase 2: Core SQL",              ["Use DATEPART, DATEDIFF, DATEADD"],                              ["date functions", "DATEPART", "DATEDIFF", "DATEADD", "GETDATE"]),
    m(8,  "Numeric Functions and Casting",      "beginner",     25, 2, "Phase 2: Core SQL",              ["ROUND, CEILING, FLOOR", "CAST and CONVERT"],                   ["numeric functions", "ROUND", "CAST", "CONVERT", "type conversion"]),
    m(9,  "INNER JOIN",                         "beginner",     35, 3, "Phase 3: Joins",                 ["Write INNER JOIN queries", "Understand matching rows"],         ["INNER JOIN", "join condition", "matching rows", "ON clause"]),
    m(10, "LEFT and RIGHT JOIN",                "beginner",     35, 3, "Phase 3: Joins",                 ["Use LEFT JOIN for optional matches", "RIGHT JOIN"],            ["LEFT JOIN", "RIGHT JOIN", "NULL from join", "outer join"]),
    m(11, "FULL OUTER JOIN and CROSS JOIN",     "intermediate", 30, 3, "Phase 3: Joins",                 ["Use FULL OUTER JOIN", "Generate Cartesian products with CROSS"],["FULL OUTER JOIN", "CROSS JOIN", "Cartesian product"]),
    m(12, "Self Joins",                         "intermediate", 30, 3, "Phase 3: Joins",                 ["Join a table to itself", "Use aliases for clarity"],           ["self join", "hierarchical data", "employee-manager", "aliases"]),
    m(13, "Multi-Table Joins",                  "intermediate", 35, 3, "Phase 3: Joins",                 ["Chain multiple JOINs", "Understand join order"],               ["multi-table join", "three-way join", "join order", "optimisation"]),
    m(14, "GROUP BY and Aggregations",          "beginner",     35, 4, "Phase 4: Aggregation",           ["COUNT, SUM, AVG, MIN, MAX", "GROUP BY basics"],                ["GROUP BY", "COUNT", "SUM", "AVG", "aggregate functions"]),
    m(15, "HAVING Clause",                      "intermediate", 25, 4, "Phase 4: Aggregation",           ["Filter groups with HAVING", "vs WHERE"],                       ["HAVING", "GROUP BY filter", "aggregate filter"]),
    m(16, "ROLLUP and CUBE",                    "advanced",     35, 4, "Phase 4: Aggregation",           ["Generate totals with ROLLUP", "Cross-tabulations with CUBE"],  ["ROLLUP", "CUBE", "GROUPING SETS", "subtotals", "totals"]),
    m(17, "Subqueries",                         "intermediate", 40, 5, "Phase 5: Advanced Queries",      ["Correlated subqueries", "Scalar subqueries", "EXISTS"],        ["subquery", "correlated", "EXISTS", "IN with subquery"]),
    m(18, "Common Table Expressions (CTEs)",    "intermediate", 40, 5, "Phase 5: Advanced Queries",      ["Write CTEs", "Use multiple CTEs in one query"],               ["CTE", "WITH", "common table expression", "readability"]),
    m(19, "Recursive CTEs",                     "advanced",     45, 5, "Phase 5: Advanced Queries",      ["Traverse hierarchies", "Calculate running totals"],           ["recursive CTE", "hierarchy", "anchor member", "recursive member"]),
    m(20, "Window Functions",                   "intermediate", 45, 5, "Phase 5: Advanced Queries",      ["ROW_NUMBER, RANK, DENSE_RANK", "PARTITION BY"],               ["window functions", "OVER", "PARTITION BY", "ROW_NUMBER", "RANK"]),
    m(21, "LAG, LEAD, FIRST_VALUE, LAST_VALUE", "intermediate", 40, 5, "Phase 5: Advanced Queries",      ["Access previous and next rows", "Offset analysis"],           ["LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE", "offset"]),
    m(22, "PERCENTILE and Statistical Functions","advanced",    40, 5, "Phase 5: Advanced Queries",      ["PERCENTILE_CONT, PERCENTILE_DISC", "NTILE"],                  ["PERCENTILE_CONT", "NTILE", "statistics", "median"]),
    m(23, "Set Operations",                     "intermediate", 30, 5, "Phase 5: Advanced Queries",      ["UNION, INTERSECT, EXCEPT"],                                    ["UNION", "INTERSECT", "EXCEPT", "set operations"]),
    m(24, "SQL Capstone — Analytical Queries",  "advanced",     75, 5, "Phase 5: Advanced Queries",      ["Solve 10 complex analytical business questions"],             ["analytical SQL", "business queries", "capstone"], milestone=True),
    m(25, "Database Design Fundamentals",       "intermediate", 35, 6, "Phase 6: Database Design",       ["ERD notation", "Entity and relationship identification"],       ["ERD", "entities", "relationships", "attributes"]),
    m(26, "Normalisation (1NF-3NF)",            "intermediate", 40, 6, "Phase 6: Database Design",       ["Apply 1NF, 2NF, 3NF", "Remove anomalies"],                    ["normalisation", "1NF", "2NF", "3NF", "functional dependencies"]),
    m(27, "Primary and Foreign Keys",           "intermediate", 30, 6, "Phase 6: Database Design",       ["Choose primary keys", "Enforce referential integrity"],        ["primary key", "foreign key", "referential integrity", "constraints"]),
    m(28, "Star and Snowflake Schemas",         "intermediate", 35, 6, "Phase 6: Database Design",       ["Design for analytics", "Fact and dimension tables"],          ["star schema", "snowflake schema", "data warehouse design"]),
    m(29, "Indexes Fundamentals",               "intermediate", 35, 7, "Phase 7: Performance",           ["Create clustered and non-clustered indexes"],                  ["indexes", "clustered index", "non-clustered", "B-tree"]),
    m(30, "Query Execution Plans",              "advanced",     45, 7, "Phase 7: Performance",           ["Read execution plans", "Identify expensive operators"],        ["execution plan", "table scan", "index seek", "statistics"]),
    m(31, "Query Optimisation Techniques",      "advanced",     50, 7, "Phase 7: Performance",           ["Rewrite slow queries", "Use covering indexes"],                ["query optimisation", "covering index", "rewrite", "sargable"]),
    m(32, "Statistics and Cardinality",         "advanced",     40, 7, "Phase 7: Performance",           ["Understand statistics", "Fix cardinality estimation errors"],  ["statistics", "cardinality estimation", "histogram", "update stats"]),
    m(33, "Stored Procedures",                  "intermediate", 35, 8, "Phase 8: T-SQL Programming",     ["Create and execute stored procedures", "Input/output params"], ["stored procedures", "EXEC", "parameters", "reusable code"]),
    m(34, "User-Defined Functions",             "intermediate", 30, 8, "Phase 8: T-SQL Programming",     ["Scalar vs table-valued functions", "RETURNS TABLE"],           ["UDF", "scalar function", "table-valued function", "RETURNS"]),
    m(35, "Triggers",                           "intermediate", 35, 8, "Phase 8: T-SQL Programming",     ["DML triggers", "AFTER and INSTEAD OF"],                       ["triggers", "DML trigger", "AFTER INSERT", "INSTEAD OF", "audit"]),
    m(36, "Error Handling with TRY/CATCH",      "intermediate", 30, 8, "Phase 8: T-SQL Programming",     ["Handle errors in T-SQL", "RAISERROR, THROW"],                 ["TRY CATCH", "error handling", "RAISERROR", "THROW", "transactions"]),
    m(37, "Transactions and Locking",           "advanced",     45, 8, "Phase 8: T-SQL Programming",     ["ACID transactions", "Isolation levels", "Deadlock avoidance"],["transactions", "ACID", "BEGIN TRAN", "isolation levels", "deadlock"]),
    m(38, "Dynamic SQL",                        "advanced",     40, 8, "Phase 8: T-SQL Programming",     ["Build and execute dynamic SQL safely", "sp_executesql"],       ["dynamic SQL", "sp_executesql", "SQL injection prevention"]),
    m(39, "JSON in SQL Server",                 "intermediate", 35, 9, "Phase 9: Modern SQL",            ["FOR JSON, OPENJSON", "JSON_VALUE, JSON_QUERY"],               ["JSON", "FOR JSON PATH", "OPENJSON", "semi-structured data"]),
    m(40, "Temporal Tables",                    "advanced",     40, 9, "Phase 9: Modern SQL",            ["System-versioned temporal tables", "Time-travel queries"],     ["temporal tables", "system-versioned", "AS OF", "history table"]),
    m(41, "Graph Tables in SQL Server",         "advanced",     40, 9, "Phase 9: Modern SQL",            ["Node and edge tables", "MATCH pattern"],                      ["graph tables", "nodes", "edges", "MATCH", "graph queries"]),
    m(42, "Columnstore Indexes",                "expert",       45, 9, "Phase 9: Modern SQL",            ["Clustered columnstore", "Batch mode execution"],              ["columnstore", "batch mode", "analytics workloads", "delta store"]),
    m(43, "In-Memory OLTP",                     "expert",       45, 9, "Phase 9: Modern SQL",            ["Memory-optimised tables", "Compiled procedures"],             ["in-memory OLTP", "Hekaton", "memory-optimised", "lock-free"]),
    m(44, "SQL Server on Azure",                "intermediate", 35, 10, "Phase 10: Cloud SQL",           ["Azure SQL Database vs Managed Instance", "Migration"],        ["azure SQL", "managed instance", "elastic pool", "migration"]),
    m(45, "SQL Performance in the Cloud",       "advanced",     40, 10, "Phase 10: Cloud SQL",           ["Tune Azure SQL queries", "DTUs vs vCores"],                   ["azure SQL performance", "DTU", "vCore", "intelligent insights"]),
    m(46, "SQL for Data Engineers",             "expert",       50, 10, "Phase 10: Cloud SQL",           ["Write SQL for Spark and Synapse", "Optimise warehouse queries"], ["SQL in Spark", "Synapse SQL", "warehouse SQL", "data engineering"]),
    m(47, "SQL Interview Prep — Beginner",      "intermediate", 40, 11, "Phase 11: Interview Prep",      ["Solve top 20 SQL interview questions"],                        ["SQL interview", "beginner questions", "common SQL"]),
    m(48, "SQL Interview Prep — Advanced",      "advanced",     55, 11, "Phase 11: Interview Prep",      ["Hard SQL interview problems", "Window function challenges"],   ["SQL interview advanced", "hard queries", "optimisation challenge"]),
    m(49, "SQL Capstone — Real Dataset",        "advanced",     90, 11, "Phase 11: Interview Prep",      ["Analyse a real-world dataset with SQL"],                       ["SQL capstone", "real dataset", "business analysis"], milestone=True),
    m(50, "SQL Expert — Architecture Design",   "expert",       75, 11, "Phase 11: Interview Prep",      ["Design a data model for a complex business domain"],          ["data model design", "schema design", "expert SQL"], milestone=True),
]


# ── Databricks Track — 50 modules ────────────────────────────────────────────

_DATABRICKS = [
    m(1,  "Databricks Platform Overview",       "beginner",     25, 1, "Phase 1: Foundations",           ["Navigate workspace", "Understand platform architecture"],      ["databricks", "workspace", "platform", "lakehouse"]),
    m(2,  "Cluster Management",                 "beginner",     30, 1, "Phase 1: Foundations",           ["Create All-Purpose and Job clusters", "Cluster policies"],     ["clusters", "all-purpose", "job cluster", "policies", "DBR"]),
    m(3,  "Databricks Notebooks",               "beginner",     30, 1, "Phase 1: Foundations",           ["Use Python, SQL, Scala notebooks", "Magic commands"],          ["notebooks", "magic commands", "%run", "widgets"]),
    m(4,  "Databricks File System (DBFS)",      "beginner",     25, 1, "Phase 1: Foundations",           ["Work with DBFS", "Mount external storage"],                   ["DBFS", "mount points", "cloud storage", "dbutils"]),
    m(5,  "Apache Spark Architecture",          "beginner",     35, 2, "Phase 2: Apache Spark",          ["Driver and executors", "DAG and stages", "Lazy evaluation"],  ["spark architecture", "driver", "executor", "DAG", "tasks"]),
    m(6,  "Spark DataFrames",                   "beginner",     40, 2, "Phase 2: Apache Spark",          ["Read CSV/JSON/Parquet", "Transform with PySpark"],             ["DataFrame", "read parquet", "filter", "select", "withColumn"]),
    m(7,  "Spark SQL",                          "beginner",     35, 2, "Phase 2: Apache Spark",          ["Register temp views", "SQL on DataFrames"],                   ["spark SQL", "createTempView", "sql()", "catalog"]),
    m(8,  "Spark Schemas and Types",            "intermediate", 35, 2, "Phase 2: Apache Spark",          ["Define and enforce schemas", "Handle complex types"],         ["StructType", "StructField", "ArrayType", "MapType", "schema"]),
    m(9,  "Data Ingestion Patterns",            "intermediate", 40, 3, "Phase 3: Data Engineering",      ["Batch vs streaming ingestion", "Auto Loader"],               ["auto loader", "cloudFiles", "batch ingestion", "streaming ingestion"]),
    m(10, "Auto Loader Deep Dive",              "intermediate", 45, 3, "Phase 3: Data Engineering",      ["Configure Auto Loader", "Schema evolution and merging"],      ["Auto Loader", "schema evolution", "cloudFiles.format", "checkpointing"]),
    m(11, "Delta Lake Fundamentals",            "intermediate", 40, 3, "Phase 3: Data Engineering",      ["Write Delta tables", "ACID transactions", "table history"],  ["delta lake", "ACID", "table versioning", "DESCRIBE HISTORY"]),
    m(12, "Delta MERGE (Upserts)",              "intermediate", 45, 3, "Phase 3: Data Engineering",      ["MERGE INTO syntax", "SCD Type 2 with MERGE"],               ["MERGE INTO", "upsert", "SCD type 2", "change data capture"]),
    m(13, "Delta Time Travel",                  "intermediate", 30, 3, "Phase 3: Data Engineering",      ["VERSION AS OF", "TIMESTAMP AS OF", "RESTORE"],               ["time travel", "VERSION AS OF", "RESTORE", "audit"]),
    m(14, "Optimize and ZORDER",                "advanced",     40, 3, "Phase 3: Data Engineering",      ["OPTIMIZE compaction", "Z-Ordering for data skipping"],        ["OPTIMIZE", "ZORDER", "compaction", "data skipping", "file size"]),
    m(15, "Vacuum and Retention",               "intermediate", 25, 3, "Phase 3: Data Engineering",      ["VACUUM tables", "Configure retention period"],               ["VACUUM", "retention", "file cleanup", "dry run"]),
    m(16, "Medallion Architecture",             "intermediate", 45, 4, "Phase 4: Architecture",          ["Implement Bronze, Silver, Gold layers"],                      ["medallion architecture", "bronze", "silver", "gold", "lakehouse"]),
    m(17, "Streaming with Structured Streaming","intermediate", 50, 4, "Phase 4: Architecture",          ["readStream/writeStream", "Trigger modes", "Checkpointing"],  ["structured streaming", "readStream", "writeStream", "checkpoint"]),
    m(18, "Delta Live Tables",                  "advanced",     55, 4, "Phase 4: Architecture",          ["Declare live tables", "Use expectations", "DLT pipelines"],  ["DLT", "live tables", "expectations", "@dlt.table"]),
    m(19, "Unity Catalog Setup",                "advanced",     40, 5, "Phase 5: Governance",            ["Create metastore", "Assign workspace to metastore"],          ["unity catalog", "metastore", "workspace assignment", "catalog"]),
    m(20, "Unity Catalog Permissions",          "advanced",     45, 5, "Phase 5: Governance",            ["GRANT and REVOKE", "Row filters and column masks"],           ["GRANT", "REVOKE", "row filter", "column mask", "fine-grained"]),
    m(21, "Data Lineage with Unity Catalog",    "advanced",     35, 5, "Phase 5: Governance",            ["Track column-level lineage", "Query lineage UI"],             ["lineage", "column-level lineage", "governance", "compliance"]),
    m(22, "Delta Sharing",                      "advanced",     35, 5, "Phase 5: Governance",            ["Share data across orgs", "Configure shares and recipients"],  ["delta sharing", "open protocol", "recipients", "data sharing"]),
    m(23, "MLflow Tracking",                    "intermediate", 40, 6, "Phase 6: ML & MLflow",           ["Log params, metrics, artifacts", "Compare runs"],            ["MLflow", "tracking", "log_metric", "log_param", "run comparison"]),
    m(24, "MLflow Model Registry",              "intermediate", 40, 6, "Phase 6: ML & MLflow",           ["Register models", "Stage transitions", "Model aliases"],     ["model registry", "staging", "production", "aliases", "transition"]),
    m(25, "Feature Store",                      "advanced",     45, 6, "Phase 6: ML & MLflow",           ["Create and use feature tables", "Point-in-time lookups"],    ["feature store", "feature tables", "training set", "point-in-time"]),
    m(26, "AutoML in Databricks",               "intermediate", 40, 6, "Phase 6: ML & MLflow",           ["Run AutoML experiments", "Interpret the notebook generated"],["AutoML", "experiment", "best model", "generated notebook"]),
    m(27, "Model Serving",                      "advanced",     50, 6, "Phase 6: ML & MLflow",           ["Deploy models to real-time endpoints", "A/B testing"],       ["model serving", "endpoint", "real-time inference", "A/B testing"]),
    m(28, "Databricks Workflows",               "advanced",     45, 7, "Phase 7: Orchestration",         ["Multi-task jobs", "Dependencies and conditions"],             ["workflows", "multi-task job", "task dependencies", "repair run"]),
    m(29, "Databricks Asset Bundles (DAB)",     "advanced",     45, 7, "Phase 7: Orchestration",         ["Deploy with DAB", "bundle.yml configuration"],               ["asset bundles", "DAB", "bundle.yml", "IaC for Databricks"]),
    m(30, "CI/CD for Databricks",               "advanced",     50, 7, "Phase 7: Orchestration",         ["GitHub Actions for Databricks", "DAB deployment pipeline"],  ["CI/CD", "GitHub Actions", "automated testing", "deployment"]),
    m(31, "Spark Performance — Partitioning",   "advanced",     45, 8, "Phase 8: Performance",           ["Repartition vs coalesce", "Avoid data skew"],               ["partitioning", "repartition", "coalesce", "skew", "shuffle"]),
    m(32, "Spark Performance — Caching",        "advanced",     35, 8, "Phase 8: Performance",           ["cache() vs persist()", "Storage levels"],                   ["caching", "persist", "MEMORY_AND_DISK", "storage level"]),
    m(33, "Adaptive Query Execution (AQE)",     "advanced",     40, 8, "Phase 8: Performance",           ["Enable AQE", "Understand dynamic partition coalescing"],     ["AQE", "adaptive query", "dynamic coalescing", "skew join"]),
    m(34, "Photon Engine",                      "expert",       35, 8, "Phase 8: Performance",           ["Understand Photon acceleration", "Benchmark query gains"],   ["Photon", "vectorised execution", "SQL performance", "acceleration"]),
    m(35, "Cluster Sizing and Cost Optimisation","expert",      50, 8, "Phase 8: Performance",           ["Right-size clusters", "Use spot instances and policies"],    ["cluster sizing", "spot instances", "cost optimisation", "right-sizing"]),
    m(36, "Databricks SQL Warehouses",          "intermediate", 35, 9, "Phase 9: SQL Analytics",         ["Create SQL warehouses", "Query in Databricks SQL editor"],   ["SQL warehouse", "serverless SQL", "pro tier", "query history"]),
    m(37, "Dashboards in Databricks SQL",       "intermediate", 30, 9, "Phase 9: SQL Analytics",         ["Build dashboards", "Refresh schedules"],                    ["dashboards", "visualisations", "widgets", "scheduled refresh"]),
    m(38, "Databricks SQL Performance",         "advanced",     40, 9, "Phase 9: SQL Analytics",         ["Query optimisation in Databricks SQL", "Query profile"],    ["SQL performance", "query profile", "explain plan", "cache"]),
    m(39, "Lakehouse for BI",                   "expert",       45, 9, "Phase 9: SQL Analytics",         ["Connect Power BI via partner connect", "Direct Lake mode"],  ["BI integration", "Power BI", "partner connect", "Direct Lake"]),
    m(40, "Production Lakehouse Design",        "expert",       75, 10, "Phase 10: Expert",              ["Design production lakehouse architecture"],                  ["lakehouse design", "production", "architecture patterns"], milestone=True),
    m(41, "Multi-Workspace Strategy",           "expert",       45, 10, "Phase 10: Expert",              ["Dev/test/prod workspace design", "Cross-workspace access"],  ["workspace strategy", "dev test prod", "cross-workspace"]),
    m(42, "Databricks Security Deep Dive",      "expert",       50, 10, "Phase 10: Expert",              ["Network isolation", "Private link", "Customer-managed keys"],["network isolation", "private link", "CMK", "IP access list"]),
    m(43, "Databricks Migration from Legacy",   "expert",       55, 10, "Phase 10: Expert",              ["Migrate from HDInsight or standalone Spark"],               ["migration", "HDInsight", "legacy Spark", "lift and shift"]),
    m(44, "Databricks Partner Ecosystem",       "expert",       35, 10, "Phase 10: Expert",              ["Fivetran, dbt, Great Expectations with Databricks"],         ["partner ecosystem", "Fivetran", "dbt", "integrations"]),
    m(45, "Databricks Certified DE Associate",  "advanced",     55, 11, "Phase 11: Certifications",      ["Prepare for Databricks DE Associate exam"],                 ["Databricks certification", "DE associate", "exam prep"], milestone=True),
    m(46, "Databricks Certified ML Associate",  "expert",       55, 11, "Phase 11: Certifications",      ["Prepare for ML Associate certification"],                   ["ML associate", "MLflow exam", "model serving certification"]),
    m(47, "Real-World Case: Retail Analytics",  "expert",       60, 12, "Phase 12: Case Studies",        ["Build retail lakehouse with Databricks"],                   ["retail", "case study", "lakehouse", "Databricks"]),
    m(48, "Real-World Case: Financial Risk",    "expert",       60, 12, "Phase 12: Case Studies",        ["Risk modelling pipeline on Databricks"],                    ["financial risk", "Monte Carlo", "compliance", "case study"]),
    m(49, "Databricks Interview Preparation",   "expert",       55, 12, "Phase 12: Case Studies",        ["System design, coding, and architecture interview prep"],   ["interview prep", "system design", "Spark coding"]),
    m(50, "Master Databricks Architect",        "expert",       120, 12, "Phase 12: Case Studies",       ["Design an enterprise lakehouse platform end-to-end"],       ["master architect", "capstone", "enterprise lakehouse"], milestone=True),
]


# ── Curriculum Assembly ────────────────────────────────────────────────────────

LEARNING_CURRICULUM = [
    {
        "name": "Azure",
        "slug": "azure-track",
        "description": "Master Microsoft Azure from fundamentals to expert-level architecture. "
                       "Covers compute, networking, storage, identity, monitoring, DevOps, and enterprise patterns.",
        "icon": "☁️",
        "difficulty_range": "Beginner → Expert",
        "estimated_hours": 80,
        "modules": _AZURE,
    },
    {
        "name": "Microsoft Fabric",
        "slug": "fabric-track",
        "description": "Complete Microsoft Fabric analytics platform — from OneLake fundamentals "
                       "to expert-level architecture, administration, and performance engineering.",
        "icon": "🗄️",
        "difficulty_range": "Beginner → Expert",
        "estimated_hours": 90,
        "modules": _FABRIC,
    },
    {
        "name": "Azure Data Engineering",
        "slug": "data-engineering-track",
        "description": "Production-grade data engineering on Azure. ADF, Spark, Delta Lake, "
                       "Synapse, Databricks, streaming, data quality, and enterprise data platforms.",
        "icon": "🔧",
        "difficulty_range": "Beginner → Expert",
        "estimated_hours": 100,
        "modules": _DATA_ENG,
    },
    {
        "name": "Power BI",
        "slug": "powerbi-track",
        "description": "Professional Power BI from desktop basics to enterprise-grade semantic models, "
                       "advanced DAX, performance optimisation, and embedded analytics.",
        "icon": "📊",
        "difficulty_range": "Beginner → Expert",
        "estimated_hours": 80,
        "modules": _POWER_BI,
    },
    {
        "name": "Azure AI",
        "slug": "azure-ai-track",
        "description": "Build intelligent AI applications on Azure using Cognitive Services, "
                       "Azure OpenAI, RAG, agents, responsible AI, and LLMOps.",
        "icon": "🧠",
        "difficulty_range": "Beginner → Expert",
        "estimated_hours": 85,
        "modules": _AZURE_AI,
    },
    {
        "name": "SQL",
        "slug": "sql-track",
        "description": "Master SQL from first SELECT to advanced performance tuning, T-SQL programming, "
                       "modern SQL features, and data engineering patterns.",
        "icon": "🗃️",
        "difficulty_range": "Beginner → Expert",
        "estimated_hours": 70,
        "modules": _SQL,
    },
    {
        "name": "Databricks",
        "slug": "databricks-track",
        "description": "Expert Databricks Lakehouse Platform — Spark, Delta Lake, Unity Catalog, "
                       "MLflow, Workflows, performance engineering, and production architecture.",
        "icon": "⚡",
        "difficulty_range": "Beginner → Expert",
        "estimated_hours": 85,
        "modules": _DATABRICKS,
    },
]
