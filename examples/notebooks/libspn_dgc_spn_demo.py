# -*- coding: utf-8 -*-
"""LibSPN DGC-SPN demo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/10AXL7oo8LBCTnw7NrJ_zTph9X7J8XRdj
"""
from libspn_keras import layers, initializers
from tensorflow import keras
import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)

sum_kwargs = dict(
    accumulator_initializer=keras.initializers.TruncatedNormal(
        stddev=0.5, mean=1.0),
    logspace_accumulators=True
)

spn = keras.Sequential([
  layers.NormalLeaf(
      input_shape=(28, 28, 1),
      num_components=16, 
      location_trainable=True,
      location_initializer=keras.initializers.TruncatedNormal(
          stddev=1.0, mean=0.0)
  ),
  layers.ConvProduct(
      depthwise=True, 
      strides=[2, 2], 
      dilations=[1, 1], 
      kernel_size=[2, 2]
  ),
  layers.SpatialLocalSum(num_sums=16, **sum_kwargs),
  layers.ConvProduct(
      depthwise=True, 
      strides=[2, 2], 
      dilations=[1, 1], 
      kernel_size=[2, 2]
  ),
  layers.SpatialLocalSum(num_sums=32, **sum_kwargs),
  layers.ConvProduct(
      depthwise=True, 
      strides=[1, 1], 
      dilations=[1, 1], 
      kernel_size=[2, 2],
      padding='full'
  ),
  layers.SpatialLocalSum(num_sums=32, **sum_kwargs),
  layers.ConvProduct(
      depthwise=True, 
      strides=[1, 1], 
      dilations=[2, 2], 
      kernel_size=[2, 2],
      padding='full'
  ),
  layers.SpatialLocalSum(num_sums=64, **sum_kwargs),
  layers.ConvProduct(
      depthwise=True, 
      strides=[1, 1], 
      dilations=[4, 4], 
      kernel_size=[2, 2],
      padding='full'
  ),
  layers.SpatialLocalSum(num_sums=64, **sum_kwargs),
  layers.ConvProduct(
      depthwise=True, 
      strides=[1, 1], 
      dilations=[8, 8], 
      kernel_size=[2, 2],
      padding='final'
  ),
  layers.ReshapeSpatialToDense(),
  layers.DenseSum(num_sums=10, **sum_kwargs),
  layers.RootSum(
      return_weighted_child_logits=True, 
      logspace_accumulators=True, 
      accumulator_initializer=keras.initializers.TruncatedNormal(
          stddev=0.0, mean=1.0)
  )
])

spn.summary()

import tensorflow_datasets as tfds
import tensorflow as tf

def _normalize_img(img, label):
  img = tf.cast(img, tf.float32)
  img_mean = tf.reduce_mean(img)
  img_stddev = tf.math.reduce_std(img)
  img = (img - img_mean) / (img_stddev + 1e-4)
  return (img, label)

def round_div_up(x, y):
  return (x + y - 1) // y


batch_size = 16

mnist_train = tfds.load(name="mnist", split="train", as_supervised=True)
mnist_test = tfds.load(name="mnist", split="test", as_supervised=True)

mnist_train = mnist_train.shuffle(10000).repeat().batch(batch_size).map(_normalize_img)

mnist_train = mnist_train.prefetch(tf.data.experimental.AUTOTUNE)

mnist_test = mnist_test.batch(100).map(_normalize_img)

optimizer = keras.optimizers.Adam(learning_rate=7e-3)
metrics = [keras.metrics.SparseCategoricalAccuracy()]
loss = keras.losses.SparseCategoricalCrossentropy(from_logits=True)

spn.compile(loss=loss, metrics=metrics, optimizer=optimizer)

spn.fit(mnist_train, steps_per_epoch=round_div_up(50000, batch_size), epochs=10)

spn.evaluate(mnist_test, steps=round_div_up(10000, 100))