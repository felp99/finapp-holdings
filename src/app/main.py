from flask import Flask, request, jsonify
from functools import wraps
import datetime
from ..analysis import TickerInvestment
import os

app = Flask(__name__)
API_KEY = os.getenv('API_KEY')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/ticker', methods=['POST'])
@require_api_key
def investment_ticker():
    data = request.json
    try:
        ticker = data['ticker']
        value = data['value']
        start = data.get('start')
        end = data.get('end')
        start = datetime.datetime.strptime(start, '%Y-%m-%d') if start else None
        end = datetime.datetime.strptime(end, '%Y-%m-%d') if end else None
        investment = TickerInvestment(ticker, value, start, end)
        result = investment.result.df_capital_cumprod.to_json(orient='records')
        return result, 200

    except KeyError as e:
        return jsonify({"error": f"Missing required parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
