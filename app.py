# Investment Property Viability Calculator (Single Page)
import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np
import numpy_financial as npf
import json
from google.oauth2.service_account import Credentials
import gspread

st.set_page_config(page_title="Investment Property Calculator", layout="wide")

# =========================
# GOOGLE SHEETS SETUP
# =========================
def init_gsheet():
    """Initialize Google Sheets connection"""
    try:
        # Check if credentials exist
        if "gcp_service_account" not in st.secrets:
            return None
            
        # Load credentials from Streamlit secrets
        credentials_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(credentials)
        
        # Open or create the spreadsheet
        sheet_name = "Housing Viability Data"
        try:
            spreadsheet = client.open(sheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = client.create(sheet_name)
            # Share with your email (optional - set in secrets)
            if "user_email" in st.secrets:
                spreadsheet.share(st.secrets["user_email"], perm_type='user', role='writer')
        
        # Get or create the worksheet
        try:
            worksheet = spreadsheet.worksheet("Apartments")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="Apartments", rows=100, cols=50)
            # Add header row
            headers = [
                "apartment_name", "saved_date", "kaufpreis", "stellplatz", "area", "land_ratio",
                "real_estate_tax_pct", "notary_pct", "land_charge_fees_pct", "equity_pct",
                "rent_per_sqm", "rent_parking", "rent_growth_rate", "furnishing_costs",
                "furnishing_depreciation_rate", "furnishing_depreciation_years",
                "maintenance_base", "wg_management_fee", "unit_management_fee", "maintenance_growth",
                "sonder_afa_rate", "sonder_afa_years", "sonder_afa_base_amount",
                "degressive_afa_rate", "degressive_years", "linear_years",
                "kfw_loan_amount", "kfw_interest_rate", "kfw_tilgung_rate",
                "main_loan_rate", "main_loan_tilgung_rate",
                "bereitstellungszins", "grace_period_months", "tax_rate",
                "contract_date", "end_construction", "output_years",
                "num_payments", "payment_schedule", "sale_growth"
            ]
            worksheet.append_row(headers)
        
        return worksheet
    except Exception:
        # Never expose error details to public users
        return None

