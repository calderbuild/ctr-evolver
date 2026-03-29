# System Architecture

## Self-Evolving SEO Agent: Architecture Overview

```mermaid
flowchart TB
    subgraph input ["Data Input"]
        GSC["Google Search Console API"]
        Cache["Parquet Cache<br/>(data/gsc/*.parquet)"]
        GSC --> Cache
    end

    subgraph data_layer ["Data Layer (seo_agent/)"]
        OPP["Opportunity Finder<br/>position-based CTR gap scoring"]
        EXEC["Executor<br/>SKILL.md + LLM → title/desc"]
        EVAL_CTR["CTR Evaluator<br/>z-test significance"]
        EVAL_LLM["LLM-as-Judge<br/>5-dimension rubric (Haiku)"]
        INT["Intervention Log<br/>(append-only JSONL)"]
    end

    subgraph evo_layer ["Evolution Layer (engine/)"]
        ENGINE["Evolution Engine<br/>orchestrates step()"]
        PROP["Proposer<br/>failure analysis + strategy (Sonnet)"]
        GEN["Skill Generator<br/>SKILL.md versioned files"]
        FRONT["Pareto Frontier<br/>K=15, 3D: lift/win/coverage"]
        MEM["Evolution Memory<br/>promising / failed / patterns"]
    end

    subgraph output ["Output"]
        SKILLS["skills/{name}/v{N}/SKILL.md"]
        ACTIVE["active_skills.json"]
        CKPT["checkpoint.json"]
    end

    Cache --> OPP
    OPP -->|"top opportunities<br/>by score"| EXEC
    EXEC -->|"new title/desc"| INT

    INT -->|"after wait period"| EVAL_CTR
    INT -->|"immediate proxy"| EVAL_LLM

    EVAL_CTR -->|"ctr_lift + significance"| ENGINE
    EVAL_LLM -->|"5D score → status"| ENGINE

    ENGINE -->|"evaluated results"| FRONT
    FRONT -->|"eliminated skills"| ENGINE
    ENGINE -->|"failures + memory"| PROP
    MEM <-->|"context injection"| PROP
    PROP -->|"strategy dict"| GEN
    GEN --> SKILLS
    GEN --> ACTIVE
    FRONT --> ACTIVE
    ENGINE --> CKPT

    style EVAL_LLM fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style EVAL_CTR fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style FRONT fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style ENGINE fill:#fce4ec,stroke:#c62828,stroke-width:2px
```

## Dual Evaluation Path

The system's key innovation: two evaluation paths that enable evolution even with sparse real-world data.

```mermaid
flowchart LR
    INT["Intervention<br/>(pending)"] --> CHECK{"Sufficient<br/>impressions?"}
    CHECK -->|">= 30 before + after"| CTR["CTR Evaluator<br/>two-proportion z-test"]
    CHECK -->|"< 30 (sparse data)"| LLM["LLM-as-Judge<br/>Haiku, 5 dimensions"]

    CTR -->|"ctr_lift, is_significant"| MERGE["Merge Results"]
    LLM -->|"score → normalized lift"| MERGE

    MERGE --> STATUS{"Map to Status"}
    STATUS -->|">= 7/10"| SUCCESS["success"]
    STATUS -->|"<= 3/10"| FAIL["failure"]
    STATUS -->|"4-6/10"| INCON["inconclusive"]

    style LLM fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style CTR fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
```

## Evolution Loop (Single Step)

```mermaid
flowchart LR
    A["1. Sync GSC Data"] --> B["2. Identify<br/>Opportunities"]
    B --> C["3. Generate<br/>(skill → title/desc)"]
    C --> D["4. Evaluate<br/>(CTR or LLM)"]
    D --> E["5. Update Frontier<br/>(Pareto elimination)"]
    E --> F["6. Analyze Failures<br/>+ Propose Strategy"]
    F --> G["7. Generate<br/>New Skill"]
    G --> H["8. Checkpoint"]
    H -.->|"next step"| A

    style A fill:#f3e5f5,stroke:#7b1fa2
    style D fill:#e8f5e9,stroke:#2e7d32
    style E fill:#e3f2fd,stroke:#1565c0
    style G fill:#fff8e1,stroke:#f9a825
```
