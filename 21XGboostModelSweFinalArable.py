
import pandas as pd
import numpy as np
import xgboost as xgb
import optuna
from sklearn.model_selection import GroupShuffleSplit, StratifiedKFold
from sklearn.metrics import matthews_corrcoef, accuracy_score, confusion_matrix, cohen_kappa_score, f1_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import shap
import matplotlib.pyplot as plt
import plotly.io as pio  # Import plotly.io for saving plots as images
import time
import seaborn as sns
import matplotlib.colors as plt_colors



# Start time measurement
start_time = time.time()

####################################################################################################
# 1. Read and preprocess data
map_df = pd.read_excel('/workspace/data/AllMapsInOneFolder/Points/ExtractedValues/FinalExtractedValues.xlsx')
print("Original columns:", map_df.columns)

xgb_df = map_df.copy()
print("Columns in XGBDataFrame:", xgb_df.columns)

# Make a copy of the DataFrame before dropping columns
xgb_df_copy = xgb_df.copy()


columns_to_drop = ['Class_txt', 'Arable', 'Three_Class_txt']
missing_columns = [col for col in columns_to_drop if col not in xgb_df.columns]
if missing_columns:
    print("Error: Columns not found in DataFrame:", missing_columns)
else:
    xgb_df.drop(columns=columns_to_drop, axis=1, inplace=True)
    print("Columns after dropping:", xgb_df.columns)


# Plot a correlationmatrix
variables = ['X', 'Y', 'Three_Class', 'Red', 'Green', 'Blue', 'Intensity', 'Hue',
             'Saturation', 'B_R', 'B_G', 'G_R', 'MinFG3', 'MedianFR19', 'GaussR10',
             'StDevFR19', 'StDevFI49', 'MedianB_R5', 'AverageG', 'AverageH',
             'AverageS', 'AverageB', 'AverageI', 'AverageR']

corr_matrix = xgb_df[variables].corr()
plt.figure(figsize=(16, 12))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm')
plt.title('Correlation Matrix')
plt.savefig('/workspace/data/XGBMoreArable/correlation_matrix.png')
plt.show()


# Plot violin plots for all variables comparing TreKlass classes
plt.figure(figsize=(20, 15))
for i, var in enumerate(variables):
    if var != 'Three_Class' and var != 'GeoJSON':
        plt.subplot(5, 5, i + 1)
        sns.violinplot(x='Three_Class', y=var, data=xgb_df, hue='Three_Class', palette={0: 'green', 1: 'yellow', 2: 'black'}, legend=False)
        plt.title(f'Violin Plot of {var} by Three_Class')
        plt.xlabel('')  # Remove x-axis label
plt.tight_layout()
plt.savefig('/workspace/data/XGBMoreArable/violinplots_all_variables.png')
plt.show()


# Add a new column "MapNo" to the DataFrame
label_encoder = LabelEncoder()
xgb_df['MapNo'] = label_encoder.fit_transform(xgb_df['GeoJSON'])
print(xgb_df.head())

class_counts = xgb_df['Three_Class'].value_counts()
print(class_counts)

####################################################################################################
# 2. Split data into training and test sets
y = xgb_df['Three_Class']
X = xgb_df.drop(columns=['X', 'Y', 'Three_Class', 'GeoJSON'])  # Drop 'GeoJSON' to avoid issues with DMatrix, Here also drop X and Y, and the text for the 3 classes.
stratify = xgb_df['MapNo']
print("Columns after dropping before splitting train/test:", xgb_df.columns)

gss = GroupShuffleSplit(n_splits=10, test_size=0.2, random_state=1)
train_idx, test_idx = next(gss.split(X, y, groups=stratify))

x_master_train, y_master_train = X.iloc[train_idx], y.iloc[train_idx]
x_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

# Drop 'MapNo' from the training and test sets
x_master_train = x_master_train.drop(columns=['MapNo'])
x_test = x_test.drop(columns=['MapNo'])

# Extract the 'Shapefile' values for the test set
test_filenames = map_df['GeoJSON'].iloc[test_idx]

# Write the filenames to a text file
with open('/workspace/data/XGBMoreArable/test_filenames.txt', 'w') as f:
    for filename in test_filenames:
        f.write(f'{filename}\n')