def save_apartment_to_sheets(worksheet, apartment_name, data):
    """Save apartment configuration to Google Sheets"""
    try:
        # Validate apartment name (prevent injection)
        if not apartment_name or len(apartment_name) > 100:
            return False
        if not apartment_name.replace(" ", "").replace("-", "").replace("_", "").isalnum():
            return False
            
        # Check total count (prevent spam)
        try:
            all_records = worksheet.get_all_records()
            if len(all_records) >= 50:  # Hard limit
                return False
        except:
            pass
        
        # Add timestamp
        data["saved_date"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        data["apartment_name"] = apartment_name
        
        # Convert data to row format matching headers
        row = [
            data["apartment_name"], data["saved_date"],
            data["kaufpreis"], data["stellplatz"], data["area"], data["land_ratio"],
            data["real_estate_tax_pct"], data["notary_pct"], data["land_charge_fees_pct"], data["equity_pct"],
            data["rent_per_sqm"], data["rent_parking"], data["rent_growth_rate"], data["furnishing_costs"],
            data["furnishing_depreciation_rate"], data["furnishing_depreciation_years"],
            data["maintenance_base"], data["wg_management_fee"], data["unit_management_fee"], data["maintenance_growth"],
            data["sonder_afa_rate"], data["sonder_afa_years"], data["sonder_afa_base_amount"],
            data["degressive_afa_rate"], data["degressive_years"], data["linear_years"],
            data["kfw_loan_amount"], data["kfw_interest_rate"], data["kfw_tilgung_rate"],
            data["main_loan_rate"], data["main_loan_tilgung_rate"],
            data["bereitstellungszins"], data["grace_period_months"], data["tax_rate"],
            data["contract_date"], data["end_construction"], data["output_years"],
            data["num_payments"], json.dumps(data["payment_schedule"]), data["sale_growth"]
        ]
        
        worksheet.append_row(row)
        return True
    except Exception:
        return False

def load_apartments_from_sheets(worksheet):
    """Load all saved apartments from Google Sheets"""
    try:
        records = worksheet.get_all_records()
        return records
    except Exception:
        return []

def delete_apartment_from_sheets(worksheet, apartment_name):
    """Delete an apartment from Google Sheets"""
    try:
        cell = worksheet.find(apartment_name)
        if cell:
            worksheet.delete_rows(cell.row)
            return True
        return False
    except Exception:
        return False

# =========================
# SIDEBAR - SAVE/LOAD
# =========================
# Rate limiting check
if 'last_save_time' not in st.session_state:
    st.session_state['last_save_time'] = 0
if 'last_delete_time' not in st.session_state:
    st.session_state['last_delete_time'] = 0

with st.sidebar:
    st.header("💾 Save/Load Apartments")
    
    # Simple authentication for save/load features
    storage_enabled = False
    if "storage_password" in st.secrets:
        if 'authenticated' not in st.session_state:
            st.session_state['authenticated'] = False
        
        if not st.session_state['authenticated']:
            with st.form("auth_form"):
                st.caption("🔒 Enter password to save/load data")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Unlock")
                if submitted:
                    if password == st.secrets["storage_password"]:
                        st.session_state['authenticated'] = True
                        st.rerun()
                    else:
                        st.error("Invalid password")
        else:
            storage_enabled = True
            if st.button("🔓 Lock", use_container_width=True):
                st.session_state['authenticated'] = False
                st.rerun()
    else:
        # No password configured, allow access if sheets are configured
        storage_enabled = True
    
    # Initialize Google Sheets only if authenticated
    worksheet = init_gsheet() if storage_enabled else None
    
    if worksheet:
        # Load saved apartments
        saved_apartments = load_apartments_from_sheets(worksheet)
        
        # Save current configuration
        st.subheader("Save Current")
        apartment_name = st.text_input("Apartment name", placeholder="e.g., Berlin Mitte 2BR", max_chars=50)
        if apartment_name and not apartment_name.replace(" ", "").replace("-", "").replace("_", "").isalnum():
            st.caption("⚠️ Use only letters, numbers, spaces, hyphens, and underscores")
        col_save, col_new = st.columns(2)
        with col_save:
            if st.button("💾 Save", type="primary", disabled=not apartment_name, use_container_width=True):
                # Rate limiting: max 1 save per 2 seconds
                import time
                current_time = time.time()
                if current_time - st.session_state.get('last_save_time', 0) < 2:
                    st.warning("Please wait before saving again")
                else:
                    st.session_state['last_save_time'] = current_time
                    st.session_state['pending_save'] = apartment_name
                    st.rerun()
        with col_new:
            if st.button("🆕 New", use_container_width=True):
                if 'loaded_data' in st.session_state:
                    del st.session_state['loaded_data']
                st.rerun()
        
        st.divider()
        
        # Load existing apartments
        st.subheader("Load Saved")
        if saved_apartments:
            apartment_names = [apt["apartment_name"] for apt in saved_apartments]
            selected_apartment = st.selectbox("Select apartment", [""] + apartment_names)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Load", disabled=not selected_apartment):
                    st.session_state['load_apartment'] = selected_apartment
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", disabled=not selected_apartment):
                    # Rate limiting: max 1 delete per 2 seconds
                    import time
                    current_time = time.time()
                    if current_time - st.session_state.get('last_delete_time', 0) < 2:
                        st.warning("Please wait before deleting again")
                    else:
                        st.session_state['last_delete_time'] = current_time
                        if delete_apartment_from_sheets(worksheet, selected_apartment):
                            st.success(f"Deleted '{selected_apartment}'")
                            st.rerun()
                        else:
                            st.error("Delete failed")
            
            st.caption(f"{len(saved_apartments)} apartment(s) saved")
        else:
            st.info("No saved apartments yet")
    else:
        st.info("💡 Storage not configured")
        st.caption("Contact the app owner to enable save/load features.")

st.title("Investment Property Viability Calculator")
st.divider()

# =========================
# INPUTS
# =========================
# Check if we have loaded data
loaded = st.session_state.get('loaded_data', {})

st.header("Purchase & Property")
col1, col2, col3 = st.columns(3)
with col1:
  kaufpreis = st.number_input("[A] Purchase price (€)", value=int(loaded.get("kaufpreis", 343200)), step=5000)
  stellplatz = st.number_input("[B] Parking garage price (€)", value=int(loaded.get("stellplatz", 30000)), step=1000)
with col2:
  area = st.number_input("[C] Living area (sqm)", value=float(loaded.get("area", 36)))
with col3:
  land_ratio = st.slider("[D] Property to land value ratio", 0.0, 1.0, float(loaded.get("land_ratio", 0.84)), 0.01)

# Summary outputs
total_purchase_price = kaufpreis + stellplatz
price_per_sqm = kaufpreis / area if area > 0 else 0
depreciation_base_price = total_purchase_price * land_ratio
col_a, col_b, col_c = st.columns(3)
col_a.metric("[E] Total purchase price {A + B}", f"€ {total_purchase_price:,.2f}")
col_b.metric("Price per sqm (apartment only) {A/C}", f"€ {price_per_sqm:,.2f}")
col_c.metric("Depreciation base (property) {E*D}", f"€ {depreciation_base_price:,.2f}")
st.divider()

st.header("Transaction Costs")
col1, col2, col3 = st.columns(3)
with col1:
  col4, col5 = st.columns(2)
  with col4:
    real_estate_transfer_tax = st.number_input("Real estate tax (%)", value=float(loaded.get("real_estate_tax_pct", 3.5))) / 100 * total_purchase_price
    notary = st.number_input("Notary (%)", value=float(loaded.get("notary_pct", 1.5))) / 100 * total_purchase_price
    land_charge_registration_fees = st.number_input("Land charge fees (%)", value=float(loaded.get("land_charge_fees_pct", 0))) / 100 * total_purchase_price
    total_nbk = real_estate_transfer_tax + notary + land_charge_registration_fees
  with col5:
    st.metric("", f"€ {real_estate_transfer_tax:,.2f}")
    st.metric("", f"€ {notary:,.2f}")
    st.metric("", f"€ {land_charge_registration_fees:,.2f}")
    st.metric("[F] Total transaction costs (NBK)", f"€ {total_nbk:,.2f}")


total_investment = total_purchase_price + total_nbk
total_afa_value = total_investment * land_ratio
with col2:
  col2.metric("[G] Total investment {E+F}", f"€ {total_investment:,.2f}")
  col2.metric("[H] Total depreciation base {G*D}", f"€ {total_afa_value:,.2f}")
st.divider()

st.header("Equity")
col1, col2 = st.columns(2)
with col1:
  col3, col4 = st.columns(2)
  with col3:
    eigenkapital = st.number_input("Equity (%)", value=float(loaded.get("equity_pct", 10.0))) / 100 * total_investment
  with col4:
    st.metric("", f"€ {eigenkapital:,.2f}")
st.divider()


st.header("Rent")
col1, col2, col3 = st.columns(3)
with col1:
  col4, col5 = st.columns(2)
  with col4:
    rent_per_sqm = st.number_input("Rent per sqm (€)", value=float(loaded.get("rent_per_sqm", 25.0)), step=0.5)
    rent_property = rent_per_sqm * area
    rent_parking = st.number_input("Parking rent (€)", value=int(loaded.get("rent_parking", 50)), step=10)
    rent_total = rent_per_sqm * area + rent_parking
  with col5:
    st.metric("Monthly Rent", f"€ {rent_property:,.2f}")
    st.metric("", f"€ {rent_parking:,.2f}")
    st.metric("Total", f"€ {rent_total:,.2f}")
with col2:
    st.metric("Annual Rent", f"€ {rent_property * 12:,.2f}")
    st.metric("", f"€ {rent_parking * 12:,.2f}")
    st.metric("Total", f"€ {rent_total * 12:,.2f}")
with col1:
    rent_growth_rate = st.number_input("Annual rent growth (%)", value=float(loaded.get("rent_growth_rate", 2.0))) / 100
st.divider()

st.header("Furnishing")
col1, col2, col3 = st.columns(3)
with col1:
  furnishing_costs = st.number_input("Furnishing costs (€)", value=int(loaded.get("furnishing_costs", 5000)))
with col2:
  furnishing_annual_depreciation_rate = st.number_input("Furnishing depreciation rate (%)", value=float(loaded.get("furnishing_depreciation_rate", 10.0))) / 100
with col3:
  furnishing_depreciation_years = st.number_input("Furnishing depreciation years", value=int(loaded.get("furnishing_depreciation_years", 10)))
  # Validate furnishing depreciation: rate * years should equal 100%
if abs(furnishing_annual_depreciation_rate * furnishing_depreciation_years - 1.0) > 1e-6:
  total_pct = (furnishing_annual_depreciation_rate * furnishing_depreciation_years) * 100
  st.warning(f"Furnishing depreciation total = {total_pct:.1f}% (rate * years). It should equal 100%.")
yearly_furnishing_depreciation = furnishing_costs * furnishing_annual_depreciation_rate
st.metric("Yearly furnishing depreciation", f"€ {yearly_furnishing_depreciation:,.2f}")
st.divider()

st.header("Maintenance")
col1, col2, col3, col4 = st.columns(4)
with col1:
  maintenance_base = st.number_input("Maintenance (monthly €)", value=int(loaded.get("maintenance_base", 30)))
with col2:
  wg_management_fee = st.number_input("WG management fee (monthly €)", value=int(loaded.get("wg_management_fee", 30)))
with col3:
  unit_management_fee = st.number_input("Unit management fee (monthly €)", value=int(loaded.get("unit_management_fee", 0)))
with col4:  
  maintenance_growth = st.number_input("Maintenance growth (annual %)", value=float(loaded.get("maintenance_growth", 2.0))) / 100
maintenance_total = maintenance_base + wg_management_fee + unit_management_fee
st.metric("Total monthly maintenance", f"€ {maintenance_total:,.2f}")
st.divider()

st.header("Depreciation")
col1, col2, col3 = st.columns(3)
with col1:
  sonder_afa_rate = st.number_input("Sonder-AfA rate (%)", value=float(loaded.get("sonder_afa_rate", 5.0))) / 100
with col2:
  sonder_afa_years = st.number_input("Sonder-AfA years", value=int(loaded.get("sonder_afa_years", 4)))
with col3:
  sonder_afa_base_amount = st.number_input("Sonder-AfA base amount (€)", value=int(loaded.get("sonder_afa_base_amount", 286000)), step=1000)
with col1:
  degressive_afa_rate = st.number_input("Degressive AfA rate (%)", value=float(loaded.get("degressive_afa_rate", 5.0))) / 100
with col2:
  degressive_years = st.number_input("Degressive AfA years", value=int(loaded.get("degressive_years", 10)))
with col3:
  linear_years = st.number_input("Linear Afa Years", value=int(loaded.get("linear_years", 40)))
# total useful years = degressive period + linear period
useful_years = degressive_years + linear_years
st.divider()

st.header("Financing")
st.subheader("KfW Loan")
col1, _, _ = st.columns(3)
with col1:
  kfw_loan_amount = st.number_input("KfW loan amount (€)", value=int(loaded.get("kfw_loan_amount", 150000)), step=1000)
col1, col2, col3 = st.columns(3)
with col1:
  kfw_interest_rate = st.number_input("KfW interest (%)", value=float(loaded.get("kfw_interest_rate", 2.3))) / 100
  kfw_tilgung_rate = st.number_input("KfW Tilgung (%)", value=float(loaded.get("kfw_tilgung_rate", 2.0))) / 100
with col2:
  kfw_interest = kfw_loan_amount * kfw_interest_rate
  kfw_tilgung = kfw_loan_amount * kfw_tilgung_rate
  st.metric("Monthly KfW interest", f"€ {kfw_interest / 12:,.2f}")
  st.metric("Monthly KfW tilgung", f"€ {kfw_tilgung / 12:,.2f}")
with col3:
  st.metric("Annual KfW interest", f"€ {kfw_interest:,.2f}")
  st.metric("Annual KfW tilgung", f"€ {kfw_tilgung:,.2f}")
   
st.subheader("Main Loan")
col1, _, _ = st.columns(3)
with col1:
  main_loan_amount = total_investment - eigenkapital - kfw_loan_amount
  st.metric("Main loan amount (€)", f"€ {main_loan_amount:,.2f}")
col1, col2, col3 = st.columns(3)
with col1:
  main_loan_rate = st.number_input("Main loan interest (%)", value=float(loaded.get("main_loan_rate", 4.0))) / 100
  main_loan_tilgung_rate = st.number_input("Main loan Tilgung (%)", value=float(loaded.get("main_loan_tilgung_rate", 2.0))) / 100
with col2:
  main_loan_interest = main_loan_amount * main_loan_rate
  main_loan_tilgung = main_loan_amount * main_loan_tilgung_rate
  st.metric("Monthly main loan interest", f"€ {main_loan_interest / 12:,.2f}")
  st.metric("Monthly main loan tilgung", f"€ {main_loan_tilgung / 12:,.2f}")
with col3:
  st.metric("Annual main loan interest", f"€ {main_loan_interest:,.2f}")
  st.metric("Annual main loan tilgung", f"€ {main_loan_tilgung:,.2f}")

with col2:
  total_monthly = (kfw_interest + main_loan_interest) / 12 + (kfw_tilgung + main_loan_tilgung) / 12
  st.metric("Total monthly loan payment", f"€ {total_monthly:,.2f}")
with col3:
  total_annual = kfw_interest + main_loan_interest + kfw_tilgung + main_loan_tilgung
  st.metric("Total annual loan payment", f"€ {total_annual:,.2f}")

col1, col2, col3 = st.columns(3)
with col1:
  bereitstellungszins = st.number_input("Bereitstellungszins (% / month)", value=float(loaded.get("bereitstellungszins", 0.25))) / 100
with col2:
  grace_period_months = st.number_input("Grace period (months)", value=int(loaded.get("grace_period_months", 12)))
st.divider()

st.header("Tax")
col1, col2, col3 = st.columns(3)
with col1:
  tax_rate = st.number_input("Marginal tax rate (%)", value=float(loaded.get("tax_rate", 42.0))) / 100
st.divider()

st.header("Timeline")
col1, col2, col3 = st.columns(3)
with col1:
  default_contract = date.fromisoformat(loaded["contract_date"]) if "contract_date" in loaded else date(2026, 2, 15)
  contract_date = st.date_input("Contract date", value=default_contract)
with col2:
  default_construction = date.fromisoformat(loaded["end_construction"]) if "end_construction" in loaded else date(2026, 12, 31)
  end_construction = st.date_input("Construction end date", value=default_construction)
with col3:
  output_years = st.number_input("Output horizon (years)", value=int(loaded.get("output_years", 30)))



# --- Timeline handling ---
start_month = pd.Timestamp(contract_date.year, contract_date.month, 1)
rent_start = pd.Timestamp(end_construction.year, end_construction.month, 1) + relativedelta(months=1)

st.subheader("Installment Payment Schedule")
with st.expander("Installment payment schedule (property)", expanded=False):
# Construction payment schedule (editable via inputs)
  default_shares = [0.30, 0.15, 0.13, 0.12, 0.14, 0.16]

  num_payments = st.number_input("Number of payment installments", min_value=1, max_value=12, value=len(default_shares), step=1)
  # compute default offsets evenly between contract date and construction end
  # months between contract and construction end (can be 0)
  months_between = max(0, (end_construction.year - contract_date.year) * 12 + (end_construction.month - contract_date.month))
  num_payments_int = int(num_payments)
  if num_payments_int > 1:
    default_offsets = [int(round(i * months_between / (num_payments_int - 1))) for i in range(num_payments_int)]
    # ensure last payment falls exactly on construction end month
    default_offsets[-1] = months_between
  else:
    # single payment => at construction end
    default_offsets = [months_between]

  st.caption("Enter each installment as a share of the property purchase price (0-1) and the month offset from contract date.")
  payment_schedule = []
  for i in range(int(num_payments)):
    col_share, col_amount, col_offset, col_date = st.columns([2, 2, 1, 1])
    with col_share:
      share = st.number_input(
        f"Installment {i+1} share",
        key=f"ps_share_{i}",
        min_value=0.0,
        max_value=1.0,
        value=float(default_shares[i]) if i < len(default_shares) else 0.0,
        step=0.01
      )

    # computed amount (share * property purchase price)
    pay_amt = total_purchase_price * float(share)
    with col_amount:
      st.write("--")
      st.write(f"€ {pay_amt:,.2f}")

    with col_offset:
      offset = st.number_input(
        f"Offset (months)",
        key=f"ps_offset_{i}",
        min_value=0,
        value=int(default_offsets[i]) if i < len(default_offsets) else i * 3,
        step=1
      )

    with col_date:
      pay_date = pd.Timestamp(contract_date.year, contract_date.month, 1) + pd.DateOffset(months=int(offset))
      st.write("--")
      st.write(pay_date.strftime("%b %Y"))

    payment_schedule.append((share, int(offset)))

  # warn user if total shares do not equal 1.0 (allow small numerical tolerance)
  total_shares = sum(s for s, _ in payment_schedule)
  if abs(total_shares - 1.0) > 1e-6:
      st.warning(f"Total installment shares = {total_shares:.3f} — should equal 1.0. Adjust shares or normalize.")
st.divider()

# =========================
# SIMULATION & DETAILED TABLES
# =========================
st.header("📋 Detailed Analysis Tables")
st.caption("Technical details of loan amortization and tax calculations")

months = []
bal_main = 0.0
bal_kfw = 0.0
equity_remaining = eigenkapital
remaining_deg_value = total_afa_value

# prepare year_data so amortization table and other logic use the same calculations
start_year = start_month.year
# last output year (used to ensure simulation runs through December of that year)
last_output_year = start_year + int(output_years) - 1
year_data = {
  y: {
    "kfw_draw": 0.0,
    "main_draw": 0.0,
    "kfw_int": 0.0,
    "kfw_princ": 0.0,
    "main_int_drawn": 0.0,
    "main_prov": 0.0,
    "main_princ": 0.0,
    "end_bal_kfw": 0.0,
    "end_bal_main": 0.0
  }
  for y in range(start_year, start_year + int(output_years))
}

# Precompute constant monthly annuity payments (based on initial loan amounts)
monthly_payment_kfw = kfw_loan_amount * (kfw_interest_rate + kfw_tilgung_rate) / 12
monthly_payment_main = main_loan_amount * (main_loan_rate + main_loan_tilgung_rate) / 12

## Amortization-first: build monthly amortization schedule from inputs
monthly_amort = []
bal_kfw = 0.0
bal_main = 0.0
cum_main_drawn = 0.0
equity_rem = eigenkapital
# simulate through December of the final output year
last_month = pd.Timestamp(last_output_year, 12, 1)
total_months = (last_month.year - start_month.year) * 12 + (last_month.month - start_month.month) + 1
for m in range(total_months):
  date_m = start_month + pd.DateOffset(months=m)

  # draws
  draw = 0.0
  if date_m == start_month:
    draw += total_nbk
    draw += furnishing_costs
  for share, offset in payment_schedule:
    if date_m == start_month + pd.DateOffset(months=offset):
      draw += total_purchase_price * share

  # equity first
  equity_used = min(draw, equity_rem)
  equity_rem -= equity_used
  financed = max(0.0, draw - equity_used)

  month_kfw_draw = 0.0
  month_main_draw = 0.0
  if financed > 0:
    if bal_kfw < kfw_loan_amount:
      kfw_draw = min(financed, kfw_loan_amount - bal_kfw)
      bal_kfw += kfw_draw
      financed -= kfw_draw
      month_kfw_draw = kfw_draw
    if financed > 0:
      bal_main += financed
      month_main_draw = financed
      cum_main_drawn += month_main_draw

  # interest/principal per amort rules
  bereitstellung = 0.0
  if date_m < rent_start:
    interest_kfw = bal_kfw * kfw_interest_rate / 12 if bal_kfw > 0 else 0.0
    principal_kfw = 0.0

    interest_main_drawn = bal_main * main_loan_rate / 12 if bal_main > 0 else 0.0
    principal_main = 0.0

    if m >= grace_period_months:
      unused_main = max(0.0, main_loan_amount - bal_main)
      bereitstellung = unused_main * bereitstellungszins
    interest_main_total = interest_main_drawn + bereitstellung
  else:
    interest_kfw = bal_kfw * kfw_interest_rate / 12
    principal_kfw = max(0.0, monthly_payment_kfw - interest_kfw)
    principal_kfw = min(principal_kfw, bal_kfw)
    bal_kfw -= principal_kfw

    interest_main_drawn = bal_main * main_loan_rate / 12
    principal_main = max(0.0, monthly_payment_main - interest_main_drawn)
    principal_main = min(principal_main, bal_main)
    bal_main -= principal_main
    interest_main_total = interest_main_drawn

  monthly_amort.append({
    "date": date_m,
    "kfw_draw": month_kfw_draw,
    "main_draw": month_main_draw,
    "equity_used": equity_used,
    # KfW grouped fields (German labels for interest/principal)
    "Zinsen KfW": interest_kfw,
    "Tilgung KfW": principal_kfw,
    "KfW Payment": interest_kfw + principal_kfw,
    "Remaining KfW Balance": bal_kfw,
    # Main loan fields
    "Main Draw": month_main_draw,
    "Zinsen Main": interest_main_drawn,
    "Tilgung Main": principal_main,
    "Main Undrawn": max(0.0, main_loan_amount - cum_main_drawn),
    "Bereitstellung": bereitstellung,
    "Remaining Main Balance": bal_main,
    # Totals
    "Total Monthly Payment": (interest_kfw + principal_kfw + interest_main_drawn + principal_main + bereitstellung),
    "Total Loan Remaining": bal_kfw + bal_main,
    # legacy fields (kept for compatibility)
    "interest_kfw": interest_kfw,
    "principal_kfw": principal_kfw,
    "interest_main_drawn": interest_main_drawn,
    "provision": bereitstellung,
    "interest_main_total": interest_main_total,
    "principal_main": principal_main,
    "bal_kfw": bal_kfw,
    "bal_main": bal_main,
    "loan_balance": bal_kfw + bal_main
  })

## Build yearly aggregation from monthly amortization
## Build yearly aggregation from monthly amortization
year_data = {}
for entry in monthly_amort:
  y = entry["date"].year
  yd = year_data.setdefault(y, {"kfw_draw":0.0, "main_draw":0.0, "kfw_int":0.0, "kfw_princ":0.0, "kfw_payment":0.0, "main_int_drawn":0.0, "main_prov":0.0, "main_princ":0.0, "main_undrawn":0.0, "total_payment":0.0, "end_bal_kfw":0.0, "end_bal_main":0.0})
  yd["kfw_draw"] += entry.get("kfw_draw", 0.0)
  yd["main_draw"] += entry.get("main_draw", 0.0)
  yd["kfw_int"] += entry.get("interest_kfw", 0.0)
  yd["kfw_princ"] += entry.get("principal_kfw", 0.0)
  yd["kfw_payment"] += entry.get("KfW Payment", 0.0)
  yd["main_int_drawn"] += entry.get("interest_main_drawn", 0.0)
  yd["main_prov"] += entry.get("provision", 0.0)
  yd["main_princ"] += entry.get("principal_main", 0.0)
  # record last seen undrawn and balances for the year (end of year values)
  yd["main_undrawn"] = entry.get("Main Undrawn", yd.get("main_undrawn", 0.0))
  yd["total_payment"] += entry.get("Total Monthly Payment", 0.0)
  yd["end_bal_kfw"] = entry.get("bal_kfw", 0.0)
  yd["end_bal_main"] = entry.get("bal_main", 0.0)


## Now build the monthly cashflow simulation using the amortization schedule
months = []
for entry in monthly_amort:
  date_m = entry["date"]
  # rent
  rent = 0.0
  if date_m >= rent_start:
    # growth starts in Jan of the second year after rental start
    months_since_rent = (date_m.year - rent_start.year) * 12 + (date_m.month - rent_start.month)
    growth_years = max(0, months_since_rent // 12)
    rent = rent_total * ((1 + rent_growth_rate) ** growth_years)

  # AfA
  afa = 0.0
  if date_m >= rent_start:
    # Use calendar-year counts from rental start for depreciation rules
    year_index = date_m.year - rent_start.year  # 0 for completion year

    # Sonder-AfA: flat annual rate (not pro rata) for the completion year and following years
    sonder_monthly = 0.0
    # annual Sonder-AfA base amount specified in euros
    annual_sonder = sonder_afa_base_amount * sonder_afa_rate
    if year_index < int(sonder_afa_years):
      if year_index == 0:
        # completion year: give full annual Sonder-AfA regardless of start month
        remaining_months_in_year = 12 - (rent_start.month - 1)
        if remaining_months_in_year > 0:
          sonder_monthly = annual_sonder / remaining_months_in_year
        else:
          sonder_monthly = annual_sonder / 12
      else:
        # subsequent years: distribute annual evenly over 12 months
        sonder_monthly = annual_sonder / 12

    # Degressive: run for exact degressive period in months (pro rata), then linear pro rata thereafter
    degressive_monthly = 0.0
    linear_monthly = 0.0
    # last month of degressive period
    degressive_end_month = rent_start + relativedelta(years=int(degressive_years)) - pd.DateOffset(months=1)
    # last month of linear period (end of useful years)
    linear_end_month = rent_start + relativedelta(years=int(useful_years)) - pd.DateOffset(months=1)

    # Last output year should be treated as a full year (12 months) per user request
    last_output_year = start_year + int(output_years) - 1

    if date_m <= degressive_end_month:
      # degressive applies this month (pro rata by month)
      degressive_monthly = remaining_deg_value * degressive_afa_rate / 12
      remaining_deg_value -= degressive_monthly
      remaining_deg_value = max(0.0, remaining_deg_value)  # FIX: AfA floor
    else:
      # linear applies from the month after degressive_end_month until linear_end_month
      # cap the linear end to the simulation's last month so the distribution uses the simulated horizon
      effective_linear_end = min(linear_end_month, last_month)
      remaining_linear_months = (effective_linear_end.year - date_m.year) * 12 + (effective_linear_end.month - date_m.month) + 1
      if remaining_linear_months > 0:
        if remaining_deg_value > 0:
          linear_monthly = remaining_deg_value / remaining_linear_months
          remaining_deg_value -= linear_monthly
          remaining_deg_value = max(0.0, remaining_deg_value)  # FIX
      else:
          linear_monthly = 0.0

    # furnishing depreciation (annual converted to monthly)
    # furnishing depreciation: fixed annual amount, pro rata in first and final year
    annual_furnishing = yearly_furnishing_depreciation
    # compute furnishing depreciation period end month
    furnishing_end = rent_start + relativedelta(years=int(furnishing_depreciation_years))
    last_furnishing_month = furnishing_end - pd.DateOffset(months=1)
    if date_m < rent_start or date_m > last_furnishing_month:
      furnishing_monthly = 0.0
    else:
      # first year (pro rata across remaining months in start year)
      if date_m.year == rent_start.year:
        remaining_months_in_year = 12 - (rent_start.month - 1)
        furnishing_monthly = annual_furnishing / remaining_months_in_year if remaining_months_in_year > 0 else annual_furnishing / 12
      # final year (pro rata across months in final year up to last_furnishing_month)
      elif date_m.year == last_furnishing_month.year:
        # If this is the final output year, treat furnishing as full-year
        if date_m.year == (start_year + int(output_years) - 1):
          months_in_final_year = 12
        else:
          months_in_final_year = last_furnishing_month.month
        furnishing_monthly = annual_furnishing / months_in_final_year if months_in_final_year > 0 else annual_furnishing / 12
      else:
        furnishing_monthly = annual_furnishing / 12

    # sum into monthly AfA
    afa += sonder_monthly + degressive_monthly + linear_monthly + furnishing_monthly

  # maintenance applies only from rental start; growth begins in Jan of the second year after rental start
  if date_m >= rent_start:
    growth_years = max(0, date_m.year - (rent_start.year + 1))
    maintenance = maintenance_total * ((1 + maintenance_growth) ** growth_years)
  else:
    maintenance = 0.0

  # tax
  interest_total = entry["interest_kfw"] + entry["interest_main_total"]
  provision = entry["provision"]
  # Gross Income = rent - interest - all depreciation - maintenance
  gross_income = rent - interest_total - afa - maintenance
  
  # Tax Refund / Tax Paid: negative gross_income => refund, positive => tax payable
  # In Germany (Vermietung und Verpachtung), rental property losses can be offset
  # against other income (e.g., salary) in the same tax year
  # Negative gross income → tax refund at your marginal rate
  # Positive gross income → additional tax owed at your marginal rate
  tax_refund = -gross_income * tax_rate

  # cashflow includes tax refund (Tax Paid column removed)
  cashflow = rent - interest_total - provision - maintenance + tax_refund
  months.append({
    "date": date_m,
    # income / basic
    "Rent": rent,
    "Zinsen": interest_total,
    # depreciation breakdown
    "Sonder-Afa": locals().get('sonder_monthly', 0.0) if date_m >= rent_start else 0.0,
    "Degressive-Afa 10": locals().get('degressive_monthly', 0.0) if date_m >= rent_start else 0.0,
    "Linear-Afa 11": locals().get('linear_monthly', 0.0) if date_m >= rent_start else 0.0,
    "Dep Furnishing": furnishing_monthly if date_m >= rent_start else 0.0,
    "Maintenance": maintenance,
    "Gross Income": gross_income,
    "Tax Refund": tax_refund,
    "Equity Invested": entry.get("equity_used", 0.0),
    # loan details (KfW)
    "Zinsen KfW": entry.get("interest_kfw", 0.0),
    "Tilgung KfW": entry.get("principal_kfw", 0.0),
    "KfW Payment": entry.get("KfW Payment", 0.0),
    "Remaining KfW Balance": entry.get("bal_kfw", 0.0),
    # loan details (Main)
    "Main Draw": entry.get("main_draw", entry.get("Main Draw", 0.0)),
    "Zinsen Main": entry.get("interest_main_drawn", 0.0),
    "Tilgung Main": entry.get("principal_main", 0.0),
    "Main Undrawn": entry.get("Main Undrawn", 0.0),
    "Bereitstellung": entry.get("provision", 0.0),
    "Remaining Main Balance": entry.get("bal_main", 0.0),
    # totals
    "Total Monthly Payment": entry.get("Total Monthly Payment", 0.0),
    "Total Loan Remaining": entry.get("loan_balance", 0.0),
    # summary
    "interest": interest_total,
    "cashflow": cashflow,
    "loan_balance": entry.get("loan_balance", 0.0)
  })

# =========================
# OUTPUT
# =========================

df = pd.DataFrame(months)
df["year"] = df["date"].dt.year
# total initial loan amount (KfW + Main)
total_loan_amount = kfw_loan_amount + main_loan_amount
# compute tilgung and cumulative tilgung on the raw df so yearly calcs can use it
df["Tilgung"] = df.get("Tilgung KfW", 0.0) + df.get("Tilgung Main", 0.0)
df["cum_tilgung"] = df["Tilgung"].cumsum()
# Aggregate yearly using the new column names introduced for Tax/Cashflow
agg_map = {}
for col in ["Rent", "Zinsen", "Sonder-Afa", "Degressive-Afa 10", "Linear-Afa 11", "Dep Furnishing", "Maintenance", "Tax Paid", "Tax Refund", "cashflow", "Total Monthly Payment"]:
  if col in df.columns:
    agg_map[col] = 'sum'
if "Total Loan Remaining" in df.columns:
  agg_map["Total Loan Remaining"] = 'last'

if agg_map:
  yearly = df.groupby("year").agg(agg_map).fillna(0)
else:
  yearly = pd.DataFrame()

# Build simplified yearly cashflow summary (and monthly-ready fields)
if not df.empty:
  # drop any existing 'year' column so it isn't summed and doesn't conflict on reset_index
  temp = df.drop(columns=["year"], errors='ignore')
  grouped = temp.groupby(temp["date"].dt.year).sum(numeric_only=True)
  grouped.index.name = "year"
  grouped = grouped.reset_index()
  # ensure tilgung fields exist
  grouped["Tilgung KfW"] = grouped.get("Tilgung KfW", 0.0)
  grouped["Tilgung Main"] = grouped.get("Tilgung Main", 0.0)
  grouped["Tilgung"] = grouped["Tilgung KfW"] + grouped["Tilgung Main"]
  grouped["Maintenance"] = grouped.get("Maintenance", 0.0)
  grouped["Tax Refund"] = grouped.get("Tax Refund", 0.0)
  grouped["Equity Invested"] = grouped.get("Equity Invested", 0.0)
  # Add AfA (depreciation) columns
  grouped["Sonder-Afa"] = grouped.get("Sonder-Afa", 0.0)
  grouped["Degressive-Afa 10"] = grouped.get("Degressive-Afa 10", 0.0)
  grouped["Linear-Afa 11"] = grouped.get("Linear-Afa 11", 0.0)
  grouped["Dep Furnishing"] = grouped.get("Dep Furnishing", 0.0)
  grouped["Total AfA"] = grouped["Sonder-Afa"] + grouped["Degressive-Afa 10"] + grouped["Linear-Afa 11"] + grouped["Dep Furnishing"]
  grouped["Total Before Tax Refund"] = grouped.get("Rent", 0.0) - grouped.get("Zinsen", 0.0) - grouped.get("Tilgung", 0.0) - grouped.get("Maintenance", 0.0)
  grouped["Total Cash Flow"] = grouped["Total Before Tax Refund"] + grouped["Tax Refund"]
  # determine year-end loan remaining based on cumulative tilgung
  # FIX: use amortization balance as single source of truth
  loan_remaining_by_year = df.groupby(df["date"].dt.year)["loan_balance"].last()
  grouped["Loan Remaining"] = grouped["year"].map(loan_remaining_by_year)
  # yearly net cash movement and Cumulative Cash Movement
  grouped["Net Cash Movement"] = grouped["Total Cash Flow"] - grouped.get("Equity Invested", 0.0)
  grouped["Cumulative Cash Movement"] = grouped["Net Cash Movement"].cumsum()
  yearly_cashflow = grouped[["year", "Rent", "Zinsen", "Tilgung", "Maintenance", "Sonder-Afa", "Degressive-Afa 10", "Linear-Afa 11", "Dep Furnishing", "Total AfA", "Total Before Tax Refund", "Tax Refund", "Total Cash Flow", "Equity Invested", "Net Cash Movement", "Cumulative Cash Movement", "Loan Remaining"]]
else:
  yearly_cashflow = pd.DataFrame()

# Yearly amortization table (from aggregated year_data)
amort_rows = []
for y in range(start_year, start_year + int(output_years)):
  yd = year_data.get(y, {"kfw_draw":0.0, "main_draw":0.0, "kfw_int":0.0, "kfw_princ":0.0, "kfw_payment":0.0, "main_int_drawn":0.0, "main_prov":0.0, "main_princ":0.0, "main_undrawn":0.0, "total_payment":0.0, "end_bal_kfw":0.0, "end_bal_main":0.0})
  main_interest_total = yd['main_int_drawn'] + yd['main_prov']
  amort_rows.append({
    'Year': y,
    # KfW group
    'KfW Drawn': yd['kfw_draw'],
    'Zinsen KfW': yd['kfw_int'],
    'Tilgung KfW': yd['kfw_princ'],
    'KfW Payment': yd['kfw_payment'],
    'Remaining KfW Balance': yd['end_bal_kfw'],
    # Main group
    'Main Drawn': yd['main_draw'],
    'Zinsen Main': yd['main_int_drawn'],
    'Tilgung Main': yd['main_princ'],
    'Main Undrawn': yd['main_undrawn'],
    'Bereitstellung': yd['main_prov'],
    'Remaining Main Balance': yd['end_bal_main'],
    # totals
    'Total Annual Payment': yd['total_payment'],
    'Annuity KfW': yd['kfw_princ'] + yd['kfw_int'],
    'Annuity Main': yd['main_princ'] + main_interest_total
  })

## Section: Amortization
st.subheader("🏦 Loan Amortization Schedule")
st.caption("Track loan draws, interest, principal payments, and remaining balances")

# Yearly amortization table (default view)
df_amort_yearly = pd.DataFrame(amort_rows)
if not df_amort_yearly.empty:
    with st.expander("📋 Show yearly amortization summary"):
        st.dataframe(df_amort_yearly.style.format({
        'KfW Drawn': "€{:,.0f}",
        'Zinsen KfW': "€{:,.0f}",
        'Tilgung KfW': "€{:,.0f}",
        'KfW Payment': "€{:,.0f}",
        'Remaining KfW Balance': "€{:,.0f}",
        'Main Drawn': "€{:,.0f}",
        'Zinsen Main': "€{:,.0f}",
        'Tilgung Main': "€{:,.0f}",
        'Main Undrawn': "€{:,.0f}",
        'Bereitstellung': "€{:,.0f}",
        'Remaining Main Balance': "€{:,.0f}",
        'Total Annual Payment': "€{:,.0f}",
        'Annuity KfW': "€{:,.0f}",
        'Annuity Main': "€{:,.0f}"
    }), use_container_width=True)
    
    # Monthly details in expander
    with st.expander("📋 Show monthly amortization details"):
        df_amort_month = pd.DataFrame(monthly_amort).copy()
        if not df_amort_month.empty:
            df_amort_month["date"] = df_amort_month["date"].dt.strftime("%Y-%m")
            display_cols = [
                "date",
                "Zinsen KfW", "Tilgung KfW", "KfW Payment", "Remaining KfW Balance",
                "Main Draw", "Zinsen Main", "Tilgung Main", "Main Undrawn", "Bereitstellung", "Remaining Main Balance",
                "Total Monthly Payment", "Total Loan Remaining"
            ]
            display_cols = [c for c in display_cols if c in df_amort_month.columns]
            num_cols = [c for c in df_amort_month.columns if c != "date"]
            fmt = {c: "€{:,.2f}" for c in num_cols}
            st.dataframe(df_amort_month[display_cols].style.format(fmt), use_container_width=True)
        else:
            st.write("No monthly amortization data")
else:
    st.info("No amortization data available")

## Section: Tax
st.subheader("💶 Tax Calculation Details")
st.caption("Understand how AfA (depreciation) reduces your taxable income")

# Yearly tax table (default view)
tax_aggs = {}
for col in ["Rent", "Zinsen", "Sonder-Afa", "Degressive-Afa 10", "Linear-Afa 11", "Dep Furnishing", "Maintenance", "Gross Income", "Tax Paid", "Tax Refund"]:
    if col in df.columns:
        tax_aggs[col] = 'sum'

if tax_aggs:
    yearly_tax = df.groupby(df["date"].dt.year).agg(tax_aggs).rename_axis("year").reset_index()
    
    with st.expander("📋 Show yearly tax summary"):
        st.dataframe(yearly_tax.style.format({
        'Rent': "€{:,.0f}",
        'Zinsen': "€{:,.0f}",
        'Sonder-Afa': "€{:,.0f}",
        'Degressive-Afa 10': "€{:,.0f}",
        'Linear-Afa 11': "€{:,.0f}",
        'Dep Furnishing': "€{:,.0f}",
        'Maintenance': "€{:,.0f}",
        'Gross Income': "€{:,.0f}",
        'Tax Paid': "€{:,.0f}",
        'Tax Refund': "€{:,.0f}"
    }), use_container_width=True)
    
    # Monthly details in expander
    with st.expander("📋 Show monthly tax calculation details"):
        df_tax_month = df.copy()
        df_tax_month["date"] = df_tax_month["date"].dt.strftime("%Y-%m")
        tax_cols = ["date", "Rent", "Zinsen", "Sonder-Afa", "Degressive-Afa 10", "Linear-Afa 11", "Dep Furnishing", "Maintenance", "Gross Income", "Tax Paid", "Tax Refund"]
        tax_cols = [c for c in tax_cols if c in df_tax_month.columns]
        fmt = {c: "€{:,.2f}" for c in tax_cols if c != "date"}
        st.dataframe(df_tax_month[tax_cols].style.format(fmt), use_container_width=True)
else:
    st.info("No tax data available")

st.divider()

# =========================
# VIEW 1: MONTHLY BUDGET IMPACT
# =========================
st.header("📊 View 1: Monthly Budget Impact")
st.caption("How much does this property cost in your monthly budget?")

if not df.empty:
    # Construction Period Summary
    st.subheader("🏗️ Construction Period")
    df_construction = df[df["date"] < rent_start].copy()
    
    if not df_construction.empty:
        # Calculate construction period budget items
        df_construction["Total Loan Payment"] = df_construction.get("Zinsen KfW", 0) + df_construction.get("Zinsen Main", 0) + df_construction.get("Tilgung KfW", 0) + df_construction.get("Tilgung Main", 0)
        df_construction["Interest Only"] = df_construction.get("Zinsen KfW", 0) + df_construction.get("Zinsen Main", 0)
        df_construction["Bereitstellung"] = df_construction.get("Bereitstellung", 0)
        df_construction["Equity Payments"] = df_construction.get("Equity Invested", 0)
        df_construction["Tax Refund"] = df_construction.get("Tax Refund", 0)
        # Cash flow: negative = you pay out, positive = you receive
        df_construction["Monthly Cash Flow (Pre-Tax)"] = -(df_construction["Interest Only"] + df_construction["Bereitstellung"] + df_construction["Equity Payments"])
        df_construction["Monthly Cash Flow (After Tax)"] = df_construction["Monthly Cash Flow (Pre-Tax)"] + df_construction["Tax Refund"]
        
        # Yearly summary for construction period
        df_construction_yearly = df_construction.groupby(df_construction["date"].dt.year).agg({
            "Equity Payments": "sum",
            "Interest Only": "sum",
            "Bereitstellung": "sum",
            "Tax Refund": "sum",
            "Monthly Cash Flow (Pre-Tax)": "sum",
            "Monthly Cash Flow (After Tax)": "sum"
        }).rename_axis("Year").reset_index()
        

        # Summary metrics for construction period
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            total_equity = df_construction["Equity Payments"].sum()
            st.metric("Total Equity Paid", f"€ {total_equity:,.0f}", help="Total equity payments during construction")
        with col2:
            total_interest = df_construction["Interest Only"].sum()
            st.metric("Total Interest Paid", f"€ {total_interest:,.0f}", help="Interest on drawn loans during construction")
        with col3:
            total_bereit = df_construction["Bereitstellung"].sum()
            st.metric("Total Bereitstellungszins", f"€ {total_bereit:,.0f}", help="Commitment fees on undrawn loan amounts")
        with col4:
            total_tax_refund = df_construction["Tax Refund"].sum()
            st.metric("Total Tax Refund", f"€ {total_tax_refund:,.0f}", help="Tax refunds from deducting interest and fees")
        with col5:
            total_cash_flow = df_construction["Monthly Cash Flow (After Tax)"].sum()
            st.metric("Net Cash Flow", f"€ {total_cash_flow:,.0f}", help="Total net cash flow (negative = you pay)")
        
        # Show detailed construction period table if requested
        with st.expander("📋 Show yearly construction summary"):
            st.dataframe(df_construction_yearly.style.format({
                "Equity Payments": "€{:,.0f}",
                "Interest Only": "€{:,.0f}",
                "Bereitstellung": "€{:,.0f}",
                "Tax Refund": "€{:,.0f}",
                "Monthly Cash Flow (Pre-Tax)": "€{:,.0f}",
                "Monthly Cash Flow (After Tax)": "€{:,.0f}"
            }), use_container_width=True)
        
        with st.expander("📋 Show monthly construction period breakdown"):
            df_construction_display = df_construction[["date", "Equity Payments", "Interest Only", "Bereitstellung", "Tax Refund", "Monthly Cash Flow (Pre-Tax)", "Monthly Cash Flow (After Tax)"]].copy()
            df_construction_display["date"] = df_construction_display["date"].dt.strftime("%Y-%m")
            st.dataframe(df_construction_display.style.format({
                "Equity Payments": "€{:,.2f}",
                "Interest Only": "€{:,.2f}",
                "Bereitstellung": "€{:,.2f}",
                "Tax Refund": "€{:,.2f}",
                "Monthly Cash Flow (Pre-Tax)": "€{:,.2f}",
                "Monthly Cash Flow (After Tax)": "€{:,.2f}"
            }))
    else:
        st.info("Construction period has already passed or starts in the future.")
    
    st.divider()
    
    # Rental Period
    st.subheader("🏠 Rental Period")
    df_rental = df[df["date"] >= rent_start].copy()
    
    if not df_rental.empty:
        # Calculate monthly budget items
        df_budget = df_rental[["date", "Rent", "Maintenance", "Zinsen KfW", "Zinsen Main", "Tilgung KfW", "Tilgung Main", "Tax Refund"]].copy()
        df_budget["Total Loan Payment"] = df_budget["Zinsen KfW"] + df_budget["Zinsen Main"] + df_budget["Tilgung KfW"] + df_budget["Tilgung Main"]
        # Monthly Out-of-Pocket (before tax benefit) - positive = you pay, negative = you profit
        df_budget["Monthly Cash Flow (Pre-Tax)"] = df_budget["Rent"] - df_budget["Total Loan Payment"] - df_budget["Maintenance"]
        # After receiving tax refund (positive refund improves your cash flow)
        df_budget["Monthly Cash Flow (After Tax)"] = df_budget["Monthly Cash Flow (Pre-Tax)"] + df_budget["Tax Refund"]
        
        # Yearly summary for rental period
        df_rental_yearly = df_budget.groupby(df_budget["date"].dt.year).agg({
            "Rent": "sum",
            "Maintenance": "sum",
            "Total Loan Payment": "sum",
            "Tax Refund": "sum",
            "Monthly Cash Flow (Pre-Tax)": "sum",
            "Monthly Cash Flow (After Tax)": "sum"
        }).rename_axis("Year").reset_index()
        

        # Reorder columns for better flow
        df_budget = df_budget[["date", "Rent", "Maintenance", "Zinsen KfW", "Zinsen Main", "Tilgung KfW", "Tilgung Main", "Total Loan Payment", "Monthly Cash Flow (Pre-Tax)", "Tax Refund", "Monthly Cash Flow (After Tax)"]]
        
        # Show first year and year 10 as examples
        first_year = df_budget[df_budget["date"].dt.year == rent_start.year].copy()
        year_10 = df_budget[df_budget["date"].dt.year == rent_start.year + 9].copy()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Year 1 (First Rental Year - {rent_start.year})")
            if not first_year.empty:
                avg_rent = first_year["Rent"].mean()
                avg_loan_payment = first_year["Total Loan Payment"].mean()
                avg_maintenance = first_year["Maintenance"].mean()
                avg_tax_refund = first_year["Tax Refund"].mean()
                avg_pre_tax_cf = first_year["Monthly Cash Flow (Pre-Tax)"].mean()
                avg_after_tax_cf = first_year["Monthly Cash Flow (After Tax)"].mean()
                
                st.caption("💶 Money Coming In")
                st.metric("Rental Income", f"€ {avg_rent:,.2f}")
                st.metric("Tax Refund", f"€ {avg_tax_refund:,.2f}", help="Tax refund from deducting interest, AfA, and maintenance")
                
                st.caption("💸 Money Going Out")
                st.metric("Loan Payment (Principal + Interest)", f"€ {avg_loan_payment:,.2f}")
                st.metric("Maintenance & Management", f"€ {avg_maintenance:,.2f}")
                
                st.caption("💰 Bottom Line")
                st.metric("Monthly Cash Flow (Pre-Tax)", f"€ {avg_pre_tax_cf:,.2f}", help="Negative = out of pocket, Positive = surplus")
                st.metric("✅ Monthly Cash Flow (After Tax)", f"€ {avg_after_tax_cf:,.2f}", help="Final monthly cash position. Negative = you pay from pocket, Positive = net income", delta=f"+€ {avg_tax_refund:,.2f}" if avg_tax_refund > 0 else None, delta_color="normal")
        
        with col2:
            st.subheader(f"Year 10 ({rent_start.year + 9})")
            if not year_10.empty:
                avg_rent = year_10["Rent"].mean()
                avg_loan_payment = year_10["Total Loan Payment"].mean()
                avg_maintenance = year_10["Maintenance"].mean()
                avg_tax_refund = year_10["Tax Refund"].mean()
                avg_pre_tax_cf = year_10["Monthly Cash Flow (Pre-Tax)"].mean()
                avg_after_tax_cf = year_10["Monthly Cash Flow (After Tax)"].mean()
                
                st.caption("💶 Money Coming In")
                st.metric("Rental Income", f"€ {avg_rent:,.2f}")
                st.metric("Tax Refund", f"€ {avg_tax_refund:,.2f}", help="Tax refund from deducting interest, AfA, and maintenance")
                
                st.caption("💸 Money Going Out")
                st.metric("Loan Payment (Principal + Interest)", f"€ {avg_loan_payment:,.2f}")
                st.metric("Maintenance & Management", f"€ {avg_maintenance:,.2f}")
                
                st.caption("💰 Bottom Line")
                st.metric("Monthly Cash Flow (Pre-Tax)", f"€ {avg_pre_tax_cf:,.2f}", help="Negative = out of pocket, Positive = surplus")
                st.metric("✅ Monthly Cash Flow (After Tax)", f"€ {avg_after_tax_cf:,.2f}", help="Final monthly cash position. Negative = you pay from pocket, Positive = net income", delta=f"+€ {avg_tax_refund:,.2f}" if avg_tax_refund > 0 else None, delta_color="normal")
            else:
                st.info("Year 10 data not available in simulation period")
        
        # Show detailed monthly table if requested
        with st.expander("📋 Show yearly rental summary"):
            st.dataframe(df_rental_yearly.style.format({
                "Rent": "€{:,.0f}",
                "Maintenance": "€{:,.0f}",
                "Total Loan Payment": "€{:,.0f}",
                "Tax Refund": "€{:,.0f}",
                "Monthly Cash Flow (Pre-Tax)": "€{:,.0f}",
                "Monthly Cash Flow (After Tax)": "€{:,.0f}"
            }), use_container_width=True)
        
        with st.expander("📋 Show detailed monthly rental period breakdown"):
            df_budget_display = df_budget.copy()
            df_budget_display["date"] = df_budget_display["date"].dt.strftime("%Y-%m")
            st.dataframe(df_budget_display.style.format({
                "Rent": "€{:,.2f}",
                "Maintenance": "€{:,.2f}",
                "Zinsen KfW": "€{:,.2f}",
                "Zinsen Main": "€{:,.2f}",
                "Tilgung KfW": "€{:,.2f}",
                "Tilgung Main": "€{:,.2f}",
                "Total Loan Payment": "€{:,.2f}",
                "Monthly Cash Flow (Pre-Tax)": "€{:,.2f}",
                "Tax Refund": "€{:,.2f}",
                "Monthly Cash Flow (After Tax)": "€{:,.2f}"
            }))
    else:
        st.info("Rental period has not started yet in the simulation timeframe.")
else:
    st.write("No data available")

st.divider()

# =========================
# VIEW 2: INVESTMENT RETURNS ANALYSIS (IRR-FOCUSED)
# =========================
st.header("📈 View 2: Investment Returns Analysis")
st.caption("Pure investment perspective: What are your returns when selling after X years?")

# Add debug toggle
col1, col2, col3 = st.columns(3)
with col1:
  sale_growth = st.slider("Property value growth (%)", min_value=0.0, max_value=10.0, value=float(loaded.get("sale_growth", 2.0)), step=0.1) / 100
with col2:
  show_irr_debug = st.checkbox("Show IRR calculation details", value=False, help="Debug: Show the cashflow series used for IRR calculation")


if not yearly_cashflow.empty:
    purchase_year = start_year
    start_calc_year = purchase_year

    yearly_filtered = yearly_cashflow[yearly_cashflow["year"] >= start_calc_year].reset_index(drop=True)
    years = yearly_filtered["year"].values

    # cumulative tracking lists
    cum_out_eq_list = []
    cum_out_interest_list = []
    cum_out_maint_list = []
    cum_in_rent_list = []
    cum_in_tax_list = []
    cum_afa_sonder_list = []
    cum_afa_degressive_list = []
    cum_afa_linear_list = []
    cum_afa_furnishing_list = []
    cum_afa_total_list = []
    total_outflow_list = []
    total_inflow_list = []
    projected_price_list = []
    profit_list = []
    roi_list = []
    cagr_list = []
    irr_list = []

    cum_out_eq = 0.0
    cum_out_interest = 0.0
    cum_out_maint = 0.0
    cum_in_rent = 0.0
    cum_in_tax = 0.0
    cum_afa_sonder = 0.0
    cum_afa_degressive = 0.0
    cum_afa_linear = 0.0
    cum_afa_furnishing = 0.0

    initial_price = total_purchase_price

    # Build discrete annual cashflow series for IRR calculation
    irr_cashflows_year_10 = []  # For debugging
    
    for i, y in enumerate(years):
        equity = yearly_filtered.loc[i, "Equity Invested"]
        interest_paid = yearly_filtered.loc[i, "Zinsen"]
        maintenance_paid = yearly_filtered.loc[i, "Maintenance"]
        rent_received = yearly_filtered.loc[i, "Rent"]
        tax_refund = yearly_filtered.loc[i, "Tax Refund"]
        loan_remaining = yearly_filtered.loc[i, "Loan Remaining"]
        # AfA (depreciation) components
        afa_sonder = yearly_filtered.loc[i, "Sonder-Afa"]
        afa_degressive = yearly_filtered.loc[i, "Degressive-Afa 10"]
        afa_linear = yearly_filtered.loc[i, "Linear-Afa 11"]
        afa_furnishing = yearly_filtered.loc[i, "Dep Furnishing"]
        afa_total = yearly_filtered.loc[i, "Total AfA"]

        # cumulative sums
        cum_out_eq += equity
        cum_out_interest += interest_paid
        cum_out_maint += maintenance_paid
        cum_in_rent += rent_received
        cum_in_tax += tax_refund
        cum_afa_sonder += afa_sonder
        cum_afa_degressive += afa_degressive
        cum_afa_linear += afa_linear
        cum_afa_furnishing += afa_furnishing

        cum_outflow = cum_out_eq + cum_out_interest + cum_out_maint
        cum_inflow = cum_in_rent + cum_in_tax

        # projected property price
        price = initial_price * ((1 + sale_growth) ** (y - purchase_year))

        # Annual discrete cashflow (FIXED: not cumulative)
        annual_outflow = equity + interest_paid + maintenance_paid
        annual_inflow = rent_received + tax_refund
        annual_net_cashflow = annual_inflow - annual_outflow
        
        # profit if sold this year
        net_sale_proceeds = price - loan_remaining
        prof = net_sale_proceeds + cum_inflow - cum_outflow

        # ROI (simple total return)
        roi_pct = (prof / cum_outflow * 100) if cum_outflow > 0 else 0.0

        # CAGR (compound annual growth rate)
        n_years = y - start_calc_year + 1
        if cum_outflow > 0 and (prof + cum_outflow) > 0:
            cagr_val = ((prof + cum_outflow) / cum_outflow) ** (1 / n_years) - 1
        else:
            cagr_val = 0.0

        # Build IRR using discrete annual cashflows
        # IRR structure: Year 0 should be TOTAL initial investment (equity), 
        # then subsequent years are net operating cashflows (rent + tax - interest - maintenance)
        # Final year adds the sale proceeds
        temp_irr_cashflows = []
        
        # Build the complete cashflow series from year 0 to current year
        for j in range(i + 1):
            j_equity = yearly_filtered.loc[j, "Equity Invested"]
            j_interest = yearly_filtered.loc[j, "Zinsen"]
            j_maint = yearly_filtered.loc[j, "Maintenance"]
            j_rent = yearly_filtered.loc[j, "Rent"]
            j_tax = yearly_filtered.loc[j, "Tax Refund"]
            
            if j == 0:
                # Year 0: Initial equity investment is a negative cashflow
                # Plus any operating cashflow in year 0 (rent - interest - maintenance + tax)
                initial_investment = -j_equity
                operating_cf = j_rent + j_tax - j_interest - j_maint
                temp_irr_cashflows.append(initial_investment + operating_cf)
            else:
                # Subsequent years: net operating cashflow only (no more equity payments typically)
                # If there are equity payments in later years, they're additional investments
                net_cf = j_rent + j_tax - j_interest - j_maint - j_equity
                temp_irr_cashflows.append(net_cf)
        
        # Add sale proceeds to the final year (i = current year index)
        temp_irr_cashflows[-1] += net_sale_proceeds
        
        # Calculate IRR
        try:
            irr_val = npf.irr(temp_irr_cashflows)
            if irr_val is None or np.isnan(irr_val) or np.isinf(irr_val):
                irr_val = 0.0
            else:
                irr_val = irr_val * 100
        except:
            irr_val = 0.0
        
        # Store cashflow series for debugging (only for year 10)
        if y == purchase_year + 9:
            irr_cashflows_year_10 = temp_irr_cashflows.copy()
            # Also store the data needed for debug breakdown
            irr_debug_data_year_10 = {
                'yearly_data': yearly_filtered.iloc[:i+1].copy()
            }

        # append to lists
        cum_out_eq_list.append(cum_out_eq)
        cum_out_interest_list.append(cum_out_interest)
        cum_out_maint_list.append(cum_out_maint)
        cum_in_rent_list.append(cum_in_rent)
        cum_in_tax_list.append(cum_in_tax)
        cum_afa_sonder_list.append(cum_afa_sonder)
        cum_afa_degressive_list.append(cum_afa_degressive)
        cum_afa_linear_list.append(cum_afa_linear)
        cum_afa_furnishing_list.append(cum_afa_furnishing)
        cum_afa_total_list.append(cum_afa_sonder + cum_afa_degressive + cum_afa_linear + cum_afa_furnishing)
        total_outflow_list.append(cum_outflow)
        total_inflow_list.append(cum_inflow)
        projected_price_list.append(price)
        profit_list.append(prof)
        roi_list.append(roi_pct)
        cagr_list.append(cagr_val * 100)
        irr_list.append(irr_val)

    # Calculate sale proceeds for display
    sale_proceeds_list = [projected_price_list[i] - yearly_filtered.loc[i, "Loan Remaining"] 
                         for i in range(len(projected_price_list))]
    
    df_real_returns = pd.DataFrame({
        "Year": years,
        "Years Held": years - purchase_year,
        # Sale scenario
        "Projected Price (€)": projected_price_list,
        "Outstanding Loan (€)": yearly_filtered["Loan Remaining"],
        "Sale Proceeds (€)": sale_proceeds_list,
        # Cumulative Outflows
        "Cum. Equity (€)": cum_out_eq_list,
        "Cum. Interest (€)": cum_out_interest_list,
        "Cum. Maintenance (€)": cum_out_maint_list,
        "Total Outflow (€)": total_outflow_list,
        # Cumulative Inflows
        "Cum. Rent (€)": cum_in_rent_list,
        "Cum. Tax Refund (€)": cum_in_tax_list,
        "Total Inflow (€)": total_inflow_list,
        # Returns Analysis
        "Net Profit (€)": profit_list,
        "IRR (%)": irr_list,
        "CAGR (%)": cagr_list,
        "ROI (%)": roi_list
    })
    
    # Reorder columns: Sale info → Outflows → Inflows → Profit → KPIs
    df_real_returns = df_real_returns[[
        "Year",
        "Years Held",
        # Sale scenario
        "Projected Price (€)",
        "Outstanding Loan (€)",
        "Sale Proceeds (€)",
        # Outflows
        "Cum. Equity (€)",
        "Cum. Interest (€)",
        "Cum. Maintenance (€)",
        "Total Outflow (€)",
        # Inflows
        "Cum. Rent (€)",
        "Cum. Tax Refund (€)",
        "Total Inflow (€)",
        # Profit & KPIs
        "Net Profit (€)",
        "IRR (%)",
        "CAGR (%)",
        "ROI (%)"
    ]]
    
    # Explanation of metrics
    with st.expander("📚 Understanding Investment Metrics", expanded=False):
        st.markdown("""
        ### 🎯 IRR (Internal Rate of Return) - **MOST IMPORTANT**
        **The gold standard for investment decisions.** IRR represents the annualized rate of return that makes the net present value of all cash flows equal to zero.
        
        - **What it means:** If you invested this money at IRR% per year, you'd get the same outcome
        - **Why it's best:** Accounts for both the timing and size of all cash flows
        - **How to use:** Compare to alternative investments (stocks typically return 7-10%, bonds 3-5%)
        - **Example:** An IRR of 8% means you're earning 8% per year on your invested capital
        
        ---
        
        ### 📈 CAGR (Compound Annual Growth Rate) - **SECOND MOST IMPORTANT**
        The annualized rate at which your total investment grows, assuming profits are reinvested.
        
        - **What it means:** Your average yearly return from start to finish
        - **Formula:** ((Final Value / Initial Investment)^(1/Years)) - 1
        - **Difference from IRR:** CAGR is simpler but doesn't account for cash flow timing
        - **Example:** CAGR of 6% means your investment grows by 6% per year on average
        
        ---
        
        ### 💰 ROI (Return on Investment) - **THIRD MOST IMPORTANT**
        Simple total return without considering time or compounding.
        
        - **What it means:** Total profit as a percentage of your total investment
        - **Formula:** (Total Profit / Total Investment) × 100
        - **Limitation:** Doesn't account for time (100% ROI over 2 years is better than over 20 years)
        - **Example:** ROI of 150% means you've made 1.5× your initial investment
        
        ---
        
        ### 🚫 Why Tilgung (Principal) is NOT Included
        
        **Tilgung is NOT an expense - it's a wealth transfer!**
        
        - When you pay Tilgung, money leaves your account ✓
        - BUT it reduces your loan balance by the exact same amount ✓
        - **Net effect on wealth: €0** (cash down, equity up)
        
        **What IS included in calculations:**
        - ✅ **Equity payments** - your actual investment
        - ✅ **Interest** - cost paid to the bank (lost forever)
        - ✅ **Maintenance** - operating expenses (consumed)
        - ✅ **Rent** - income received
        - ✅ **Tax refunds** - money returned to you
        - ❌ **Tilgung** - your own money moving between accounts
        
        **When you sell:** You recover all Tilgung paid as increased equity (Property Value - Remaining Loan).
        Including Tilgung as a cost would double-count it!
        
        ---
        
        ### 📊 AfA (Depreciation) - Tax Benefit Explained
        
        AfA is a **non-cash tax deduction** that reduces your taxable income without requiring actual spending.
        
        **Types in this calculator:**
        - **Sonder-AfA:** Special accelerated depreciation (5% for 4 years for new buildings)
        - **Degressive AfA:** Declining balance method (5% for 10 years)
        - **Linear AfA:** Straight-line depreciation after degressive period
        - **Furnishing depreciation:** For furniture and fixtures (10% for 10 years)
        
        **Impact:** Higher AfA → Lower taxable income → Bigger tax refund → More cash in your pocket
        """)
    
    # Highlight year 10 if available (define year_10_data first for use in debug section)
    if len(df_real_returns) >= 10:
        year_10_data = df_real_returns[df_real_returns["Years Held"] == 9].iloc[0]  # Year 10 is index 9 (0-based)
        
        # IRR Debug section
        if show_irr_debug:
            st.subheader("🔍 IRR Calculation Debug (Year 10)")
            st.caption("Shows the annual cashflow series used to calculate IRR for a 10-year hold period")
            
            if 'irr_cashflows_year_10' in locals() and len(irr_cashflows_year_10) > 0 and 'irr_debug_data_year_10' in locals():
                # Build detailed breakdown using stored debug data
                yearly_data = irr_debug_data_year_10['yearly_data']
                
                debug_data = []
                for j in range(len(irr_cashflows_year_10)):
                    j_equity = yearly_data.iloc[j]["Equity Invested"]
                    j_interest = yearly_data.iloc[j]["Zinsen"]
                    j_maint = yearly_data.iloc[j]["Maintenance"]
                    j_rent = yearly_data.iloc[j]["Rent"]
                    j_tax = yearly_data.iloc[j]["Tax Refund"]
                    j_loan_remaining = yearly_data.iloc[j]["Loan Remaining"]
                    j_year = yearly_data.iloc[j]["year"]
                    
                    # Calculate projected price for this year
                    j_price = initial_price * ((1 + sale_growth) ** (j_year - purchase_year))
                    
                    if j == 0:
                        operating = j_rent + j_tax - j_interest - j_maint
                        total_cf = -j_equity + operating
                        sale_proceeds = 0
                        desc = "Initial equity + Year 0 operating"
                    elif j == len(irr_cashflows_year_10) - 1:
                        operating = j_rent + j_tax - j_interest - j_maint
                        sale_proceeds = j_price - j_loan_remaining
                        total_cf = operating + sale_proceeds
                        desc = f"Year {j} operating + sale proceeds"
                    else:
                        operating = j_rent + j_tax - j_interest - j_maint - j_equity
                        total_cf = operating
                        sale_proceeds = 0
                        desc = f"Year {j} operating"
                    
                    debug_data.append({
                        'Year': j,
                        'Rent': j_rent,
                        'Tax Refund': j_tax,
                        'Interest': -j_interest,
                        'Maintenance': -j_maint,
                        'Equity': -j_equity if j == 0 else (-j_equity if j_equity > 0 else 0),
                        'Sale Proceeds': sale_proceeds,
                        'Net Cashflow': irr_cashflows_year_10[j],
                        'Description': desc
                    })
                
                debug_df = pd.DataFrame(debug_data)
                st.dataframe(debug_df.style.format({
                    'Rent': '€{:,.0f}',
                    'Tax Refund': '€{:,.0f}',
                    'Interest': '€{:,.0f}',
                    'Maintenance': '€{:,.0f}',
                    'Equity': '€{:,.0f}',
                    'Sale Proceeds': '€{:,.0f}',
                    'Net Cashflow': '€{:,.0f}'
                }), use_container_width=True)
                
                # Calculate and verify IRR manually
                test_irr = npf.irr(irr_cashflows_year_10) * 100 if npf.irr(irr_cashflows_year_10) else 0
                st.caption(f"✅ Calculated IRR from these cashflows = {test_irr:.2f}%")
                
                st.info("""
                **How to read this table:**
                - **Year 0:** Your initial equity investment (negative) plus any operating cashflow
                - **Years 1-9:** Operating cashflow only (Rent + Tax Refund - Interest - Maintenance - Any additional equity)
                - **Year 9 (final):** Operating cashflow PLUS sale proceeds (Property Price - Outstanding Loan)
                
                **Key insight:** The positive cashflows in years 1-8 come from tax refunds at your 42% rate, NOT from selling!
                Each row in the main table shows IRR "if you sell in that year."
                """)
        
        st.subheader("📍 10-Year Investment Summary (KPIs Ordered by Importance)")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🥇 IRR (Internal Rate of Return)", f"{year_10_data['IRR (%)']:.2f}%", 
                     help="Your annualized return - compare this to stocks (7-10%) or bonds (3-5%). This is the MOST IMPORTANT metric.")
        with col2:
            st.metric("🥈 CAGR (Compound Annual Growth)", f"{year_10_data['CAGR (%)']:.2f}%", 
                     help="Your average yearly return rate. Simpler than IRR but doesn't account for cash flow timing.")
        with col3:
            st.metric("🥉 ROI (Return on Investment)", f"{year_10_data['ROI (%)']:.2f}%", 
                     help="Total profit as % of investment. Useful but doesn't consider that this took 10 years.")
        with col4:
            st.metric("💶 Net Profit", f"€{year_10_data['Net Profit (€)']:,.0f}", 
                     help="Total profit in euros if you sell after 10 years")
        
        st.caption("📊 **Metrics ordered by importance:** IRR > CAGR > ROI. IRR is the best for comparing to alternative investments.")

    st.dataframe(df_real_returns.style.format({
        "Projected Price (€)": "€{:,.0f}",
        "Outstanding Loan (€)": "€{:,.0f}",
        "Sale Proceeds (€)": "€{:,.0f}",
        "Cum. Equity (€)": "€{:,.0f}",
        "Cum. Interest (€)": "€{:,.0f}",
        "Cum. Maintenance (€)": "€{:,.0f}",
        "Total Outflow (€)": "€{:,.0f}",
        "Cum. Rent (€)": "€{:,.0f}",
        "Cum. Tax Refund (€)": "€{:,.0f}",
        "Total Inflow (€)": "€{:,.0f}",
        "Net Profit (€)": "€{:,.0f}",
        "IRR (%)": "{:.2f}%",
        "CAGR (%)": "{:.2f}%",
        "ROI (%)": "{:.2f}%"
    }))
    
    st.caption("📊 **Table structure:** Sale scenario → Your outflows → Your inflows → Net profit → KPIs (IRR/CAGR/ROI). See 'Understanding Investment Metrics' section above for detailed explanations.")
else:
    st.write("No yearly cashflow data to calculate returns.")

# =========================
# HANDLE SAVE/LOAD OPERATIONS
# =========================
# Check if we need to save
if 'pending_save' in st.session_state and st.session_state['pending_save']:
    apartment_name = st.session_state['pending_save']
    
    # Collect all input data
    data_to_save = {
        "kaufpreis": kaufpreis,
        "stellplatz": stellplatz,
        "area": area,
        "land_ratio": land_ratio,
        "real_estate_tax_pct": real_estate_transfer_tax / total_purchase_price * 100,
        "notary_pct": notary / total_purchase_price * 100,
        "land_charge_fees_pct": land_charge_registration_fees / total_purchase_price * 100,
        "equity_pct": eigenkapital / total_investment * 100,
        "rent_per_sqm": rent_per_sqm,
        "rent_parking": rent_parking,
        "rent_growth_rate": rent_growth_rate * 100,
        "furnishing_costs": furnishing_costs,
        "furnishing_depreciation_rate": furnishing_annual_depreciation_rate * 100,
        "furnishing_depreciation_years": furnishing_depreciation_years,
        "maintenance_base": maintenance_base,
        "wg_management_fee": wg_management_fee,
        "unit_management_fee": unit_management_fee,
        "maintenance_growth": maintenance_growth * 100,
        "sonder_afa_rate": sonder_afa_rate * 100,
        "sonder_afa_years": sonder_afa_years,
        "sonder_afa_base_amount": sonder_afa_base_amount,
        "degressive_afa_rate": degressive_afa_rate * 100,
        "degressive_years": degressive_years,
        "linear_years": linear_years,
        "kfw_loan_amount": kfw_loan_amount,
        "kfw_interest_rate": kfw_interest_rate * 100,
        "kfw_tilgung_rate": kfw_tilgung_rate * 100,
        "main_loan_rate": main_loan_rate * 100,
        "main_loan_tilgung_rate": main_loan_tilgung_rate * 100,
        "bereitstellungszins": bereitstellungszins * 100,
        "grace_period_months": grace_period_months,
        "tax_rate": tax_rate * 100,
        "contract_date": contract_date.isoformat(),
        "end_construction": end_construction.isoformat(),
        "output_years": output_years,
        "num_payments": num_payments,
        "payment_schedule": payment_schedule,
        "sale_growth": sale_growth * 100
    }
    
    if worksheet:
        if save_apartment_to_sheets(worksheet, apartment_name, data_to_save):
            st.success(f"✅ Saved '{apartment_name}' successfully!")
            del st.session_state['pending_save']
            st.balloons()
        else:
            st.error("Save failed. Please try again.")
            del st.session_state['pending_save']
    else:
        st.error("Storage not available")
        del st.session_state['pending_save']
    
# Check if we need to load
if 'load_apartment' in st.session_state and st.session_state['load_apartment']:
    selected_name = st.session_state['load_apartment']
    
    # Find the apartment data
    if worksheet:
        saved_apartments = load_apartments_from_sheets(worksheet)
        apartment_data = next((apt for apt in saved_apartments if apt["apartment_name"] == selected_name), None)
        
        if apartment_data:
            st.info(f"📂 Loaded '{selected_name}'. The page will refresh with the saved values.")
            st.session_state['loaded_data'] = apartment_data
            del st.session_state['load_apartment']
            st.rerun()

# Clear loaded data after use (so next time defaults are used)
if 'loaded_data' in st.session_state and loaded:
    # Data has been loaded and used, clear it so changing values doesn't conflict
    pass  # Keep it in session state for the full session
