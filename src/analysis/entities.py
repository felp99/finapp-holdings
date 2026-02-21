# Importing necessary libraries
from abc import ABC
import pandas as pd
import requests
import datetime
import yfinance

# Base class representing data
class Data(ABC):
  def __init__(self,
               df : pd.DataFrame = None,
               df_cumprod : pd.DataFrame = None,
               df_capital : pd.DataFrame = None,
               df_capital_cumprod : pd.DataFrame = None,) -> None:
    super().__init__()
    self.df = df  # DataFrame holding data
    self.df_cumprod = df_cumprod  # DataFrame holding cumulative product data
    self.df_capital = df_capital  # DataFrame holding capital data
    self.df_capital_cumprod = df_capital_cumprod  # DataFrame holding cumulative capital data

# Abstract class for working with DataFrames
class DataFrameUtil(ABC):
  def __init__(self):
    self.attrs = ['df', 'df_cumprod', 'df_capital', 'df_capital_cumprod']
    pass

  def generate_df(self) -> None:
    pass

  '''
  Method used to merge DataFrames while preserving their nature:
  View the illustration for better understanding.
  '''
  def join_dataframes(self, df: pd.DataFrame, dfs_to_be_joinned: list) -> pd.DataFrame:

    # Joining DataFrames using right join to respect attributes
    for i, df_to_be_joinned in enumerate(dfs_to_be_joinned):

      df = df.join(df_to_be_joinned, rsuffix=f"_{i}")

    # Forward fill to fill missing values downwards
    df.ffill(inplace=True)

    # Trimming the DataFrame to keep data within valid range
    return df[df.first_valid_index():df.last_valid_index()]

  # Method to generate a blank DataFrame with specified start and end dates
  def generate_blank_df(self, start: datetime.datetime, end:datetime.datetime, freq="D") -> pd.DataFrame:
      df = pd.DataFrame(index =
                           pd.date_range(
                               start=start,
                               end=end,
                               freq=freq))
      df.index.rename('date', inplace=True)
      return df

  def set_result(self):
    pass

  def set_default(self):
    pass

# Class representing individual investments
class Investment(DataFrameUtil, ABC):

    # Initializes the investment with basic parameters such as Name, Value, Start, and End
    def __init__(self, ticker: str, value: float, start: datetime.datetime, end: datetime.datetime) -> None:
      super().__init__()
      self.ticker = ticker  # Ticker symbol
      self.value = value  # Investment value
      self.start = start  # Start date
      self.end = end  # End date

      self.set_result()  # Setting investment result
      self.set_default()  # Setting default investment

    def set_result(self):
      df = self.generate_df()  # Generating investment data
      df_cumprod = df.cumprod()  # Calculating cumulative product
      self.result = Data(  # Saving investment results
        df = df,
        df_capital = df.copy()/df.copy() * self.value,  # Capital data
        df_cumprod = df_cumprod,  # Cumulative product data
        df_capital_cumprod = df_cumprod * self.value  # Cumulative capital data
      )

      self.result.df_capital_cumprod.reset_index(inplace=True)

    def set_default(self):
      self.default = Data(  # Default investment data
        df=self.result.df/self.result.df,
        df_capital = self.result.df/self.result.df * self.value,
        df_cumprod = self.result.df.cumprod()/self.result.df.cumprod(),
        df_capital_cumprod = self.result.df_cumprod/self.result.df_cumprod * self.value
      )

    def __str__(self):
      return f"Standalone Investment: \
      \n ticker: {self.ticker} \
      \n start: {self.start} \
      \n end: {self.end} \
      \n value: {self.value} \
      \n"

