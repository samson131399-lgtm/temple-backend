# 刑世宮濟靈堂廟務系統

## 本機開發

在 PowerShell 切換到此資料夾後執行：

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

管理後台：`http://127.0.0.1:8000/admin/`

## 資料庫備份

在 PowerShell 執行：

```powershell
.\backup_database.ps1
```

備份預設寫入 `backups` 資料夾，保留最近 30 天。也可以直接執行 Django 管理命令：

```powershell
.\.venv\Scripts\python.exe manage.py backup_database --keep-days 30
```

可用 `TEMPLE_BACKUP_DIR` 指定備份資料夾。SQLite 備份使用資料庫線上備份介面，不需先停止本機伺服器；PostgreSQL 備份使用 `pg_dump`，執行環境需安裝 PostgreSQL Client Tools。備份檔含帳號、信眾及收支資料，應限制存取並另外保存一份在不同裝置或受控雲端儲存空間。

SQLite 還原前先停止伺服器，將目前 `db.sqlite3` 改名留存，再把選定備份複製為 `db.sqlite3`。PostgreSQL 還原應先還原至新的空資料庫並核對資料，再切換正式連線；不要直接對正式資料庫執行清除式還原。

## 正式部署環境變數

部署環境需設定：

- `DJANGO_ENV=production`
- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY`：至少 50 個隨機字元，僅存放於主機的機密設定
- `DJANGO_ALLOWED_HOSTS`：正式網域主機名稱，不含 `https://`
- `DJANGO_CSRF_TRUSTED_ORIGINS`：正式來源網址，需含 `https://`
- `DATABASE_URL`：託管 PostgreSQL 私有連線網址

正式環境會強制 HTTPS、設定安全 Cookie、HSTS，並使用 WhiteNoise 提供 Django 靜態檔案。SQLite 僅作為本機預設資料庫；多位管理者共用資料時，正式環境應連到同一個託管 PostgreSQL。

安裝正式環境套件後，建置流程需收集靜態檔並套用資料庫遷移；Web 服務入口為 `temple_backend.wsgi:application`。不可使用 Django `runserver` 作為正式伺服器。

若使用 Render，Web Service 的 Build Command 可設為 `bash build.sh`，Start Command 設為 `gunicorn temple_backend.wsgi:application`。在服務環境變數中設定上述正式環境值，並將 `DATABASE_URL` 連到同一個 Render PostgreSQL。不要把連線網址或 Django 金鑰放進程式碼或 Git。

## 目前狀態

如需每日自動備份，可在 Windows「工作排程器」建立每日工作，動作選「啟動程式」：程式填 `powershell.exe`，引數填 `-NoProfile -ExecutionPolicy Bypass -File "完整路徑\temple-backend\backup_database.ps1"`。建議選擇系統已開機且備份磁碟可用的時間，並定期確認備份檔有新增、可讀取。

目前資料仍在本機 SQLite。設定和 Render 建置指令已準備好讀取 PostgreSQL 連線，但正式資料庫尚未建立，也尚未將本機資料搬移至雲端。請先完成資料庫建立、遷移和資料核對，再切換正式流量。正式資料庫應先套用 migrations，再以安全的資料搬移方式匯入本機帳號、角色、信眾、收支及活動資料；搬移含個資資料前，須確認目的資料庫與備份保存位置。