# Verify the filenames
with open('/workspace/data/XGBMoreArable/test_filenames.txt', 'r') as f:
    filenames = set(line.strip() for line in f)
filenames = sorted(filenames)
count = len(filenames)
print(f'There are {count} unique maps in the test dataset.')

# Write the sorted filenames to the text file again
with open('/workspace/data/XGBMoreArable/test_filenames.txt', 'w') as f:
    for filename in filenames:
        f.write(f'{filename}\n')

# Extract the 'GeoJSON' values for the training set
train_filenames = map_df['GeoJSON'].iloc[train_idx]

# Write the filenames to a text file
with open('/workspace/data/XGBMoreArable/train_filenames.txt', 'w') as f:
    for filename in train_filenames:
        f.write(f'{filename}\n')

# Verify the filenames
with open('/workspace/data/XGBMoreArable/train_filenames.txt', 'r') as f:
    filenames = set(line.strip() for line in f)
filenames = sorted(filenames)
count = len(filenames)
print(f'There are {count} unique maps in the training dataset.')

# Write the sorted filenames to the text file again
with open('/workspace/data/XGBMoreArable/train_filenames.txt', 'w') as f:
    for filename in filenames:
        f.write(f'{filename}\n')

from sklearn.utils.class_weight import compute_class_weight

# Calculate class weights
class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y), y=y)
class_weights_dict = {i: weight for i, weight in enumerate(class_weights)}
print("Class weights:", class_weights_dict)

####################################################################################################
# 3. Construct DMatrix
#print(xgb.__version__)
#d_master_train = xgb.DMatrix(x_master_train, label=y_master_train)
#d_test = xgb.DMatrix(x_test, label=y_test)

# Create DMatrix with class weights
d_master_train = xgb.DMatrix(x_master_train, label=y_master_train, weight=[class_weights_dict[label] for label in y_master_train])
d_test = xgb.DMatrix(x_test, label=y_test, weight=[class_weights_dict[label] for label in y_test])

####################################################################################################
# 4. Define the objective function for Bayesian optimization

def mcc_eval(preds, dtrain):
    labels = dtrain.get_label()
    preds = np.rint(preds)  # Convert probabilities to binary predictions
    mcc = matthews_corrcoef(labels, preds)
    return 'mcc', mcc

def objective(trial):
        
    # Define the parameter grid
    params = {
        'objective': 'multi:softmax', #'multi:softmax' is used for multi-classification tasks.
        'num_class': 3, # Number of classes
        'eval_metric': 'mlogloss',  # Logarithmic loss, a common metric for binary classification.
        'tree_method': 'hist',  # Disable GPU usage
        'booster': 'gbtree',
        'lambda': trial.suggest_float('lambda', 10.0, 50.0),  # L2 regularization weight
        'alpha': trial.suggest_float('alpha', 5.0, 10.0),  # L1 regularization weight
        'eta': trial.suggest_float('eta', 0.001, 0.1),  # Lowered the upper limit to 0.1 to allow the model to learn more slowly and reduce overfitting.
        'max_depth': trial.suggest_int('max_depth', 2, 6), # This parameter specifies the maximum depth of the trees. Increasing this value makes the model more complex and more likely to overfit.
        'gamma': trial.suggest_float('gamma', 1, 5), # This parameter specifies the minimum loss reduction required to make a further partition on a leaf node of the tree. It acts as a regularization parameter.
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.3, 0.7), # This parameter specifies the fraction of features to be randomly sampled for each tree. It helps in reducing overfitting.
        'subsample': trial.suggest_float('subsample', 0.5, 0.8), # This parameter specifies the fraction of samples to be randomly sampled for each tree. It helps in reducing overfitting.
        'min_child_weight': trial.suggest_int('min_child_weight', 5, 15), # This parameter specifies the minimum sum of instance weight (hessian) needed in a child. It is used to control overfitting.

    }

  
    scv = StratifiedKFold(n_splits=3, shuffle=True, random_state=1)
    score_mcc = []
    train_logloss = []
    val_logloss = []

    for fold, (train_idx, val_idx) in enumerate(scv.split(x_master_train, y_master_train)):
        x_train_fold, y_train_fold = x_master_train.iloc[train_idx, :], y_master_train.iloc[train_idx]
        x_val_fold, y_val_fold = x_master_train.iloc[val_idx, :], y_master_train.iloc[val_idx]

        dtrain_fold = xgb.DMatrix(x_train_fold, label=y_train_fold)
        dval_fold = xgb.DMatrix(x_val_fold, label=y_val_fold)

        evals_result = {}
        bst = xgb.train(params, dtrain_fold, evals=[(dval_fold, 'eval'), (dtrain_fold, 'train')],
                        evals_result=evals_result, early_stopping_rounds=10, verbose_eval=False)
        
        # Predict class labels directly
        pred_labels = bst.predict(dval_fold)

        # Print the predicted labels
        print(pred_labels)

        if len(np.unique(pred_labels)) > 1:
            mcc = matthews_corrcoef(y_val_fold, pred_labels)
        else:
            mcc = 0
        score_mcc.append(mcc)

        # Log training and validation logloss
        train_logloss.append(evals_result['train']['mlogloss'])
        val_logloss.append(evals_result['eval']['mlogloss'])

        # Print training and validation performance for each fold
        print(f"Fold {fold + 1} - Training Logloss: {evals_result['train']['mlogloss'][-1]}, Validation Logloss: {evals_result['eval']['mlogloss'][-1]}, MCC: {mcc}")

    # Plot learning curves
    plt.figure(figsize=(10, 6))
    plt.plot(np.mean(train_logloss, axis=0), label='Train Logloss')
    plt.plot(np.mean(val_logloss, axis=0), label='Validation Logloss')
    plt.xlabel('Boosting Rounds')
    plt.ylabel('MLogloss')
    plt.title('Learning Curves')
    plt.legend()
    plt.close()

    return np.mean(score_mcc)

