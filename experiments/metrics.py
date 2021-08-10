"""
Score function to analyze how well simulation parameters performed.
Used in simulation parameter search
"""
import os
import pandas as pd
import numpy as np
import statsmodels.formula.api as sm
from scipy.spatial.distance import cosine
from sklearn.preprocessing import StandardScaler
from experiments.system_model_v3.post_process_search import post_process_results

def score_file(experiment_folder, results_id, params=None):
    experiment_results = os.path.join(experiment_folder, 'experiment_results.hdf5')
    experiment_results_key = 'results_' + results_id
    df_raw = pd.read_hdf(experiment_results, experiment_results_key)

    return score(df_raw, params)

def score(df_raw, params=None):
    s = 0

    df = post_process_results(df_raw)

    n_runs = len(df['run'].unique())

    # get last timesetp
    last_timestep = df['timestep'].iloc[-1]

    # Short-term stability
    cv_ratios = []
    for i in range(1, n_runs + 1):
        market_std = df.query("run == @i")['market_price'].std()
        market_mean = df.query("run == @i")['market_price'].mean()
        eth_std = df.query("run == @i")['eth_price'].std()
        eth_mean = df.query("run == @i")['eth_price'].mean()

        market_cv = market_std / market_mean
        eth_cv = eth_std / eth_mean
        cv_ratios.append(market_cv/eth_cv)

    mean_cv_ratios = np.mean(cv_ratios)
    s += min(10, mean_cv_ratios)

    # How many runs didn't finish successfully
    n_finished = len(df.query("timestep == @last_timestep"))
    n_unfinished = n_runs - n_finished
    unfinished_pct = n_unfinished/n_runs
    s += 10 * (unfinished_pct)

    # Long-term stability
    cosine_sims = []
    for i in range(1, n_runs+1):
        scaler = StandardScaler()
        df_reg = df.query(f'run == @i')
        try:

            target_price_scaled = scaler.fit_transform(df_reg['target_price'].values.reshape(-1,1))
            data = pd.DataFrame()
            data['target_price_scaled'] = target_price_scaled.flatten()
            data['timestep'] = df_reg['timestep']
            data.columns = ['target_price_scaled', 'timestep']
            target_result = sm.ols(formula="target_price_scaled ~ timestep", data=data).fit()
            target_coeff = target_result.params[1]
            cos_sim = cosine([1, 0], [1, target_coeff])
            cosine_sims.append(min(1, cos_sim/0.20))
        except Exception as e:
            cosine_sims.append(1)

    mean_cosine_sim = np.mean(cosine_sims)
    s += 10 * mean_cosine_sim

    # Rates
    n_low_rates = sum((df[['run','apy']].groupby(['run']).max() < 10)['apy'])
    low_rates_pct = n_low_rates / n_runs
    s += 5 * low_rates_pct

    n_high_rates = sum((df[['run','apy']].groupby(['run']).max() > 200)['apy'])
    high_rates_pct = n_high_rates / n_runs
    s += 5 * high_rates_pct

    # Market/Target Convergence
    df['squared_error'] = (df['market_price'] - df['target_price']) ** 2
    mse = df['squared_error'].mean()
    rmse = mse ** 0.5
    nrmse = rmse / df['market_price'].std()
    s +=  min(10, 10 * nrmse)

    #print(f"{s=}, {mean_cv_ratios=}, {unfinished_pct=}, {mean_cosine_sim=}, "
    #      f"{low_rates_pct=}, {high_rates_pct=}, {mse=}, {rmse=}, {nrmse=}")

    return s

if __name__ == "__main__":
    import doctest
    doctest.testmod()
