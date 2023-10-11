from imports import *

class ImageDataset(Dataset):
    def __init__(self, directory, image_transforms=None):
        self.directory = directory
        self.image_files = sorted(os.listdir(directory))
        self.image_transforms = image_transforms

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, index):
        image_path = os.path.join(self.directory, self.image_files[index])
        image = Image.open(image_path).convert("L")
        
        if self.image_transforms:
            image = self.image_transforms(image)
        
        return image

def process_dataset(batch_size=8, is_validation=False,
                    train_dir="/home/groups/comp3710/OASIS/keras_png_slices_train", 
                    test_dir="/home/groups/comp3710/OASIS/keras_png_slices_test", 
                    val_dir="/home/groups/comp3710/OASIS/keras_png_slices_validate"):
    
    # Given images are preprocessed with the size of 256 x 256
    image_transforms = Compose([
        Grayscale(),
        ToTensor(), 
        Lambda(lambda t: (t * 2) - 1),
    ])
    
    if is_validation:
        val_data = ImageDataset(directory=val_dir, image_transforms=image_transforms)
        return DataLoader(val_data, batch_size=batch_size, shuffle=True)
    
    else:
        train_data = ImageDataset(directory=train_dir, image_transforms=image_transforms)
        test_data = ImageDataset(directory=test_dir, image_transforms=image_transforms)

        # Combine all three datasets into single dataset for training
        combined_data = ConcatDataset([train_data, test_data])

        return DataLoader(combined_data, batch_size=batch_size, shuffle=True)

####################################################################### 
# dataset tester

# if __name__ == '__main__':
#     image_dir = os.path.expanduser('/home/groups/comp3710/OASIS/keras_png_slices_train')
#     save_dir = os.path.expanduser('~/demo_eiji/sd/images')  # New directory for saved images

#     # Check if Python can see the path
#     if os.path.exists(image_dir):
#         print(f"Directory exists: {image_dir}")
#     else:
#         print(f"Directory does not exist: {image_dir}")
#         print(f"Current working directory: {os.getcwd()}")

#     # Initialize DataLoader
#     data_loader = process_dataset(batch_size=4)

#     # Fetch and visualize a batch of images
#     batch = next(iter(data_loader))
#     for i, image in enumerate(batch):
#         plt.subplot(1, 4, i+1)
#         plt.imshow(image.squeeze(0))
#         plt.axis('off')
        
#     # Save the image
#     save_path = os.path.join(save_dir, f'image_{i}.png')
#     plt.savefig(save_path)