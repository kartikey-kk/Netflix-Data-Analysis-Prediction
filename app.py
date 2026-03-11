"""
Netflix Data Analysis - Interactive Streamlit Dashboard

A web-based interactive dashboard for exploring Netflix content,
viewing statistics, and getting personalized recommendations.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import os

# Import the analyzer
from netflix_analyzer import NetflixAnalyzer


# Page configuration
st.set_page_config(
    page_title="Netflix Data Explorer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Netflix-like styling
st.markdown(
    """
<style>
    .stApp {
        background-color: #141414;
    }
    .main-header {
        color: #E50914;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: #221f1f;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #E50914;
    }
    .stat-number {
        color: #E50914;
        font-size: 2rem;
        font-weight: bold;
    }
    .stat-label {
        color: #ffffff;
        font-size: 1rem;
    }
    .recommendation-card {
        background-color: #221f1f;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #E50914;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_analyzer():
    """Load and cache the Netflix analyzer."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "netflix_titles.csv")
    return NetflixAnalyzer(data_path)


def main():
    """Main application function."""
    # Load data
    try:
        analyzer = load_analyzer()
    except FileNotFoundError:
        st.error("⚠️ Dataset not found. Please ensure 'netflix_titles.csv' is in the same directory.")
        return

    # Sidebar
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg",
        width=200,
    )
    st.sidebar.title("Navigation")

    page = st.sidebar.radio(
        "Go to",
        ["📊 Dashboard", "🔍 Search & Filter", "🎬 Recommendations", "📈 Analytics"],
    )

    # Main content
    st.markdown('<h1 class="main-header">🎬 Netflix Data Explorer</h1>', unsafe_allow_html=True)

    if page == "📊 Dashboard":
        show_dashboard(analyzer)
    elif page == "🔍 Search & Filter":
        show_search_filter(analyzer)
    elif page == "🎬 Recommendations":
        show_recommendations(analyzer)
    elif page == "📈 Analytics":
        show_analytics(analyzer)


def show_dashboard(analyzer):
    """Display the main dashboard with key statistics."""
    stats = analyzer.get_basic_stats()

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Titles", f"{stats['total_titles']:,}")
    with col2:
        st.metric("Movies", f"{stats['movies']:,}")
    with col3:
        st.metric("TV Shows", f"{stats['tv_shows']:,}")
    with col4:
        st.metric("Countries", f"{stats['unique_countries']}")

    st.markdown("---")

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📺 Content Type Distribution")
        fig = analyzer.plot_type_distribution()
        st.pyplot(fig)
        plt.close()

    with col2:
        st.subheader("🌍 Top 10 Countries")
        fig = analyzer.plot_top_countries(10)
        st.pyplot(fig)
        plt.close()

    # Second row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Content Added Over Years")
        fig = analyzer.plot_content_over_years()
        st.pyplot(fig)
        plt.close()

    with col2:
        st.subheader("🎭 Top 10 Genres")
        fig = analyzer.plot_top_genres(10)
        st.pyplot(fig)
        plt.close()

    # Word Cloud
    st.subheader("☁️ Netflix Titles Word Cloud")
    fig = analyzer.plot_wordcloud()
    st.pyplot(fig)
    plt.close()


def show_search_filter(analyzer):
    """Display the search and filter interface."""
    st.subheader("🔍 Search & Filter Netflix Content")

    tab1, tab2, tab3, tab4 = st.tabs(["Search Titles", "Filter by Genre", "Filter by Year", "Filter by Rating"])

    with tab1:
        search_query = st.text_input("Search for a title:", placeholder="e.g., Breaking Bad, Stranger...")
        if search_query:
            results = analyzer.search_titles(search_query)
            if len(results) > 0:
                st.success(f"Found {len(results)} titles matching '{search_query}'")
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("No titles found matching your search.")

    with tab2:
        # Get all unique genres
        all_genres = (
            analyzer.df["listed_in"]
            .str.split(",")
            .explode()
            .str.strip()
            .dropna()
            .unique()
        )
        selected_genre = st.selectbox("Select a genre:", sorted(all_genres))
        if selected_genre:
            results = analyzer.filter_by_genre(selected_genre)
            st.success(f"Found {len(results)} titles in '{selected_genre}'")
            st.dataframe(
                results[["title", "type", "release_year", "rating", "description"]].head(50),
                use_container_width=True,
            )

    with tab3:
        col1, col2 = st.columns(2)
        min_year = int(analyzer.df["release_year"].min())
        max_year = int(analyzer.df["release_year"].max())

        with col1:
            start_year = st.number_input("From year:", min_value=min_year, max_value=max_year, value=min_year)
        with col2:
            end_year = st.number_input("To year:", min_value=min_year, max_value=max_year, value=max_year)

        if start_year <= end_year:
            results = analyzer.filter_by_year(int(start_year), int(end_year))
            st.success(f"Found {len(results)} titles from {start_year} to {end_year}")
            st.dataframe(
                results[["title", "type", "release_year", "rating", "listed_in"]].head(50),
                use_container_width=True,
            )

    with tab4:
        all_ratings = analyzer.df["rating"].dropna().unique()
        selected_rating = st.selectbox("Select a rating:", sorted(all_ratings))
        if selected_rating:
            results = analyzer.df[analyzer.df["rating"] == selected_rating]
            st.success(f"Found {len(results)} titles with rating '{selected_rating}'")
            st.dataframe(
                results[["title", "type", "release_year", "listed_in", "description"]].head(50),
                use_container_width=True,
            )


def show_recommendations(analyzer):
    """Display the recommendation system interface."""
    st.subheader("🎬 Content Recommendation System")
    st.markdown(
        """
    Enter a Netflix title you like, and our AI-powered recommendation engine will suggest similar content
    based on description, cast, director, and genre similarity.
    """
    )

    # Title input with autocomplete
    all_titles = analyzer.df["title"].dropna().tolist()

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_title = st.selectbox(
            "Select or type a title:",
            [""] + all_titles,
            index=0,
            help="Start typing to search for a title",
        )
    with col2:
        num_recommendations = st.slider("Number of recommendations:", 3, 10, 5)

    if selected_title:
        recommendations = analyzer.recommend(selected_title, num_recommendations)

        if recommendations:
            # Show the original title info
            original = analyzer.df[analyzer.df["title"] == selected_title].iloc[0]
            st.markdown("### 🎯 You selected:")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{original['title']}**")
                st.markdown(f"Type: {original['type']}")
                st.markdown(f"Rating: {original['rating']}")
            with col2:
                st.markdown(f"**Genres:** {original['listed_in']}")
                st.markdown(f"**Description:** {original['description'][:200]}...")

            st.markdown("---")
            st.markdown(f"### ✨ Top {num_recommendations} Similar Titles:")

            for i, rec in enumerate(recommendations, 1):
                with st.expander(f"#{i} - {rec['title']} ({rec['type']}) - Similarity: {rec['similarity_score']}"):
                    st.markdown(f"**Genres:** {rec['genres']}")
                    st.markdown(f"**Description:** {rec['description']}")
        else:
            st.error(f"Could not find '{selected_title}' in the database.")


def show_analytics(analyzer):
    """Display advanced analytics and insights."""
    st.subheader("📈 Advanced Analytics")

    tab1, tab2, tab3 = st.tabs(["Rating Analysis", "Trends", "Duration Analysis"])

    with tab1:
        st.markdown("### Content Rating Distribution")
        fig = analyzer.plot_rating_distribution()
        st.pyplot(fig)
        plt.close()

        # Rating breakdown by type
        st.markdown("### Ratings by Content Type")
        rating_type = pd.crosstab(analyzer.df["rating"], analyzer.df["type"])
        st.dataframe(rating_type, use_container_width=True)

    with tab2:
        st.markdown("### Content Addition Trends")

        # Monthly trends
        monthly_data = analyzer.df.groupby(["year_added", "type"]).size().unstack(fill_value=0)

        fig, ax = plt.subplots(figsize=(14, 6))
        monthly_data.plot(kind="area", stacked=True, ax=ax, color=["#E50914", "#221f1f"], alpha=0.7)
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Number of Titles", fontsize=12)
        ax.set_title("Content Addition by Type Over Years", fontsize=14, fontweight="bold")
        ax.legend(title="Type")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Genre trends
        st.markdown("### Genre Popularity by Year")
        year_filter = st.slider(
            "Select year range:",
            int(analyzer.df["year_added"].min() or 2015),
            int(analyzer.df["year_added"].max() or 2021),
            (2018, 2021),
        )

        filtered_df = analyzer.df[
            (analyzer.df["year_added"] >= year_filter[0])
            & (analyzer.df["year_added"] <= year_filter[1])
        ]
        genre_counts = (
            filtered_df["listed_in"]
            .str.split(",")
            .explode()
            .str.strip()
            .value_counts()
            .head(10)
        )

        fig, ax = plt.subplots(figsize=(12, 6))
        colors = sns.color_palette("Reds_r", 10)
        ax.barh(genre_counts.index[::-1], genre_counts.values[::-1], color=colors[::-1])
        ax.set_xlabel("Number of Titles", fontsize=12)
        ax.set_title(f"Top Genres ({year_filter[0]}-{year_filter[1]})", fontsize=14, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with tab3:
        st.markdown("### Movie Duration Analysis")

        movies_df = analyzer.df[analyzer.df["type"] == "Movie"].copy()
        movies_df["duration_mins"] = movies_df["duration"].str.extract(r"(\d+)").astype(float)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.hist(movies_df["duration_mins"].dropna(), bins=30, color="#E50914", alpha=0.7, edgecolor="black")
        ax.set_xlabel("Duration (minutes)", fontsize=12)
        ax.set_ylabel("Number of Movies", fontsize=12)
        ax.set_title("Movie Duration Distribution", fontsize=14, fontweight="bold")
        ax.axvline(movies_df["duration_mins"].mean(), color="yellow", linestyle="--", label=f"Mean: {movies_df['duration_mins'].mean():.0f} min")
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        st.markdown("### TV Show Seasons Analysis")
        tv_df = analyzer.df[analyzer.df["type"] == "TV Show"].copy()
        tv_df["seasons"] = tv_df["duration"].str.extract(r"(\d+)").astype(float)

        season_counts = tv_df["seasons"].value_counts().sort_index()

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(season_counts.index, season_counts.values, color="#E50914", alpha=0.7, edgecolor="black")
        ax.set_xlabel("Number of Seasons", fontsize=12)
        ax.set_ylabel("Number of TV Shows", fontsize=12)
        ax.set_title("TV Show Seasons Distribution", fontsize=14, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Movie Duration", f"{movies_df['duration_mins'].mean():.0f} min")
        with col2:
            st.metric("Average TV Show Seasons", f"{tv_df['seasons'].mean():.1f}")


if __name__ == "__main__":
    main()
