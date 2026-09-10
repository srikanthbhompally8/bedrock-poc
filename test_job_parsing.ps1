Write-Host "Step 1: Logging in..."
$loginBody = @{
    email = "testuser@example.com"
    password = "TestPassword123!"
} | ConvertTo-Json

$loginResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json" -UseBasicParsing
$loginData = $loginResponse.Content | ConvertFrom-Json
$token = $loginData.access_token

Write-Host "Login response: $($loginResponse.Content)"
Write-Host "Token: $token`n"

if (-not $token) {
    Write-Host "ERROR: No token received!"
    exit 1
}

Write-Host "Step 2: Testing job parsing endpoint...`n"

$parseBody = @{
    job_description = "Senior Python Developer with 5 years of experience. Required: Python, PostgreSQL, Django. Nice to have: Kubernetes, AWS. Salary: 120k-160k. Education: BS Computer Science"
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host "Headers: $($headers | ConvertTo-Json)`n"

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/parse" -Method POST -Body $parseBody -Headers $headers -UseBasicParsing -ErrorAction Stop
    Write-Host "SUCCESS:`n" $response.Content
} catch {
    Write-Host "ERROR:`n" $_.ErrorDetails.Message
}
