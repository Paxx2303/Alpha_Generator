# Các Lệnh Thường Dùng - Hệ Thống Queue

## 🚀 Khởi Động Worker

```bash
# Khởi động worker (chạy liên tục)
python scripts/queue_manager_cli.py start-worker

# Hoặc sử dụng main.py
python main.py --queue-worker

# Với custom poll interval (3 giây)
python main.py --queue-worker --poll-interval 3.0
```

## ➕ Thêm Job Vào Hàng Đợi

### Pipeline Job (Tạo alpha thông thường)

```bash
# Momentum strategy, 5 alphas
python scripts/queue_manager_cli.py add-job \
  --type pipeline \
  --strategy momentum \
  --count 5

# Mean-reversion strategy, 8 alphas, không submit
python scripts/queue_manager_cli.py add-job \
  --type pipeline \
  --strategy mean-reversion \
  --count 8 \
  --no-submit

# Dry run mode (test không submit thật)
python scripts/queue_manager_cli.py add-job \
  --type pipeline \
  --strategy momentum \
  --count 3 \
  --dry-run
```

### Bruteforce Job (Tạo alpha theo grid)

```bash
# Bruteforce momentum, 10 alphas
python scripts/queue_manager_cli.py add-job \
  --type bruteforce \
  --strategy momentum \
  --count 10

# Bruteforce mean-reversion, không submit
python scripts/queue_manager_cli.py add-job \
  --type bruteforce \
  --strategy mean-reversion \
  --count 20 \
  --no-submit
```

### Continuous Job (Chạy liên tục 24/7)

```bash
# Chạy liên tục, mỗi cycle tạo 8 alphas
python scripts/queue_manager_cli.py add-job \
  --type continuous \
  --strategy momentum \
  --count 8
```

## 📊 Xem Trạng Thái

```bash
# Xem trạng thái hàng đợi
python scripts/queue_manager_cli.py status

# Hoặc sử dụng main.py
python main.py --queue-status
```

Output sẽ hiển thị:
- 🔄 Job đang chạy (với alpha ID đang xử lý)
- 📋 Jobs đang đợi trong hàng đợi
- ⏸️ Jobs bị pause (có checkpoint)
- ✅ Jobs đã hoàn thành
- ❌ Jobs thất bại

## 🧹 Cleanup

```bash
# Xóa jobs cũ hơn 7 ngày
python scripts/queue_manager_cli.py cleanup

# Xóa jobs cũ hơn 3 ngày
python scripts/queue_manager_cli.py cleanup --max-age 259200

# Hoặc sử dụng main.py
python main.py --queue-cleanup
```

## 🛑 Dừng Worker (Graceful Shutdown)

```bash
# Nhấn Ctrl+C trong terminal đang chạy worker
# Worker sẽ:
# 1. Lưu checkpoint của job đang chạy
# 2. Release lock
# 3. Exit gracefully

# Hoặc gửi SIGTERM
kill -TERM <worker_pid>
```

## 🔄 Resume Job Sau Khi Tắt

```bash
# Chỉ cần khởi động worker lại
python scripts/queue_manager_cli.py start-worker

# Worker sẽ tự động:
# 1. Tìm jobs có status "paused"
# 2. Load checkpoint
# 3. Tiếp tục chạy từ vị trí đã lưu
```

## 🧪 Test Hệ Thống

```bash
# Chạy test script
python scripts/test_queue_system.py
```

## 📝 Ví Dụ Workflow Hoàn Chỉnh

### Scenario 1: Chạy 3 jobs liên tiếp

```bash
# Terminal 1: Khởi động worker
python scripts/queue_manager_cli.py start-worker

# Terminal 2: Thêm 3 jobs
python scripts/queue_manager_cli.py add-job --type pipeline --strategy momentum --count 5
python scripts/queue_manager_cli.py add-job --type pipeline --strategy mean-reversion --count 5
python scripts/queue_manager_cli.py add-job --type bruteforce --strategy momentum --count 10

# Terminal 2: Xem trạng thái
python scripts/queue_manager_cli.py status
```

