# Investment Property Viability Calculator (Single Page)
import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np
import numpy_financial as npf

st.set_page_config(page_title="Investment Property Calculator", layout="wide")

st.title("Investment Property Viability Calculator")
st.divider()

# =========================
# INPUTS
# =========================
st.header("Purchase & Property")
col1, col2, col3 = st.columns(3)
with col1:
  kaufpreis = st.number_input("[A] Purchase price (€)", value=389000, step=5000)
  stellplatz = st.number_input("[B] Parking garage price (€)", value=39900, step=1000)
with col2:
  area = st.number_input("[C] Living area (sqm)", value=41.39)
with col3:
  land_ratio = st.slider("[D] Property to land value ratio", 0.0, 1.0, 0.81, 0.01)

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
    real_estate_transfer_tax = st.number_input("Real estate tax (%)", value=3.5) / 100 * total_purchase_price
    notary = st.number_input("Notary (%)", value=1.5) / 100 * total_purchase_price
    land_charge_registration_fees = st.number_input("Land charge fees (%)", value=0.5) / 100 * total_purchase_price
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
    eigenkapital = st.number_input("Equity (%)", value=10.0) / 100 * total_investment
  with col4:
    st.metric("", f"€ {eigenkapital:,.2f}")
st.divider()


st.header("Rent")
col1, col2, col3 = st.columns(3)
with col1:
  col4, col5 = st.columns(2)
  with col4:
    rent_per_sqm = st.number_input("Rent per sqm (€)", value=28.0, step=0.5)
    rent_property = rent_per_sqm * area
    rent_parking = st.number_input("Parking rent (€)", value=100, step=10)
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
    rent_growth_rate = st.number_input("Annual rent growth (%)", value=2.0) / 100
st.divider()

st.header("Furnishing")
col1, col2, col3 = st.columns(3)
with col1:
  furnishing_costs = st.number_input("Furnishing costs (€)", value=5000)
with col2:
  furnishing_annual_depreciation_rate = st.number_input("Furnishing depreciation rate (%)", value=10.0) / 100
with col3:
  furnishing_depreciation_years = st.number_input("Furnishing depreciation years", value=10)
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
  maintenance_base = st.number_input("Maintenance (monthly €)", value=5)
with col2:
  wg_management_fee = st.number_input("WG management fee (monthly €)", value=30)
with col3:
  unit_management_fee = st.number_input("Unit management fee (monthly €)", value=0)
with col4:  
  maintenance_growth = st.number_input("Maintenance growth (annual %)", value=2.0) / 100
maintenance_total = maintenance_base + wg_management_fee + unit_management_fee
st.metric("Total monthly maintenance", f"€ {maintenance_total:,.2f}")
st.divider()

st.header("Depreciation")
col1, col2, col3 = st.columns(3)
with col1:
  sonder_afa_rate = st.number_input("Sonder-AfA rate (%)", value=5.0) / 100
with col2:
  sonder_afa_years = st.number_input("Sonder-AfA years", value=4)
with col3:
  sonder_afa_base_amount = st.number_input("Sonder-AfA base amount (€)", value=100000, step=1000)
with col1:
  degressive_afa_rate = st.number_input("Degressive AfA rate (%)", value=5.0) / 100
with col2:
  degressive_years = st.number_input("Degressive AfA years", value=10)
with col3:
  linear_years = st.number_input("Linear Afa Years", value=40)
# total useful years = degressive period + linear period
useful_years = degressive_years + linear_years
st.divider()

st.header("Financing")
st.subheader("KfW Loan")
col1, _, _ = st.columns(3)
with col1:
  kfw_loan_amount = st.number_input("KfW loan amount (€)", value=100000, step=1000)
col1, col2, col3 = st.columns(3)
with col1:
  kfw_interest_rate = st.number_input("KfW interest (%)", value=2.19) / 100
  kfw_tilgung_rate = st.number_input("KfW Tilgung (%)", value=2.0) / 100
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
  main_loan_rate = st.number_input("Main loan interest (%)", value=4.0) / 100
  main_loan_tilgung_rate = st.number_input("Main loan Tilgung (%)", value=1.5) / 100
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
  bereitstellungszins = st.number_input("Bereitstellungszins (% / month)", value=0.25) / 100
