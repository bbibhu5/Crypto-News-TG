import feedparser
from binance.client import Client
import openai
import telegram
from apscheduler.schedulers.blocking import BlockingScheduler
import requests

# --- Configuration ---
cointelegraph_rss_url = "https://cointelegraph.com/rss"
binance_api_key = "Sy7iJrEDmnFxnkx3w9Nor4cjhbce2gStz1bcqPKXJiyQUmlqLzVpCqsr8s4uttfR"  # Replace with your actual key
binance_api_secret = "MqMXFSDS4h2BECvvpTDLQGGkQaPIErzohZZv26zfwtCemiKMtHbhw2DOk5911exW"  # Replace with your actual secret
openai.api_key = "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"  # Replace with your actual key
telegram_bot_token = "7151812396:AAFnS6DKGk09jYxc6bKFDLCeSq2-toNS-VI"  # Replace with your actual token
telegram_chat_id = "1002336805236"  # Replace with your chat ID
unsplash_access_key = "mMFj3xFACoz6Ixbt35hhAfMYNjTo4xYxbGog7RUzTxQ"  # Replace with your Unsplash API key

# --- Functions ---

def fetch_cointelegraph_news():
    feed = feedparser.parse(cointelegraph_rss_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'description': entry.description,
            'link': entry.link,
        })
    return articles

def fetch_binance_data():
    client = Client(binance_api_key, binance_api_secret)
    btc_price = client.get_symbol_ticker(symbol="BTCUSDT") 
    return btc_price  

def generate_content(article, btc_price):
    try:
        # Summarization
        summary_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Summarize this article:\n\n{article['description']}",
            max_tokens=100 
        )
        summary = summary_response.choices[0].text.strip()

        # Analysis (simple example - you can expand this)
        analysis = f"Current BTC Price: ${btc_price['price']}\nThis may impact the events in the article." 

        # Image generation - try OpenAI first
        try:
            image_response = openai.Image.create(
                prompt=f"Generate an image related to this article: {article['title']}",
                n=1,
                size="256x256"
            )
            image_url = image_response['data'][0]['url']
        except openai.error.OpenAIError as e:
            print(f"OpenAI Image generation error: {e}")
            image_url = None

        # If OpenAI fails, use Unsplash
        if image_url is None:
            image_url = get_image_from_unsplash(article['title'])

        # Combine content
        content = f"**{article['title']}**\n\n{summary}\n\n{analysis}\n\n{image_url}\n\nRead more: {article['link']}" 
        return content

    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return f"Error generating content for {article['title']}"


def get_image_from_unsplash(query):
    """Fetches an image from Unsplash based on the query."""
    try:
        url = f"https://api.unsplash.com/photos/random?query={query}&client_id={unsplash_access_key}"
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        return data['urls']['regular']
    except requests.exceptions.RequestException as e:
        print(f"Unsplash API error: {e}")
        return None  


def send_to_telegram(content):
    bot = telegram.Bot(token=telegram_bot_token)
    try:
        bot.send_message(chat_id=telegram_chat_id, text=content, parse_mode=telegram.ParseMode.MARKDOWN)
    except telegram.error.TelegramError as e:
        print(f"Telegram API error: {e}")


def crypto_news_job():
    news = fetch_cointelegraph_news()
    btc_price = fetch_binance_data()
    for article in news:
        content = generate_content(article, btc_price)
        send_to_telegram(content)

# --- Scheduling ---
scheduler = BlockingScheduler()
scheduler.add_job(crypto_news_job, 'interval', hours=4)  # Run every 4 hours
scheduler.start()
