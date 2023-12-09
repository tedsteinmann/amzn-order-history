import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pandas as pd
from collections import Counter
import string
import re

accountName='personal'

# Add your custom stop words
custom_stop_words = ['pack', 'fl', 'oz','ct','free', 'natural','naturally', 'company', 'replacement','count','adult','bag']
# Define a set of color names to exclude
color_words = {'red', 'orange', 'yellow', 'green', 'blue', 'purple', 'brown', 'magenta', 'tan', 'cyan', 'olive', 'maroon', 'navy', 'aquamarine', 'turquoise', 'silver', 'lime', 'teal', 'indigo', 'violet', 'pink', 'black', 'white', 'gray', 'grey'}

# Mapping of words to a common representative
word_mapping = {
    'vitamin': 'supplement',
    'vitamins': 'supplement',
    # Add more words as needed
}

# Patterns
oz_pattern = re.compile(r'\d+oz')
kg_pattern = re.compile(r'\d+kg')
# Add more patterns as needed

# Patterns list
patterns = [oz_pattern, kg_pattern]

nltk.download('stopwords')
nltk.download('punkt')

# Replace with your CSV file path
df = pd.read_csv(f'{accountName}/order_items.csv')

# Function to clean and tokenize text
def clean_tokenize(description, word_mapping, patterns):
    # Convert to lowercase
    description = description.lower()
    # Remove punctuation
    description = description.translate(str.maketrans('', '', string.punctuation))
    # Tokenize
    tokens = word_tokenize(description)
    # Check against patterns
    def is_excluded(word):
        return any(pattern.match(word) for pattern in patterns)
    # Replace words according to the mapping and remove stop words, numbers, color words, and patterns
    return [word_mapping.get(word, word) for word in tokens if word not in stop_words and not word.isdigit() and word not in color_words and not is_excluded(word)]


# Function to check if a description contains any of the most common words
def contains_common_word(description, common_words):
    # Tokenize and convert to lowercase
    tokens = word_tokenize(description.lower())
    return any(common_word in tokens for common_word in common_words)




# main -------------------------------

descriptions = df['itemDescription'].astype(str)

# Set of English stop words
stop_words = set(stopwords.words('english'))

stop_words.update(custom_stop_words)

# Assuming 'descriptions' is your pandas Series of item descriptions
# and 'word_mapping' is your dictionary for mapping words
# and 'patterns' is a list of common patterns to ignore
tokens_list = descriptions.apply(lambda x: clean_tokenize(x, word_mapping, patterns))


# Flatten the list of tokens and count occurrences
all_tokens = [token for tokens in tokens_list for token in tokens]
word_counts = Counter(all_tokens)

# Get most common words
most_common_words = word_counts.most_common(20)  # You can change the number as needed

print(most_common_words)

#get words from above stats
most_common_words = [word[0] for word in word_counts.most_common(10)]


# Filter descriptions
filtered_descriptions = df[df['itemDescription'].apply(lambda x: contains_common_word(x, most_common_words))]

#print(filtered_descriptions)

# Group by 'itemDescription' and calculate the size
group_sizes = filtered_descriptions.groupby('itemDescription').size().reset_index(name='count')


print(group_sizes)

# Optionally, save to a new CSV file
group_sizes.to_csv(f'{accountName}/categories.csv', index=False)