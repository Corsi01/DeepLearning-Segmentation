# -*- coding: utf-8 -*-
"""3 - 3DUNet_DataAugmentation OutsideTraining.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1I-ZkVPQLe4h2qle2w_Eg2EDy6Lt8umWZ

# IMPORT LIBRARIES AND DATA
"""

!pip install tensorflow==2.16.0rc0
!pip install volumentations-3D
!PYTHONHASHSEED=0

# Import other modules
from matplotlib import pyplot as plt
import zipfile
from shutil import copyfile
from time import time
import numpy as np
import pandas as pd
import random as python_random
import os
import shutil
import glob
from volumentations import *

# Import TensorFlow/Keras
import tensorflow as tf
import keras
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, Conv2DTranspose, MaxPooling2D, Dropout, Activation, concatenate
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv3D, Conv3DTranspose, MaxPooling3D, concatenate, Dropout, Activation, BatchNormalization, GroupNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, CSVLogger
import tensorflow.keras.backend as K


from google.colab import drive
drive.mount('/content/gdrive')

# Zip file's path on Gdrive
drive_zip_path = '/content/gdrive/MyDrive/DL_Project/data/128.zip'
local_extract_path = '/content/Training_Data'
os.makedirs(local_extract_path, exist_ok=True
            )
# Unzip on local directory
with zipfile.ZipFile(drive_zip_path, 'r') as zip_ref:
    zip_ref.extractall(local_extract_path)

print("Decompressione completata.")

train_img_dir = "/content/Training_Data/X_train/"
train_mask_dir = "/content/Training_Data/Y_train/"
train_img_list = sorted(os.listdir(train_img_dir))
train_mask_list = sorted(os.listdir(train_mask_dir))

val_img_dir = "/content/Training_Data/X_val/"
val_mask_dir = "/content/Training_Data/Y_val/"
val_img_list = sorted(os.listdir(val_img_dir))
val_mask_list = sorted(os.listdir(val_mask_dir))

"""# DATA AUGMENTATION"""

def get_augmentation(volume_size):
    return Compose([
        Rotate((-30, 30), (-30, 30), (-30, 30), p = 1),
        RandomCropFromBorders(crop_value = 0.1, p = 1),
        ElasticTransform((0, 0.25), interpolation = 2, p = 1),
        Resize(volume_size, interpolation = 1, resize_type = 0, always_apply = True, p = 1.0),
        Flip(0, p = 0.5),
        Flip(1, p = 0.5),
        Flip(2, p = 0.5),
        RandomRotate90(p = 1),
    ], p = 1.0)

augmentation = get_augmentation((128,128,128))

def apply_augmentation(image, mask, augmentation):
  augmented = augmentation(image = image, mask = mask)
  augmented_image = augmented['image']
  augmented_mask = augmented['mask']

  return augmented_image, augmented_mask

output_dir_x = 'Training_Data/augmented_x/'
output_dir_y = 'Training_Data/augmented_y/'

os.makedirs(output_dir_x, exist_ok = True)
os.makedirs(output_dir_y, exist_ok = True)

for idx, name in enumerate(train_img_list):

  x_path = os.path.join(train_img_dir, train_img_list[idx])
  y_path = os.path.join(train_mask_dir, train_mask_list[idx])

  x_data = np.load(x_path)
  y_data = np.load(y_path)

  base_name = os.path.basename(name)
  number = base_name.split('_')[1].split('.')[0]

  augmented_x1, augmented_y1 = apply_augmentation(x_data, y_data, augmentation)
  #augmented_x2, augmented_y2 = apply_augmentation(x_data, y_data, augmentation)

  augmented_x_path1 = os.path.join(output_dir_x, f'augmented(1)_image_{number}.npy')
  augmented_y_path1 = os.path.join(output_dir_y, f'augmented(1)_mask_{number}.npy')

  #augmented_x_path2 = os.path.join(output_dir_x, f'augmented(2)_image_{number}.npy')
  #augmented_y_path2 = os.path.join(output_dir_y, f'augmented(2)_mask_{number}.npy')

  np.save(augmented_x_path1, augmented_x1)
  np.save(augmented_y_path1, augmented_y1)

  print(number)

  #np.save(augmented_x_path2, augmented_x2)
 # np.save(augmented_y_path2, augmented_y2)

"""# TEST"""

x1 = sorted(os.listdir(train_img_dir))
y1 = sorted(os.listdir(train_mask_dir))

x1 = ["/content/Training_Data/X_train/" + file for file in x1]
y1 = ["/content/Training_Data/Y_train/" + file for file in y1]

x1[:10]

y1[:10]

# Get sorted list of files in the directories
x2 = sorted(os.listdir("/content/Training_Data/augmented_x"))
y2 = sorted(os.listdir("/content/Training_Data/augmented_y"))

# Add the directory path to each filename
X2 = ["/content/Training_Data/augmented_x/" + file for file in x2]
Y2 = ["/content/Training_Data/augmented_y/" + file for file in y2]

