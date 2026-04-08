import streamlit as st
from datetime import datetime, timedelta
import dukascopy_python
import pandas as pd
import io
from dukascopy_python.instruments import (
    INSTRUMENT_FX_MAJORS_GBP_USD,
    INSTRUMENT_FX_MAJORS_AUD_USD,
    INSTRUMENT_FX_MAJORS_EUR_USD,
    INSTRUMENT_FX_MAJORS_NZD_USD,
    INSTRUMENT_FX_MAJORS_USD_CAD,
    INSTRUMENT_FX_MAJORS_USD_JPY,
)

# Page configuration
st.set_page_config(
    page_title="Forex Data Downloader",
    page_icon="💱",
    layout="wide"
)

st.title("💱 Forex Data Downloader")
st.markdown("Download forex data for various currency pairs")

# Available currency pairs
PAIRS = {
    "GBP/USD": INSTRUMENT_FX_MAJORS_GBP_USD,
    "AUD/USD": INSTRUMENT_FX_MAJORS_AUD_USD,
    "EUR/USD": INSTRUMENT_FX_MAJORS_EUR_USD,
    "NZD/USD": INSTRUMENT_FX_MAJORS_NZD_USD,
    "USD/CAD": INSTRUMENT_FX_MAJORS_USD_CAD,
    "USD/JPY": INSTRUMENT_FX_MAJORS_USD_JPY,
}

# Interval options
INTERVALS = {
    "1 Hour": dukascopy_python.INTERVAL_HOUR_1,
    "4 Hours": dukascopy_python.INTERVAL_HOUR_4,
    "Daily": dukascopy_python.INTERVAL_DAY_1,
}

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Select currency pairs
    selected_pairs = st.multiselect(
        "Select Currency Pairs",
        list(PAIRS.keys()),
        default=["EUR/USD", "GBP/USD"],
        help="Choose one or more currency pairs to download"
    )
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime(2025, 1, 1),
            help="Select the start date for data"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime(2025, 2, 1),
            help="Select the end date for data"
        )
    
    # Select interval
    selected_interval = st.selectbox(
        "Time Interval",
        list(INTERVALS.keys()),
        help="Choose the candlestick interval"
    )
    
    # Download format
    download_format = st.radio(
        "Download Format",
        ["CSV", "JSON"],
        help="Choose the format for downloading data"
    )

# Main content area
if not selected_pairs:
    st.warning("⚠️ Please select at least one currency pair from the sidebar")
elif start_date >= end_date:
    st.error("❌ End date must be after start date")
else:
    # Convert to datetime
    start = datetime.combine(start_date, datetime.min.time())
    end = datetime.combine(end_date, datetime.min.time())
    interval = INTERVALS[selected_interval]
    offer_side = dukascopy_python.OFFER_SIDE_BID
    
    # Display configuration
    st.markdown("### 📊 Configuration")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Selected Pairs", len(selected_pairs))
    with col2:
        st.metric("Days", (end_date - start_date).days)
    with col3:
        st.metric("Interval", selected_interval)
    with col4:
        st.metric("Format", download_format)
    
    # Fetch data button
    if st.button("🔄 Fetch Data", use_container_width=True, type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        dataframes = []
        try:
            for idx, (code, instrument) in enumerate([(k, PAIRS[k]) for k in selected_pairs]):
                status_text.text(f"Fetching {code}... ({idx + 1}/{len(selected_pairs)})")
                df = dukascopy_python.fetch(
                    instrument,
                    interval,
                    offer_side,
                    start,
                    end,
                )
                df["code"] = code
                dataframes.append(df)
                progress_bar.progress((idx + 1) / len(selected_pairs))
            
            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                status_text.text("✅ Data fetched successfully!")
                
                # Display data preview
                st.markdown("### 📈 Data Preview")
                st.dataframe(combined_df, use_container_width=True)
                
                # Display statistics
                st.markdown("### 📊 Statistics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Records", len(combined_df))
                with col2:
                    st.metric("Date Range", f"{start_date} to {end_date}")
                
                # Download section
                st.markdown("### ⬇️ Download Data")
                col1, col2 = st.columns(2)
                
                with col1:
                    if download_format == "CSV":
                        csv_buffer = io.StringIO()
                        combined_df.to_csv(csv_buffer, index=False)
                        csv_data = csv_buffer.getvalue()
                        
                        filename = f"forex_data_{start_date}_{end_date}.csv"
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        json_data = combined_df.to_json(orient="records", date_format="iso")
                        filename = f"forex_data_{start_date}_{end_date}.json"
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_data,
                            file_name=filename,
                            mime="application/json",
                            use_container_width=True
                        )
                
                with col2:
                    st.info(f"📦 Total Size: {len(csv_data if download_format == 'CSV' else json_data) / 1024:.2f} KB")
        
        except Exception as e:
            st.error(f"❌ Error fetching data: {str(e)}")
            status_text.text("Failed to fetch data")

# Footer
st.markdown("---")
st.markdown("💡 **Tips:** Select multiple pairs for comparison. Larger date ranges may take longer to process.")