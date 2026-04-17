$ToolsDir = "D:\Tools"
if (!(Test-Path -Path $ToolsDir)) {
    New-Item -ItemType Directory -Path $ToolsDir
}

# 1. Download and extract uv
$uvUrl = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
$uvZip = "$ToolsDir\uv.zip"
$uvExtractDir = "$ToolsDir\uv"

if (!(Test-Path -Path "$uvExtractDir\uv.exe")) {
    Write-Host "Downloading uv..."
    Invoke-WebRequest -Uri $uvUrl -OutFile $uvZip
    Expand-Archive -Path $uvZip -DestinationPath $ToolsDir -Force
    Rename-Item -Path "$ToolsDir\uv-x86_64-pc-windows-msvc" -NewName "uv"
    Remove-Item -Path $uvZip
}
Write-Host "uv is ready at $uvExtractDir\uv.exe"

# 2. Download and extract MongoDB
$mongoUrl = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.0.5.zip"
$mongoZip = "$ToolsDir\mongo.zip"
$mongoExtractDir = "$ToolsDir\mongodb-windows-x86_64-7.0.5"

if (!(Test-Path -Path "$mongoExtractDir\bin\mongod.exe")) {
    Write-Host "Downloading MongoDB (this may take a few minutes)..."
    Invoke-WebRequest -Uri $mongoUrl -OutFile $mongoZip
    Expand-Archive -Path $mongoZip -DestinationPath $ToolsDir -Force
    Remove-Item -Path $mongoZip
}

# Create MongoDB data directory
$mongoDataDir = "$ToolsDir\mongodb_data"
if (!(Test-Path -Path $mongoDataDir)) {
    New-Item -ItemType Directory -Path $mongoDataDir
}

Write-Host "MongoDB is ready. To start it, run:"
Write-Host "$mongoExtractDir\bin\mongod.exe --dbpath $mongoDataDir"

# Add them to user path temporarily for this session (or permanently if needed)
Write-Host "Environment setup script completed."
