# -*- coding: utf-8 -*-
"""Membuat Model Machine Learning dengan Data Time Series.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dJa3iFosUEr0cgEIZyM6WHqG24C_PFEQ
"""

import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from keras.layers import Dense, LSTM

df = pd.read_csv('/content/drive/MyDrive/Dataset/jena_climate_2009_2016.csv')
df

df.info()

df['Date Time']=pd.to_datetime(df['Date Time'])
df['Date Time'].head


df['T (degC)'].fillna(df['T (degC)'].mean(), inplace=True) # we will fill the null row

df = df[['Date Time','T (degC)' ]]
df.head

df.columns

df.columns = ['Date Time', 'T_degC']

df.info()

jena=df[['Date Time','T_degC']].copy()
jena['Date'] = jena['Date Time'].dt.date

jena_f=jena.drop('Date Time',axis=1)
jena_f.set_index('Date', inplace= True)

jena_f.head

# plot data

plt.figure(figsize=(25,10))
plt.plot(jena_f)
plt.title('Jena Climate')
plt.xlabel('Date')
plt.ylabel('temperature')
plt.show()

# get values of data 

date = df['Date Time'].values.astype(float)
tmp = df['T_degC'].values.astype(float)

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

"""Validation set sebesar 20% dari total dataset."""

x_train, x_test, y_train, y_test = train_test_split(tmp, date, test_size = 0.2, random_state = 0 , shuffle=False)
print(len(x_train), len(x_test))

data_x_train = windowed_dataset(x_train, window_size=60, batch_size=100, shuffle_buffer=5000)
data_x_test = windowed_dataset(x_test, window_size=60, batch_size=100, shuffle_buffer=5000)

model = tf.keras.models.Sequential([
  tf.keras.layers.Conv1D(filters=32, kernel_size=5,
                      strides=1, padding="causal",
                      activation="relu",
                      input_shape=[None, 1]),
  tf.keras.layers.LSTM(64, return_sequences=True),
  tf.keras.layers.LSTM(64, return_sequences=True),
  tf.keras.layers.Dense(30, activation="relu"),
  tf.keras.layers.Dense(10, activation="relu"),
  tf.keras.layers.Dense(1),
  tf.keras.layers.Lambda(lambda x: x * 400)
])

lr_schedule = tf.keras.callbacks.LearningRateScheduler(
    lambda epoch: 1e-8 * 10**(epoch / 20))
optimizer = tf.keras.optimizers.SGD(lr=1e-8, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])

model.summary()

max = df['T_degC'].max()
print('Maximal value : ' )
print(max)

min = df['T_degC'].min()
print('Minimal Value : ')
print(min)

x = (37.28 - (-23.01)) * (1 / 100)
print(x)

# callback

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae')< x):
      self.model.stop_training = True
      print("\nMAE of the model less than 10% of data scale")
callbacks = myCallback()

tf.keras.backend.set_floatx('float64')
number_epochs = 10

history = model.fit(data_x_train,
                    epochs=number_epochs,
                    validation_data=data_x_test,
                    batch_size=64,
                    shuffle=False,
                    callbacks=[callbacks])

# MAE Plot

plt.plot(history.history['mae'])
plt.plot(history.history['val_mae'])
plt.title('MAE')
plt.ylabel('mae')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

# loss plot

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

"""Rokhmat Febrianto

Bergabung sejak 16 Mar 2021

Kabupaten Sidoarjo, Jawa Timur 
"""