import sys
import unittest
import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

# Ensure src/ is importable when running tests via python -m unittest
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.as_posix() not in sys.path:
    sys.path.insert(0, SRC_PATH.as_posix())

from analysis.entities import DataFrameUtil, TickerInvestment, SelicInvestment


class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.dfu = DataFrameUtil()
        self.ticker_history = pd.DataFrame(
            {"Close": [10.0, 10.5, 11.0]},
            index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
        )
        self.ticker_patcher = patch("analysis.entities.yfinance.Ticker")
        mock_ticker_cls = self.ticker_patcher.start()
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = self.ticker_history
        mock_ticker_cls.return_value = mock_ticker
        self.requests_patcher = patch("analysis.entities.requests.get")
        mock_requests_get = self.requests_patcher.start()
        self.fake_selic_payload = [
            {"data": "01/01/2020", "valor": "0.1"},
            {"data": "02/01/2020", "valor": "0.2"},
            {"data": "03/01/2020", "valor": "0.3"},
        ]
        fake_response = MagicMock()
        fake_response.json.return_value = self.fake_selic_payload
        mock_requests_get.return_value = fake_response
        self.addCleanup(self.ticker_patcher.stop)
        self.addCleanup(self.requests_patcher.stop)

    def test_ticker_investment(self):
        investment = TickerInvestment(
            ticker="PETZ3.SA",
            value=2000,
            start=datetime.datetime(year=2020, month=1, day=1),
            end=datetime.datetime(year=2020, month=1, day=4),
        )

        self.assertEqual(len(investment.result.df), len(self.ticker_history))
        self.assertIn(
            investment.ticker,
            investment.result.df_capital_cumprod.columns,
        )

    def test_selic_investment(self):
        investment = SelicInvestment(
            ticker="SELIC",
            value=2000,
            start=datetime.datetime(year=2020, month=1, day=1),
            end=datetime.datetime(year=2020, month=1, day=4),
        )

        self.assertEqual(len(investment.result.df), len(self.fake_selic_payload))
        self.assertGreater(
            investment.result.df_capital_cumprod[investment.ticker].iloc[-1], 0
        )


if __name__ == "__main__":
    unittest.main()
