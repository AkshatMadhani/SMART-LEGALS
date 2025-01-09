import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()
os.getenv("google_key")

# Title of the Streamlit app
st.title("Legal Chatbot and Lawyer Recommender")

# Input text box for user query
user_query = st.text_area("Enter your legal query:", placeholder="Describe your legal situation in detail...")

# Minimum length for the query to be processed
MIN_QUERY_LENGTH = 20

# Function to classify the legal query using Google NLP API
def classify_text_with_google_nlp(text, api_key):
    url = f"https://language.googleapis.com/v1/documents:classifyText?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "document": {
            "type": "PLAIN_TEXT",
            "content": text
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            categories = response.json().get("categories", [])
            return [cat['name'] for cat in categories]
        else:
            error = response.json()
            if error['error']['code'] == 400 and "too few tokens" in error['error']['message']:
                st.error("Your query is too short. Please provide more details.")
            else:
                st.error(f"Error from Google NLP API: {error}")
            return []
    except Exception as e:
        st.error(f"An error occurred while contacting Google NLP API: {e}")
        return []

# Replace with your Google Cloud API key
GOOGLE_API_KEY = os.getenv("google_key")

# Execute on button click
if st.button("Get Recommendations"):
    if not user_query.strip():
        st.warning("Please enter a legal query.")
    elif len(user_query.split()) < MIN_QUERY_LENGTH:
        st.warning(f"Your query is too short. Please provide at least {MIN_QUERY_LENGTH} words for better results.")
    else:
        # Get categories from Google NLP API
        google_categories = classify_text_with_google_nlp(user_query, GOOGLE_API_KEY)
        st.write(f"Google NLP API Categories: {google_categories}")

        if not google_categories:
            st.warning("No categories returned by Google NLP API. Please refine your query.")
        else:
            # Map Google categories to predefined legal categories
            def map_to_legal_categories(categories):
                predefined_categories = [
                    "Banking and Finance", "Civil", "Constitutional", "Consumer Protection", "Corporate",
                    "Criminal", "Environmental", "Family", "Human Rights", "Immigration", "Intellectual Property",
                    "Labor", "Media and Entertainment", "Medical", "Real Estate", "Tax"
                ]
                mapped_categories = []
                
                # For each returned category, check if it contains any part of the predefined categories
                for google_category in categories:
                    for predef in predefined_categories:
                        if predef.lower() in google_category.lower():  # Partial matching
                            mapped_categories.append(predef)
                            break  # Stop checking further once a match is found
                return mapped_categories[:3]  # Return top 3 categories

            categories = map_to_legal_categories(google_categories)

            if not categories:
                st.warning("No relevant categories found. Please provide a more detailed query or use one of the legal categories: Banking, Criminal, Family, etc.")
            else:
                # Load lawyer dataset
                try:
                    df_new = pd.read_csv("FINALFINALdataset.csv")  # Replace with your actual file path
                    df_new = df_new.loc[:, ~df_new.columns.str.contains('^Unnamed')]
                except FileNotFoundError:
                    st.error("The lawyer dataset file is missing. Please ensure the file exists.")
                else:
                    # Filter lawyers based on categories
                    filtered_df = df_new[df_new['Type_of_Lawyer'].str.contains('|'.join(categories), na=False)]

                    if filtered_df.empty:
                        st.warning("No lawyers found matching the selected categories.")
                    else:
                        # Matching algorithm to calculate match scores
                        def matching_algorithm(lawyer):
                            score = 0
                            ty = [i.strip() for i in lawyer['Type_of_Lawyer'].replace("[", "").replace("]", '').replace("'", '').split(", ")]
                            for x in categories:
                                if x in ty:
                                    score += 1
                            return score

                        # Add match score column
                        filtered_df['Match_Score'] = filtered_df.apply(matching_algorithm, axis=1)

                        # Sort lawyers based on match score, rating, years of experience, and charges
                        top_lawyers = filtered_df.sort_values(
                            by=['Match_Score', 'Rating', 'Years_of_Experience', 'Charges'],
                            ascending=[False, False, False, True]
                        )

                        # Display the top 10 recommended lawyers
                        st.write("Top 10 Recommended Lawyers:")
                        st.dataframe(top_lawyers.head(10))

