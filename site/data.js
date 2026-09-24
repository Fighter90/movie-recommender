// Global variables for storing movie and rating data
let movies = [];
let ratings = [];

// Genre names as defined in the u.item file
const genreNames = [
    "unknown", "Action", "Adventure", "Animation", "Children's", "Comedy",
    "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
];

// Primary function to load data from files
async function loadData() {
    try {
        const moviesResponse = await fetch('u.item');
        if (!moviesResponse.ok) {
            throw new Error(`Failed to load movie data: ${moviesResponse.status}`);
        }

        const moviesBuffer = await moviesResponse.arrayBuffer();
        const moviesText = new TextDecoder('latin1').decode(moviesBuffer);
        parseItemData(moviesText);

        const ratingsResponse = await fetch('u.data');
        if (!ratingsResponse.ok) {
            throw new Error(`Failed to load rating data: ${ratingsResponse.status}`);
        }

        const ratingsText = await ratingsResponse.text();
        parseRatingData(ratingsText);
    } catch (error) {
        console.error('Error loading data:', error);
        const resultElement = document.getElementById('result');
        if (resultElement) {
            resultElement.textContent = `Error: ${error.message}. Please make sure u.item and u.data files are in the correct location.`;
            resultElement.className = 'error';
        }
        throw error;
    }
}

// Parse movie data from u.item format
function parseItemData(text) {
    const lines = text.split('\n');

    for (const line of lines) {
        if (line.trim() === '') continue;

        const fields = line.split('|');
        if (fields.length < 24) continue;

        const id = parseInt(fields[0], 10);
        const title = fields[1];
        const genreValues = fields.slice(5, 24).map(value => parseInt(value, 10));
        const genres = genreNames.filter((_, index) => genreValues[index] === 1);

        movies.push({ id, title, genres });
    }
}

// Parse rating data from u.data format
function parseRatingData(text) {
    const lines = text.split('\n');

    for (const line of lines) {
        if (line.trim() === '') continue;

        const fields = line.split('\t');
        if (fields.length < 4) continue;

        const userId = parseInt(fields[0], 10);
        const itemId = parseInt(fields[1], 10);
        const rating = parseFloat(fields[2]);
        const timestamp = parseInt(fields[3], 10);

        ratings.push({ userId, itemId, rating, timestamp });
    }
}
