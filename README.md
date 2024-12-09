# stock_picker: CS210 Project
Predicting Top 5 Tech Stocks To Buy

## Our Python Environment

### Create Python Virtual Environment
In this project, we utilized Python virtual enviroments to keep pip packages consistent across all machines, while avoiding  externally managed environment errors. 

To create it, we use:
```shell
bash create_venv.sh
```

which implicitly runs:
```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If we want to update the requirements.txt file with the packages that we've installed with pip thus far, we can run:
```shell
pip freeze > requirements.txt
```

and then if we need to update the requirements again later:
```shell
pip install -r requirements.txt
```


### Storing API calls
For our database, we chose sqlite as the entire database can be stored in a single file, making it the perfect solution for keeping in version control like Git. 

1. First, we made sure that `sql-lite` exists on our system by typing:
```shell
sqlite3 --version
```

2. Next, we create our database file with
```shell
mkdir db
source .env
sqlite3 $DB_PATH
```
*This launches the sqlite shell, where the file `db/database.sqlite` will constantly be updated based on the actions we perform in the database.*

3. We first created the `api_responses` table with:
```sql
CREATE TABLE api_responses (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    response_json TEXT
);
```

4. We then tested that this table was created successfully by inserting a test record:
```sql
sqlite> INSERT INTO api_responses (response_json) VALUES ('{"example": "data"}');
```

5. We can confirm that the data works by selecting from it:
```sql
sqlite> SELECT * FROM api_responses;
1|2024-12-08 21:45:05|{"example": "data"}
```

6. We then delete the test record and exit the sqlite shell by typing:
```sql
DELETE FROM api_responses;
.exit
```

### Accessing the Database from Python
Check out `test_sqlite_connection.py` to see how we tested the connection to the database file and made sure the data stayed consistent. You can run the test locally with
```shell
pip install python-dotenv
python3 test_sqlite_connection.py
```

## Locating Stocks in the Technology Sector
One of the most difficult parts of this project was trying to locate an online resource that would provide a list of stocks that exist in the technology sector, as that is what we are targetting. Doing some research, we were able to locate [this StockAnalysis website](https://stockanalysis.com/list/nasdaq-stocks/), which listed every stock and allowed a column for sector. There was no *last updated* anywhere, but based on stock prices we realized that the data isn't more than a day old. As this step in the process was only to accumulate NASDAQ stocks in the technology sector anyways, it was good enough for that so we went with it.

After inspecting the data in the Chrome developer tools, we saw that the site sends http get requests to **api.stockanalysis.com**. Surely we thought there was some client authentication involved as most of their filters are locked behind a paywall. After doing some testing in Postman, we realized that this API was completely open and not rate-limited in any way, and we could even ask the API for columns locked behind the web interface's paywall!

So, we created `tech_stock_list_dl.py`, which let us download all the stocks listed on that website in JSON format. In a nutshell, it:

1. Confirms that our database file exists
2. Saves the full result of the API call to `stock_list_dl.json`
3. Removes any duplicates. There weren't any, but we felt it was necessary given we were exploiting their open API, which sometimes uses pagination depending on the normal of columns we requested
4. Prints out how many stocks it fetched
5. Uses the **Sector** key to filter out stocks in the Technology sector, then prints out how many tech stocks it found
6. Creates a table in our database called **tech_stocks**, with some of the data that we have in this call, while also adding more columns that we planned on filling in later from a more accurate stock source
7. Inserts each tech stock into the table
8. Printed out the count afterwards executed on the table to ensure that all the records were accounted for and inserted successfully

In all, we fetched **3319** stocks, where **559** of them ended up being technology stocks:

```shell
(venv) user@computer stock_picker % python3 tech_stock_list_dl.py
```
```
Raw API data saved to stock_list_dl.json
Total stocks fetched: 3319
Found 559 technology stocks
Unique technology stocks after deduplication: 559
Data inserted: 559 stocks successfully into tech_stocks table.
Number of records in the database: 559
```

## Section Intentionally Left Blank for the finance side of things



(After talking about how we decided the top X stocks)

## Ticker Relevance in the Media

### Finding the Articles
Surely we can create models and analyze stock data to figure out the top technology stocks in a given moment. However, we realize the need for supplementing this data with actual news source data, as knowing how people discuss/report on a stock is also important to take into consideration. So, we decided to look for an API that would give us news articles for each ticker, allowing us to count how many there are, and scrape the new articles in order to locate keywords in each article.

We found an API called Finnhub. Conveniently, they also provide a Pip package to interact with their API. So we created the script `find_articles.py`, which does the following:

1. Connects to our database
2. Creates the following table if it doesn't already exist:

```sql
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Helps us uniquely identify each news article later
    ticker TEXT NOT NULL, -- NOT NULL anything that is crucial
    category TEXT,
    datetime TEXT NOT NULL,
    headline TEXT NOT NULL,
    image TEXT,
    related TEXT,
    source TEXT NOT NULL,
    summary TEXT,
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Help us know when the script pulled in the article
    FOREIGN KEY (ticker) REFERENCES tech_stocks(symbol), -- Keeps tickers consistent to help aggregate data later
    UNIQUE (ticker, datetime, headline, source) -- Keeps entries unique, so that all articles are unique and there are no duplicates
);
```

3. With each provided ticker, queries the Finnhub API, retrieving all articles for each `ticker` written between `from_date` and `to_date`

4. Displays how many articles were found, how many new articles were found, and how many duplicates were skipped

When ran for the first time with tickers `["AAPL", "GOOGL", "AMZN", "MSFT", "TSLA"]`, for example, the table doesn't exist, nor do any articles for these tickers exist so all articles will be added to the table:

```shell
(venv) user@computer stock_picker % python3 find_articles.py  
AAPL:   Found 174 articles, inserted 174 new articles, skipped 0 duplicate articles.
GOOGL:  Found 178 articles, inserted 178 new articles, skipped 0 duplicate articles.
AMZN:   Found 220 articles, inserted 220 new articles, skipped 0 duplicate articles.
MSFT:   Found 199 articles, inserted 199 new articles, skipped 0 duplicate articles.
TSLA:   Found 212 articles, inserted 212 new articles, skipped 0 duplicate articles.
```

However, if we adjust the dates slightly to overlap some of the last date range, and adjust the tickers, some results will be skipped.

If we exchange 3 tickers:
```shell
(venv) user@computer stock_picker % python3 find_articles.py  
AAPL:   Found 174 articles, inserted 0 new articles, skipped 174 duplicate articles.
TSLA:   Found 212 articles, inserted 0 new articles, skipped 212 duplicate articles.
ADP:    Found 12 articles, inserted 12 new articles, skipped 0 duplicate articles.
LYFT:   Found 12 articles, inserted 12 new articles, skipped 0 duplicate articles.
OKTA:   Found 39 articles, inserted 39 new articles, skipped 0 duplicate articles.
```

If we add 3 more days of history, totalling 10:
```shell
(venv) user@computer stock_picker % python3 find_articles.py
AAPL:   Found 215 articles, inserted 41 new articles, skipped 174 duplicate articles.
TSLA:   Found 239 articles, inserted 27 new articles, skipped 212 duplicate articles.
ADP:    Found 17 articles, inserted 5 new articles, skipped 12 duplicate articles.
LYFT:   Found 14 articles, inserted 2 new articles, skipped 12 duplicate articles.
OKTA:   Found 45 articles, inserted 6 new articles, skipped 39 duplicate articles.
```

### Sentiment Analysis
To programmatically analyze each article, we needed a way where we could calculate the postive, negative, and neutral sentiments. Here's how we did that:

```shell
(venv) example@computer stock_picker % cd sentiment_scraper
# Example Run (We don't care about seeing the response of every article, so we append --nolog here)
(venv) example@computer sentiment_scraper % scrapy crawl db_spider --nolog
../db/database.sqlite
Processing article 32/3108 (1.0296010296010296%)...
```

#### 1. Scraping Each Article
We already had each article for every stock that we wanted to discover the sentiments of, so we utilized Scrapy to visit every website and pull the HTML code from the website source.

#### 2. Parsing the Article Contents
After each response came back, if it returned a `200 OK` status code, we took the content of the site and used the Python newspaper library to automatically retrieve the text content of the actual body of the article. We do this so that we avoid "sentimizing" words that aren't a part of the article itself, such as log in buttons, advertisements, cookies, etc.

Notice how we specifically mention the response having a `200` status code. Ultimately, web scraping means that the computer is visiting the website on your behalf, as opposed to you the user physically visiting the website. Some sites don't like when this happens, potentially because of analytical or advertisement reasons, so it is possible that the scraper faced several bot challenges and was not able to load the website successfully. We saw a decent handful of `400 Bad Request`, `401 Unauthorized`, and `403 Forbidden` statuses, and in our runs, we noticed about half of the articles faced this issue:

```sql
-- News articles that returned a 200 OK status code (had a matching sentiment added)
sqlite> SELECT COUNT(*) FROM news AS N LEFT JOIN sentiments AS S ON N.id = S.article_id WHERE S.article_id != "";
1535

