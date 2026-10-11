$dllPath = Join-Path $PSScriptRoot "bin\livekit_ffi.dll"

# Get or create certificate
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -like "*LiveKit*" } | Select-Object -First 1

if (-not $cert) {
    Write-Host "Creating local self-signed Code Signing Certificate..."
    $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=LiveKit-Dev-Signer" -CertStoreLocation "Cert:\CurrentUser\My" -FriendlyName "LiveKit Dev Signing"
}

# Trust certificate in CurrentUser Root and TrustedPublisher stores
$rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store "Root", "CurrentUser"
$rootStore.Open("ReadWrite")
$rootStore.Add($cert)
$rootStore.Close()

$pubStore = New-Object System.Security.Cryptography.X509Certificates.X509Store "TrustedPublisher", "CurrentUser"
$pubStore.Open("ReadWrite")
$pubStore.Add($cert)
$pubStore.Close()

Write-Host "Signing $dllPath..."
$sig = Set-AuthenticodeSignature -FilePath $dllPath -Certificate $cert

Write-Host "Signature Status: " $sig.Status
Get-AuthenticodeSignature $dllPath
