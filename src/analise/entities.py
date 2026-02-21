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
      ticker_df[self.ticker] = ticker_df[self.ticker].pct_change() + 1

      # Renaming index
      ticker_df.index.rename('date', inplace=True)

      # Modifying index to match the desired format (daily)
      ticker_df.index = pd.to_datetime(ticker_df.index.strftime('%Y-%m-%d'))

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
      selic_df['data'] = pd.to_datetime(selic_df['data'], dayfirst=True)

      # Converting 'valor' column to the correct format
      selic_df[self.ticker] = selic_df['valor'].astype(float)

      # Dropping old 'valor' column
      selic_df.drop(columns=['valor'], inplace = True)

      # Setting index to the new 'data' column with correct format
      selic_df.set_index('data', inplace = True)

      # Converting SELIC to percentage
      selic_df[self.ticker] = (selic_df[self.ticker]/100) + 1

      # Renaming index
      selic_df.index.rename('date', inplace=True)

      # Trimming the DataFrame with the specified start and end dates
      return selic_df[self.start:self.end]

# Class for recurring investments
class RecurringInvestment(Investment, ABC):

    # Initializes the recurring investment with the frequency at which the value will be invested
    def __init__(self, freq="M", *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.freq = freq

      '''
      The main DataFrame has already been initialized earlier but it is changed to several DataFrames
      that loaded different investment values for each month.
      setup_recurrence creates new DataFrames based on the frequency.
      The other common attributes are created after this.
      '''
      self.set_result()

      self.set_default()

      self.group_result()

    # Basically cuts the main DataFrame based on each investment date
    def setup_recurrence(self, df: pd.DataFrame) -> pd.DataFrame:

      # Generates a DataFrame with only investment dates (1 per month in the monthly case, for example)
      start_dates_of_investments = self.generate_blank_df(start=self.start, end=self.end, freq="M").index.values

      # Iteration and joining into a list
      dfs_from_cut = []
      for start_date in start_dates_of_investments:
        _df_to_append = df[start_date:self.end].copy()
        dfs_from_cut.append(_df_to_append)

      # Drop the initial column as there is already one in the list
      df.drop(columns=[self.ticker], inplace=True)

      # Use the method to join the DataFrames again
      df = self.join_dataframes(df=df, dfs_to_be_joinned=dfs_from_cut)
      return df

    def set_result(self):
      df = self.generate_df()
      df_rec = self.setup_recurrence(df)
      df_cumprod = df_rec.cumprod()
      self.result = Data(
        df = df_rec,
        df_capital = df_rec/df_rec * self.value,
        df_cumprod = df_cumprod,
        df_capital_cumprod = df_cumprod * self.value,
      )

    def group_result(self):
      '''
      All DataFrames that exist now are extensions of an initial DataFrame changing the start date.
      This is because when you change the start date, you change the entire investment.
      At this point in the code, we transform all attributes like df_capital_cumprod into just one series,
      transitioning from a series of DataFrame columns to just one series without losing any information.
      '''

      self.result = Data(
        df = pd.DataFrame({self.ticker: self.result.df.transpose().sum()}),
        df_capital = pd.DataFrame({self.ticker:self.result.df_capital.transpose().sum()}),
        df_cumprod = pd.DataFrame({self.ticker:self.result.df_cumprod.transpose().sum()}),
        df_capital_cumprod = pd.DataFrame({self.ticker:self.result.df_capital_cumprod.transpose().sum()}),
      )

      self.default = Data(
        df = pd.DataFrame({self.ticker: self.default.df.transpose().sum()}),
        df_capital = pd.DataFrame({self.ticker:self.default.df_capital.transpose().sum()}),
        df_cumprod = pd.DataFrame({self.ticker:self.default.df_cumprod.transpose().sum()}),
        df_capital_cumprod = pd.DataFrame({self.ticker:self.default.df_capital_cumprod.transpose().sum()}),
      )

    def __str__(self):
      return f"Recurring Investment: \
      \n ticker: {self.ticker} \
      \n start: {self.start} \
      \n end: {self.end} \
      \n value: {self.value} \
      \n freq: {self.freq} \
      \n"

# Access specifically to recurrence and generation of Selic data
class RecurringSelicInvestment(SelicInvestment, RecurringInvestment):
    def __init__(self, *args, **kwargs):
        SelicInvestment.__init__(self, *args, **kwargs)
        RecurringInvestment.__init__(self,*args, **kwargs)

# Access specifically to recurrence and generation of Yahoo Finance Ticker data
class RecurringTickerInvestment(TickerInvestment, RecurringInvestment):
    def __init__(self, *args, **kwargs):
        TickerInvestment.__init__(self, *args, **kwargs)
        RecurringInvestment.__init__(self,*args, **kwargs)

# Class for portfolio management
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