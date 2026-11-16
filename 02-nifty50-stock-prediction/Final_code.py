# 1. Importing and loading the data

import pandas as pd #tables
import numpy as np #arrays 
import matplotlib.pyplot as plt 
import seaborn as sns #visuals

from sklearn.preprocessing import StandardScaler #normalization (Makes features mean = 0, std = 1)
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score #evaluation metrics
from sklearn.linear_model import LogisticRegression 
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from tensorflow.keras.models import Sequential 
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras import Input #defines the shape of the data entering your neural network
from tensorflow.keras.layers import LSTM, GRU
from statsmodels.stats.outliers_influence import variance_inflation_factor #VIF to check multicollinearity
from statsmodels.tsa.arima.model import ARIMA 


def create_sequences(X, y, time_steps=5): #Converts data → time series format for LSTM/GRU
    X_seq, y_seq = [], []

    for i in range(len(X) - time_steps):
        X_seq.append(X[i:i+time_steps])
        y_seq.append(y[i+time_steps]) #“Given last 5 days → predict next”

    return np.array(X_seq), np.array(y_seq)


df = pd.read_csv("NIFTY_50_COMPANIES.csv")

df['Date'] = pd.to_datetime(df['Date']) #Convert to time format
df = df.sort_values(by=['Ticker', 'Date']).reset_index(drop=True)  #Ensures time order and Avoids data leakage
df = df.dropna()



# 2. EDA

lower = df['Daily_Return_%'].quantile(0.01) #removes extreme outliers - It finds the 1st percentile of your data: 1% of values are below this number and 99% are above it
upper = df['Daily_Return_%'].quantile(0.99) #finds the 99th percentile: 99% of values are below this number and Only 1% are above it
#lower → very small extreme values  and upper → very large extreme values  so < lower are replaced with lower, > upper are replaced with upper, and in between are unchanged

plt.figure(figsize=(8,5)) #Shows distribution → noisy, centered
sns.histplot(df['Daily_Return_%'].clip(lower, upper), bins=50, kde=True)

plt.title("Distribution of Daily Returns (Clipped)") 
plt.xlabel("Daily Return (%)")
plt.ylabel("Frequency")
plt.show()

print("Mean:", df['Daily_Return_%'].mean())
print("Std:", df['Daily_Return_%'].std())

lags = range(1, 21) #Measures dependence on past values - creates [1, 2, 3, ..., 20] (short term dependencies and trading days)
acf = [df['Daily_Return_%'].autocorr(lag=l) for l in lags] 

plt.plot(lags, acf)
plt.title("Autocorrelation")
plt.show()


numeric_df = df.select_dtypes(include=[np.number])
numeric_df = numeric_df.dropna()

plt.figure(figsize=(12,8))

corr = numeric_df.corr() #relationship bw features

sns.heatmap(corr, cmap='coolwarm', annot=False)

plt.title("Correlation Heatmap (All Features)")
plt.show()


numeric_df = df.select_dtypes(include=[np.number]) #Detects multicollinearity - only selecting numeric features
numeric_df = numeric_df.dropna()

vif_data = pd.DataFrame()
vif_data["Feature"] = numeric_df.columns #storing feature names
vif_data["VIF"] = [variance_inflation_factor(numeric_df.values, i) #VIF=1/1−R2
                  for i in range(len(numeric_df.columns))]

print(vif_data)


plt.figure(figsize=(12,5)) 
plt.plot(df['Date'], df['Daily_Return_%'])
plt.title("Daily Returns Over Time")
plt.show() #How daily returns change over time



# 3. Feature engineering

for lag in [1,2,3,5]: 
    df[f'Return_Lag_{lag}'] = df.groupby('Ticker')['Daily_Return_%'].shift(lag) #it shifts data backwards in time
    #Return_Lag_1	yesterday’s return
    #Return_Lag_2	2 days ago
    #Return_Lag_3	3 days ago
    #Return_Lag_5	5 days ago  

    #Helps model learn: “Does past return influence future return?”

