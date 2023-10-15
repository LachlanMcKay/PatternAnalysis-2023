# dataset.py
import torch
import torchvision
import torchvision.transforms as transforms
import random

# Path for dataset
train_path = r"C:/Users/wongm/Downloads/ADNI_AD_NC_2D/AD_NC/train"
test_path = r"C:/Users/wongm/Downloads/ADNI_AD_NC_2D/AD_NC/test"

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(0.5, 0.5),
    transforms.RandomCrop(128, padding=16)

])


def pair_dataset(dataset):
    # 0 is different class pair, 1 is same class pair
    pair_dataset = []
    AD_images = []
    NC_images = []
    try:
        pair_dataset = torch.load(r"C:\Users\wongm\Desktop\COMP3710\project\paired_images.pth")
        print("paired image list loaded")
    except FileNotFoundError as e:
        print("paired image list not found")

    if len(pair_dataset) == 0:
        for (image, label) in dataset:
            if label == 0:
                AD_images.append(image)
            else:
                NC_images.append(image)

        print("label splitted")
        # AD
        for i, image1 in enumerate(AD_images):
            # AD + AD
            idx = random.randint(0, len(AD_images) - 1)
            while idx == i:
                idx = random.randint(0, len(AD_images) - 1)
            image2 = AD_images[idx]
            pair_dataset.append(((image1, image2), 1))
            # AD+NC
            idx = random.randint(0, len(NC_images) - 1)
            image2 = NC_images[idx]
            pair_dataset.append(((image1, image2), 0))

        # NC
        for i, image1 in enumerate(NC_images):
            # NC+NC
            idx = random.randint(0, len(NC_images) - 1)
            while idx == i:
                idx = random.randint(0, len(NC_images) - 1)
            image2 = NC_images[idx]
            pair_dataset.append(((image1, image2), 1))
            # NC+AD
            idx = random.randint(0, len(AD_images) - 1)
            image2 = AD_images[idx]
            pair_dataset.append(((image1, image2), 0))
        torch.save(pair_dataset, r"C:\Users\wongm\Desktop\COMP3710\project\paired_images.pth")
    return pair_dataset


def load_data(train_path, test_path):
    trainset = torchvision.datasets.ImageFolder(root=train_path, transform=transform)
    testset = torchvision.datasets.ImageFolder(root=test_path, transform=transform)

    paired_trainset = pair_dataset(trainset)
    # paired_testset=pair_dataset(testset)

    train_loader = torch.utils.data.DataLoader(paired_trainset, batch_size=64, shuffle=True)
    test_loader = torch.utils.data.DataLoader(testset, batch_size=64)
    return train_loader, test_loader


# for debug only
# train_loader, validation_loader, test_loader = load_data(train_path, test_path)
def load_data2(train_path, test_path):
    dataset = torchvision.datasets.ImageFolder(root=train_path, transform=transform)
    testset = torchvision.datasets.ImageFolder(root=test_path, transform=transform)

    val_size = int(0.2 * len(dataset))
    train_size = len(dataset) - val_size
    trainset, validation_set = torch.utils.data.random_split(dataset, [train_size, val_size])

    paired_trainset = SiameseDatset_contrastive(trainset)
    paired_validationset = SiameseDatset_contrastive(validation_set)
    #paired_testset = SiameseDatset_contrastive(testset)
    train_loader = torch.utils.data.DataLoader(paired_trainset, batch_size=64, shuffle=True)
    validation_loader = torch.utils.data.DataLoader(paired_validationset, batch_size=64, shuffle=True)
    test_loader = torch.utils.data.DataLoader(testset, batch_size=64, shuffle=True)
    return train_loader,validation_loader,test_loader
class SiameseDatset_contrastive(torch.utils.data.Dataset):
    #same person label ==1, else label ==0
    def __init__(self, dataset):
        self.dataset = dataset
        self.num_samples = len(dataset)

    def __getitem__(self, idx):
        is_same_class = random.randint(0, 1)
        idx1 = random.randint(0, self.num_samples - 1)
        idx2 = random.randint(0, self.num_samples - 1)
        idx3 = random.randint(0, self.num_samples - 1)
        image1, label1 = self.dataset[idx1]
        image2, label2 = self.dataset[idx2]
        image3, label3 = self.dataset[idx3]
        while label1 != label2:
            idx2 = random.randint(0, self.num_samples - 1)
            image2, label2 = self.dataset[idx2]
        while label1 == label3:
            idx3 = random.randint(0, self.num_samples - 1)
            image3, label3 = self.dataset[idx3]
        # if label1 == label2:
        #     label = 1
        # else:
        #     label = 0
        labela = 1
        labelb = 0

        return (image1, image2, image3), labela,labelb

    def __len__(self):
        return self.num_samples

