import streamlit as st

# Set the title of the home page
st.title("Welcome to Christina's Annotation Tool")

# Add a description or introduction to your app
st.write("""

### Features of the App:
- **Annotate Text**: Use the annotator tool to extract ontology-based information for any text you enter.
- **Explore Definitions**: Look up definitions, synonyms, and preferred labels from the ontology database.

""")

# Add some images or diagrams (optional)

# Add a quick instruction or guide for new users
st.markdown("""
### How to Use This App:
1. Use the **Annotate Text** page to analyze text for biomedical entities.
2. The **Hierarchy Information** page allows you to explore the relationships between terms.
3. Switch between pages using the sidebar on the left.
""")

# Optionally add buttons or links to pag