-- Total amount of news articles
sqlite> SELECT COUNT(*) FROM news;
3108
```

#### 3. Performing Sentiment Analysis on the Text
After we retrieved only the body of the article, we decided to run it through a Sentiment Analyzer from nltk (`from nltk.sentiment.vader import SentimentIntensityAnalyzer`). This would take our blob of text, run an algorithm to decide the amount of positive, negative and neutral words come out of it, and rate it with corresponding numbers. If our compound score came out to at least `0.05`, we determined it as an overall positive article. If less, negative, and if exactly `0.05`, neutral. This gave us great weights as to how we can classify the article as a whole so that we can make a final determination about that ticker in the future.


#### 4. Inserting the Results into the Database
Scraping is quite computationally expensive, so we only wanted to do it once. Because of this, we decided to store each of the sentiment results in this table:

```sql
CREATE TABLE IF NOT EXISTS sentiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    url TEXT,
    score_neg REAL,
    score_neu REAL,
    score_pos REAL,
    score_compound REAL,
    overall_sentiment TEXT,
    FOREIGN KEY (article_id) REFERENCES news(id), -- References the news table for easier joins later!
    UNIQUE (article_id)
)
```

Together, with this data now in our database, we could make predictions on the best stocks to buy based on how the tickers were discussed in the media.

## Making the Final Decision



