param(
    [string]$AuthBaseUrl = "http://127.0.0.1:8001",
    [string]$JobBaseUrl = "http://127.0.0.1:8002",
    [string]$CvBaseUrl = "http://127.0.0.1:8000",
    [string]$PdfPath = "C:\Users\safsa\Desktop\New folder\cvservice\cv_service\sample_cv.pdf",
    [int]$PollAttempts = 20,
    [int]$PollIntervalSeconds = 3
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-JsonRequest {
    param(
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )

    $request = @{
        Method = $Method
        Uri = $Url
        Headers = $Headers
    }

    if ($null -ne $Body) {
        $request["ContentType"] = "application/json"
        $request["Body"] = ($Body | ConvertTo-Json -Depth 8)
    }

    return Invoke-RestMethod @request
}

if (-not (Test-Path -LiteralPath $PdfPath)) {
    throw "Sample CV not found at $PdfPath"
}

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$email = "workflow.$stamp@example.com"
$password = "WorkflowPass123!"

Write-Host "Registering test user $email"
$registerPayload = @{
    nom = "Workflow"
    prenom = "Runner"
    role = "RECRUTEUR"
    email = $email
    entreprise = "QA Team"
    telephone = "0000000000"
    password = $password
    password_confirm = $password
}

$registerResponse = Invoke-JsonRequest -Method POST -Url "$AuthBaseUrl/api/auth/register/" -Body $registerPayload

Write-Host "Logging in"
$loginResponse = Invoke-JsonRequest -Method POST -Url "$AuthBaseUrl/api/auth/login/" -Body @{
    email = $email
    password = $password
}

$headers = @{
    Authorization = "Bearer $($loginResponse.access)"
}

Write-Host "Creating job"
$jobResponse = Invoke-JsonRequest -Method POST -Url "$JobBaseUrl/api/jobs/" -Headers $headers -Body @{
    title = "Senior Python Engineer $stamp"
    description = "Python Django RabbitMQ observability microservices scoring"
}

$jobId = $jobResponse.id
Write-Host "Created job id $jobId"

Write-Host "Uploading CV"
$uploadRaw = & curl.exe -s -X POST "$CvBaseUrl/api/upload/" `
    -H "Authorization: Bearer $($loginResponse.access)" `
    -F "candidate_name=Workflow Candidate" `
    -F "email=candidate.$stamp@example.com" `
    -F "job_id=$jobId" `
    -F "file=@$PdfPath;type=application/pdf"

$uploadResponse = $uploadRaw | ConvertFrom-Json
if ($uploadResponse.status -ne "processing") {
    throw "CV upload did not enter processing state. Response: $uploadRaw"
}

$uploadedCvId = $uploadResponse.cv_id

Write-Host "Polling ranking endpoint"
$rankingResponse = $null
for ($attempt = 1; $attempt -le $PollAttempts; $attempt++) {
    Start-Sleep -Seconds $PollIntervalSeconds
    $rankingResponse = Invoke-JsonRequest -Method GET -Url "$CvBaseUrl/api/job/$jobId/" -Headers $headers
    $scoredCv = $rankingResponse.cvs | Where-Object { $_.score -ne $null } | Select-Object -First 1
    if ($scoredCv) {
        Write-Host "Score received for CV $($scoredCv.cv_id): $($scoredCv.score)"
        break
    }
}

if (-not $rankingResponse -or -not ($rankingResponse.cvs | Where-Object { $_.score -ne $null })) {
    throw "No scored CV was returned after polling."
}

$notificationVerified = $false
try {
    $composeLogs = & docker compose -f "C:\Users\safsa\Desktop\New folder\cvservice\cv_service\docker-compose.yml" logs notification_service --tail 200
    $notificationPattern = '"event":\s*"cv_scored_notification".*"cv_id":\s*' + [regex]::Escape([string]$uploadedCvId) + '.*"job_id":\s*' + [regex]::Escape([string]$jobId)
    if ($composeLogs -match $notificationPattern) {
        $notificationVerified = $true
    }
} catch {
    Write-Warning "Notification log verification skipped because Docker logs were unavailable."
}

$result = [ordered]@{
    user_email = $email
    job_id = $jobId
    cv_id = $uploadedCvId
    score = ($rankingResponse.cvs | Where-Object { $_.score -ne $null } | Select-Object -First 1).score
    notification_verified = $notificationVerified
}

Write-Host "Workflow completed"
$result | ConvertTo-Json -Depth 5
