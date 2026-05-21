# WorldQuant Brain Documentation Corpus

Đây là thư mục chứa tài liệu chính thức tải từ
<https://platform.worldquantbrain.com/learn/documentation> phục vụ cho
`knowledge_base.wq_docs_rag.WQBrainDocsRAG`. Hermes và LLM generator
(`pipeline/generator/llm_generator.py`) sẽ truy vấn corpus này trước khi
sinh alpha để bám sát đúng operator/field/quy ước của Brain.

## Cách đổ tài liệu vào

1. Đăng nhập <https://platform.worldquantbrain.com/learn/documentation>.
2. Lưu mỗi trang (operator reference, data fields, alpha lifecycle,
   simulation settings, neutralization, decay, fitness, self-correlation,
   submission rules, …) thành Markdown / HTML / TXT / PDF.
3. Đặt vào thư mục này theo cấu trúc tự do, ví dụ:

   ```
   docs/wq_brain/
     operators/arithmetic.md
     operators/time_series.md
     data/fundamentals.md
     simulation/neutralization.md
     simulation/decay_truncation.md
     submission/self_correlation.md
   ```

4. Chạy lại `python -u run_hermes_real.py` hoặc `python -u main.py` —
   RAG sẽ tự load lần đầu và cache trong RAM của tiến trình.

## File định dạng hỗ trợ

`.md`, `.txt`, `.json`, `.html`, `.pdf` (xem
`knowledge_base/rag_loader.py`).

## Kiểm tra nhanh

```powershell
python -c "from knowledge_base.wq_docs_rag import WQBrainDocsRAG; \
rag = WQBrainDocsRAG(); rag.load(); \
print(rag.query('ts_rank operator semantics', k=2))"
```

Nếu output rỗng → corpus chưa có file phù hợp.