####################################################################################################
# 5. Optimize hyperparameters using Optuna
study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=1))
study.optimize(objective, n_trials=1000, show_progress_bar=True)

# Save the results to a dataframe and a CSV file
df = study.trials_dataframe()
df.to_csv('/workspace/data/XGBMoreArable/optuna_map_results_ModelArable.csv', index=False)

# Generate and save plots of the optimization results
fig = optuna.visualization.plot_optimization_history(study)
pio.write_image(fig, '/workspace/data/XGBMoreArable/optimization_history.png')
fig = None  # Release the figure

try:
    fig = optuna.visualization.plot_param_importances(study)
    pio.write_image(fig, '/workspace/data/XGBMoreArable/param_importances.png')
    fig = None  # Release the figure
except RuntimeError as e:
    print(f"Skipping parameter importances plot due to error: {e}")

fig = optuna.visualization.plot_slice(study, params=["gamma", "eta", "colsample_bytree", "lambda"])
pio.write_image(fig, '/workspace/data/XGBMoreArable/slice_plot1.png')
fig = None  # Release the figure

fig = optuna.visualization.plot_slice(study, params=["alpha", "subsample", "max_depth", "min_child_weight"])
pio.write_image(fig, '/workspace/data/XGBMoreArable/slice_plot2.png')
fig = None  # Release the figure

plt.close('all')  # Close all Matplotlib figures

####################################################################################################
# 6. Train the final model with the best hyperparameters

# Calculate the number of unique classes in the target variable
num_classes = len(np.unique(y_master_train))
print(f"Number of classes: {num_classes}")

# Define the parameters for multi-class classification
best_params = study.best_params
best_params['num_class'] = num_classes
best_params['objective'] = 'multi:softmax'
best_params['eval_metric'] = 'mlogloss'
best_params['tree_method'] = 'hist'

# Train the final model
evals_result = {}
final_model = xgb.train(best_params, d_master_train, num_boost_round=200, evals=[(d_master_train, 'train'), (d_test, 'test')], evals_result=evals_result)

# Print the evaluation results
print("Evaluation results:", evals_result)

####################################################################################################
# 7. Evaluate model quality
# Predict on the test set
y_pred = final_model.predict(d_test)
y_pred_labels = np.rint(y_pred)  # Convert probabilities to binary predictions

# Define the label mapping
label_mapping = {0: 'Other', 1: 'Arable', 2:'Graphics'}

# Calculate the evaluation metrics
test_accuracy = accuracy_score(y_test, y_pred_labels)
print("Testing accuracy:", test_accuracy)