# Display the first 10 entries to check
print(X2[:10])
print(Y2[:10])

X_files = x1 + X2
Y_files = y1 + Y2

combined = list(zip(X_files, Y_files))
np.random.shuffle(combined)
X_shuffled, Y_shuffled = zip(*combined)

X_shuffled[:10]

Y_shuffled[:10]

"""# DATA GENERATOR"""

##### TRAIN DATA
import numpy as np

def load_img_from_paths(paths):
    images = []
    for path in paths:
        image = np.load(path)
        images.append(image)
    images = np.array(images)
    return images

def image_loader_train(x_list, y_list, batch_size=4):
    L = len(x_list)
    while True:
        batch_start = 0
        batch_end = batch_size
        while batch_start < L:
            limit = min(L, batch_end)
            img_batch = load_img_from_paths(x_list[batch_start:limit])
            mask_batch = load_img_from_paths(y_list[batch_start:limit])
            yield (img_batch, mask_batch)
            batch_start += batch_size
            batch_end += batch_size

############ VALIDATION DATA
def load_img(img_dir, img_list):
    images=[]
    for i, image_name in enumerate(img_list):
        if (image_name.split('.')[1] == 'npy'):

            image = np.load(img_dir + image_name)

            images.append(image)

    images = np.array(images)

    return images


def image_loader_validation(img_dir, img_list, mask_dir, mask_list, batch_size):

    L = len(img_list)

    while True:

        batch_start = 0
        batch_end = batch_size

        while batch_start < L:

            limit = min(L, batch_end)

            img = load_img(img_dir, img_list[batch_start:limit])
            mask = load_img(mask_dir, mask_list[batch_start:limit])

            yield(img, mask)

        batch_start += batch_size
        batch_end += batch_size

"""#  FIXED PARAMETERS"""

#Compute weight of classes

columns = ['0','1', '2', '3']
df = pd.DataFrame(columns=columns)
train_mask_list = sorted(glob.glob('/content/Training_Data/Y_train/*.npy'))
for img in range(len(train_mask_list)):

  temp_image=np.load(train_mask_list[img])
  temp_image = np.argmax(temp_image, axis=3)
  val, counts = np.unique(temp_image, return_counts=True)

  conts_dict = {str(i): 0 for i in range(4)}
  for v, c in zip(val, counts):
    conts_dict[str(v)] = c

  row_df = pd.DataFrame([conts_dict])

  # add new row
  df = pd.concat([df, row_df], ignore_index=True)

label_0 = df['0'].sum()
label_1 = df['1'].sum()
label_2 = df['2'].sum()
label_3 = df['3'].sum()
total_labels = label_0 + label_1 + label_2 + label_3
n_classes = 4

wt0 = round((total_labels/(n_classes*label_0)), 2) #round to 2 decimals
wt1 = round((total_labels/(n_classes*label_1)), 2)
wt2 = round((total_labels/(n_classes*label_2)), 2)
wt3 = round((total_labels/(n_classes*label_3)), 2)

print(wt0, wt1, wt2, wt3)

CFC_loss = keras.losses.CategoricalFocalCrossentropy(alpha = [wt0, wt1, wt2, wt3])

IoU_0 = keras.metrics.OneHotIoU(num_classes = 4, target_class_ids = [0])
IoU_1 = keras.metrics.OneHotIoU(num_classes = 4, target_class_ids = [1])
IoU_2 = keras.metrics.OneHotIoU(num_classes = 4, target_class_ids = [2])
IoU_3 = keras.metrics.OneHotIoU(num_classes = 4, target_class_ids = [3])

Mean_IoU = keras.metrics.OneHotMeanIoU(num_classes = 4)

metrics = ["accuracy",  Mean_IoU, IoU_0, IoU_1, IoU_2, IoU_3]

#Define the optimizer
batch_size = 4

