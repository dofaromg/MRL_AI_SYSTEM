# MRL_dl580_local_run.ps1 — DL580 本地全接起（零外部 API、零按次計費）
# origin_signature = MrLiouWord
#
# 目標（建構者要求）：整套系統跑在你自己的 DL580 上，腦是本地 Ollama，
#   每次問答 $0。不經 Cloudflare、不經 Anthropic，不跟開發者多收錢。
#
# 用法：  powershell -ExecutionPolicy Bypass -File deploy\dl580\MRL_dl580_local_run.ps1
# 先備：  1) 安裝 Ollama 並啟動（ollama serve，預設 127.0.0.1:11434）
#         2) 拉一個模型，例如：ollama pull qwen2.5

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MrlHome = if ($env:MRL_HOME) { $env:MRL_HOME } else { (Resolve-Path (Join-Path $ScriptDir "..\..")).Path }
$MrlPort = if ($env:MRL_PORT) { $env:MRL_PORT } else { "8790" }
$OllamaHost = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { "http://127.0.0.1:11434" }
$env:OLLAMA_HOST = $OllamaHost
$env:MRL_PORT = $MrlPort
Set-Location $MrlHome

Write-Host "MRL_DL580_LOCAL_RUN  origin_signature=MrLiouWord"
Write-Host "MRL_HOME=$MrlHome  MRL_PORT=$MrlPort  OLLAMA_HOST=$OllamaHost"

# 1) 本地模型檢查（不通不中斷）
Write-Host "[1/4] 檢查本地 Ollama ..."
try {
  $tags = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -TimeoutSec 5
  $names = ($tags.models | ForEach-Object { $_.name }) -join " "
  if ($names) { Write-Host "   OK，可用模型：$names" } else { Write-Host "   連到 Ollama，但尚未 pull 模型：ollama pull qwen2.5" }
} catch {
  Write-Host "   [!] 連不到 Ollama ($OllamaHost)。請先： ollama serve  且  ollama pull qwen2.5"
  Write-Host "       平台仍會啟動，但 /api/chat 會走降級流程，直到 Ollama 就緒。"
}

# 2) 啟動母體平台（本地；/api/chat 優先用本地 Ollama）
Write-Host "[2/4] 啟動 MRL 平台（python MRL_Platform_Server.py）..."
$plat = Start-Process -FilePath "python" -ArgumentList "$MrlHome\MRL_Platform_Server.py" -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput "$MrlHome\MRL_platform.log" -RedirectStandardError "$MrlHome\MRL_platform.err.log"
Write-Host "   PID=$($plat.Id)（log: MRL_platform.log）"

# 3) 健康檢查
Write-Host "[3/4] 健康檢查 ..."
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
  try { Invoke-RestMethod -Uri "http://127.0.0.1:$MrlPort/health" -TimeoutSec 3 | Out-Null; $ok = $true; break } catch { Start-Sleep -Seconds 1 }
}
if ($ok) { Write-Host "   平台存活 http://127.0.0.1:$MrlPort/health" } else { Write-Error "平台未起，看 MRL_platform.log"; exit 1 }

# 4) 實測一句（走本地模型）
Write-Host "[4/4] 測 /api/chat（本地模型回答，`$0）..."
try {
  $r = Invoke-RestMethod -Uri "http://127.0.0.1:$MrlPort/api/chat" -Method Post -TimeoutSec 125 `
    -ContentType "application/json" -Body '{"message":"用一句繁體中文自我介紹"}'
  Write-Host ("   via=" + $r.via + "  model=" + $r.model)
  Write-Host ("   reply=" + $r.reply)
} catch { Write-Host "   /api/chat 失敗：$_" }

Write-Host ""
Write-Host "=== 完成：整套在你本地跑，每次問答零外部費用 ==="
Write-Host "平台 PID=$($plat.Id)（停止： Stop-Process -Id $($plat.Id)）。要給別人用就把此埠對外（方式你決定），腦始終在你機器上。"
