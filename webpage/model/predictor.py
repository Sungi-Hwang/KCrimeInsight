
# webpage/model/predictor.py

import pandas as pd
from typing import Tuple, Dict, List
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import RidgeCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

class CrimePredictor:
    def __init__(self, top_n: int = 15):
        self.top_n     = top_n
        self.cols: List[str] = []
        self.model     = None
        self.train_df_: pd.DataFrame = pd.DataFrame()

    def _select(self, df: pd.DataFrame, target: str) -> List[str]:
        # 1) 불필요 문자열 컬럼(지역, 연도, target) 제거
        num = (
            df
            .drop(columns=[target, "연도", "지역"], errors="ignore")
            .select_dtypes(include="number")
        )
        # 2) target 시리즈도 숫자형으로 가져오기
        y = pd.to_numeric(df[target], errors="coerce")
        # 3) 상관계수 계산, 절댓값 기준 top_n
        corrs = num.corrwith(y).abs()
        return corrs.nlargest(self.top_n).index.tolist()

    def fit(self,
            df: pd.DataFrame,
            target_col: str,
            region: str,
            target_year: int):

        # 전체 _rate 컬럼에서 target_col 빼고
        all_rates = [c for c in df.columns if c.endswith("_rate")]
        feature_rates = [c for c in all_rates if c != target_col]
        train_cols = [target_col] + feature_rates

        if region == "전국":
            train = (
                df[df["연도"] < target_year]
                  .groupby("연도")[train_cols]
                  .mean()
                  .reset_index()    # ← 여기 drop=True 제거!
            )
        else:
            train = (
                df[(df["지역"] == region) & (df["연도"] < target_year)]
                .copy()
            )

        if len(train) < 2:
            raise ValueError("학습 데이터가 부족합니다.")

        self.cols = sorted(self._select(train, target_col))
        if not self.cols:
            raise ValueError("상관계수 기반 feature가 없습니다.")

        X = train[self.cols].to_numpy()
        y = train[target_col].to_numpy()

        if len(y) < 3:
            self.model = Pipeline([
                ("scaler", StandardScaler()),
                ("ridge", RidgeCV(alphas=[0.1, 1.0, 10.0]))
            ])
        else:
            self.model = XGBRegressor(
                objective="count:poisson",
                n_estimators=120,
                max_depth=2,
                learning_rate=0.1,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42
            )

        self.model.fit(X, y)
        self.train_df_ = train        # 이제 train_df_ 에 '연도' 컬럼이 남습니다

    def predict(self,
                df: pd.DataFrame,
                target_col: str,
                region: str,
                target_year: int
               ) -> Tuple[float, Dict]:

        if region == "전국":
            all_rates = [c for c in df.columns if c.endswith("_rate")]
            feature_rates = [c for c in all_rates if c != target_col]
            test_cols = [target_col] + feature_rates

            test = (
                df[df["연도"] == target_year]
                  .groupby("연도")[test_cols]
                  .mean()
                  .reset_index(drop=True)
            )
        else:
            test = df[(df["지역"] == region) & (df["연도"] == target_year)].copy()

        if test.empty:
            ref = (
                df[df["연도"] < target_year]
                  .groupby("연도")[self.cols]
                  .mean()
                  .tail(1)
                if region == "전국"
                else df[df["지역"] == region][self.cols].tail(1)
            )
            ref = ref.reindex(columns=self.cols, fill_value=0)
            y_hat = float(self.model.predict(ref.to_numpy())[0])
            return y_hat, {}

        X_test = test.reindex(columns=self.cols, fill_value=0).to_numpy()
        y_true = test[target_col].to_numpy()
        y_hat   = self.model.predict(X_test)

        return float(y_hat[0]), {
            "mae":  mean_absolute_error(y_true, y_hat),
            "mape": mean_absolute_percentage_error(y_true, y_hat)
        }
