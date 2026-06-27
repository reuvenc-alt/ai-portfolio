# ============================================================
#  התקנת מנוע הסריקה כמשימה מתוזמנת (רץ אוטומטית בכל כניסה למחשב)
#  הרצה: לחץ ימני על הקובץ -> "Run with PowerShell" (כמנהל)
#         או הדבק את התוכן בחלון PowerShell שנפתח As Administrator
# ============================================================

$pyw = "C:\Users\reuve\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"
$workDir = "E:\AI_Portfolio_Hebrew"

$action   = New-ScheduledTaskAction -Execute $pyw -Argument "worker.py" -WorkingDirectory $workDir
$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
                -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName "AI Portfolio Worker" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "Background AI stock scanner - emails alerts" -Force

Write-Host ""
Write-Host "✅ המשימה נוצרה! המנוע ירוץ אוטומטית בכל כניסה למחשב." -ForegroundColor Green
Write-Host "להפעלה מיידית עכשיו (בלי להתנתק):" -ForegroundColor Cyan
Write-Host "    Start-ScheduledTask -TaskName 'AI Portfolio Worker'"
