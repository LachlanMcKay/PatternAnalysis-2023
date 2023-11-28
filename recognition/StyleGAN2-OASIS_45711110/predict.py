#example usage of the trained model

import torch
import os

import matplotlib.pyplot as plt
from torchvision.utils import save_image
from utils import get_w, get_noise
from config import save

'''
Plot a 10x5 graph of the Generator and Discriminator loss during training over iteration
'''
def plot_loss(G_Loss, D_Loss):
    plt.figure(figsize=(10,5))
    plt.title("Generator Loss During Training")
    plt.plot(G_Loss, label="G", color="blue")
    plt.xlabel("Iterations")
    plt.ylabel("Loss")
    plt.legend()
    plt.savefig('gen_loss.png')

    plt.figure(figsize=(10,5))
    plt.title("Discriminator Loss During Training")
    plt.plot(D_Loss, label="D", color="red")
    plt.xlabel("Iterations")
    plt.ylabel("Loss")
    plt.legend()
    plt.savefig('disc_loss.png')

'''
Generate Imagees using the generator.
n=10 Images are saved for the epoch interval as defined in parameter

Epoch intervals is sent as parameter while the number of imgs and path is hard coded below.
'''
def generate_examples(gen, mapping_network, epoch, device):
    
    n = 10
    for i in range(n):
        with torch.no_grad():
            w     = get_w(1, mapping_network, device)
            noise = get_noise(1, device)
            img = gen(w, noise)
            if not os.path.exists(f'saved_examples_{save}'):
                os.makedirs(f'saved_examples_{save}')
            save_image(img*0.5+0.5, f"saved_examples_{save}/epoch{epoch}_img_{i}.png")