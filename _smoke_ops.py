from knowledge_base.wq_docs_rag import WQBrainDocsRAG, get_wq_docs_context
from pipeline.generator.llm_generator import OFFICIAL_OPERATORS, OPERATOR_CALL

rag = WQBrainDocsRAG.shared()
rag.load()
print("empty=", rag.is_empty, "kbs=", len(rag._kbs))
ctx = get_wq_docs_context("operators ts_rank ts_decay_linear group_neutralize trade_when", k=2)
print("ctx_chars=", len(ctx))
print(ctx[:600])
print("---")
print("n_ops=", len(OFFICIAL_OPERATORS))
print("rank match:", bool(OPERATOR_CALL.search("rank(ts_delta(close, 10))")))
print("group_neutralize match:", bool(OPERATOR_CALL.search("group_neutralize(rank(close), subindustry)")))
print("fake rank1 match:", bool(OPERATOR_CALL.search("rank1(close, 5)")))
