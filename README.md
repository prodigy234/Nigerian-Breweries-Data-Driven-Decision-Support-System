
# Nigerian Breweries – CEO Pitch Dashboard (Streamlit)

This Streamlit app is wired to your **nb_analytics_small.xlsx** dataset and provides an executive-ready, interactive dashboard to discuss sales, stockouts, pricing power, logistics cost-to-serve, distributor risks, quality & counterfeit issues, media & social impact, and macro sensitivity.

## Quick Start

1. Put the dataset file in the same folder:
   - `nb_analytics_small.xlsx` (from this chat)

2. Create and activate a virtual environment (recommended).

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```

5. In the sidebar, upload the Excel file (or the app will auto-load `nb_analytics_small.xlsx` if present). Use the filters and scenario sliders to explore.

## Pages/Sections

- **Executive Summary** – KPI tiles for Revenue, Units, Estimated Lost Sales. Trend and OOS heatmap.
- **Pricing Power & Compliance** – Price gap vs competitors, price vs volume elasticity proxy.
- **Logistics & Cost-to-Serve** – Lane scatter (distance vs cost, bubble=on-time), lead-time distribution.
- **Distributor Risk Radar** – DSO vs OTIF bubble chart and risk table.
- **Quality & Counterfeit** – Returns, complaints, and counterfeit signals.
- **Media & Social Impact** – CPM efficiency and net sentiment by platform × age.
- **Macro & Scenario Simulator** – Price/promo/OOS sliders with revenue impact.

## Notes

- The app auto-detects revenue (`revenue`) or computes as `qty × effective_price`.
- Scenario Simulator uses transparent rules-of-thumb:
  - Price elasticity = **-0.9**
  - +10pp promo intensity ⇒ **+3%** volume
  - -5pp OOS ⇒ **+4%** volume
- Feel free to tweak these levers to match your models.

## Files

- `app.py` – Streamlit app
- `requirements.txt` – dependencies
