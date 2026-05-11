from typing import Optional

import numpy as np
import xgboost as xgb


def predict_next_price_xgb(series: list[float], window: int = 3) -> Optional[float]:
    """Sliding-window XGBoost regressor fit on this product's own price_history."""
    if len(series) < window + 2:
        return None
    arr = np.asarray(series, dtype=np.float32)
    X_list: list[list[float]] = []
    y_list: list[float] = []
    for i in range(window, len(arr)):
        X_list.append(arr[i - window : i].tolist())
        y_list.append(float(arr[i]))
    X = np.asarray(X_list, dtype=np.float32)
    y = np.asarray(y_list, dtype=np.float32)
    model = xgb.XGBRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.12,
        subsample=0.95,
        colsample_bytree=0.95,
        random_state=42,
        verbosity=0,
        n_jobs=0,
    )
    model.fit(X, y)
    tail = arr[-window:].reshape(1, -1)
    pred = float(model.predict(tail)[0])
    return max(0.0, pred)
