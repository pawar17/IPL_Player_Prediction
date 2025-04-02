# Build the React frontend
Write-Host "Building React frontend..."
Set-Location frontend
npm run build

# Create static directory if it doesn't exist
Write-Host "Creating static directory..."
Set-Location ..
New-Item -ItemType Directory -Force -Path static

# Copy built files to static directory
Write-Host "Copying built files to static directory..."
Copy-Item -Path "frontend/build/*" -Destination "static/" -Recurse -Force

# Create deployment package
Write-Host "Creating deployment package..."
Remove-Item -Path "deploy" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path deploy

# Copy necessary files
Write-Host "Copying application files..."
Copy-Item "app.py" -Destination "deploy/"
Copy-Item "requirements.txt" -Destination "deploy/"
Copy-Item "Procfile" -Destination "deploy/"
Copy-Item "static" -Destination "deploy/" -Recurse

# Create ZIP file
Write-Host "Creating deployment ZIP..."
Compress-Archive -Path "deploy/*" -DestinationPath "deploy.zip" -Force

# Deploy to Azure App Service
Write-Host "Deploying to Azure App Service..."

# Register Microsoft.Web namespace if not already registered
Write-Host "Checking Microsoft.Web namespace registration..."
$registration = az provider show --namespace Microsoft.Web --query "registrationState" -o tsv
if ($registration -ne "Registered") {
    Write-Host "Registering Microsoft.Web namespace..."
    az provider register --namespace Microsoft.Web
    Write-Host "Waiting for registration to complete..."
    Start-Sleep -Seconds 30
}

# Create App Service Plan
Write-Host "Creating App Service Plan..."
az appservice plan create --name ipl-player-prediction-plan `
                        --resource-group ipl-player-prediction-rg `
                        --sku F1 `
                        --is-linux `
                        --location eastus

# Create the web app
Write-Host "Creating Web App..."
az webapp create --name ipl-player-prediction `
                --resource-group ipl-player-prediction-rg `
                --plan ipl-player-prediction-plan `
                --runtime "PYTHON:3.9"

# Configure the web app
Write-Host "Configuring Web App..."
az webapp config set --name ipl-player-prediction `
                    --resource-group ipl-player-prediction-rg `
                    --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app"

# Deploy the code
Write-Host "Deploying application code..."
az webapp deploy --name ipl-player-prediction `
                --resource-group ipl-player-prediction-rg `
                --src-path deploy.zip `
                --type zip

# Clean up
Write-Host "Cleaning up..."
Remove-Item "deploy.zip" -Force

Write-Host "Deployment complete! Your application should be available at:"
Write-Host "https://ipl-player-prediction.azurewebsites.net" 