# Get the confusion matrix
cm = confusion_matrix(y_test, y_pred_labels)
print('Confusion matrix for testing:')
print(pd.DataFrame(cm, index=['Other', 'Arable', 'Graphics'], columns=['Other', 'Arable', 'Graphics']))

# Calculate additional evaluation metrics
print('Cohen\'s kappa score for testing:', cohen_kappa_score(y_test, y_pred_labels))
print('Model F1 score for testing:', f1_score(y_test, y_pred_labels, average='macro'))
print('Individual class F1 score for testing:', f1_score(y_test, y_pred_labels, average=None))
print('MCC score for testing:', matthews_corrcoef(y_test, y_pred_labels))

from sklearn.metrics import precision_score, recall_score

# Predict on the test set
y_pred = final_model.predict(d_test)
y_pred_labels = np.rint(y_pred)  # Convert probabilities to class labels

# Calculate precision and recall for each class
precision_per_class = precision_score(y_test, y_pred_labels, average=None)
recall_per_class = recall_score(y_test, y_pred_labels, average=None)

# Calculate macro-averaged precision and recall
precision_macro = precision_score(y_test, y_pred_labels, average='macro')
recall_macro = recall_score(y_test, y_pred_labels, average='macro')

# Calculate micro-averaged precision and recall
precision_micro = precision_score(y_test, y_pred_labels, average='micro')
recall_micro = recall_score(y_test, y_pred_labels, average='micro')

# Print the results
print("Precision per class:", precision_per_class)
print("Recall per class:", recall_per_class)
print("Macro-averaged precision:", precision_macro)
print("Macro-averaged recall:", recall_macro)
print("Micro-averaged precision:", precision_micro)
print("Micro-averaged recall:", recall_micro)

# Plot the training and test loss curves
epochs = len(evals_result['train']['mlogloss'])
x_axis = range(0, epochs)
plt.figure()
plt.plot(x_axis, evals_result['train']['mlogloss'], label='Train')
plt.plot(x_axis, evals_result['test']['mlogloss'], label='Test')
plt.legend()
plt.ylabel('M Log Loss')
plt.title('XGBoost Log Loss')
plt.savefig('/workspace/data/XGBMoreArable/xgboost_losscurve.png', dpi=300)
plt.close()


####################################################################################################
# 8. Gernerate a CSV file with the test results for viewing in GIS software
# Extract X and Y coordinates for the test set
test_coords = map_df[['X', 'Y']].iloc[test_idx]

# Create a DataFrame with the test results
test_results = pd.DataFrame({
    'X': test_coords['X'],
    'Y': test_coords['Y'],
    'True_Label': y_test,
    'Predicted_Label': y_pred_labels
})

# Save the test results to a CSV file
test_results.to_csv('/workspace/data/XGBMoreArable/GIStest_results_confusion_matrix.csv', index=False)

print("Test results with confusion matrix labels saved to '/workspace/data/XGBMoreArable/test_results_with_confusion_matrix.csv'")

####################################################################################################
import shap
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as plt_colors

# 1. Calculate SHAP values
explainer = shap.TreeExplainer(final_model)
shap_values = explainer.shap_values(x_test)

# 2. Define class names and colors
classes = ['Other', 'Arable', 'Graphics']
colors = [(39/255, 115/255, 0), (254/255, 255/255, 1/255), (1/255, 0, 40/255)]

# 3. Get class ordering from SHAP values
class_inds = np.argsort([-np.abs(shap_values[i]).mean() for i in range(len(shap_values))])

# 4. Create a custom colormap
cmap = plt_colors.ListedColormap(np.array(colors)[class_inds])

# 5. Plot the SHAP summary plot with custom color scheme
shap.summary_plot(shap_values, x_test, feature_names=x_test.columns, color=cmap, class_names=classes, plot_type="bar")

# 6. Save the plot
plt.savefig('/workspace/data/XGBMoreArable/summary_shap_plot_newsummarybar.png')
plt.close()


####################################################################################################
# 10. Save the final model

model_file_path = '/workspace/data/XGBMoreArable/xgboost_modelArable.json'
final_model.save_model(model_file_path)
print(f"Model saved to {model_file_path}")

####################################################################################################
# End time measurement
end_time = time.time()
elapsed_time = end_time - start_time
print(f'Total execution time: {elapsed_time:.2f} seconds')



