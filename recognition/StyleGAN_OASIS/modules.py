# -*- coding: utf-8 -*-
"""
File: modules.py

Purpose: Contains the necessary components for the Style GAN model. This includes
        - Alpha Scheduler
        - Generator model including the mapping network and synthesis blocks
        - Discriminator model including convolution blocks

@author: Peter Beardsley
"""

import numpy as np
import torch
from torch import nn, optim
from torchvision import datasets, transforms
import torch.nn.functional as F

"""
Define an alpha scheduler:
    fade_epochs     np.array of size max_depth-1 (or more) for number of epochs per
                    depth level in which to fade with the previous depth level. Index
                    0 is depth 1.
    hold_epochs     np.array of the size max_depth-1 (or more) for number of epochs per
                    depth level in which alpha will be held a 1 before progresing
                    to the next depth. Index 0 is depth 1.
    max_depth       Int describing how deep to control the fading
    batch_sizes     List of batch sizes per depth level
    data_size       Int of number of images in an epoch
    
Notes: This is a scheduler for controlling the fading factor alpha that will
       blend a new progressive GAN layer with the previous layer. Depth will
       always start at 1, since style GAN doesn't start training at the depth=0
       layer (4x4), but rather depth=1 (8x8).
       self.steps counts the number of iterations within an epoch over the
       required number of epochs.
"""
class AlphaScheduler():
    def __init__(self, fade_epochs, hold_epochs, max_depth, batch_sizes, data_size):
        # Convert epochs into total number of iterations, AKA steps.
        self.fade_steps = np.array([np.ceil(fade_epochs[i]*data_size/batch_sizes[i]) for i in range(len(batch_sizes))])
        self.hold_steps = np.array([np.ceil(hold_epochs[i]*data_size/batch_sizes[i]) for i in range(len(batch_sizes))])
        self.max_depth = max_depth
        # Alpha is just the inverse of the number of steps
        self.alpha_steps = 1/self.fade_steps
        self.depth = 1
        self.steps = 0
        self.alpha = 0
        self.is_fade = False
        
    """
    Signal the scheduler that an epoch iteration has finished. This will generally
    increment self.alpha, finish fading and hold, or switch to the next depth.
    """
    def step(self):

        self.steps += 1
        # Within a fade, so increment alpha
        if self.steps < self.fade_steps[self.depth-1]:
            self.alpha += self.alpha_steps[self.depth-1]
            self.is_fade = True
        # Fade has finished but need to keep holding at alpha = 1
        elif self.steps < self.fade_steps[self.depth-1] + self.hold_steps[self.depth-1]:
            self.alpha = 1
            self.is_fade = False
        # Fade and hold are finished, time to move to next depth
        elif self.depth < self.max_depth:
            self.depth += 1
            self.alpha = 0
            self.steps = 0
            self.is_fade = True
        else:
            self.depth = self.max_depth
            self.alpha = 1
    """
    Return the current alpha value
    """
    def alpha(self):
        return self.alpha
    
    """
    Return the current depth level
    """
    def depth(self):
        return self.depth
    
    """
    Return if fading is currently scheduled (that is, 0<alpha<1)
    """
    def is_fade(self):
        return self.is_fade




"""
Define a PyTorch module that can normalise using RMS

Notes: A very small epsilon=1e-8 is added prior to taking the square root
       to avoid a potential sqrt(0) error.
"""
class RMS(nn.Module):
    def __init__(self):
        super(RMS, self).__init__()
        
    def forward(self, x):
        return x / (((x**2).mean(dim=1, keepdim=True) + 1e-8).sqrt())
    
  
"""
Define a PyTorch module that can equalise a Linear/Conv module using
the He constant
     bias_fill  Set the module bias, typical values are 0 or 1
     f          Factor to scale the He constant, typical values are 1 or 0.01
"""
class HeLayer(nn.Module):
    
    def __init__(self, module, bias_fill, f=1.0):
        super(HeLayer, self).__init__()
        self.module = module
        self.module.bias.data.fill_(bias_fill)
        self.module.weight.data.normal_(0,1)
        self.module.weight.data /= f
        HeConst = (2.0/np.prod(module.weight.size()[1:]))**0.5
        self.weight = HeConst*f
           
    def forward(self, x):
        x = self.module(x)
        x *= self.weight
        return x

"""
Extend the HeLayer to define an equalised Conv2d module
"""
class Conv2dHe(HeLayer):
    def __init__(self, in_ch, out_ch, kernel_size=3, stride=1, padding=1):
        HeLayer.__init__(self, nn.Conv2d(in_ch, out_ch, kernel_size=kernel_size, stride=stride, padding=padding, bias=True), bias_fill=0)

