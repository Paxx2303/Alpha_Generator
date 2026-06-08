# config.py — Tất cả config tập trung 1 chỗ, không hardcode path
from pathlib import Path

BASE_DIR = Path(__file__).parent
ALPHA_SKILLS_DIR = BASE_DIR / "alpha_skills"

# ── Paths ──────────────────────────────────────────────────────────────────────
RAW_DATA_DIR       = ALPHA_SKILLS_DIR / "rawdata"
PROCESSED_DATA_DIR = ALPHA_SKILLS_DIR / "processed_data"
CHUNKS_DIR         = ALPHA_SKILLS_DIR / "chunks"
FINAL_DATASET_DIR  = ALPHA_SKILLS_DIR / "final_dataset"
REFERENCE_DIR      = ALPHA_SKILLS_DIR / "reference"

GOLD_ALPHAS_PATH   = BASE_DIR / "gold_alphas.json"
SKILL_PATH         = ALPHA_SKILLS_DIR / "wq-alpha.skill"
MCP_SKILL_PATH     = BASE_DIR / "mcp_skill.md"

# ── Document quality gates ─────────────────────────────────────────────────────
MIN_WORDS_PER_DOC  = 50        # Docs shorter than this are rejected
MAX_WORDS_PER_DOC  = 15000     # Docs longer than this need special chunking
MIN_CHUNK_WORDS    = 30        # Chunks shorter than this are discarded
MAX_CHUNK_WORDS    = 600       # Chunks longer than this are split further
IDEAL_CHUNK_WORDS  = 200       # Target chunk size for length-penalty scoring

# ── Training split ─────────────────────────────────────────────────────────────
TRAIN_RATIO        = 0.70
VAL_RATIO          = 0.20
TEST_RATIO         = 0.10
RANDOM_SEED        = 42        # Reproducible shuffle

# ── RAG retrieval ──────────────────────────────────────────────────────────────
TOP_K_RESULTS              = 5
RAG_SIM_WEIGHT             = 0.60   # Vector similarity weight
RAG_LENGTH_PENALTY_WEIGHT  = 0.20   # Length-penalty weight
RAG_QUALITY_WEIGHT         = 0.20   # Quality-score weight
MIN_QUALITY_FOR_IMPORTANT  = 40     # Docs below this score skipped for high-priority queries

# ── Category definitions (keyword scoring) ────────────────────────────────────
CATEGORIES = {
    "technical_indicators": {
        "keywords": [
            "rsi", "macd", "bollinger", "moving average", "momentum", "oscillator",
            "stochastic", "atr", "ema", "sma", "technical indicator", "overbought",
            "oversold", "divergence", "signal line",
        ],
        "description": "Technical analysis indicators and price-based signals",
    },
    "quantitative_methods": {
        "keywords": [
            "regression", "correlation", "covariance", "pca", "factor model",
            "statistical arbitrage", "mean reversion", "time series", "stationarity",
            "cointegration", "kalman", "bayesian", "machine learning", "neural network",
            "optimization", "backtest", "monte carlo",
        ],
        "description": "Quantitative and statistical methods for alpha research",
    },
    "platform_guides": {
        "keywords": [
            "worldquant", "brain", "wqb", "iqc", "simulation", "universe", "neutralization",
            "truncation", "decay", "fitness", "sharpe", "turnover", "pasteurize",
            "ts_rank", "ts_delta", "group_neutralize", "trade_when", "data field",
        ],
        "description": "WorldQuant Brain platform guides and operator documentation",
    },
    "academic_papers": {
        "keywords": [
            "fama", "french", "capm", "sharpe ratio", "efficient market", "hypothesis",
            "anomaly", "factor", "premium", "cross-section", "abnormal return",
            "momentum effect", "value premium", "size effect", "liquidity",
        ],
        "description": "Academic finance papers and peer-reviewed research",
    },
    "research_insights": {
        "keywords": [
            "insight", "finding", "evidence", "suggest", "implication", "conclusion",
            "result", "performance", "strategy", "portfolio", "alpha", "signal",
        ],
        "description": "Synthesized research insights and trading ideas",
    },
    "core_concepts": {
        "keywords": [
            "definition", "concept", "theory", "model", "framework", "principle",
            "volatility", "beta", "risk", "return", "portfolio", "diversification",
            "drawdown", "var", "cvar", "hedge",
        ],
        "description": "Foundational concepts in quantitative finance",
    },
}

# ── Noise exclusion patterns (regex) ──────────────────────────────────────────
NOISE_PATTERNS = [
    r".*personal.*weight.*loss.*",
    r".*diet.*health.*",
    r"sign in.*sign up",
    r"footer navigation",
    r"meta-.*:",
    r"^\s*\d+\s*$",
    r"github\.com.*©.*inc\.",
]

# ── WQB quality scoring ────────────────────────────────────────────────────────
WQB_FORMULA_PATTERNS = [
    r"rank\(", r"ts_delta\(", r"ts_mean\(", r"ts_corr\(",
    r"ts_rank\(", r"ts_std_dev\(", r"group_neutralize\(",
    r"pasteurize\(", r"trade_when\(",
]

SOURCE_QUALITY_MAP = {
    "official_docs": 20,
    "paper":         20,
    "example":       15,
    "forum":         10,
    "general":        5,
}
