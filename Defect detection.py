import warnings
warnings.filterwarnings("ignore")
import numpy
import pandas
import matplotlib
import seaborn
import plotly
import tensorflow
import keras
!pip install chart_studio
!pip install ann_visualizer
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_row', None)
import matplotlib.pyplot as plt
plt.rcdefaults()
from pylab import rcParams
import seaborn as sns
%matplotlib inline
import datetime
#################
#######Ploltly
import plotly
import chart_studio.plotly as py
import plotly.graph_objs as go
import plotly.offline as pyo
import plotly.figure_factory as ff
from   plotly.tools import FigureFactory as FF, make_subplots
import plotly.graph_objs as go
from   plotly.graph_objs import *
from   plotly import tools
from   plotly.offline import download_plotlyjs, init_notebook_mode, iplot
import cufflinks as cf
init_notebook_mode(connected=True)
cf.go_offline()
pyo.offline.init_notebook_mode()
####### Deep learning libraries
import tensorflow as tf
import keras
from keras.models import Model, load_model
from keras.layers import Input, Dense
from keras.callbacks import ModelCheckpoint, TensorBoard
from keras import regularizers
from ann_visualizer.visualize import ann_viz
from sklearn.preprocessing import  StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

from sklearn.metrics import (confusion_matrix, classification_report, accuracy_score, roc_auc_score, auc,
                             precision_score, recall_score, roc_curve, precision_recall_curve,
                             precision_recall_fscore_support, f1_score,
                             precision_recall_fscore_support)
#
from IPython.display import display, Math, Latex
df = pd.read_csv('datanew.csv',index_col=0)
df.index
df.reset_index(inplace=True, drop= True)
df.index
df.head()
df.Label.value_counts()
df.columns
numerical_cols = ['1ofa small damper opening', '2 corner OFA wind volume',
       'ADS input switch', 'AGC load instruction',
       'Total primary wind on side A',
       'Total flow of A side ammonia injection valve',
       'Heartbeat signal on side A', 'A-side smoke volume',
       'A side valve total opening', 'A side valve instruction',
       'A coal mill output', 'A Coal mill hot air door opening',
       'B coal mill output', 'B Coal mill hot air door opening',
       'C coal mill output', 'C Coal mill hot air door opening',
       'D coal mill output', 'D Coal mill hot air door opening',
       'E coal mill output', 'E Coal mill hot air door opening',
       'E coal mill output.1', 'F Coal mill hot air door opening',
       'Upper level (#1-F level) secondary small damper opening', 'Total coal',
       'Total air volume', 'O2 concentration on the a side of economizer',
       'O2 concentration on b side of economizer',
       'After selection, the total amount of secondary air on the A side',
       'Boiler load', 'NOX concentration at side A input']
       df.Label.unique()

labels = df['Label'].astype(int)
labels[labels != 0] = 1
len(labels[labels !=0])
len(labels[labels !=1])

RANDOM_SEED = 101

X_train, X_test = train_test_split(df, test_size=0.2, random_state = RANDOM_SEED)

X_train = X_train[X_train['Label'] == 0]
X_train = X_train.drop(['Label'], axis=1)
y_test  = X_test['Label']
X_test  = X_test.drop(['Label'], axis=1)
X_train = X_train.values
X_test  = X_test.values
print('Training data size   :', X_train.shape)
print('Validation data size :', X_test.shape)

scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)
# Number of Neurons in each Layer [30,6,3,2,3,6,30]
input_dim = X_train.shape[1]
encoding_dim = 6

input_layer = Input(shape=(input_dim, ))
encoder = Dense(encoding_dim, activation="tanh",activity_regularizer=regularizers.l1(10e-5))(input_layer)
encoder = Dense(int(encoding_dim / 2), activation="tanh")(encoder)
encoder = Dense(int(2), activation="tanh")(encoder)
decoder = Dense(int(encoding_dim/ 2), activation='tanh')(encoder)
decoder = Dense(int(encoding_dim), activation='tanh')(decoder)
decoder = Dense(input_dim, activation='tanh')(decoder)
autoencoder = Model(inputs=input_layer, outputs=decoder)
autoencoder.summary()

