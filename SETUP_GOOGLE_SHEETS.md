# Google Sheets Setup Guide

Follow these steps to enable data persistence for your Housing Viability Calculator.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it (e.g., "Housing Calculator")
4. Click "Create"

## Step 2: Enable Google Sheets API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it and press "Enable"
4. Also search for "Google Drive API" and enable it

## Step 3: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Name it (e.g., "streamlit-app")
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"

## Step 4: Create & Download JSON Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON" format
5. Click "Create" - a JSON file will download

## Step 5: Add to Streamlit Secrets

### For Local Development:

1. Create a folder `.streamlit` in your project directory
2. Create a file `.streamlit/secrets.toml`
3. Open the downloaded JSON file and copy its contents
4. Format it in `secrets.toml` like this:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Private-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"

# Optional: Your email to share the sheet with
user_email = "your-email@gmail.com"

# RECOMMENDED: Password to protect save/load features from public users
storage_password = "your-secure-password-here"
```

**Important:** Change `your-secure-password-here` to a strong password. This prevents random visitors from saving data to your Google Sheets.

### For Streamlit Cloud:

1. Go to your Streamlit Cloud dashboard
2. Click on your app
3. Go to "Settings" → "Secrets"
4. Paste the same TOML content above
5. Click "Save"

## Step 6: Test the App

1. Run your Streamlit app locally: `streamlit run app.py`
2. The sidebar should show "Save/Load Apartments"
3. Try saving an apartment configuration
4. Check your Google Drive - a new spreadsheet "Housing Viability Data" should appear

## Security Notes

- ✅ Service account credentials are safe in Streamlit secrets (never exposed to users)
- ✅ The spreadsheet is only accessible to the service account (and your email if you added it)
- ✅ Website visitors cannot access your Google Sheets data
- ✅ **Password protection** prevents public users from saving/deleting data (if configured)
- ✅ **Rate limiting** prevents spam (max 1 save/delete per 2 seconds)
- ✅ **Input validation** prevents malicious apartment names
- ✅ **Hard limit** of 50 saved apartments prevents abuse
- ✅ **No error details** exposed to prevent system information leakage
- ❌ Never commit `.streamlit/secrets.toml` to Git (already in .gitignore)

### Recommended Security Setup

1. **Set a strong password** in `storage_password` secret
2. Only share this password with trusted users
3. Public users can still use the calculator, but cannot save/load data without the password
4. You can lock/unlock the storage feature using the sidebar button

## Troubleshooting

**Error: "Failed to connect to Google Sheets"**
- Check that both Google Sheets API and Google Drive API are enabled
- Verify your secrets.toml formatting (especially the private_key with `\n` characters)

**Error: "SpreadsheetNotFound"**
- The app will create the spreadsheet automatically on first save
- Check your Google Drive for "Housing Viability Data"

**Error: "Permission denied"**
- Make sure the service account has been created properly
- The service account email should match in your secrets

## Usage

Once set up:
1. Enter apartment details in the calculator
2. Go to sidebar → Enter a name → Click "Save"
3. Your data persists across sessions
4. Load any saved apartment to restore its values
5. Delete apartments you no longer need

**Data Location:** The spreadsheet will appear in the service account's Google Drive. To access it easily, share it with your personal email (the app does this automatically if you set `user_email` in secrets).
