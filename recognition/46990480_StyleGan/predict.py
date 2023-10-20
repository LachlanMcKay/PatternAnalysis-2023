"""
Example usage of the trained model
"""
import argparse
import torch
import torchvision.utils as vutils
import numpy as np
import matplotlib.pyplot as plt
from modules import Generator, MappingNetwork
from config import learning_rate, channels, batch_size, image_size, log_resolution, image_height
from config import image_width, z_dim, w_dim, lambda_gp

log_resolution = 8
z_dim = 512
w_dim = 512

parser = argparse.ArgumentParser()
parser.add_argument('-model_name', default='./Models/', help='Name of model under inference')
parser.add_argument('-load_path_mapping', default='./Models/MAPPING_NETWORK_OASIS_With_Preprocessing_A100_512_lat.pth', help='Checkpoint to load path from')
parser.add_argument('-load_path', default='./Models/GENERATOR_OASIS_With_Preprocessing_A100_512_lat.pth', help='Checkpoint to load path from')
parser.add_argument('-num_output', default=64, help='Number of generated outputs')
parser.add_argument('-plt_title', default="Generated Images", help='Title for the plot')
args = parser.parse_args()

# Set the device to run on GPU if available
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if not torch.cuda.is_available():
    print("Warning CUDA not Found. Using CPU")

# Create the mapping network
mapping_network = MappingNetwork(z_dim, w_dim).to(device)
mapping_network.load_state_dict(torch.load(args.load_path_mapping, map_location=device))

# TODO: refactor these into a different modules so it can be used in both the predict & train files
def get_w(batch_size, log_resolution):
    '''
    Creates a style latent vector w, from a random noise z latent vector.
    '''
    # Random noise z latent vector
    z = torch.randn(batch_size, w_dim).to(device)

    # Forward pass z through the mapping network to generate w latent vector
    w = mapping_network(z)
    return w[None, :, :].expand(log_resolution, -1, -1)

def get_noise(batch_size):
    '''
    Generates a random noise vector for a batch of images
    '''
    noise = []
    resolution = 4

    for i in range(log_resolution):
        if i == 0:
            n1 = None
        else:
            n1 = torch.randn(batch_size, 1, resolution, resolution, device=device)
        n2 = torch.randn(batch_size, 1, resolution, resolution, device=device)

        noise.append((n1, n2))

        resolution *= 2

    return noise

# Create the generator network.
generator = Generator(log_resolution, w_dim).to(device)

# Load the trained generator weights.
generator.load_state_dict(torch.load(args.load_path, map_location=device))
print(generator)

print(f'Number of images to output: {args.num_output}')

# Turn off gradient calculation to speed up the process.
with torch.no_grad():
    # Get generated images from the noise vector using the trained generator.
    # Get latent vector style vecotr (w).
    w = get_w(args.num_output, log_resolution)

    # Get some random noise
    noise = get_noise(args.num_output)
    generated_img = generator(w, noise).detach().cpu()

# Display the generated image.
plt.axis("off")
plt.title(args.plt_title)
plt.imshow(np.transpose(vutils.make_grid(generated_img, padding=2, normalize=True), (1, 2, 0)))
plt.show()
