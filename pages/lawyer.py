import streamlit as st
import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk import download
import nltk

# Download necessary NLTK data files
nltk.download('stopwords')
nltk.download('wordnet')

# Title of the Streamlit app
st.title("Legal Chatbot and Lawyer Recommender")

# Input text box for user query
user_query = st.text_area("Enter your legal query:", placeholder="Describe your legal situation in detail...")

# Minimum length for the query to be processed
MIN_QUERY_LENGTH = 20

# Predefined legal categories and their associated keywords
LEGAL_CATEGORIES = {
    "Banking and Finance": ["loan", "bank", "finance", "mortgage", "credit"],
    "Civil": ["property", "contract", "negligence", "tort"],
    "Constitutional": ["constitution", "rights", "amendment", "federal"],
    "Consumer Protection": ["consumer", "refund", "warranty", "product"],
    "Corporate": ["company", "business", "merger", "acquisition", "startup"],
    "Criminal": ["crime", "theft", "murder", "fraud", "assault"],
    "Environmental": ["pollution", "environment", "climate", "wildlife"],
    "Family": ["divorce", "custody", "adoption", "marriage"],
    "Human Rights": ["discrimination", "freedom", "equality", "justice"],
    "Immigration": ["visa", "immigration", "asylum", "citizenship"],
    "Intellectual Property": ["copyright", "patent", "trademark", "infringement"],
    "Labor": ["employment", "wages", "harassment", "labor"],
    "Media and Entertainment": ["media", "entertainment", "defamation", "privacy"],
    "Medical": ["malpractice", "healthcare", "doctor", "hospital"],
    "Real Estate": ["property", "real estate", "lease", "tenant"],
    "Tax": ["tax", "income", "audit", "deduction"]
}

# Function for preprocessing the query
def preprocess_text(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))
    
    # Tokenize and clean the text using regex
    tokens = re.findall(r'\b[a-z]+\b', text.lower())
    filtered_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return filtered_tokens

# Function for manual classification
def classify_query(query):
    tokens = preprocess_text(query)
    category_matches = {category: 0 for category in LEGAL_CATEGORIES}
    
    # Match keywords with tokens
    for token in tokens:
        for category, keywords in LEGAL_CATEGORIES.items():
            if token in keywords:
                category_matches[category] += 1

    # Sort categories by match count and return top matches
    sorted_categories = sorted(category_matches.items(), key=lambda x: x[1], reverse=True)
    top_categories = [cat[0] for cat in sorted_categories if cat[1] > 0]
    return top_categories[:3]

# Execute on button click
if st.button("Get Recommendations"):
    if not user_query.strip():
        st.warning("Please enter a legal query.")
    elif len(user_query.split()) < MIN_QUERY_LENGTH:
        st.warning(f"Your query is too short. Please provide at least {MIN_QUERY_LENGTH} words for better results.")
    else:
        # Classify the query manually
        categories = classify_query(user_query)
        st.write(f"Detected Categories: {categories}")

        if not categories:
            st.warning("No relevant categories found. Please refine your query.")
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
