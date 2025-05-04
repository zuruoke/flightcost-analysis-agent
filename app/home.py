"""
Streamlit app for flight search.

This module provides a web interface for the flight search agent.
"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
from app.agent.runner import run_agent

# Configure page
st.set_page_config(
    page_title="Flight Search Agent",
    page_icon="✈️",
    layout="wide"
)

# Initialize session state
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None

# Title and description
st.title("✈️ Flight Search Agent")
st.markdown("""
    Search for flights and get comprehensive results including:
    - Flight quotes
    - Aggregated prices
    - Screenshots of flight details
    - Analytics and statistics
""")

# Sidebar for input
with st.sidebar:
    st.header("Search Parameters")
    
    # Origin and destination
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("Origin (e.g., LHR)", max_chars=3, value="LHR").upper()
    with col2:
        destination = st.text_input("Destination (e.g., JFK)", max_chars=3, value="JFK").upper()
    
    # Number of adults
    adults = st.number_input("Number of Adults", min_value=1, max_value=9, value=1)
    
    # Departure date
    min_date = datetime.now().date()
    max_date = min_date + timedelta(days=365)
    departure_date = st.date_input(
        "Departure Date",
        min_value=min_date,
        max_value=max_date,
        value=min_date + timedelta(days=30)
    )

# Search button
if st.button("Search Flights", type="primary"):
    try:
        # Prepare request
        user_request = {
            "origin": origin,
            "destination": destination,
            "num_adults": adults,
            "departure_date": departure_date.strftime("%Y-%m-%d"),
        }
        
        # Show progress
        with st.spinner("Searching for flights..."):
            # Run the agent using asyncio
            result = asyncio.run(run_agent(user_request))
            
            # Display results
            st.success("Search completed!")
            
            # Quotes
            st.subheader("Flight Quotes")
            if result.get("quotes"):
                for quote in result["quotes"]:
                    with st.expander(f"Flight: ${quote.get('price', 'N/A')}"):
                        st.json(quote)
            
            # Aggregated quotes
            st.subheader("Price Summary")
            if result.get("aggregated_quotes"):
                st.json(result["aggregated_quotes"])
            
            # Screenshots
            st.subheader("Flight Details")
            if result.get("screenshots"):
                for url in result["screenshots"]:
                    st.image(url, caption="Flight Details Screenshot")
            
            # Analytics
            st.subheader("Analytics")
            if result.get("analytics"):
                st.json(result["analytics"])
                
    except Exception as e:
        st.error(f"Error during flight search: {str(e)}")
        st.exception(e)
