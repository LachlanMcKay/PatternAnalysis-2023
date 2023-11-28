'''contains the hyperparameters and path config'''

# Path
DATA = "/home/groups/comp3710/OASIS"

# Hyper Parameters
epochs = 300            # Number of epochs to train
learning_rate = 0.001    # Learning rate
channels = 1            # Number of channels (3 channels for the image if RGB)
batch_size = 32         # Batch Size
image_size = 64         # Spatial size of the images - OASIS 256px
log_resolution = 7      # 256*256 image size as such 2^8 = 256 # use 2^7 for single gpu (faster)
image_height = 2**log_resolution    # The height of the generated image
image_width = 2**log_resolution     # The width of the generated image
z_dim = 256             # Size of the z latent space [initialise to 256 for lower VRAM usage or faster training]
w_dim = 256             # Size of the style vector latent space [initialise to 256 for lower VRAM usage or faster training]
lambda_gp = 10          # WGAN-GP set to standard value 10

interpolation = "bilinear"          # MRI scans are curvy, using bilinear may produce more edges at high resolution
                        

save = "save"           # Rename if changing a parameter and require a new dir for saved eg
