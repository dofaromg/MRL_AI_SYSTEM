import streamlit as st
import json
import zipfile
import os
from io import BytesIO

# Load data
with open('data/master_concise_v1.3.json') as json_file:
    data_json = json.load(json_file)

with open('data/master_summary_v1.3.md') as md_file:
    data_md = md_file.read()
    
# Sidebar for search
st.sidebar.header('Search')
search_term = st.sidebar.text_input('Enter keyword:')

# Function to check signature presence
def check_signature(data):
    signature = 'MrLiouWord'
    return signature in json.dumps(data)

# Check signatures
json_signature_present = check_signature(data_json)
md_signature_present = signature in data_md

# Main tabs
tabs = st.tabs(['Core Laws', 'Genesis 16', 'Flowseed', 'Fluin', 'ASI'])

for tab in tabs:
    with tab:
        st.header(tab)
        st.write(data_md)  # Placeholder for displaying data

# Keyword search logic (basic)
if search_term:
    # Implement search logic here
    st.markdown(f'Search results for: {search_term}')

# Download button for exporting data as zip
if st.button('Download Data as ZIP'):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        zip_file.writestr('master_concise_v1.3.json', json.dumps(data_json).encode())
        zip_file.writestr('master_summary_v1.3.md', data_md.encode())
    st.download_button('Download ZIP', buffer.getvalue(), 'data.zip', 'application/zip')

# Display whether signature is present
st.sidebar.write('Signature in JSON:', json_signature_present)
st.sidebar.write('Signature in MD:', md_signature_present)