with col2:
  grace_period_months = st.number_input("Grace period (months)", value=12)
st.divider()

st.header("Tax")
col1, col2, col3 = st.columns(3)
with col1:
  tax_rate = st.number_input("Marginal tax rate (%)", value=42.0) / 100
st.divider()

st.header("Timeline")
col1, col2, col3 = st.columns(3)
with col1:
  contract_date = st.date_input("Contract date", value=date(2025, 9, 1))
with col2:
  end_construction = st.date_input("Construction end date", value=date(2027, 12, 31))
with col3:
  output_years = st.number_input("Output horizon (years)", value=30)



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
# SIMULATION
# =========================
st.header("Simulation")

show_monthly = st.checkbox("Show monthly details", value=False)

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
  grouped["Total Before Tax Refund"] = grouped.get("Rent", 0.0) - grouped.get("Zinsen", 0.0) - grouped.get("Tilgung", 0.0) - grouped.get("Maintenance", 0.0)
  grouped["Total Cash Flow"] = grouped["Total Before Tax Refund"] + grouped["Tax Refund"]
  # determine year-end loan remaining based on cumulative tilgung
  # FIX: use amortization balance as single source of truth
  loan_remaining_by_year = df.groupby(df["date"].dt.year)["loan_balance"].last()
  grouped["Loan Remaining"] = grouped["year"].map(loan_remaining_by_year)
  # yearly net cash movement and Cumulative Cash Movement
  grouped["Net Cash Movement"] = grouped["Total Cash Flow"] - grouped.get("Equity Invested", 0.0)
  grouped["Cumulative Cash Movement"] = grouped["Net Cash Movement"].cumsum()
  yearly_cashflow = grouped[["year", "Rent", "Zinsen", "Tilgung", "Maintenance", "Total Before Tax Refund", "Tax Refund", "Total Cash Flow", "Equity Invested", "Net Cash Movement", "Cumulative Cash Movement", "Loan Remaining"]]
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
# monthly amortization DataFrame
df_amort_month = pd.DataFrame(monthly_amort).copy()
if show_monthly:
  st.subheader("Monthly Amortization")
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
    fmt = {c: "{:,.2f}" for c in num_cols}
    st.dataframe(df_amort_month[display_cols].style.format(fmt))
  else:
    st.write("No monthly amortization data")
else:
  st.subheader("Yearly Amortization")
  st.dataframe(pd.DataFrame(amort_rows).style.format("{:,.2f}"))

## Section: Tax
# monthly tax table
df_tax_month = df.copy()
df_tax_month["date_str"] = df_tax_month["date"].dt.strftime("%Y-%m")
if show_monthly:
  st.subheader("Monthly Tax")
  tax_cols = ["date_str", "Rent", "Zinsen", "Sonder-Afa", "Degressive-Afa 10", "Linear-Afa 11", "Dep Furnishing", "Maintenance", "Gross Income", "Tax Paid", "Tax Refund"]
  tax_cols = [c for c in tax_cols if c in df_tax_month.columns]
  fmt = {c: "{:,.2f}" for c in tax_cols if c != "date_str"}
  st.dataframe(df_tax_month[tax_cols].rename(columns={"date_str":"date"}).style.format(fmt))
else:
  st.subheader("Yearly Tax")
  tax_aggs = {}
  for col in ["Rent", "Zinsen", "Sonder-Afa", "Degressive-Afa 10", "Linear-Afa 11", "Dep Furnishing", "Maintenance", "Gross Income", "Tax Paid", "Tax Refund"]:
    if col in df.columns:
      tax_aggs[col] = 'sum'
  if tax_aggs:
    yearly_tax = df.groupby(df["date"].dt.year).agg(tax_aggs).rename_axis("year").reset_index()
    st.dataframe(yearly_tax.style.format({c:"{:,.0f}" for c in yearly_tax.columns if c != 'year'}))
  else:
    st.write("No tax data available")

