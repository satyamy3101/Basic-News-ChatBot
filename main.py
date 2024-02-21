import nltk
from flask import Flask, render_template, request
import requests
from datetime import datetime
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

app = Flask(__name__)

nltk.download('punkt')
nltk.download('stopwords')

class NewsChatbot:
    def __init__(self):
        self.news_api_key = 'e26089a0360047708de20c0efe0a90e4'  # Replace with your News API key
        self.responses = {
            'hello': 'Hi there! How can I help you?',
            'how are you': 'I am doing well, thank you!',
            'bye': 'Goodbye! Have a great day!',
            'news': 'Sure, I can help you with the latest news. What topic are you interested in?',
            'time': self.get_current_time,
            'date': self.get_current_date,
        }
        self.ps = PorterStemmer()

    def preprocess_text(self, text):
        words = word_tokenize(text.lower())
        words = [self.ps.stem(word) for word in words if word.isalnum() and word not in stopwords.words('english')]
        return words

    def get_news(self, topic):
        url = f'https://newsapi.org/v2/top-headlines?apiKey={self.news_api_key}&category={topic}&country=us'
        response = requests.get(url)
        if response.status_code == 200:
            news_data = response.json()
            articles = news_data.get('articles', [])

            # Create a list of structured news items
            news_list = []
            for idx, article in enumerate(articles[:5], start=1):
                news_item = {
                    'title': article['title'],
                    'summary': article['description'],
                    'link': article['url']
                }
                news_list.append(news_item)

            return news_list
        return None

    def get_current_time(self):
        current_time = datetime.now().strftime('%H:%M:%S')
        return f'The current time is {current_time}.'

    def get_current_date(self):
        current_date = datetime.now().strftime('%Y-%m-%d')
        return f'Today\'s date is {current_date}.'

    def get_response(self, user_input):
        user_words = self.preprocess_text(user_input)
        for word in user_words:
            if word in self.responses:
                if callable(self.responses[word]):
                    return self.responses[word]()
                else:
                    return self.responses[word]

        return "I'm sorry, I don't understand. Can you please rephrase?"

# Instantiate the chatbot
chatbot = NewsChatbot()

# Keep track of the last requested topic
last_requested_topic = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    response = chatbot.get_response(user_input)
    return {'response': response}

@app.route('/news', methods=['POST'])
def get_news():
    global last_requested_topic

    user_input = request.form['user_input'].lower()

    if 'news' in user_input:
        last_requested_topic = None  # Reset last requested topic when asking for general news
        return {'response': chatbot.responses['news']}

    print(f"User Input: {user_input}")

    # Get the topic directly from the user input
    topic = request.form['user_input'].lower()

    print(f"Selected Topic: {topic}")

    # Check if the topic has changed
    if topic != last_requested_topic:
        # Clear previous news if the topic has changed
        last_requested_topic = topic
        news_list = chatbot.get_news(topic)
    else:
        # If the topic is the same, don't fetch news again
        news_list = None

    if news_list:
        return {'response': news_list}  # Return the news as a list
    else:
        return {'response': "I'm sorry, I couldn't fetch the news at the moment. Please try again later."}

if __name__ == '__main__':
    app.run(debug=True)