lr_schedule = keras.optimizers.schedules.ExponentialDecay(
    initial_learning_rate = 5e-4,
    decay_steps  = (len(train_img_list) // 4),
    decay_rate = 0.985)

optim = keras.optimizers.Adam(0.001)

"""# ARCHITECTURE"""

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv3D, Conv3DTranspose, MaxPooling3D, concatenate, Dropout, Activation, GroupNormalization

def conv_block(input, n_filters):

    x = Conv3D(n_filters, 3, padding='same')(input)
    x = GroupNormalization(groups = 32)(x)
    x = Activation('relu')(x)

    x = Conv3D(n_filters, 3, padding='same')(x)
    x = GroupNormalization(groups = 32)(x)
    x = Activation('relu')(x)

    return x

def encoder_block(input, num_filters):

    x = conv_block(input, num_filters)
    p = MaxPooling3D((2, 2, 2))(x)

    return x, p

def decoder_block(input, skip_features, num_filters):

    x = Conv3DTranspose(num_filters, (2, 2, 2), strides=(2, 2, 2), padding = 'same')(input)
    x = concatenate([x, skip_features])
    x = conv_block(x, num_filters)

    return x

def build_unet(input_shape, n_classes):
    inputs = Input(input_shape)

    s1, p1 = encoder_block(inputs, 32)
    s2, p2 = encoder_block(p1, 64)
    s3, p3 = encoder_block(p2, 128)
    s4, p4 = encoder_block(p3, 256)

    b1 = conv_block(p4, 512)

    d1 = decoder_block(b1, s4, 256)
    d2 = decoder_block(d1, s3, 128)
    d3 = decoder_block(d2, s2, 64)
    d4 = decoder_block(d3, s1, 32)

    outputs = Conv3D(n_classes, 1, padding='same', activation='softmax')(d4)

    model = Model(inputs, outputs, name='3D_U-Net')
    return model

input_shape = (128, 128, 128, 4)
n_classes = 4

model = build_unet(input_shape, n_classes)
model.compile(optimizer = optim, loss = CFC_loss, metrics = metrics)
model.summary()

"""# FIT"""

from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Define path to save model
checkpoint_path = "content/best_model3D.h5.keras"

# Callback to save best model based on validation loss
checkpoint_callback = ModelCheckpoint(
    filepath=checkpoint_path,
    save_best_only=True,
    monitor='val_loss',
    mode='min',
    verbose=1
)

# Define callbackf for early stopping
early_stopping_callback = EarlyStopping(
    monitor = 'val_loss',    # MonitorTrack validation loss
    patience = 10,           # Max number of epoch without improvement
    restore_best_weights = True
)

csv = CSVLogger("/content/gdrive/MyDrive/DL_Project/history_3dDataAugm.csv")

batch_size = 4

steps_per_epoch = len(train_img_list)*2//batch_size
val_steps_per_epoch = len(val_img_list)//batch_size

train_img_datagen = image_loader_train(X_shuffled, Y_shuffled, batch_size)
val_img_datagen = image_loader_validation(val_img_dir, val_img_list, val_mask_dir, val_mask_list, batch_size)

train_img_dir = "/content/Training_Data/X_train/"
train_mask_dir = "/content/Training_Data/Y_train/"
train_img_list = sorted(os.listdir(train_img_dir))
train_mask_list = sorted(os.listdir(train_mask_dir))

val_img_dir = "/content/Training_Data/X_val/"
val_mask_dir = "/content/Training_Data/Y_val/"
val_img_list = sorted(os.listdir(val_img_dir))
val_mask_list = sorted(os.listdir(val_mask_dir))

history = model.fit(
    train_img_datagen,
    steps_per_epoch=steps_per_epoch,
    epochs=30,
    validation_data=val_img_datagen,
    validation_steps=val_steps_per_epoch,
    callbacks=[checkpoint_callback, early_stopping_callback, csv]
)

loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'y', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

plt.plot(epochs, acc, 'y', label='Training Accuracy')
plt.plot(epochs, val_acc, 'r', label='Validation Accuracy')
plt.title('Training and validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Dice')
plt.legend()
plt.show()



a1 = history.history['one_hot_io_u']
a2 = history.history['val_one_hot_io_u']
b1 = history.history['one_hot_io_u_1']
b2 = history.history['val_one_hot_io_u_1']
c1 = history.history['one_hot_io_u_2']
c2 = history.history['val_one_hot_io_u_2']
d1 = history.history['one_hot_io_u_3']
d2 = history.history['val_one_hot_io_u_3']
e1 = history.history['one_hot_mean_io_u']
e2 = history.history['val_one_hot_mean_io_u']

colors = ['b', 'g', 'c', 'm', 'y', 'k']
line_styles = ['-', '--', '-.', ':']

plt.figure(figsize=(12, 8))

plt.plot(epochs, a1, color=colors[0], linestyle=line_styles[0], label='Training IoU (0)')
plt.plot(epochs, a2, color=colors[0], linestyle=line_styles[1], label='Validation IoU (0)')
plt.plot(epochs, b1, color=colors[1], linestyle=line_styles[0], label='Training IoU (1)')
plt.plot(epochs, b2, color=colors[1], linestyle=line_styles[1], label='Validation IoU (1)')
plt.plot(epochs, c1, color=colors[2], linestyle=line_styles[0], label='Training IoU (2)')
plt.plot(epochs, c2, color=colors[2], linestyle=line_styles[1], label='Validation IoU (2)')
plt.plot(epochs, d1, color=colors[3], linestyle=line_styles[0], label='Training IoU (3)')
plt.plot(epochs, d2, color=colors[3], linestyle=line_styles[1], label='Validation IoU (3)')
plt.plot(epochs, e1, color=colors[4], linestyle=line_styles[0], label='Training Mean IoU')
plt.plot(epochs, e2, color=colors[4], linestyle=line_styles[1], label='Validation Mean IoU')

plt.title('Training and validation IoU')
plt.xlabel('Epochs')
plt.ylabel('IoU')
plt.legend()
plt.show()

# Salva il modello completo
model.save('/content/gdrive/MyDrive/DL_Project/complete_model3D.h5')