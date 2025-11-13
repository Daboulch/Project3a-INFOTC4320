import pygal
import lxml
import requests
from datetime import datetime
import sys
import webbrowser


api_key = "EDR5KNC8XVI980TW"
url = "https://www.alphavantage.co/query"

def get_symbol():
    while True:
        symbol = input("Enter the stock symbol (e.g., AAPL, TSLA, MSFT): ").upper().strip()

        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": symbol,
            "apikey": api_key,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "Information" in data:
                print(f"API limit reached: {data['Information']}")
                sys.exit()

            if "Error Message" in data:
                print(f"API returned an error: {data['Error Message']}")
                sys.exit()

            matches = []
            for x in data.get("bestMatches", []):
                value = x.get("1. symbol", "")
                if value:
                    matches.append(value.upper().strip())
            
            if symbol.upper() in matches:
                return symbol.upper()
            else:
                print("Stock symbol is invalid. Please enter a valid symbol.")

        except requests.RequestException as error:
            print(error)
            sys.exit()



def get_chart():
    print("\nChoose a chart type:")
    print("1. Line")
    print("2. Bar")
    
    while True:
        chart_choice = input("Enter your choice (1-2): ").strip()
        if chart_choice == "1":
            chart_type = "line"
        elif chart_choice == "2":
            chart_type = "bar"
        else:
            print("Invalid choice, please choose 1 or 2.")
            continue

        return chart_type


def get_time_series():
    print("\nChoose a time series function:")
    print("1. TIME_SERIES_INTRADAY")
    print("2. TIME_SERIES_DAILY")
    print("3. TIME_SERIES_WEEKLY")
    print("4. TIME_SERIES_MONTHLY")

    while True:
        time_choice = input("Enter your choice (1-4): ").strip()

        if time_choice == "1":
            time_series = "TIME_SERIES_INTRADAY"
        elif time_choice == "2":
            time_series = "TIME_SERIES_DAILY"
        elif time_choice == "3":
            time_series = "TIME_SERIES_WEEKLY"
        elif time_choice == "4":
            time_series = "TIME_SERIES_MONTHLY"
        else:
            print("Invalid choice, please choose 1-4.")
            continue

        return time_series


def get_dates():
    while True:
        start_input = input("Enter the start date (YYYY-MM-DD): ")
        end_input = input("Enter the end date (YYYY-MM-DD): ")
        try:
            start_date = datetime.strptime(start_input, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_input, "%Y-%m-%d").date()
        except ValueError:
            print("Error: Invalid date format. Please enter a date in (YYYY-MM-DD) format.")
            continue

        if start_date > end_date:
            print("Error: Start date cannot be later than end date. Please enter valid dates.")
        else:
            return start_date, end_date

    


def get_data(symbol, start_date, end_date, api_key, function):  
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "full",
    }

    TIME_SERIES_KEYS = {
        "TIME_SERIES_INTRADAY": "Time Series (5min)",
        "TIME_SERIES_DAILY": "Time Series (Daily)",
        "TIME_SERIES_WEEKLY": "Weekly Time Series",
        "TIME_SERIES_MONTHLY": "Monthly Time Series",
    }

    if function == "TIME_SERIES_INTRADAY":
        params["interval"] = "5min"

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    #Error checking incase the API returns an error because of rate limits or other reasons.
    key_check = TIME_SERIES_KEYS.get(function)
    if "Error Message" in data:
        raise ValueError(f"API returned an error: {data["Error Message"]}")
    if "Note" in data:
        raise ValueError(f"API limit reached: {data["Note"]}")
    if key_check not in data:
        raise ValueError(f"No time series data found. Response: {data}")
    
    raw_data = data[TIME_SERIES_KEYS[function]]

    #Takes key value pairs from raw_data and makes a new sorted dictionary that only contains data between the user selected start_date and end_date
    filtered_data = {
        date: values
        for date, values in raw_data.items()
        if start_date <= datetime.strptime(date[:10], "%Y-%m-%d").date() <= end_date
    }

    sorted_data = dict(sorted(filtered_data.items()))
    
    return sorted_data

def create_graph(stock_data, symbol, chart_type, start_date, end_date):
    if not stock_data:
        print("No data to display.")
        return

    sorted_items = list(stock_data.items())
    dates = [datetime.strptime(date, "%Y-%m-%d") for date, _ in sorted_items]
    date_labels = [d.strftime("%Y-%m-%d") for d in dates]

    open_prices = [float(values["1. open"]) for _, values in sorted_items]
    high_prices = [float(values["2. high"]) for _, values in sorted_items]
    low_prices = [float(values["3. low"]) for _, values in sorted_items]
    close_prices = [float(values["4. close"]) for _, values in sorted_items]


    # Choose chart type
    if chart_type.lower() == 'line':
        chart = pygal.Line(x_label_rotation=25)
    elif chart_type.lower() == 'bar':
        chart = pygal.Bar(x_label_rotation=25)
    else:
        print("Invalid chart type. Defaulting to line chart.")
        chart = pygal.Line(x_label_rotation=25)


    chart.title = f"{symbol} Stock Data ({start_date} → {end_date})"
    chart.x_labels = date_labels
    chart.show_minor_x_labels = True
    chart.show_x_guides = True

    chart.add('Open', open_prices)
    chart.add('High', high_prices)
    chart.add('Low', low_prices)
    chart.add('Close', close_prices)

    # Save and open graph
    filename = f"{symbol}_stock_chart.svg"
    chart.render_to_file(filename)
    print(f"Graph saved as {filename} and opened in your browser.")
    webbrowser.open(filename)
    return()


while True:
    function = get_time_series()
    symbol = get_symbol()
    start_date, end_date = get_dates()
    chart_type = get_chart()

    try:
        stock_data = get_data(symbol, start_date, end_date, api_key, function)
        print(f"Data for {symbol} using {function} from {start_date} to {end_date}")
        if len(stock_data) == 0:
            print("No data found for the selected date range.")
        else:
            for date, values in stock_data.items():
                open_ = values.get("1. open")
                high = values.get("2. high")
                low = values.get("3. low")
                close = values.get("4. close")
                print(f"{date} | Open: {open_} | High: {high} | Low: {low} | Close: {close}")
            create_graph(stock_data, symbol, chart_type, start_date, end_date)
    except ValueError as e:
        print(e)
 
    retry = input("\nWould you like to fetch another dataset? (y/n): ").strip().lower()
    if retry != 'y':
        print("Exiting program.")
        break