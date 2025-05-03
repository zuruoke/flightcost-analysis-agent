import time
from typing import Annotated, Any, Dict, List, TypedDict
import streamlit as st
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage
import datetime
from app.agent.graph import flight_agent

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container):
        self.container = container
        self.text = ""
        self.placeholder = container.empty()
    
    def on_llm_new_token(self, token, **kwargs):
        self.text += token
        self.placeholder.markdown(self.text)

def main():
    # Page configuration
    st.set_page_config(page_title="Flight Search", page_icon="✈️", layout="wide")

    # Title and description
    st.title("Find Your Perfect Flight ✈️")
    st.markdown("---")

    # Initialize session state for chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = "chat_" + str(int(time.time()))

    # Search Form
    with st.form("flight_search_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            origin = st.text_input("Origin", placeholder="Enter city")
            adults = st.number_input("Number of Adults", min_value=1, max_value=10, value=1)
        
        with col2:
            destination = st.text_input("Destination", placeholder="Enter city")
            trip_type = st.selectbox("Trip Type", ["One Way", "Round Trip"])
        
        with col3:
            departure_date = st.date_input("Departure Date", min_value=datetime.date.today())
            if trip_type == "Round Trip":
                return_date = st.date_input("Return Date", 
                                        min_value=departure_date,
                                        value=departure_date + datetime.timedelta(days=7))
            
        flight_class = st.selectbox("Flight Class", ["Economy", "Business", "First Class"])
        search_button = st.form_submit_button("Search Flights")

    # Handle search and display results
    if search_button:
        with st.spinner('Searching for flights...'):
            # Prepare the search query
            query = f"Find flights from {origin} to {destination} on {departure_date.strftime('%Y-%m-%d')} "
            query += f"for {adults} {'adult' if adults == 1 else 'adults'} in {flight_class} class. "
            if trip_type == "Round Trip":
                query += f"Return flight on {return_date.strftime('%Y-%m-%d')}."
        
            # Create message container for results
            results_container = st.container()
            stream_handler = StreamHandler(results_container)
            
            # Add the search query to messages
            st.session_state.messages.append({"role": "user", "content": query})

            print(st.session_state.messages)
            print("--------------------------------")
            print(query)

            # Create the initial state
            initial_state = {
                "user_query": query,
                "quotes": [],
                "agg_quotes": [],
                "screenshots": [],
                "analytics": {},
                "final_markdown": ""
            }
            
            # Invoke the graph
            response = flight_agent.invoke(
                initial_state,
                {
                    "configurable": {"thread_id": st.session_state.thread_id},
                    "callbacks": [stream_handler],
                }
            )
            
            # Display the results
            st.subheader("Search Results")
            with results_container:
                if "final_markdown" in response and response["final_markdown"]:
                    st.markdown(response["final_markdown"])
                else:
                    st.info("No results found. Please try a different search.")


if __name__ == "__main__":
    main()
