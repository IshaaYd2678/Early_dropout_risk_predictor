import streamlit as st
import pandas as pd
import numpy as np

st.title("🎓 Early Warning System - Test")
st.write("This is a test to see if Streamlit is working properly.")

# Simple test data
data = pd.DataFrame({
    'Student': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'Risk Score': [85, 45, 72, 23],
    'Department': ['CS', 'Engineering', 'Business', 'Arts']
})

st.dataframe(data)

# Simple chart
st.bar_chart(data.set_index('Student')['Risk Score'])

st.success("✅ Streamlit is working correctly!")