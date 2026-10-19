# Registers a Windows scheduled task that runs the data pipeline every weekday at 18:00,
# after the London Stock Exchange closes at 16:30.
#
#   powershell -ExecutionPolicy Bypass -File schedule_pipeline.ps1
#
# Remove it with:  Unregister-ScheduledTask -TaskName "InvestX Pipeline"

$backend = $PSScriptRoot
$python = (Get-Command python).Source

$action = New-ScheduledTaskAction -Execute $python -Argument "pipeline.py" -WorkingDirectory $backend
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 18:00
# Battery flags matter on laptops: by default Windows will not start the task on battery power
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName "InvestX Pipeline" -Action $action -Trigger $trigger -Settings $settings `
    -Description "Fetches, validates and stores daily prices for InvestX" -Force

Write-Host "Scheduled 'InvestX Pipeline' to run weekdays at 18:00 using $python"
