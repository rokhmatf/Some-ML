# -*- coding: utf-8 -*-
"""Dicoding Image Classification Model Deployment.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FRXIkgMAUkZtgSGfGWF0ESAjqOG1KQQT
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import PIL
import shutil
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.models import Sequential

from PIL import Image

!pip install -q kaggle

from google.colab import files
files.upload()

!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
!ls ~/.kaggle

!kaggle datasets download -d madisona/translated-animals10

# unzip
!mkdir animals
!unzip -qq translated-animals10.zip -d animals
!ls animals

animals = os.path.join('/content/animals/animals10/raw-img/')

print(os.listdir(animals))

ignore = ['squirrel', 'cat', 'sheep', 'cow', 'elephant']

for x in ignore:
  path = os.path.join(animals, x)
  shutil.rmtree(path)

list_animals = os.listdir(animals)
print(list_animals)

tot = 0

for x in list_animals:
  dir = os.path.join(animals, x)
  y = len(os.listdir(dir))
  print(x+':', y)
  tot = tot + y
  
  img_name = os.listdir(dir)

  for z in range(4):
    img_path = os.path.join(dir, img_name[z])
    img = Image.open(img_path)
    print('-',img.size)
  print('---------------')

print('\nTotal Image :', tot)

"""**Dataset dibagi menjadi 80% train set dan 20% test set.**"""

train_datagen = ImageDataGenerator(
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    rescale=1/255,
    zoom_range=0.3,
    horizontal_flip=True,
    fill_mode='nearest',
    validation_split=0.2    # Dataset dibagi menjadi 80% train set dan 20% test set.   
)

batch_size = 256
img_height = 180
img_width = 180

train_ds = train_datagen.flow_from_directory(
  animals,
  subset="training",
  class_mode='categorical',
  target_size=(img_height, img_width),
  batch_size=batch_size)

val_ds = train_datagen.flow_from_directory(
  animals,
  subset="validation",
  class_mode='categorical',
  target_size=(img_height, img_width),
  batch_size=batch_size)

normalization_layer = layers.experimental.preprocessing.Rescaling(1./255)

number_classes = 5
tf.device('/device:GPU:0')

model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(64, (3,3), activation='relu', input_shape=(img_height, img_width, 3)),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(128, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(128, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(256, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dropout(0.5), 
    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.Dense(number_classes, activation='softmax')
])

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics = ['accuracy'])

model.summary()

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('accuracy')>0.92 and logs.get('val_accuracy')>0.92):
      print("\nAccuracy above 92%, finish training!")
      self.model.stop_training = True

callbacks = myCallback()

number_epochs = 50

history = model.fit(train_ds, 
                    epochs = number_epochs, 
                    steps_per_epoch = train_ds.samples // batch_size,
                    validation_data = val_ds, 
                    validation_steps = val_ds.samples // batch_size,
                    verbose = 1,
                    callbacks = [callbacks])

plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with tf.io.gfile.GFile('model.tflite', 'wb') as f:
  f.write(tflite_model)

!ls -la | grep 'model'