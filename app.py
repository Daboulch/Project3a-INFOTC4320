from flask import Flask, render_template, request, flash, abort
import pygal
import requests
from datetime import datetime
import csv

API_KEY = "EDR5KNC8XVI980TW"
ALPHA_URL = "https://www.alphavantage.co/query"

# Make a Flask application object called app
app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = 'your secret key'

#Load CSV data
def load_csv(csv_file="stocks.csv"):
    symbols = []
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbols.append(row["Symbol"].upper().strip())
        return sorted(symbols)

csv_symbols = load_csv()


def get_data(symbol, start_date, end_date, function):
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": API_KEY,
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

    response = requests.get(ALPHA_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if "Error Message" in data:
        raise ValueError(data["Error Message"])
    if "Note" in data:
        raise ValueError(data["Note"])
    if "Information" in data:
        raise ValueError(data["Information"])

    key_check = TIME_SERIES_KEYS.get(function)
    if key_check not in data:
        raise ValueError("No data found for this selection.")

    raw_data = data[key_check]

    # Filter date range
    filtered = {}
    for date_str, values in raw_data.items():
        if len(date_str) == 10:
            current_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        else:
            current_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
        if start_date <= current_date <= end_date:
            filtered[date_str] = values

    return dict(sorted(filtered.items()))

def create_graph(stock_data, symbol, chart_type, start_date, end_date):
    #Acquire sorted data
    sorted_items = list(stock_data.items())

    #Extract dates for the x-axis labels
    dates = []
    for date_str, values in sorted_items:
        if len(date_str) == 10:
            dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
        else:
            dates.append(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"))

    #Extract data
    open_prices = []
    high_prices = []
    low_prices = []
    close_prices = []

    for _, values in sorted_items:
        open_prices.append(float(values["1. open"]))
        high_prices.append(float(values["2. high"]))
        low_prices.append(float(values["3. low"]))
        close_prices.append(float(values["4. close"]))

    #Selecting chart type
    if chart_type.lower() == "line":
        chart = pygal.Line(x_label_rotation=30)
    elif chart_type.lower() == "bar":
        chart = pygal.Bar(x_label_rotation=30)
    else:
        raise ValueError("Invalid chart type selected.")

    total_points = len(dates)
    all_labels = [d.strftime("%Y-%m-%d %H:%M") for d in dates]
    chart.x_labels = all_labels
    if total_points > 30:
        step = total_points // 30
        chart.x_labels_major = [all_labels[i] for i in range(0, total_points, step)]
        chart.show_minor_x_labels = False
    else:
        chart.show_minor_x_labels = True
        

    #Set chart title and labels for x-axis
    chart.title = f"{symbol} Stock Data ({start_date} → {end_date})"
    chart.show_x_guides = False

    #Add stock data to the chart
    chart.add("Open", open_prices)
    chart.add("High", high_prices)
    chart.add("Low", low_prices)
    chart.add("Close", close_prices)

    #Save graph to static folder
    filename = f"static/charts/{symbol}_{chart_type}_chart.svg"
    chart.render_to_file(filename)
    return filename

@app.route('/', methods=["GET","POST"])
def index():
    chart_url = None
    error_message = None

    #Get symbols from stocks csv and get users inputs
    if request.method == "POST":
        symbol = request.form.get("symbol").upper().strip()
        chart_type = request.form.get("chart_type")
        time_series = request.form.get("time_series")
        start_input = request.form.get("start_date")
        end_input = request.form.get("end_date")
        try:
            start_date = datetime.strptime(start_input, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_input, "%Y-%m-%d").date()

            if start_date > end_date:
                raise ValueError("Start date cannot be after end date.")
            
            if symbol not in csv_symbols:
                raise ValueError("Invalid stock symbol.")

            stock_data = get_data(symbol,start_date, end_date, time_series)

            if not stock_data:
                raise ValueError("No data available for the selected range.")
            

            chart_file = create_graph(stock_data, symbol, chart_type, start_date, end_date)
            chart_url = f"/{chart_file}"

        except Exception as e:
            error_message = str(e)

    return render_template("index.html", chart_url=chart_url, error=error_message, symbols=csv_symbols)

app.run(host="0.0.0.0")