df['Volatility_5'] = df.groupby('Ticker')['Daily_Return_%'].rolling(5).std().reset_index(0, drop=True) #Volatility - Measures how much returns fluctuate , Look at last 5 days and Compute standard deviation
df['Volatility_10'] = df.groupby('Ticker')['Daily_Return_%'].rolling(10).std().reset_index(0, drop=True) #Look at last 10 days and Compute standard deviation

df['Momentum_5'] = df.groupby('Ticker')['Daily_Return_%'].rolling(5).sum().reset_index(0, drop=True) #momentum - trend strength , Adds last 5 returns
df['Momentum_10'] = df.groupby('Ticker')['Daily_Return_%'].rolling(10).sum().reset_index(0, drop=True) 

# Positive → upward trend and Negative → downward trend
# We create these features because raw data does not contain enough usable patterns for the model to learn from. Lag - tells the model “What happened before?”; volatility - “Is market stable or chaotic?”; momentum - trend
# Machine learning models cannot understand time automatically so we convert time into these features


# 4. Creating the target variable - Will the stock go UP or DOWN in the next 5 days?

df['Future_5D_Return'] = df.groupby('Ticker')['Daily_Return_%'].shift(-5)  #It shifts data UP (future → present), for each row - Future_5D_Return = return 5 days ahead
df['Target'] = (df['Future_5D_Return'] > 0).astype(int) #Convert continuous values → binary classification : >0 then up and if <=0 then down

df = df.dropna().reset_index(drop=True)

# without shifting - model would use present info to predict present but with shifting: Past → predict future


# 5. Feature selection - “These are the inputs (X) you should use to predict the target”

features = [
    'Return_Lag_1','Return_Lag_2','Return_Lag_3','Return_Lag_5', #memory
    'Volatility_5','Volatility_10', #risk - how unstable the market is (high volaitility then unpredictable)
    'Momentum_5','Momentum_10', #trend - upward or downward movement
    'RSI_14','MACD', #RSI (Relative Strength Index): Measures overbought / oversold ; if High RSI → overbought → may fall, if Low RSI → oversold → may rise + MACD: Measures trend + momentum
    'Volume' #Measures trading activity - High volume → strong movement IF Low volume → weak signal
]


# 6. Evaluation metrics function

def evaluate_model(model, X, y, ann=False): #model - trained model, X-input features,y-true labels, ann-whether model is neural network, ann=FALSE because sklearn models use predict_proba() ANN uses predict(), They behave differently → need handling
    if ann:
        probs = model.predict(X).flatten() 
    else:
        probs = model.predict_proba(X)[:,1] #we want only the up (1) probs

    preds = (probs > 0.5).astype(int) #Convert probabilities → predictions - Models output probabilities, not labels so We convert probabilities → decisions

    return {
        "accuracy": accuracy_score(y, preds), 
        "f1": f1_score(y, preds), 
        "precision": precision_score(y, preds), #TP/TP+FP
        "recall": recall_score(y, preds), #TP/TP+FN
        "auc": roc_auc_score(y, probs)
    }


# 7. train-val-test split

df['Year'] = df['Date'].dt.year #extracts the year

results = [] 

final_y_true = None
final_y_pred = None
final_dates = None #initial storage

min_year = df['Year'].min() #1997
max_year = df['Year'].max() #2025