# Class for investments using ticker data
class TickerInvestment(Investment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Generates data for the main DataFrame TickerInvestment.df
    def generate_df(self) -> pd.DataFrame:

      # Retrieving ticker data using yfinance library
      ticker = yfinance.Ticker(self.ticker)

      # Fetching historical data within specified start and end dates
      ticker_df = ticker.history(start=self.start, end=self.end)

      # Extracting 'Close' column
      ticker_df = pd.DataFrame(ticker_df['Close'])

      # Renaming 'Close' column to ticker symbol
      ticker_df.rename(columns={'Close':self.ticker}, inplace=True)

      # Converting raw values to percentage change
      ticker_df.loc[:, self.ticker] = ticker_df[self.ticker].pct_change() + 1

      # Normalize index to timezone-naive daily timestamps
      ticker_df.index = pd.to_datetime(ticker_df.index).tz_localize(None).normalize()
      ticker_df.index.rename('date', inplace=True)

      return ticker_df

# Class for investments using SELIC data
class SelicInvestment(Investment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Generates data for the main DataFrame SelicInvestment.df
    def generate_df(self):

      # Fetching SELIC data from Banco do Brasil API
      res = requests.get('https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json')

      # Converting data to DataFrame
      selic_df = pd.DataFrame(res.json())

      # Converting 'data' column to the correct format
      selic_df.loc[:, 'data'] = pd.to_datetime(selic_df['data'], dayfirst=True)

      # Converting 'valor' column to the correct format
      selic_df.loc[:, self.ticker] = selic_df['valor'].astype(float)

      # Dropping old 'valor' column
      selic_df.drop(columns=['valor'], inplace = True)

      # Setting index to the new 'data' column with correct format
      selic_df.index = pd.DatetimeIndex(selic_df['data'].to_numpy())
      selic_df.drop(columns=['data'], inplace=True)

      # Converting SELIC to percentage
      selic_df.loc[:, self.ticker] = (selic_df[self.ticker]/100) + 1

      # Renaming index
      selic_df.index.rename('date', inplace=True)

      # Trimming the DataFrame with the specified start and end dates
      return selic_df[self.start:self.end]

class Portfolio(DataFrameUtil, ABC):
  def __init__(self, investments):

    # Checks if the list contains only Investment objects
    assert all(isinstance(investment, Investment) for investment in investments), "Error"
    self.investments = investments

    self.set_result()

    self.set_default()

    self.join_investments()

  def set_result(self):
    self.blank_df = self.generate_blank_df(start=datetime.datetime(year=1900, month=1, day=1),
                                     end=datetime.datetime.now())

    self.result = Data(
      df = self.blank_df.copy(),
      df_cumprod = self.blank_df.copy(),
      df_capital = self.blank_df.copy(),
      df_capital_cumprod = self.blank_df.copy(),
    )

  def set_default(self):
    self.default = Data(
      df = self.blank_df.copy(),
      df_cumprod = self.blank_df.copy(),
      df_capital = self.blank_df.copy(),
      df_capital_cumprod = self.blank_df.copy(),
    )

  # Aggregates each DataFrame related to each category according to each investment using the attribute
  def join_investments(self) -> None:

    self.result.df= self.join_dataframes(df=self.result.df, dfs_to_be_joinned=[i.result.df for i in self.investments])
    self.result.df_cumprod= self.join_dataframes(df=self.result.df_cumprod, dfs_to_be_joinned=[i.result.df_cumprod for i in self.investments])
    self.result.df_capital= self.join_dataframes(df=self.result.df_capital, dfs_to_be_joinned=[i.result.df_capital for i in self.investments])
    self.result.df_capital_cumprod= self.join_dataframes(df=self.result.df_capital_cumprod, dfs_to_be_joinned=[i.result.df_capital_cumprod for i in self.investments])

    self.default.df= self.join_dataframes(df=self.default.df, dfs_to_be_joinned=[i.default.df for i in self.investments])
    self.default.df_cumprod= self.join_dataframes(df=self.default.df_cumprod, dfs_to_be_joinned=[i.default.df_cumprod for i in self.investments])
    self.default.df_capital= self.join_dataframes(df=self.default.df_capital, dfs_to_be_joinned=[i.default.df_capital for i in self.investments])
    self.default.df_capital_cumprod= self.join_dataframes(df=self.default.df_capital_cumprod, dfs_to_be_joinned=[i.default.df_capital_cumprod for i in self.investments])

  def __str__(self):
      str_ = f"Portfolio: \n"
      for i in self.investments:
        str_ += f"{i} \n"
      return str_