"""
Extend the HeLayer to define an equalised Linear module
"""
class LinearHe(HeLayer):
    def __init__(self, in_ch, out_ch, f=1.0):
        HeLayer.__init__(self, nn.Linear(in_ch, out_ch, bias=True), bias_fill=0, f=0.01)

"""
Define a PyTorch module that concatenates the mean standard deviation to the
layer output. This is a technique that aims to improve control, diversity, and
regularisation.
"""
class ConcatStdDev(nn.Module):
    def __init__(self):
        super(ConcatStdDev, self).__init__()
    
    def forward(self, x):
        size = list(x.size())
        size[1] = 1
        
        std = torch.std(x, dim=0)
        mean = torch.mean(std)
        return torch.cat((x, mean.repeat(size)), dim=1)
    
    
"""
Define the StyleGAN Mapping Network as a PyTorch module. This aims to learn a
manifold of latent z, expressed as w.
     in_ch      The dimension of z
     out_ch     The dimension of w
     depth      The mapping network depth, usually set to size 8
"""
class MappingNetwork(nn.Module):
    def __init__(self, in_ch, out_ch, depth=8):
        super(MappingNetwork, self).__init__()
        self.mappingNetwork = nn.ModuleList()
        
        ch = in_ch
        for i in range(depth):
            self.mappingNetwork.append(LinearHe(ch, out_ch, f=1)) # Try f=0.01
            ch = out_ch
        
        self.relu = torch.nn.LeakyReLU(0.2)
    
    """
    Feed forward:
       x    The normalised output of latent z
    """ 
    def forward(self, x):
        for fc in self.mappingNetwork:
            x = self.relu(fc(x))
            
        return x
"""
Adaptive Instance Normalisation PyTorch module
     channels   Number of channels of the synthesis layer
     w_size     The size of the Mapping Network output, w
     
Notes: scale and bias are derived from w by using an equaliser linear layer. This
       is typically done by outputing twice the channels but I've opted for 
       two seperate linear modules instead for simplicity
"""
class AdaIN(nn.Module):
    def __init__(self, channels, w_size):
        super(AdaIN, self).__init__()
        self.instance_norm = nn.InstanceNorm2d(channels)
        self.style_scale = LinearHe(w_size, channels)
        self.style_bias = LinearHe(w_size, channels)

    """
    Feed forward:
        x   The signal to feed into AdaIN
        w   The manifold output
    """
    def forward(self, x, w):
        x = self.instance_norm(x)
        style_scale = self.style_scale(w).unsqueeze(2).unsqueeze(3)
        style_bias = self.style_bias(w).unsqueeze(2).unsqueeze(3)
        return style_scale * x + style_bias
    
"""
The B module from the style-based generator architecture that connects the noise
to the AdaIN.
     channels   Number of channels of the synthesis layer
    
Notes: weights are initialised to zero.
"""
class B(nn.Module):
    def __init__(self, channels):
        super(B, self).__init__()
        self.weight = nn.Parameter(torch.zeros(1, channels, 1, 1))

    """
    Feed forward:
        noise   Generate from torch.randn((Batches, 1, img_size, img_size), device=device)
    """
    def forward(self, noise):
        return self.weight * noise
    
"""
The first synthesis block of the StyleGAN generator architecture. This is similar
to the following blocks except for the constant 4x4 input.
     ch_in  The number of channels for the constant, typically 512
     ch_out The number of channels to output from the block
     w_size     The size of the Mapping Network output, w
"""
class SynthesisInitialBlock(nn.Module):
    def __init__(self, ch_in, ch_out, w_size):
        super(SynthesisInitialBlock, self).__init__()
        self.activate = nn.LeakyReLU(0.2, inplace=True)
        self.const = nn.Parameter(torch.ones((1, ch_in, 4, 4)))
        self.B1 = B(ch_out)
        self.adaIN1 = AdaIN(ch_out, w_size)
        self.conv2 = Conv2dHe(ch_out, ch_out)
        self.B2 = B(ch_out)
        self.adaIN2 = AdaIN(ch_out, w_size)
 
    """
    Feed Forward:
        a   The manifold output w
    
    Note: x is generated from a constant 4x4
    """
    def forward(self, a):
        x = self.const
        
        b1 = self.B1(torch.randn((x.shape[0], 1, x.shape[2], x.shape[3]), device=a.device))
        b2 = self.B2(torch.randn((x.shape[0], 1, x.shape[2], x.shape[3]), device=a.device))
        
        x = x + b1
        x = self.adaIN1(x, a)
        x = x + b2
        x = self.adaIN2(x, a)
        x = self.activate(x)
        return x