## Section: Cashflow
if show_monthly:
  st.subheader("Monthly Cashflow & Tax Details")
  df_monthly = df.copy()
  df_monthly["date"] = df_monthly["date"].dt.strftime("%Y-%m")
  # compute monthly tilgung and totals for display
  df_monthly["Tilgung"] = df_monthly.get("Tilgung KfW", 0.0) + df_monthly.get("Tilgung Main", 0.0)
  df_monthly["Total Before Tax Refund"] = df_monthly.get("Rent", 0.0) - df_monthly.get("Zinsen", 0.0) - df_monthly.get("Tilgung", 0.0) - df_monthly.get("Maintenance", 0.0)
  df_monthly["Total Cash Flow"] = df_monthly["Total Before Tax Refund"] + df_monthly.get("Tax Refund", 0.0)
  # include equity invested as outflow for liquidity tracking
  df_monthly["Equity Invested"] = df_monthly.get("Equity Invested", 0.0)
  df_monthly["Net Cash Movement"] = df_monthly["Total Cash Flow"] - df_monthly["Equity Invested"]
  df_monthly["Cumulative Cash Movement"] = df_monthly["Net Cash Movement"].cumsum()
  # cumulative principal paid (Tilgung) and loan remaining based on total loan - cumulative tilgung
  df_monthly["Cum Tilgung"] = df_monthly.get("Tilgung", 0.0).cumsum()
  df_monthly["Loan Remaining"] = total_loan_amount - df_monthly["Cum Tilgung"]
  cashflow_cols = ["date", "Rent", "Zinsen", "Tilgung", "Maintenance", "Total Before Tax Refund", "Tax Refund", "Total Cash Flow", "Equity Invested", "Net Cash Movement", "Cumulative Cash Movement", "Loan Remaining"]
  cashflow_cols = [c for c in cashflow_cols if c in df_monthly.columns]
  num_cols = [c for c in cashflow_cols if c != "date"]
  fmt = {c: "{:,.2f}" for c in num_cols}
  st.dataframe(df_monthly[cashflow_cols].rename(columns={"date":"Date"}).style.format(fmt))
else:
  st.subheader("Yearly Cashflow Results")
  if not yearly_cashflow.empty:
    st.dataframe(yearly_cashflow.style.format({c:"{:,.2f}" for c in yearly_cashflow.columns if c != 'year'}))
  else:
    st.write("No cashflow data available")

# =========================
# KPIs
# =========================

col1, col2, col3 = st.columns(3)
with col1:
  sale_growth = st.number_input("Property value growth (%)", value=2.0, step=0.5) / 100


st.write(yearly_cashflow)


import numpy_financial as npf

# =========================
# Realistic Investment Returns (From Year 5 Onwards, Detailed + IRR)
# =========================
st.header("Investment Returns from Year 5 (with IRR)")

