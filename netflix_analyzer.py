"""
Netflix Data Analysis - Main Analysis Script

This script provides comprehensive analysis of Netflix's content library,
including statistics, visualizations, and content recommendations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import argparse
import os


class NetflixAnalyzer:
    """A class to analyze Netflix content data."""

    def __init__(self, data_path: str = "netflix_titles.csv"):
        """Initialize the analyzer with data."""
        self.data_path = data_path
        self.df = None
        self.cosine_sim = None
        self.load_data()
        self._prepare_recommendation_system()

    def load_data(self) -> pd.DataFrame:
        """Load and preprocess the Netflix dataset."""
        self.df = pd.read_csv(self.data_path)

        # Convert date_added to datetime
        self.df["date_added"] = pd.to_datetime(
            self.df["date_added"], format="%B %d, %Y", errors="coerce"
        )
        self.df["year_added"] = self.df["date_added"].dt.year
        self.df["month_added"] = self.df["date_added"].dt.month

        # Extract duration as numeric
        self.df["duration_value"] = self.df["duration"].str.extract(r"(\d+)").astype(
            float
        )

        return self.df

    def _prepare_recommendation_system(self):
        """Prepare the TF-IDF matrix and cosine similarity for recommendations."""
        # Fill missing descriptions
        self.df["description"] = self.df["description"].fillna("")

        # Combine features for better recommendations
        self.df["combined_features"] = (
            self.df["title"].fillna("")
            + " "
            + self.df["listed_in"].fillna("")
            + " "
            + self.df["description"]
            + " "
            + self.df["cast"].fillna("")
            + " "
            + self.df["director"].fillna("")
        )

        # Create TF-IDF matrix
        tfidf = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf_matrix = tfidf.fit_transform(self.df["combined_features"])

        # Compute similarity
        self.cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    def get_basic_stats(self) -> dict:
        """Get basic statistics about the dataset."""
        stats = {
            "total_titles": len(self.df),
            "movies": len(self.df[self.df["type"] == "Movie"]),
            "tv_shows": len(self.df[self.df["type"] == "TV Show"]),
            "unique_countries": self.df["country"].nunique(),
            "unique_genres": self.df["listed_in"]
            .str.split(",")
            .explode()
            .str.strip()
            .nunique(),
            "year_range": f"{self.df['release_year'].min()} - {self.df['release_year'].max()}",
            "missing_values": self.df.isnull().sum().to_dict(),
        }
        return stats

    def get_top_countries(self, n: int = 10) -> pd.Series:
        """Get the top N content-producing countries."""
        return self.df["country"].value_counts().head(n)

    def get_top_genres(self, n: int = 10) -> pd.Series:
        """Get the top N genres."""
        genres = self.df["listed_in"].str.split(",").explode().str.strip()
        return genres.value_counts().head(n)

    def get_content_by_year(self) -> pd.Series:
        """Get content count by year added."""
        return self.df["year_added"].value_counts().sort_index()

    def get_rating_distribution(self) -> pd.Series:
        """Get distribution of content ratings."""
        return self.df["rating"].value_counts()

    def recommend(self, title: str, n: int = 5) -> list:
        """Recommend similar titles based on content similarity."""
        idx = self.df[self.df["title"].str.lower() == title.lower()].index
        if len(idx) == 0:
            return []

        idx = idx[0]
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1 : n + 1]

        recommendations = []
        for i, score in sim_scores:
            desc = self.df.iloc[i]["description"]
            if desc and len(desc) > 150:
                desc = desc[:150] + "..."
            elif not desc:
                desc = "No description available."
            recommendations.append(
                {
                    "title": self.df.iloc[i]["title"],
                    "type": self.df.iloc[i]["type"],
                    "genres": self.df.iloc[i]["listed_in"],
                    "description": desc,
                    "similarity_score": round(score, 3),
                }
            )
        return recommendations

    def search_titles(self, query: str) -> pd.DataFrame:
        """Search for titles containing the query string."""
        mask = self.df["title"].str.lower().str.contains(query.lower(), na=False)
        return self.df[mask][["title", "type", "release_year", "rating", "listed_in"]]

    def filter_by_genre(self, genre: str) -> pd.DataFrame:
        """Filter content by genre."""
        mask = self.df["listed_in"].str.lower().str.contains(genre.lower(), na=False)
        return self.df[mask][
            ["title", "type", "release_year", "rating", "listed_in", "description"]
        ]

    def filter_by_year(
        self, start_year: int, end_year: int = None
    ) -> pd.DataFrame:
        """Filter content by release year range."""
        if end_year is None:
            end_year = start_year
        mask = (self.df["release_year"] >= start_year) & (
            self.df["release_year"] <= end_year
        )
        return self.df[mask][
            ["title", "type", "release_year", "rating", "listed_in", "description"]
        ]

    # Visualization methods
    def plot_type_distribution(self, save_path: str = None):
        """Plot distribution of Movies vs TV Shows."""
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#E50914", "#221f1f"]
        type_counts = self.df["type"].value_counts()
        ax.pie(type_counts.values, labels=type_counts.index, colors=colors, autopct="%1.1f%%")
        ax.set_title("Movies vs TV Shows on Netflix", fontsize=14, fontweight="bold")
        ax.set_ylabel("")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    def plot_top_countries(self, n: int = 10, save_path: str = None):
        """Plot top N content-producing countries."""
        fig, ax = plt.subplots(figsize=(12, 6))
        top_countries = self.get_top_countries(n)
        colors = sns.color_palette("Reds_r", n)
        ax.barh(top_countries.index[::-1], top_countries.values[::-1], color=colors[::-1])
        ax.set_xlabel("Number of Titles", fontsize=12)
        ax.set_title(f"Top {n} Content-Producing Countries", fontsize=14, fontweight="bold")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    def plot_content_over_years(self, save_path: str = None):
        """Plot content added over the years."""
        fig, ax = plt.subplots(figsize=(12, 6))
        yearly_data = self.get_content_by_year().dropna()
        ax.fill_between(yearly_data.index, yearly_data.values, alpha=0.3, color="#E50914")
        ax.plot(yearly_data.index, yearly_data.values, color="#E50914", linewidth=2)
        ax.set_xlabel("Year", fontsize=12)
        ax.set_ylabel("Number of Titles Added", fontsize=12)
        ax.set_title("Netflix Content Added Over the Years", fontsize=14, fontweight="bold")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    def plot_top_genres(self, n: int = 10, save_path: str = None):
        """Plot top N genres."""
        fig, ax = plt.subplots(figsize=(12, 6))
        top_genres = self.get_top_genres(n)
        colors = sns.color_palette("Reds_r", n)
        ax.barh(top_genres.index[::-1], top_genres.values[::-1], color=colors[::-1])
        ax.set_xlabel("Number of Titles", fontsize=12)
        ax.set_title(f"Top {n} Genres on Netflix", fontsize=14, fontweight="bold")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    def plot_wordcloud(self, save_path: str = None):
        """Generate a word cloud from titles."""
        text = " ".join(self.df["title"].dropna())
        wc = WordCloud(
            width=1200,
            height=600,
            background_color="black",
            colormap="Reds",
            max_words=200,
        ).generate(text)

        fig, ax = plt.subplots(figsize=(14, 7))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title("Netflix Titles Word Cloud", fontsize=14, fontweight="bold")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig

    def plot_rating_distribution(self, save_path: str = None):
        """Plot distribution of content ratings."""
        fig, ax = plt.subplots(figsize=(10, 6))
        rating_data = self.get_rating_distribution()
        colors = sns.color_palette("Reds_r", len(rating_data))
        ax.bar(rating_data.index, rating_data.values, color=colors)
        ax.set_xlabel("Rating", fontsize=12)
        ax.set_ylabel("Number of Titles", fontsize=12)
        ax.set_title("Content Rating Distribution", fontsize=14, fontweight="bold")
        plt.xticks(rotation=45)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        return fig


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Netflix Data Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python netflix_analyzer.py --stats
  python netflix_analyzer.py --recommend "Narcos"
  python netflix_analyzer.py --search "Breaking"
  python netflix_analyzer.py --genre "Comedy"
  python netflix_analyzer.py --visualize
        """,
    )

    parser.add_argument(
        "--data",
        type=str,
        default="netflix_titles.csv",
        help="Path to the Netflix dataset CSV file",
    )
    parser.add_argument("--stats", action="store_true", help="Show basic statistics")
    parser.add_argument(
        "--recommend", type=str, metavar="TITLE", help="Get recommendations for a title"
    )
    parser.add_argument(
        "--search", type=str, metavar="QUERY", help="Search for titles"
    )
    parser.add_argument(
        "--genre", type=str, metavar="GENRE", help="Filter by genre"
    )
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        metavar="YEAR",
        help="Filter by year (single year or range)",
    )
    parser.add_argument(
        "--top-countries", type=int, metavar="N", help="Show top N countries"
    )
    parser.add_argument("--top-genres", type=int, metavar="N", help="Show top N genres")
    parser.add_argument(
        "--visualize", action="store_true", help="Generate and save visualizations"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory for saving visualizations",
    )

    args = parser.parse_args()

    # Get script directory for default data path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = args.data
    if not os.path.isabs(data_path):
        data_path = os.path.join(script_dir, data_path)

    # Initialize analyzer
    analyzer = NetflixAnalyzer(data_path)

    if args.stats:
        print("\n📊 Netflix Dataset Statistics")
        print("=" * 50)
        stats = analyzer.get_basic_stats()
        print(f"Total Titles: {stats['total_titles']:,}")
        print(f"  - Movies: {stats['movies']:,}")
        print(f"  - TV Shows: {stats['tv_shows']:,}")
        print(f"Unique Countries: {stats['unique_countries']}")
        print(f"Unique Genres: {stats['unique_genres']}")
        print(f"Release Year Range: {stats['year_range']}")

    if args.recommend:
        print(f"\n🎬 Recommendations for '{args.recommend}':")
        print("=" * 50)
        recommendations = analyzer.recommend(args.recommend)
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec['title']} ({rec['type']})")
                print(f"   Genres: {rec['genres']}")
                print(f"   Similarity: {rec['similarity_score']}")
        else:
            print(f"Title '{args.recommend}' not found in the dataset.")

    if args.search:
        print(f"\n🔍 Search results for '{args.search}':")
        print("=" * 50)
        results = analyzer.search_titles(args.search)
        if len(results) > 0:
            print(results.to_string(index=False))
        else:
            print("No results found.")

    if args.genre:
        print(f"\n🎭 Content in genre '{args.genre}':")
        print("=" * 50)
        results = analyzer.filter_by_genre(args.genre)
        print(f"Found {len(results)} titles")
        if len(results) > 0:
            print(results.head(20).to_string(index=False))

    if args.year:
        start_year = args.year[0]
        end_year = args.year[1] if len(args.year) > 1 else start_year
        print(f"\n📅 Content from {start_year} to {end_year}:")
        print("=" * 50)
        results = analyzer.filter_by_year(start_year, end_year)
        print(f"Found {len(results)} titles")
        if len(results) > 0:
            print(results.head(20).to_string(index=False))

    if args.top_countries:
        print(f"\n🌍 Top {args.top_countries} Content-Producing Countries:")
        print("=" * 50)
        countries = analyzer.get_top_countries(args.top_countries)
        for country, count in countries.items():
            print(f"  {country}: {count:,} titles")

    if args.top_genres:
        print(f"\n🎭 Top {args.top_genres} Genres:")
        print("=" * 50)
        genres = analyzer.get_top_genres(args.top_genres)
        for genre, count in genres.items():
            print(f"  {genre.strip()}: {count:,} titles")

    if args.visualize:
        print(f"\n📈 Generating visualizations...")
        os.makedirs(args.output_dir, exist_ok=True)

        visualizations = [
            ("type_distribution.png", analyzer.plot_type_distribution),
            ("top_countries.png", lambda p: analyzer.plot_top_countries(10, p)),
            ("content_over_years.png", analyzer.plot_content_over_years),
            ("top_genres.png", lambda p: analyzer.plot_top_genres(10, p)),
            ("wordcloud.png", analyzer.plot_wordcloud),
            ("rating_distribution.png", analyzer.plot_rating_distribution),
        ]

        for filename, plot_func in visualizations:
            save_path = os.path.join(args.output_dir, filename)
            plot_func(save_path)
            print(f"  ✓ Saved {filename}")
            plt.close()

        print(f"\nVisualizations saved to '{args.output_dir}/' directory.")

    # If no arguments provided, show help
    if not any(
        [
            args.stats,
            args.recommend,
            args.search,
            args.genre,
            args.year,
            args.top_countries,
            args.top_genres,
            args.visualize,
        ]
    ):
        parser.print_help()


if __name__ == "__main__":
    main()
