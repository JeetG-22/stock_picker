# stock_picker: CS210 Project
Predicting Top 5 Tech Stocks To Buy

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

### Locating Stocks in the Technology Sector
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
(venv) example@example stock_picker % python3 tech_stock_list_dl.py
```
```
Raw API data saved to stock_list_dl.json
Total stocks fetched: 3319
Found 559 technology stocks
Unique technology stocks after deduplication: 559
Data inserted: 559 stocks successfully into tech_stocks table.
Number of records in the database: 559
```