if not yearly_cashflow.empty:
    purchase_year = start_year
    start_calc_year = purchase_year  # 5th year after purchase

    yearly_filtered = yearly_cashflow[yearly_cashflow["year"] >= start_calc_year].reset_index(drop=True)
    years = yearly_filtered["year"].values

    # cumulative tracking lists
    cum_out_eq_list = []
    cum_out_interest_list = []
    cum_out_maint_list = []
    cum_in_rent_list = []
    cum_in_tax_list = []
    total_outflow_list = []
    total_inflow_list = []
    projected_price_list = []
    profit_list = []
    roi_list = []
    ann_roi_list = []
    irr_list = []

    cum_out_eq = 0.0
    cum_out_interest = 0.0
    cum_out_maint = 0.0
    cum_in_rent = 0.0
    cum_in_tax = 0.0

    initial_price = total_purchase_price

    for i, y in enumerate(years):
        equity = yearly_filtered.loc[i, "Equity Invested"]
        interest_paid = yearly_filtered.loc[i, "Zinsen"]
        maintenance_paid = yearly_filtered.loc[i, "Maintenance"]
        rent_received = yearly_filtered.loc[i, "Rent"]
        tax_refund = yearly_filtered.loc[i, "Tax Refund"]
        loan_remaining = yearly_filtered.loc[i, "Loan Remaining"]

        # cumulative sums
        cum_out_eq += equity
        cum_out_interest += interest_paid
        cum_out_maint += maintenance_paid
        cum_in_rent += rent_received
        cum_in_tax += tax_refund

        cum_outflow = cum_out_eq + cum_out_interest + cum_out_maint
        cum_inflow = cum_in_rent + cum_in_tax

        # projected property price
        price = initial_price * ((1 + sale_growth) ** (y - purchase_year))

        # profit
        prof = (price - loan_remaining) + cum_inflow - cum_outflow

        # ROI
        roi_pct = (prof / cum_outflow * 100) if cum_outflow > 0 else 0.0

        # Annualized ROI (CAGR)
        n_years = y - start_calc_year + 1
        ann_roi_val = ((prof + cum_outflow) / cum_outflow) ** (1 / n_years) - 1 if cum_outflow > 0 else 0.0

        # Build IRR for cumulative cashflows up to this year
        cashflow_series = []
        for j in range(i + 1):
            outflow = yearly_filtered.loc[j, "Equity Invested"] + yearly_filtered.loc[j, "Zinsen"] + yearly_filtered.loc[j, "Maintenance"]
            inflow = yearly_filtered.loc[j, "Rent"] + yearly_filtered.loc[j, "Tax Refund"]
            cashflow_series.append(inflow - outflow)
        # Add net sale proceeds to the last year's cashflow
        cashflow_series[-1] += price - loan_remaining
        try:
            irr_val = npf.irr(cashflow_series)
        except:
            irr_val = 0.0
        irr_val = irr_val * 100 if irr_val is not None else 0.0

        # append to lists
        cum_out_eq_list.append(cum_out_eq)
        cum_out_interest_list.append(cum_out_interest)
        cum_out_maint_list.append(cum_out_maint)
        cum_in_rent_list.append(cum_in_rent)
        cum_in_tax_list.append(cum_in_tax)
        total_outflow_list.append(cum_outflow)
        total_inflow_list.append(cum_inflow)
        projected_price_list.append(price)
        profit_list.append(prof)
        roi_list.append(roi_pct)
        ann_roi_list.append(ann_roi_val * 100)
        irr_list.append(irr_val)

    df_real_returns = pd.DataFrame({
        "Year": years,
        "Projected Price (€)": projected_price_list,
        "Outstanding Loan (€)": yearly_filtered["Loan Remaining"],
        # Outflow breakdown
        "Equity Invested (€)": cum_out_eq_list,
        "Interest Paid (€)": cum_out_interest_list,
        "Maintenance Paid (€)": cum_out_maint_list,
        "Total Outflow (€)": total_outflow_list,
        # Inflow breakdown
        "Rent Received (€)": cum_in_rent_list,
        "Tax Refund (€)": cum_in_tax_list,
        "Total Inflow (€)": total_inflow_list,
        "Profit (€)": profit_list,
        "ROI (%)": roi_list,
        "Annualized ROI (%)": ann_roi_list,
        "IRR (%)": irr_list
    })

    st.dataframe(df_real_returns.style.format({
        "Projected Price (€)": "{:,.2f}",
        "Outstanding Loan (€)": "{:,.2f}",
        "Equity Invested (€)": "{:,.2f}",
        "Interest Paid (€)": "{:,.2f}",
        "Maintenance Paid (€)": "{:,.2f}",
        "Total Outflow (€)": "{:,.2f}",
        "Rent Received (€)": "{:,.2f}",
        "Tax Refund (€)": "{:,.2f}",
        "Total Inflow (€)": "{:,.2f}",
        "Profit (€)": "{:,.2f}",
        "ROI (%)": "{:.2f}%",
        "Annualized ROI (%)": "{:.2f}%",
        "IRR (%)": "{:.2f}%"
    }))
else:
    st.write("No yearly cashflow data to calculate returns.")