for split_year in range(min_year + 6, max_year - 2): #min year + At least 6 years of training data, maxyear-2: Enough future data for val + test

    train_df = df[df['Year'] <= split_year] #Uses ALL past data
    val_df   = df[(df['Year'] >= split_year+1) & (df['Year'] <= split_year+2)] #Next 2 years
    test_df  = df[df['Year'] == split_year+3] #Future year

    if len(val_df) == 0 or len(test_df) == 0: #Skip invalid splits
        continue

    X_train = train_df[features].values
    y_train = train_df['Target'].values

    X_val = val_df[features].values
    y_val = val_df['Target'].values

    X_test = test_df[features].values
    y_test = test_df['Target'].values

    print("Train balance:", np.mean(y_train)) #checking class balance
    print("Val balance:", np.mean(y_val))
    print("Test balance:", np.mean(y_test))

    scaler = StandardScaler() #normalising - We normalize after splitting to avoid data leakage and ensure that scaling parameters are learned only from the training data.
    X_train = scaler.fit_transform(X_train) #fit on train only - Avoid data leakage
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

   # time steps for LSTM and GRU
   #Although the data is time-ordered, models like LSTM require data in a specific 3D sequence format, so we explicitly create sequences to provide past time steps as input.
   #Time steps = how many past time points you give the model as input
    time_steps = 5 #Use last 5 days

    X_train_seq, y_train_seq = create_sequences(X_train, y_train, time_steps) #[X1, X2, X3, X4, X5] → predict X6, LSTM needs sequence input
    X_val_seq, y_val_seq = create_sequences(X_val, y_val, time_steps)
    X_test_seq, y_test_seq = create_sequences(X_test, y_test, time_steps)

    if len(X_train_seq) == 0 or len(X_test_seq) == 0: #Skip if not enough data
        continue


    #feature selection using ANN 
    # ANN: Input → Hidden layers → Output; OUTPUT=activation(w1x1+w2x2+..+b) so It learns weights (importance of features)
    # ANN can Can learn non-linear relationships and can combine features in complex ways - Which features help predict stock movement
    ann = Sequential([
        Input(shape=(X_train.shape[1],)),
        Dense(64, activation='relu'), #64 neurons
        Dropout(0.3), #Randomly drops 30% neurons to prevent overfitting
        Dense(32, activation='relu'), #2nd hidden layer - compresses info
        Dense(1, activation='sigmoid') #output layer - outputs prob 0 → DOWN  and 1 → UP
    ])

    ann.compile(optimizer='adam', loss='binary_crossentropy') #adam (Adaptive Moment Estimation) optimiser - Adjusts weights efficiently : Tracks past gradients (momentum) and then Adjusts learning rate for each parameter

    ann.fit(X_train, y_train, epochs=3, batch_size=32, verbose=0) 

    baseline_preds = ann.predict(X_val).flatten() #How good model is with ALL features
    baseline_score = roc_auc_score(y_val, baseline_preds)

    importances = []

    for i in range(X_val.shape[1]): #loops over each feature
        scores = []

        for _ in range(5): #repeat 5 times - Shuffle is random → reduce noise
            X_perm = X_val.copy() #Shuffles ONLY one feature - if feature is important: Shuffle it → model performance drops, and if not important then no change
            np.random.shuffle(X_perm[:, i]) 

            perm_preds = ann.predict(X_perm).flatten() #RE-COMPUTE PERFORMANCE
            perm_score = roc_auc_score(y_val, perm_preds) 

            scores.append(baseline_score - perm_score) #Larger drop = more important feature

        importances.append(np.mean(scores)) #Average importance

    importance_df = pd.DataFrame({
        'Feature': features,
        'Importance': importances
    }).sort_values(by='Importance', ascending=False)

    top_features = importance_df.head(6)['Feature'].tolist() #selects best 6 features

    print(f"\nYear {split_year} - Selected Features (ANN):")
    print(top_features)

    print("\nFeature Importance:")
    print(importance_df)

    #updating data with top features - Now model uses ONLY important features
    X_train_sel = train_df[top_features].values
    X_val_sel   = val_df[top_features].values
    X_test_sel  = test_df[top_features].values

    scaler = StandardScaler() #re-scale Because features changed
    X_train_sel = scaler.fit_transform(X_train_sel)
    X_val_sel = scaler.transform(X_val_sel)
    X_test_sel = scaler.transform(X_test_sel)

    # ML models
    lr = LogisticRegression(max_iter=1000) #Allow the model to update its weights up to 1000 times while learning
    rf = RandomForestClassifier(n_estimators=100)
    xgb = XGBClassifier(n_estimators=100, eval_metric='logloss') #logloss - Measures classification error during training

    lr.fit(X_train_sel, y_train) #model learns X (features) → y (Target) in training
    rf.fit(X_train_sel, y_train)
    xgb.fit(X_train_sel, y_train)

    # DL models
    ann_final = Sequential([ #Treats each row independently - each row -> prediction, doesnt understand time sequence
        Input(shape=(X_train_sel.shape[1],)),
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid')
    ]) #Input → Hidden Layer → Output - ann model built

    ann_final.compile(optimizer='adam', loss='binary_crossentropy') #Binary crossentropy → classification loss
    ann_final.fit(X_train_sel, y_train, epochs=3, verbose=0) #Epoch = one full pass through the entire training dataset


    lstm_model = Sequential([ # A special neural network for time series: past → present → future - Learn patterns from the last few days (time steps) to predict future movement
        LSTM(32, input_shape=(time_steps, X_train_seq.shape[2])), #32 neurons , At each step: Keeps important info and Forgets irrelevant info
        Dense(1, activation='sigmoid') #1 neuron in the output layer - ONE output → probability of UP(classification problem)
    ])

    lstm_model.compile(optimizer='adam', loss='binary_crossentropy') 

    lstm_model.fit( #[Last 5 days] → predict next movement
        X_train_seq, y_train_seq,
        epochs=3,
        batch_size=32,
        verbose=0
    )

    lstm_probs = lstm_model.predict(X_test_seq).flatten() #Probability of UP
    lstm_preds = (lstm_probs > 0.5).astype(int) 

    lstm_acc = accuracy_score(y_test_seq, lstm_preds)
    lstm_f1 = f1_score(y_test_seq, lstm_preds)
    lstm_prec = precision_score(y_test_seq, lstm_preds)
    lstm_rec = recall_score(y_test_seq, lstm_preds)
    lstm_auc = roc_auc_score(y_test_seq, lstm_probs)

  # LSTM is powerful ONLY if time patterns exist - from eda, autocorrelation is almost 0 so data acts as noise so Even LSTM cannot learn strong patterns

    gru_model = Sequential([ #Gated Recurrent Unit - Learn patterns from past time steps (like LSTM) and predict future movement (simpler + faster)
        GRU(32, input_shape=(time_steps, X_train_seq.shape[2])),
        Dense(1, activation='sigmoid')
    ])

    gru_model.compile(optimizer='adam', loss='binary_crossentropy')

    gru_model.fit(
        X_train_seq, y_train_seq,
        epochs=3,
        batch_size=32,
        verbose=0
    )

    gru_probs = gru_model.predict(X_test_seq).flatten()
    gru_preds = (gru_probs > 0.5).astype(int)

    gru_acc = accuracy_score(y_test_seq, gru_preds)
    gru_f1 = f1_score(y_test_seq, gru_preds)
    gru_prec = precision_score(y_test_seq, gru_preds)
    gru_rec = recall_score(y_test_seq, gru_preds)
    gru_auc = roc_auc_score(y_test_seq, gru_probs)

    #ARIMA (time series model)
    try: #this prevents your code from crashing
        stock_name = train_df['Ticker'].iloc[0] #Picks first stock in dataset bcuz ARIMA works on single time series

        train_series = train_df[train_df['Ticker'] == stock_name]['Daily_Return_%'].dropna() #Filters: only selected stock, only returns, removes missing values
        test_series  = test_df[test_df['Ticker'] == stock_name]['Daily_Return_%'].dropna()

        if len(train_series) < 20 or len(test_series) == 0: #ensures enough data - at least 20 data points in training
            raise ValueError("Not enough data")

        model = ARIMA(train_series, order=(1,0,1)) #model learns Current value = past value + past error
        model_fit = model.fit() #Learns parameters from training data

        forecast = model_fit.forecast(steps=len(test_series)) #Predict future values - Same length as test set

        y_pred = (forecast > 0).astype(int) #Convert to classification
        y_true = (test_series.values > 0).astype(int) #Convert actual values to UP/DOWN

        arima_acc = accuracy_score(y_true, y_pred)
        arima_f1 = f1_score(y_true, y_pred)
        arima_prec = precision_score(y_true, y_pred)
        arima_rec = recall_score(y_true, y_pred)
        arima_auc = roc_auc_score(y_true, y_pred)

    except Exception as e: 
        print("ARIMA ERROR:", e)
        arima_acc, arima_f1, arima_prec, arima_rec, arima_auc = 0,0,0,0,0

    #evaluation metrics
    lr_test = evaluate_model(lr, X_test_sel, y_test)
    rf_test = evaluate_model(rf, X_test_sel, y_test)
    xgb_test = evaluate_model(xgb, X_test_sel, y_test)
    ann_test = evaluate_model(ann_final, X_test_sel, y_test, ann=True)

    final_y_true = y_test.copy() #store actual labels

    final_probs = xgb.predict_proba(X_test_sel)[:,1]
    final_y_pred = (final_probs > 0.5).astype(int)

    final_dates = test_df['Date'].values

    results.append({
        "Year": split_year,

        # Logistic Regression
        "LR_Acc": lr_test["accuracy"],
        "LR_F1": lr_test["f1"],
        "LR_Precision": lr_test["precision"],
        "LR_Recall": lr_test["recall"],
        "LR_AUC": lr_test["auc"],

        # Random Forest
        "RF_Acc": rf_test["accuracy"],
        "RF_F1": rf_test["f1"],
        "RF_Precision": rf_test["precision"],
        "RF_Recall": rf_test["recall"],
        "RF_AUC": rf_test["auc"],

        # XGBoost
        "XGB_Acc": xgb_test["accuracy"],
        "XGB_F1": xgb_test["f1"],
        "XGB_Precision": xgb_test["precision"],
        "XGB_Recall": xgb_test["recall"],
        "XGB_AUC": xgb_test["auc"],

        # ANN
        "ANN_Acc": ann_test["accuracy"],
        "ANN_F1": ann_test["f1"],
        "ANN_Precision": ann_test["precision"],
        "ANN_Recall": ann_test["recall"],
        "ANN_AUC": ann_test["auc"],

        # LSTM
        "LSTM_Acc": lstm_acc,
        "LSTM_F1": lstm_f1,
        "LSTM_Precision": lstm_prec,
        "LSTM_Recall": lstm_rec,
        "LSTM_AUC": lstm_auc,

        # GRU
        "GRU_Acc": gru_acc,
        "GRU_F1": gru_f1,
        "GRU_Precision": gru_prec,
        "GRU_Recall": gru_rec,
        "GRU_AUC": gru_auc,

        # ARIMA
        "ARIMA_Acc": arima_acc,
        "ARIMA_F1": arima_f1,
        "ARIMA_Precision": arima_prec,
        "ARIMA_Recall": arima_rec,
        "ARIMA_AUC": arima_auc,
    })

