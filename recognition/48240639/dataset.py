"""
Created on Wednesday October 18 
ADNI Dataset and Data Loaders

This code defines a custom dataset class, ADNIDataset, for loading and processing
ADNI dataset images for use in Siamese Network training and testing. It also provides
functions to get train and test datasets from a specified data path.

@author: Aniket Gupta 
@ID: s4824063

"""


import os
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


class SiameseADNIDataset(Dataset):
    def __init__(self, data_path):
        super(SiameseADNIDataset, self).__init__()

        self.transform = transforms.ToTensor()

        # Load AD and NC images
        self.ad_path = os.path.join(data_path, 'AD')
        self.nc_path = os.path.join(data_path, 'NC')

        # Load images
        self.ad_images = [self.transform(Image.open(os.path.join(self.ad_path, img))) for img in
                          os.listdir(self.ad_path)]
        self.nc_images = [self.transform(Image.open(os.path.join(self.nc_path, img))) for img in
                          os.listdir(self.nc_path)]

        # Stack images into tensors
        self.ad_images = torch.stack(self.ad_images)
        self.nc_images = torch.stack(self.nc_images)

    def __len__(self):
        # Return the length of the smaller dataset
        return min(len(self.ad_images), len(self.nc_images))

    def __getitem__(self, index):
        if index % 2 == 0:
            # Positive example (both images are AD)
            img1 = self.ad_images[index % len(self.ad_images)] # Get the image at the current index
            img2 = self.ad_images[(index + 1) % len(self.ad_images)] # Get the next image
            label = torch.tensor(1, dtype=torch.float) # Set the label to 1
        else:
            # Negative example (one image is AD, the other is NC)
            img1 = self.ad_images[index % len(self.ad_images)] # Get the image of ad at the current index
            img2 = self.nc_images[index % len(self.nc_images)] # Get the image of nc at the current index
            label = torch.tensor(0, dtype=torch.float) # Set the label to 0

        return img1, img2, label


def get_training(data_path):
    # Get the training dataset
    train_dataset = SiameseADNIDataset(os.path.join(data_path, 'train'))
    return train_dataset


def get_testing(data_path):
    # Get the test dataset
    test_dataset = SiameseADNIDataset(os.path.join(data_path, 'test'))
    return test_dataset