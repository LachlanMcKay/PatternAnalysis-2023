import os
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Dataset
from PIL import Image

root_path = 'data/keras_png_slices_data'

# Define data transformations
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.RandomHorizontalFlip(),                      
    transforms.ToTensor(), # Data is scaled into [0, 1]
    transforms.Lambda(lambda t: (t * 2) - 1) # Scale between [-1, 1]
])

# Define batch size of data
batch_size = 32

# Custom OASIS brain dataset class referenced from ChatGPT3.5: how to create custom dataset class for OASIS
class OASISDataset(Dataset):
    def __init__(self, root, transform=None):
        self.root_dir = root
        self.transform = transform

        # List all image files in root directory
        self.image_files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))]
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, index):
        image_path = os.path.join(self.root_dir, self.image_files[index])
        
        # Load and preprocess the image
        image = self.load_image(image_path)
        return image
    
    def load_image(self, path):
        image = Image.open(path)
        if self.transform:
            image = self.transform(image)
        return image
    
    
# Specifying paths to train, test and validate directories
train_data = OASISDataset(root=f'{root_path}/keras_png_slices_train', transform=transform)
test_data = OASISDataset(root=f'{root_path}/keras_png_slices_test', transform=transform)
validate_data = OASISDataset(root=f'{root_path}/keras_png_slices_validate', transform=transform)

# Create data loaders for each set
train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True) # Image shape [32, 1, 224, 224]
test_loader = DataLoader(test_data, batch_size=batch_size)
validate_loader = DataLoader(validate_data, batch_size=batch_size)