# Results
results_df = pd.DataFrame(results)

print("\nFINAL RESULTS:")
print(results_df.head())

results_df.to_csv("final_results.csv", index=False)

print("\nAVERAGE PERFORMANCE:")
print(results_df.mean(numeric_only=True))


#Qualitative analysis
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

if final_y_true is not None: #Ensures predictions exist

    y_true = np.array(final_y_true)
    y_pred = np.array(final_y_pred)
    dates = np.array(final_dates) #for plotting

    subset = 200
    if len(y_true) > subset:
        y_true = y_true[-subset:]
        y_pred = y_pred[-subset:]
        dates = dates[-subset:]

    # actual vs predicted plot
    correct = y_true == y_pred
    incorrect = y_true != y_pred

    plt.figure(figsize=(14,6))

    plt.plot(dates, y_true, label='Actual', linestyle='--')
    plt.plot(dates, y_pred, label='Predicted', alpha=0.7)

    plt.scatter(dates[correct], y_true[correct], label='Correct', marker='o')
    plt.scatter(dates[incorrect], y_true[incorrect], label='Incorrect', marker='x')

    plt.title("Actual vs Predicted Stock Movement")
    plt.xlabel("Date")
    plt.ylabel("Movement (0 = Down, 1 = Up)")
    plt.legend()

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    #confusion matrix
    cm = confusion_matrix(y_true, y_pred)

    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot()

    plt.title("Confusion Matrix (Test Set)")
    plt.show()