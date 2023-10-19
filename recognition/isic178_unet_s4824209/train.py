'''
Author: s4824209

Program for training and testing the model

'''

from dataset import customDataset, data_sorter
import torch 
import torch.nn as nn
from torchvision import transforms
from torch.utils.data import DataLoader
from modules import IuNet
from utils import Diceloss
from utils import Train_Transform, Test_Transform
from torchvision.utils import save_image
import sys
from sklearn.model_selection import train_test_split

#Computation will run on GPU if possible 
device = torch.device('cuda'if torch.cuda.is_available() else 'cpu')
if not torch.cuda.is_available():
    print('CUDA not found, using CPU')


#PARAMETERS

Num_epochs = 10
batch_size = 2 #will only be applied to the trainset
LR = 5e-4         



#LOAD DATA

#fetching root path of images and ground truth
img_root = '/home/groups/comp3710/ISIC2018/ISIC2018_Task1-2_Training_Input_x2'
gt_root = '/home/groups/comp3710/ISIC2018/ISIC2018_Task1_Training_GroundTruth_x2'

#Creating sorted lists of image and ground truth path for test and train (80%/20% split)
img_train_path,gt_train_path, img_test_path, gt_test_path = data_sorter(img_root='data', gt_root='GT_data', mode='Train')

#Defining transforms for trainset and testset
train_transform = transforms.Compose([Train_Transform()])
test_transform = transforms.Compose([Test_Transform()])

#Loading the trainset into dataloader with defined transforms
train_set = customDataset(images=img_train_path, GT=gt_train_path, transform=train_transform)
train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)

#Loading the test set into dataloader
#Test loader has batch_size=1 to be able to check dice score of each separate image 
test_set = customDataset(images=img_test_path, GT=gt_test_path, transform=test_transform)
test_loader = DataLoader(test_set, batch_size=1)


#MODEL
model = IuNet()
model = model.to(device)


#create a Dice loss function, Adam optimizer, and a step learning rate scheduler
criterion = Diceloss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR) 
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.985) 

#compative variables used for saving the model with best performance during testing
best_min_dcs = 0
best_avg_dcs = 0


        

def train(model, train_loader, criterion):
    '''
    Function for training the model
    args:
        model (class torch.nn.Module): Model to train
        train_loader (class Dataloader): The dataloader with the training set
        criterion: Loss function
    '''

    running_loss = 0.0
    model.train()
    print('>>>training')
    for i, element in enumerate(train_loader):
        
        #separating train loader into image and ground truth
        image, ground_t = element
        image, ground_t = image.to(device), ground_t.to(device)
        output = model(image)

        #calculation the loss
        loss = criterion(output, ground_t)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        #determening total loss for each epoch   
        running_loss += loss.item()
        
    #prints the avg loss of each epoch
    print(f'[{epoch + 1}] avg_loss: {running_loss/(i+1) :.3f}')
            
    #learning rate scheduler step every epoch
    scheduler.step()


def eval(model, test_loader):
    '''
    Function for testing the module during training
    args:
        model (class Module): Trained model to test
        test_loader (class Dataloader): Dataloader with test set

    returns:
        avg_DCS (Float): Average Dice score of the entire test 
        min_dcs (Float): Worst dice score on a single segmentation
    '''

    print('>>> testing')
    model.eval()
    
    #Variables used to determine average and minimum DCS during testing
    avg_DCS = 0
    min_DCS = 1
    with torch.no_grad():
        #Iterate the test data
        for i, elements in enumerate(test_loader):
            data, ground_t = elements
            
            #send to GPU
            data = data.to(device)
            ground_t = ground_t.to(device)
            
            output = model(data)
            
            #The output is rounded so each pixel value <0.5 counts as class 0 and each >0.5 counts as class 1 
            output = torch.round(output)

            #Compute the Dice coefficiet from the dice loss (criterion given by 1-dice)
            DCS = 1-criterion(output, ground_t)
            
            #Determine average DCS and lowest DCS scores
            avg_DCS += DCS.item()
            if DCS.item() < min_DCS:
                min_DCS = DCS.item()
        
        #prints average and minimum DCS 
        print(f'[Test, epoch:{epoch+1}] avg DCS:{avg_DCS/(i+1) :.3f}, min:{round(min_DCS,3)}')

        return avg_DCS, min_DCS  


#TRAINING / TESTING

for epoch in range(Num_epochs):
    #train model
    train(model, train_loader, criterion)
    
    #evaluate model
    avg_dcs, min_dcs = eval(model, test_loader)

    #save model with best minimum DCS score:
    if min_dcs > best_min_dcs:
        torch.save(model.state_dict(), 'trained_model_bestmin.pt')
        best_min_dcs = min_dcs
    
    #save model with best average DCS score:
    if avg_dcs > best_avg_dcs:
        torch.save(model.state_dict(), 'trained_model_bestavg.pt')
        best_avg_dcs = avg_dcs




