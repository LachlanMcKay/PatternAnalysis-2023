import torch
import matplotlib.pyplot as plt
import os

# Import the necessary modules
import modules as m

# Set a random seed for reproducibility
torch.manual_seed(42)

# Determine the device to use (mps if available, else CPU)
D = 'mps' if torch.backends.mps.is_available() else 'cpu'
X_DIM = 512
Y_DIM = 512
Z_CHANNELS = 512
IMG_CHANNELS = 3

# Initialize the generator
generator = m.Generator(X_DIM, Y_DIM, Z_CHANNELS, IMG_CHANNELS).to(D)

# Load the pre-trained generator model weights
generator.load_state_dict(torch.load('Generator.pth'))

# Set the generator to evaluation mode
generator.eval()

# Generate a specified number of sample images
num_samples = 9
z_samples = torch.randn(num_samples, X_DIM).to(D)
with torch.no_grad():
    generated_pictures = generator(z_samples, alpha=1.0, steps=5)

# Transform and prepare the generated images for visualization
generated_pictures = (generated_pictures + 1) / 2
generated_pictures = generated_pictures.cpu().numpy().transpose(0, 2, 3, 1)

# Create a 3x3 grid to display the generated images
_, ax = plt.subplots(3, 3, figsize=(8, 8))
plt.suptitle('Generated pictures')

# Display the generated images in the grid
for i in range(3):
    for j in range(3):
        idx = i * 3 + j
        if idx < len(generated_pictures):
            ax[i][j].imshow(generated_pictures[idx])

# Ensure the output_images directory exists
if not os.path.exists("output_images"):
    os.makedirs("output_images")

# Save the generated image grid to a file
path_to_save = os.path.join("output_images", "generated_pictures.png")
plt.savefig(path_to_save)

# Close the plot
plt.close()