"""
The scaling synthesis blocks of the StyleGAN generator architecture. 
     ch_in  The number of channels for the previous block
     ch_out The number of channels to output from the block
     w_size     The size of the Mapping Network output, w
"""
class SynthesisBlock(nn.Module):
    def __init__(self, ch_in, ch_out, w_size):
        super(SynthesisBlock, self).__init__()
        self.activate = nn.LeakyReLU(0.2, inplace=True)
        self.conv1 = Conv2dHe(ch_in, ch_out)
        self.B1 = B(ch_out)
        self.adaIN1 = AdaIN(ch_out, w_size)
        self.conv2 = Conv2dHe(ch_out, ch_out)
        self.B2 = B(ch_out)
        self.adaIN2 = AdaIN(ch_out, w_size)

    """
    Feed Forward:
        x   The output of the previous layer
        a   The manifold output w
    """
    def forward(self, x, a):
        b1 = self.B1(torch.randn((x.shape[0], 1, x.shape[2], x.shape[3]), device=x.device))
        b2 = self.B2(torch.randn((x.shape[0], 1, x.shape[2], x.shape[3]), device=x.device))
        
        x = self.conv1(x)
        x = self.activate(x + b1)
        x = self.adaIN1(x, a)
        x = self.activate(x + b2)
        x = self.adaIN2(x, a)

        return x
    
"""
A PyTorch module implementation of the style-based generator architecture. The
main components are:
    RMS(z) -> Mapping Network -> w
    Synthesis Network for layer depth d:
        [0]: Const -> + B(Noise) -> + AdaIN(w) -> Conv + B(Noise) -> + AdaIN(w)
        [d]: Upsample -> Conv + B(Noise) -> + AdaIN(w) -> Conv + B(Noise) -> + AdaIN(w)
    RGB Output [d]: Conv (channels to RGB channels)

Parameters:
    z_size      Size of latent z
    w_size      Size of manifold w
    channels    np.array[d] for channels at layer d
    rgb_ch      Number of RGB channels (3 for this project, 1 for grayscale)
    alphaSched  The AlphaScheduler object for managing the progresive GAN fading
"""
class Generator(nn.Module):
    def __init__(self, z_size, w_size, channels, rgb_ch, alphaSched):
        super(Generator, self).__init__()
        self.alphaSched = alphaSched
        self.normalise = RMS()
        self.mappingNetwork = MappingNetwork(z_size, w_size)
        self.synthesisNetwork = nn.ModuleList()
        self.rgbOutput = nn.ModuleList()
        
        self.synthesisNetwork.append(SynthesisInitialBlock(channels[0], channels[0], w_size))
        self.rgbOutput.append(Conv2dHe(channels[0], rgb_ch, kernel_size=1, stride=1, padding=0))
        
        for d in range(len(channels) - 1):
            ch_in = int(channels[d])
            ch_out = int(channels[d + 1])
            self.synthesisNetwork.append(SynthesisBlock(ch_in, ch_out, w_size))
            self.rgbOutput.append(Conv2dHe(ch_out, rgb_ch, kernel_size=1, stride=1, padding=0))
            
    def forward(self, z):
        # Normalise latent z, then pass to the mapping network
        w = self.mappingNetwork(self.normalise(z))

        # Scale depth based on the current AlphaScheduler depth
        for depth in range(self.alphaSched.depth+1):
            # First depth must be the SynthesisInitialBlock
            if isinstance(self.synthesisNetwork[depth], SynthesisInitialBlock):
                out = self.synthesisNetwork[0](w)
            # Subsequent blocks of SynthesisBlocks
            else:
                upsample = F.interpolate(out, scale_factor=2, mode="bilinear")
                out = self.synthesisNetwork[depth](upsample, w)
        
        # Transform from the current depth to RGB
        rgb_out = self.rgbOutput[self.alphaSched.depth](out)        
        
        # If fading, combine with the upscaled RGB output of the previous depth
        if self.alphaSched.is_fade:
            rgb_out_previous = self.rgbOutput[self.alphaSched.depth - 1](upsample)
            rgb_out = self.alphaSched.alpha * rgb_out + (1 - self.alphaSched.alpha) * rgb_out_previous
        
        # Map to a pixel value
        return torch.tanh(rgb_out)