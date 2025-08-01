from datetime import date


class InsufficientOHLCVDataError(Exception):
    """Raised when indicator computation fails due to missing OHLCV candles."""

    def __init__(self, security_id: int, start_date: date, end_date: date):
        self.security_id = security_id
        self.start_date = start_date
        self.end_date = end_date
        msg = (
            f"Insufficient OHLCV data for security {security_id} "
            f"from {start_date} to {end_date}"
        )
        super().__init__(msg)
