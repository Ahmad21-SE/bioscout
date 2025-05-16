import streamlit as st
import pandas as pd
import os
import glob
import uuid
import datetime

##############################
# --- Config/Constants
OBS_CSV_PATH = "data/observations.csv"
KB_DIR = "data/kb_snippets"

##############################
# --- Helper Functions

def load_observations():
    if not os.path.exists(OBS_CSV_PATH):
        # Create a starter CSV if not present
        df = pd.DataFrame(columns=[
            "observation_id", "species_name", "common_name", "date_observed",
            "location", "image_url", "notes", "submitted_by"
        ])
        df.to_csv(OBS_CSV_PATH, index=False)
    return pd.read_csv(OBS_CSV_PATH)

def save_observation(row):
    df = load_observations()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(OBS_CSV_PATH, index=False)

def get_kb_snippets():
    snippets = []
    for fname in glob.glob(f"{KB_DIR}/*.txt"):
        with open(fname, 'r', encoding='utf-8') as f:
            snippets.append(f.read())
    return snippets

def ai_species_id(image_file):
    # MOCKED AI ID (replace with model/API integration if available)
    # For demo, always return 3 plausible options for Islamabad region
    return [
        {"species": "Parus major (Great Tit)", "confidence": "High"},
        {"species": "Panthera pardus (Leopard)", "confidence": "Medium"},
        {"species": "Psittacula krameri (Rose-ringed Parakeet)", "confidence": "Low"}
    ]

def simple_rag_query(query, obs_df, kb_snippets):
    # Simple keyword search: return matching knowledge base and observations
    query_lower = query.lower()
    kb_hits = [s for s in kb_snippets if query_lower in s.lower()]
    obs_hits = []
    for _, row in obs_df.iterrows():
        if (
            query_lower in str(row["species_name"]).lower()
            or query_lower in str(row["common_name"]).lower()
            or query_lower in str(row["notes"]).lower()
            or query_lower in str(row["location"]).lower()
        ):
            obs_hits.append(row)
    return kb_hits, obs_hits

def get_top_observer(obs_df):
    if obs_df.empty:
        return "N/A"
    return obs_df['submitted_by'].value_counts().idxmax()

##############################
# --- Streamlit Layout

st.set_page_config(page_title="BioScout Islamabad", layout="wide")
st.title("🦜 BioScout Islamabad")
st.subheader("AI for Community Biodiversity & Sustainable Insights in Islamabad")

tabs = st.tabs(["Observation Hub", "AI-powered Q&A", "About"])