def load_data3(train_path, test_path):
    dataset = torchvision.datasets.ImageFolder(root=train_path, transform=transform)
    testset = torchvision.datasets.ImageFolder(root=test_path, transform=transform)

    val_size = int(0.2 * len(dataset))
    train_size = len(dataset) - val_size
    trainset, validation_set = torch.utils.data.random_split(dataset, [train_size, val_size])


    paired_trainset = SiameseDatset_triplet(trainset)
    paired_validation_set = SiameseDatset_triplet(testset)

    train_loader = torch.utils.data.DataLoader(paired_trainset, batch_size=64, shuffle=True)
    validation_loader = torch.utils.data.DataLoader(paired_validation_set, batch_size=64,shuffle=True)
    test_loader = torch.utils.data.DataLoader(testset, batch_size=64, shuffle=True)
    return train_loader,validation_loader,test_loader

class SiameseDatset_triplet(torch.utils.data.Dataset):
    def __init__(self, dataset):
        self.dataset = dataset
        self.num_samples = len(dataset)

    def __getitem__(self, idx):
        is_same_class = random.randint(0, 1)
        idx1 = random.randint(0, self.num_samples - 1)
        idx2 = random.randint(0, self.num_samples - 1)
        idx3 = random.randint(0, self.num_samples - 1)
        anchor_image, label1 = self.dataset[idx1]
        #get positive image
        pos_image, label2 = self.dataset[idx2]
        while(label1 != label2 or idx1==idx2):
            idx2 = random.randint(0, self.num_samples - 1)
            pos_image, label2 = self.dataset[idx2]
        #get negative image
        neg_image, label3 = self.dataset[idx3]
        while (label1 == label3):
            idx3 = random.randint(0, self.num_samples - 1)
            neg_image, label3 = self.dataset[idx3]

        return anchor_image, pos_image, neg_image

    def __len__(self):
        return self.num_samples

class SiameseDatset_test(torch.utils.data.Dataset):
    def __init__(self, trainset,testset):
        self.trainset = trainset
        self.testset = testset
        self.num_samples_train = len(trainset)
        self.num_samples_test = len(testset)

    def __getitem__(self, idx):
        idx = random.randint(0, self.num_samples_test - 1)
        pos_idx1 = random.randint(0, self.num_samples_train - 1)
        pos_idx2 = random.randint(0, self.num_samples_train - 1)
        pos_idx3 = random.randint(0, self.num_samples_train - 1)
        pos_idx4 = random.randint(0, self.num_samples_train - 1)
        pos_idx5 = random.randint(0, self.num_samples_train - 1)
        neg_idx1 = random.randint(0, self.num_samples_train - 1)
        neg_idx2 = random.randint(0, self.num_samples_train - 1)
        neg_idx3 = random.randint(0, self.num_samples_train - 1)
        neg_idx4 = random.randint(0, self.num_samples_train - 1)
        neg_idx5 = random.randint(0, self.num_samples_train - 1)
        test_image, label1 = self.testset[idx]

        #get positive image
        pos_image1, label2 = self.trainset[pos_idx1]
        while(label1 != label2):
            pos_idx1 = random.randint(0, self.num_samples_train - 1)
            pos_image1, label2 = self.trainset[pos_idx1]

        pos_image2, label2 = self.trainset[pos_idx2]
        while (label1 != label2):
            pos_idx2 = random.randint(0, self.num_samples_train - 1)
            pos_image2, label2 = self.trainset[pos_idx2]

        pos_image3, label2 = self.trainset[pos_idx3]
        while (label1 != label2):
            pos_idx3 = random.randint(0, self.num_samples_train - 1)
            pos_image3, label2 = self.trainset[pos_idx3]

        pos_image4, label2 = self.trainset[pos_idx4]
        while (label1 != label2):
            pos_idx4 = random.randint(0, self.num_samples_train - 1)
            pos_image4, label2 = self.trainset[pos_idx4]

        pos_image5, label2 = self.trainset[pos_idx5]
        while (label1 != label2):
            pos_idx5 = random.randint(0, self.num_samples_train - 1)
            pos_image5, label2 = self.trainset[pos_idx5]

        #get negative image
        neg_image1, label3 = self.trainset[neg_idx1]
        while (label1 == label3):
            neg_idx1 = random.randint(0, self.num_samples_train - 1)
            neg_image1, label3 = self.trainset[neg_idx1]

        neg_image2, label3 = self.trainset[neg_idx2]
        while (label1 == label3):
            neg_idx2 = random.randint(0, self.num_samples_train - 1)
            neg_image2, label3 = self.trainset[neg_idx2]

        neg_image3, label3 = self.trainset[neg_idx3]
        while (label1 == label3):
            neg_idx3 = random.randint(0, self.num_samples_train - 1)
            neg_image3, label3 = self.trainset[neg_idx3]

        neg_image4, label3 = self.trainset[neg_idx4]
        while (label1 == label3):
            neg_idx4 = random.randint(0, self.num_samples_train - 1)
            neg_image4, label3 = self.trainset[neg_idx4]

        neg_image5, label3 = self.trainset[neg_idx5]
        while (label1 == label3):
            neg_idx5 = random.randint(0, self.num_samples_train - 1)
            neg_image5, label3 = self.trainset[neg_idx5]

        return test_image, pos_image1,pos_image2,pos_image3,pos_image4,pos_image5, neg_image1,neg_image2,neg_image3,neg_image4, neg_image5, label1

    def __len__(self):
        return self.num_samples_test