def train_validation_loss(df_history):
    
    trace = []
    
    for label, loss in zip(['Train', 'Validation'], ['loss', 'val_loss']):
        trace0 = {'type' : 'scatter', 
                  'x'    : df_history.index.tolist(),
                  'y'    : df_history[loss].tolist(),
                  'name' : label,
                  'mode' : 'lines'
                  }
        trace.append(trace0)
    data = Data(trace)
    
    layout = {'title' : 'Model train-vs-validation loss', 'titlefont':{'size' : 30},
              'xaxis' : {'title':  '<b> Epochs', 'titlefont':{ 'size' : 25}},
              'yaxis' : {'title':  '<b> Loss', 'titlefont':{ 'size' : 25}},
              }
    fig = Figure(data = data, layout = layout)
    
    return pyo.iplot(fig)

    nb_epoch = 50
batch_size = 50
autoencoder.compile(optimizer='adam', loss='mse' )

t_ini = datetime.datetime.now()
history = autoencoder.fit(X_train_scaled, X_train_scaled,
                        epochs=nb_epoch,
                        batch_size=batch_size,
                        shuffle=True,
                        validation_split=0.1,
                        verbose=0
                        )

t_fin = datetime.datetime.now()
print('Time to run the model: {} Sec.'.format((t_fin - t_ini).total_seconds()))



df_history = pd.DataFrame(history.history)
# validation_data=(X_test_scaled, X_test_scaled)
train_validation_loss(df_history)

plt.plot(history.history['loss'], label='train')
plt.plot(history.history['val_loss'], label='test')
plt.legend()
plt.show()

predictions = autoencoder.predict(X_test_scaled)

mse = np.mean(np.power(X_test_scaled - predictions, 2), axis=1)
df_error = pd.DataFrame({'reconstruction_error': mse, 'Label': y_test}, index=y_test.index)
df_error.describe()


# change X_tes_scaled to pandas dataframe
data_n = pd.DataFrame(X_test_scaled, index= y_test.index, columns=numerical_cols)

def compute_error_per_dim(point):
    
    initial_pt = np.array(data_n.loc[point,:]).reshape(1,30)
    reconstrcuted_pt = autoencoder.predict(initial_pt)
    
    return abs(np.array(initial_pt  - reconstrcuted_pt)[0])

outliers = df_error.index[df_error.reconstruction_error > 0.05].tolist()
outliers
RE_per_dim = {}
for ind in outliers:
    RE_per_dim[ind] = compute_error_per_dim(ind)
    
RE_per_dim = pd.DataFrame(RE_per_dim, index= numerical_cols).T
RE_per_dim.head()


def bar_plot(df, data_pt):
    x = df.columns.tolist()
    y = df.loc[data_pt]
    
    trace = {'type': 'bar',
             'x'   : x,
             'y'   : y}
    data = Data([trace])
    layout = {'title' : "<b>Reconstruction error in each dimension for data poitn {}".format(data_pt),
              'titlefont':{'size' : 20},
              'xaxis' : {'title': '<b>Features',
                         'titlefont':{'size' : 20},
                         'tickangle': -45, 'tickfont': {'size':15} },
              'yaxis' : {'title': '<b>Reconstruction Error',
                         'titlefont':{'size' : 20},
                         'tickfont': {'size':15}},
              'margin' : {'l':100, 'r' : 1, 'b': 200, 't': 100, 'pad' : 1},
              'height' : 1000, 'width' : 1000,
             }
    
    fig = Figure(data = data, layout = layout)
    
    return pyo.iplot(fig)

    for pt in outliers[:5]:
    bar_plot(RE_per_dim, pt)

df_error.loc[18694]

autoencoder.predict(np.array(data_n.loc[18694]).reshape(1,30))