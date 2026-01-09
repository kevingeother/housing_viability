# Housing Viability Calculator - Data Persistence Feature

## What Was Added

Your app now has the ability to save and load apartment configurations using Google Sheets as the backend storage.

## Features

### Save Apartments
- Save current configuration with a custom name
- All input values are preserved (purchase price, rent, loans, depreciation, etc.)
- Timestamps automatically added

### Load Apartments
- View list of all saved apartments
- Load any saved apartment to restore all its values
- Apartment data persists across sessions

### Delete Apartments
- Remove apartments you no longer need
- Keeps your list clean and manageable

### New Apartment
- Clear loaded data to start fresh with default values
- Useful when comparing multiple properties

## Files Changed

1. **app.py** - Added Google Sheets integration:
   - Import statements for gspread and google-auth
   - Functions to save/load/delete apartments
   - Sidebar UI for save/load operations
   - Modified all inputs to use loaded values as defaults

2. **requirements.txt** - Added dependencies:
   - gspread
   - google-auth
   - google-auth-oauthlib
   - google-auth-httplib2

3. **SETUP_GOOGLE_SHEETS.md** - Complete setup guide

4. **.gitignore** - Protect your secrets file

## Setup Required

Before the feature works, you need to:

1. Create a Google Cloud project (free)
2. Enable Google Sheets API
3. Create a service account and download credentials
4. Add credentials to Streamlit secrets

**See SETUP_GOOGLE_SHEETS.md for detailed step-by-step instructions.**

## How It Works

### Data Storage
- Creates a Google Sheet named "Housing Viability Data"
- Each row is one saved apartment
- Columns match your input fields
- Only accessible to your service account

### Security
- Credentials stored in Streamlit secrets (never exposed)
- Service account can only access its own sheets
- Website visitors cannot access your data
- Optional: Share sheet with your personal email

## Usage Flow

1. **First Time Setup:**
   - Follow SETUP_GOOGLE_SHEETS.md
   - Add secrets to `.streamlit/secrets.toml` (local) or Streamlit Cloud settings

2. **Daily Use:**
   - Open app, enter apartment details
   - Sidebar → Enter name → Click "Save"
   - To load: Select from dropdown → Click "Load"
   - To start fresh: Click "New"

3. **Deployment:**
   - Push code to GitHub
   - Deploy on Streamlit Cloud
   - Add secrets in Streamlit Cloud dashboard
   - Your data persists across deployments

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Create secrets file
mkdir .streamlit
# Edit .streamlit/secrets.toml (see SETUP_GOOGLE_SHEETS.md)

# Run app
streamlit run app.py
```

## What Data Is Saved

All input fields are saved, including:
- Purchase price, parking, area, land ratio
- Transaction costs percentages
- Equity percentage
- Rent per sqm, parking rent, growth rate
- Furnishing costs and depreciation
- Maintenance fees and growth
- All depreciation settings (Sonder-AfA, degressive, linear)
- KfW and main loan amounts and rates
- Bereitstellungszins and grace period
- Tax rate
- Contract and construction dates
- Output horizon
- Property value growth rate

**Note:** Payment schedule currently uses defaults when loading (can be manually adjusted after load).

## Limitations

- Streamlit Cloud free tier: Container can restart (rare)
- Google Sheets: No built-in version history in UI (but Google Sheets keeps history)
- Max ~10 apartments recommended for best performance (no hard limit)

## Troubleshooting

If save/load doesn't work:
1. Check sidebar for error messages
2. Verify Google Sheets API is enabled
3. Check secrets.toml formatting
4. Ensure service account has permissions
5. Look for "Housing Viability Data" in Google Drive

For detailed troubleshooting, see SETUP_GOOGLE_SHEETS.md