Worker sẽ tự động:
1. Chạy job 1 (momentum pipeline)
2. Khi job 1 xong, tự động chạy job 2 (mean-reversion pipeline)
3. Khi job 2 xong, tự động chạy job 3 (momentum bruteforce)

### Scenario 2: Chạy liên tục 24/7

```bash
# Thêm continuous job
python scripts/queue_manager_cli.py add-job \
  --type continuous \
  --strategy momentum \
  --count 8

# Khởi động worker
python scripts/queue_manager_cli.py start-worker

# Worker sẽ chạy mãi mãi:
# - Mỗi cycle tạo 8 alphas
# - Sau khi xong, tự động queue lại
# - Lặp lại vô hạn
```

### Scenario 3: Graceful shutdown và resume

```bash
# Terminal 1: Khởi động worker
python scripts/queue_manager_cli.py start-worker

# Terminal 2: Thêm job
python scripts/queue_manager_cli.py add-job --type pipeline --strategy momentum --count 10

# Sau một lúc, nhấn Ctrl+C ở Terminal 1
# Worker sẽ lưu checkpoint

# Xem trạng thái
python scripts/queue_manager_cli.py status
# Output: Job có status "paused"

# Khởi động lại worker
python scripts/queue_manager_cli.py start-worker
# Worker sẽ tự động resume job từ checkpoint
```

## 🔍 Monitoring

### Xem logs

```bash
# Tail logs
tail -f logs/queue_worker.log

# Grep errors
grep ERROR logs/queue_worker.log

# Grep specific job
grep "job_id_here" logs/queue_worker.log
```

### Xem trạng thái real-time

```bash
# Watch status (cập nhật mỗi 2 giây)
watch -n 2 "python scripts/queue_manager_cli.py status"
```

## 🚨 Troubleshooting

### Worker không lấy job

```bash
# Kiểm tra lock file
ls -la runtime/job_queue/active.lock

# Xóa lock nếu bị stale
rm runtime/job_queue/active.lock

# Khởi động lại worker
python scripts/queue_manager_cli.py start-worker
```

### Job bị stuck

```bash
# Kiểm tra worker process
ps aux | grep queue-worker

# Nếu không còn process, xóa lock
rm runtime/job_queue/active.lock

# Khởi động lại worker
python scripts/queue_manager_cli.py start-worker
```

### Checkpoint bị corrupt

```bash
# Xóa checkpoint
rm runtime/job_queue/checkpoints/<job_id>.json

# Job sẽ chạy lại từ đầu
```

## 📦 Backup & Restore

### Backup

```bash
# Backup toàn bộ queue data
tar -czf queue_backup_$(date +%Y%m%d_%H%M%S).tar.gz runtime/job_queue/

# Backup chỉ jobs
tar -czf jobs_backup_$(date +%Y%m%d_%H%M%S).tar.gz runtime/job_queue/jobs/
```

### Restore

```bash
# Restore từ backup
tar -xzf queue_backup_20260520_120000.tar.gz

# Khởi động lại worker
python scripts/queue_manager_cli.py start-worker
```

## 🎯 Tips & Best Practices

1. **Luôn chạy worker như một service** (systemd, supervisor, etc.)
2. **Monitor logs thường xuyên** để phát hiện lỗi sớm
3. **Backup queue data định kỳ** (mỗi ngày hoặc mỗi tuần)
4. **Cleanup old jobs thường xuyên** để tránh disk đầy
5. **Sử dụng dry-run mode** khi test để tránh submit nhầm
6. **Graceful shutdown** (Ctrl+C) thay vì kill -9

## 📚 Tài Liệu Liên Quan

- [QUEUE_SYSTEM.md](docs/QUEUE_SYSTEM.md) - Tài liệu chi tiết về hệ thống queue
- [ALL_WORKFLOWS.md](docs/ALL_WORKFLOWS.md) - Workflow tổng quan của hệ thống
