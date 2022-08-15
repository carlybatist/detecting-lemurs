from opensoundscape.torch.models.cnn import CNN
from opensoundscape.audio import Audio
from opensoundscape.spectrogram import Spectrogram
from opensoundscape.annotations import BoxedAnnotations
from opensoundscape.annotations import categorical_to_one_hot
from opensoundscape.preprocess.utils import show_tensor_grid, show_tensor
from opensoundscape.torch.datasets import AudioFileDataset
import torch
import pandas as pd
from pathlib import Path
import numpy as np
import pandas as pd
import random
from glob import glob
from matplotlib import pyplot as plt
from sklearn.model_selection import train_test_split
plt.rcParams['figure.figsize']=[15,5]
import warnings

# warnings.filterwarnings("ignore")

# set manual seeds
#probably don’t want to do this when actually training model, but useful for debugging
torch.manual_seed(0)
random.seed(0)
np.random.seed(0)

# ----------------------------


#For this self-contained tutorial, we can use relative paths 
# (starting with a dot and referring to files in the same folder), 
# but you may want to use absolute paths for your training.

# paired = pd.read_csv("paired.csv")
# with open('paired.csv', 'r') as f:
#     paired2 = f.readlines()
#     print(paired2[:10])
# #print(paired.head())
# specky_table = pd.read_csv("processed_files2.csv")
# print(specky_table.head())
# audio = paired['audio_file']
# print(audio.head())

# # create a dictionary that maps filenames to full paths:
# audio_filename_to_full_path = {}
# for i, row in enumerate(paired2):
#     #print(row)
#     if i==0:
#         continue  
#     filename = row.split(',')[0]
#     audio_file_path = row.split(',')[1]
#     # audio_file_path = audio_file_path.replace('/azure_blob','')
#     audio_filename_to_full_path[filename]= audio_file_path
# #print(audio_filename_to_full_path)

# audiofile = []

# for row in specky_table['file']:
#     #print(row)
#     row = row.split('.')[0]
#     #print(audio_filename_to_full_path[row])
#     audiofile.append(audio_filename_to_full_path[row])
# #specky_table.file = paired.audio_file
# #print(audiofile)

# specky_table['audio_file_path'] = audiofile

# # specky_table_df = pd.DataFrame(specky_table)
# print(specky_table.head)
# specky_table.to_csv('specky_table.csv')

# print(len(audio))
# print(len(specky_table_df))

# audio_array = np.array(audio)
# raven_array = np.array(specky_table['file'])
# print(len(audio_array))
# print(len(raven_array))

# audio_files_trimmed = []

# for txt in audio_array:
#     x = txt.split('/')[-1]
#     # x = x.split('.')[0]
#     audio_files_trimmed.append(x)
#     #print(x)

# audio_array=np.array(audio_files_trimmed)
# print(audio_array[:10])
# print(raven_array[:10])
# missing = np.setdiff1d(raven_array, audio_array) #specky_table bigger
# print(missing)
# missing_df = pd.DataFrame(missing)
# missing_df.to_csv('missing2.csv')

# to create one-hot labels (already done from annotations script)
#one_hot_labels, classes = categorical_to_one_hot(specky_table[['detection']].values)
#print(one_hot_labels)
#print(classes)
#labels = pd.DataFrame(index=specky_table['audio_file_path'],data=one_hot_labels,columns=classes)
#assert 0

# ----------------------------


classes=[0,1]
input_file = pd.read_csv("all_one_hot_encoded_labels2.csv")
labels = pd.DataFrame(input_file)
print(labels.head())

#print(labels.dtypes)
#print(labels.index)
#print(input_file)
# print(len(input_file))
# print(type(input_file))

# load one-hot labels dataframe
labels = pd.read_csv('all_one_hot_encoded_labels2.csv').set_index('file')
# prepend the folder location to the file paths
#labels.index = pd.Series(labels.index).apply(lambda f: './'+f)
#create class list
classes = labels.columns
#inspect
labels.head()
#print(type(labels))


# split training & test data
train_df, test_df = train_test_split(labels,test_size=0.2,random_state=2)
train_df, validation_df = train_test_split(train_df, test_size = 0.2, random_state=2) 

#print(type(train_df))
print(train_df.head())
print(validation_df.head())
print(test_df.head())
print(len(train_df))
print(len(validation_df))
print(len(test_df))
#print(train_df.columns)

#assert 0

# Create model object
classes = train_df.columns
model = CNN('resnet50',classes=classes,sample_duration=10,single_target=True)

# check what the samples generated by model look like

#pick some random samples from the training set
sample_of_4 = train_df.sample(n=4)
print(sample_of_4)
#generate a dataset with the samples we wish to generate and the model's preprocessor
inspection_dataset = AudioFileDataset(sample_of_4, model.preprocessor)
print(inspection_dataset)
#generate the samples using the dataset
samples = [sample['X'] for sample in inspection_dataset]
labels = [sample['y'] for sample in inspection_dataset]
#display the samples
fig = show_tensor_grid(samples,4,labels=labels)
plt.savefig('fig1.png')

#turn augmentation off for the dataset
inspection_dataset.bypass_augmentations = True
#generate the samples without augmentation
samples = [sample['X'] for sample in inspection_dataset]
labels = [sample['y'] for sample in inspection_dataset]
#display the samples
fig = show_tensor_grid(samples,4,labels=labels)
plt.savefig('fig2.png')

#assert 0

# train model

model.logging_level = 1 #3 request lots of logged content, 0 requests none
model.log_file = './binary_train/training_log.txt' #specify a file to log output to
Path(model.log_file).parent.mkdir(parents=True,exist_ok=True) #make the folder ./binary_train

print(model.device)

# train_df.bypass_augmentations = True
# validation_df.bypass_augmentations = True

print('model.train')
model.train(
    train_df=train_df,
    validation_df=validation_df,
    save_path='./binary_train/', #where to save the trained model
    epochs=5,
    batch_size=100,
    save_interval=1, #save model every 5 epochs (the best model is always saved in addition)
    num_workers=4, #specify 4 if you have 4 CPU processes, eg; 0 means only the root process
)
print('done training model')

#plot the loss from each epoch 
# (should decline as the model learns, but may have ups and downs along the way)
fig = plt.scatter(model.loss_hist.keys(),model.loss_hist.values())
plt.xlabel('epoch')
plt.ylabel('loss')
plt.figsave('loss.png')

assert 0

model.logging_level = 3 #request lots of logged content
model.log_file = './binary_train/training_log.txt' #specify a file to log output to
Path(model.log_file).parent.mkdir(parents=True,exist_ok=True) #make the folder ./binary_train

#printing and logging outputs
model.verbose = 0 #don't print anything to the screen during training
# model.train(
#     train_df=train_df,
#     validation_df=validation_df,
#     save_path='./binary_train/', #where to save the trained model
#     epochs=1,
#     batch_size=8,
#     save_interval=5, #save model every 5 epochs (the best model is always saved in addition)
#     num_workers=0, #specify 4 if you have 4 CPU processes, eg; 0 means only the root process
# )