# --- TAB 1: Observation Hub
with tabs[0]:
    st.header("1. Community Biodiversity Observation Hub")

    st.markdown(
        "Submit your biodiversity observations for Islamabad & Margalla Hills below. "
        "Your data helps conservation efforts and community science!"
    )

    # --- Submission Form
    st.markdown("#### Submit a New Observation")
    with st.form("observation_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            species_name = st.text_input("Species Name (if known, scientific or common)")
            common_name = st.text_input("Common Name (if different)")
            date_observed = st.date_input("Date Observed", value=datetime.date.today())
            location = st.text_input("Location (e.g., Margalla Hills Trail 3, Rawal Lake)")
        with col2:
            image_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
            notes = st.text_area("Notes (behavior, habitat, etc.)")
            submitted_by = st.text_input("Your Name or Nickname")

        submitted = st.form_submit_button("Submit Observation")

    if submitted:
        # Save image to local folder (simulate image hosting)
        if image_file:
            img_folder = "data/images"
            os.makedirs(img_folder, exist_ok=True)
            img_path = os.path.join(img_folder, f"{uuid.uuid4()}.jpg")
            with open(img_path, "wb") as f:
                f.write(image_file.getbuffer())
            image_url = img_path
        else:
            image_url = ""

        obs_row = {
            "observation_id": str(uuid.uuid4()),
            "species_name": species_name,
            "common_name": common_name,
            "date_observed": str(date_observed),
            "location": location,
            "image_url": image_url,
            "notes": notes,
            "submitted_by": submitted_by or "Anonymous",
        }
        save_observation(obs_row)
        st.success("Observation submitted! Thank you for contributing 🌱")

        # Mock AI species identification
        st.markdown("##### 🧠 AI Species ID Suggestions:")
        ai_suggestions = ai_species_id(image_file)
        for sug in ai_suggestions:
            st.write(f"- {sug['species']} (Confidence: {sug['confidence']})")
        st.info(
            "These are AI-generated suggestions. For real-time ID, integrate with iNaturalist or Hugging Face models."
        )

    # --- Display Observations
    st.markdown("#### Community Observations")
    obs_df = load_observations()
    if obs_df.empty:
        st.info("No observations yet. Submit the first one!")
    else:
        # Gamification: Top observer
        top_observer = get_top_observer(obs_df)
        st.markdown(f"🏆 *Top Observer:* {top_observer}")
        st.dataframe(obs_df[["species_name", "common_name", "date_observed", "location", "notes", "submitted_by"]])

# --- TAB 2: RAG Q&A
with tabs[1]:
    st.header("2. Biodiversity Q&A (AI-powered RAG)")

    st.markdown(
        "Ask any question about Islamabad’s biodiversity, Margalla Hills fauna/flora, or recent community sightings. "
        "Our AI will find the most relevant info from the knowledge base and observations."
    )

    query = st.text_input("Enter your question (e.g., 'What birds are common in Margalla Hills?')")
    if st.button("Ask AI"):
        obs_df = load_observations()
        kb_snippets = get_kb_snippets()
        kb_hits, obs_hits = simple_rag_query(query, obs_df, kb_snippets)

        st.markdown("##### 🔍 *Relevant Info from Knowledge Base:*")
        if kb_hits:
            for hit in kb_hits:
                st.info(hit)
        else:
            st.info("No direct match found in the knowledge base.")

        st.markdown("##### 🔍 *Relevant Community Observations:*")
        if obs_hits:
            for row in obs_hits:
                st.write(
                    f"- {row['species_name']} ({row['common_name']}) @ {row['location']} on {row['date_observed']} — {row['notes']}"
                )
        else:
            st.info("No matching observations found.")

        # Simulated LLM answer
        st.markdown("##### 🤖 *AI Answer:*")
        if kb_hits or obs_hits:
            st.success(
                "Based on available data, here's what we found:\n\n"
                + "\n".join(["• " + hit.split('\n')[0] for hit in kb_hits])
                + ("\n" if kb_hits else "")
                + "\n".join([
                    f"• {row['species_name']} observed at {row['location']} ({row['date_observed']})"
                    for row in obs_hits
                ])
            )
        else:
            st.write(
                "Sorry, I could not find relevant information. Try using different keywords or submit new observations!"
            )

        st.info(
            "This Q&A uses simple keyword search for retrieval and a simulated answer. "
            "For advanced RAG, integrate with free LLM APIs and use embeddings for semantic search."
        )

# --- TAB 3: About
with tabs[2]:
    st.header("About BioScout Islamabad MVP")
    st.markdown("""
*BioScout Islamabad* is a community-driven biodiversity platform for Islamabad and Margalla Hills, built in 24 hours for the AI4Sustainability Hackathon.  
- 💡 *Submission:* Record species sightings with images and notes.  
- 🧠 *AI Species ID:* Get instant (mocked) suggestions for your photo.  
- 🤖 *RAG Q&A:* Ask questions and get answers from a knowledge base + community data.  
- 🏆 *Gamification:* See top contributors.  
- 📊 *Open Data:* All data is stored in editable CSV files for transparency and ease of scaling.

*Intended scaling:* Future versions could include real-time AI species identification, richer maps, Urdu/multilingual support, and integrations with conservation partners.

*Team:* [Your Names Here]  
*GitHub:* [Your Repo Here]
    """)

##############################
# --- END ---