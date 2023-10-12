import torch
import torch.nn as nn
import torch.nn.functional as F

class Context(nn.Module):
    def __init__(self, size):
        super(Context, self).__init__()
        self.pdrop = 0.3
        self.neagative_slope = 10**(-2)

        self.instNorm = nn.InstanceNorm2d(size)
        self.conv = nn.Conv2d(
            size, size, kernel_size=3, padding=(1,1)
        )
        self.dropOut = nn.Dropout2d(self.pdrop)

    def forward(self, input):
        out = input
        out = F.leaky_relu(self.instNorm(self.conv(out)), self.neagative_slope)
        out = self.dropOut(out)
        out = F.leaky_relu(self.instNorm(self.conv(out)), self.neagative_slope)
        return torch.add(out, input)

class Upsampling(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Upsampling, self).__init__()

        self.upsample = nn.Upsample(scale_factor=2)
        self.instNorm = nn.InstanceNorm2d(out_channels)
        self.conv = nn.Conv2d(
           in_channels, out_channels, kernel_size=3 , padding=(1,1)
        ) 

    def forward(self, out):
        print(f"before upsamp: \n{out.shape}")
        out = self.upsample(out)
        print(f"after upsamp: \n{out.shape}")
        out = F.leaky_relu(self.instNorm(self.conv(out)), 10**(-2))
        return out
        
class Localization(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Localization, self).__init__()
        self.conv1 = nn.Conv2d(
            in_channels, in_channels, kernel_size=3, padding=(1,1)
        )
        self.instNorm1 = nn.InstanceNorm2d(in_channels)
        self.conv2 = nn.Conv2d(
            in_channels, out_channels, kernel_size=1
        )
        self.instNorm2 = nn.InstanceNorm2d(out_channels)
        
    def forward(self, out):
        out = F.leaky_relu(self.instNorm1(self.conv1(out)), 10**(-2))
        out = F.leaky_relu(self.instNorm2(self.conv2(out)), 10**(-2)) 
        return out
        
class ImpUNet(nn.Module):
    def __init__(self, in_channel, negative_slope=10**(-2)):
        super(ImpUNet, self).__init__()
        self.negative_slope = negative_slope
        # arcitecture components
        self.conv1 = nn.Conv2d(
            in_channel, 16, kernel_size=3, padding=(1,1)
        )
        self.instNorm1 = nn.InstanceNorm2d(16)
        self.context1 = Context(16)

        self.conv2 = nn.Conv2d(
            16, 32, kernel_size=3, stride=2, padding=(1,1)
        )
        self.instNorm2 = nn.InstanceNorm2d(32)
        self.context2 = Context(32)

        self.conv3 = nn.Conv2d(
            32, 64, kernel_size=3, stride=2, padding=(1,1)
        )
        self.instNorm3 = nn.InstanceNorm2d(64)
        self.context3 = Context(64)
        
        self.conv4 = nn.Conv2d(
            64, 128, kernel_size=3, stride=2, padding=(1,1)
        )
        self.instNorm4 = nn.InstanceNorm2d(128)
        self.context4 = Context(128)
        
        self.conv5 = nn.Conv2d(
            128, 256, kernel_size=3, stride=2, padding=(1,1)
        )
        self.instNorm5 = nn.InstanceNorm2d(256)
        self.context5 = Context(256)
        
        self.upsample0 = Upsampling(256, 128)
        
        self.localize1 = Localization(256, 128)
        self.upsample1 = Upsampling(128, 64)

        self.localize2 = Localization(128, 64)
        self.upsample2 = Upsampling(64, 32)

        self.localize3 = Localization(64, 32)
        self.upsample3 = Upsampling(32, 16)
        
        self.conv6 = nn.Conv2d(
            32, 32, kernel_size=3, padding=(1,1)
        )
        self.instNorm6 = nn.InstanceNorm2d(32)

        self.upscale = nn.Upsample(scale_factor=2)
        
        self.softmax = nn.Softmax(dim=3)
        # segmentation layers
        self.seg1 = nn.Conv2d(
            64, 3, kernel_size=1
        )
        self.segNorm1 = nn.InstanceNorm2d(3)
        self.seg2 = nn.Conv2d(
            32, 3, kernel_size=1
        )
        self.segNorm2 = nn.InstanceNorm2d(3)
        self.seg3 = nn.Conv2d(
            32, 3, kernel_size=1
        )
        self.segNorm3 = nn.InstanceNorm2d(3)
        
    def forward(self, out):
        # convolution layer. input 3d image output 16 channels
        out = F.leaky_relu(self.instNorm1(self.conv1(out)), self.negative_slope) 
        # contaxt block. input/output 16 channels
        out = self.context1(out)
        # save information
        layer1 = out
        # convolution layer. input 16 channels, output 32 channels
        out = F.leaky_relu(self.instNorm2(self.conv2(out)), self.negative_slope)
        # context block. input/output 32 channels
        out = self.context2(out)
        # save information
        layer2 = out
        # convolution layer. input 32 channels. output 64 channels
        out = F.leaky_relu(self.instNorm3(self.conv3(out)), self.negative_slope) 
        # context block. input/output 64 channels
        out = self.context3(out)
        # save information
        layer3 = out
        # convolutional layer. input 64 channels. output 128 channels
        out = F.leaky_relu(self.instNorm4(self.conv4(out)), self.negative_slope)
        # context block. input/output 128 channels
        out = self.context4(out)
        # save information
        layer4 = out
        # convolutional layer. input 128 channels. output 256 channels
        out = F.leaky_relu(self.instNorm5(self.conv5(out)), self.negative_slope)
        # context block. input/output 256 channels
        out = self.context5(out)
        # upsample module. input 256 channels. output 128 channels
        out = self.upsample0(out)
        # concatinate. 0 here is dimension
        out = torch.cat((out, layer4), 1)
        # localization module. input 256 channels. output 128 channels
        out = self.localize1(out)
        # upsampling module. input 128 channels. output 64 channels
        out = self.upsample1(out)
        # concatinate 
        out = torch.cat((out, layer3), 1)
        # localization layer. input 128 channels. output 64 channels
        out = self.localize2(out)
        # first segmentation layer
        seg1 = self.upscale(F.leaky_relu(self.segNorm1(self.seg1(out)), self.negative_slope))
        # upsampling module. input 64 channels. output 32 channels
        out = self.upsample2(out)
        # concatinate
        out = torch.cat((out, layer2), 1)
        # localization module. input 64 channels, output 32 channels
        out = self.localize3(out)
        # second segmentation layer
        seg2 = self.upscale(torch.add(F.leaky_relu(self.segNorm2(self.seg2(out)), self.negative_slope), seg1))
        # upsampling module. input 32 channels. output 16 channels
        out = self.upsample3(out)
        # concatinate
        out = torch.cat((out, layer1), 1)
        # convolutional layer. input/output 32 channels
        out = F.leaky_relu(self.instNorm6(self.conv6(out)), self.negative_slope)
        # elementwise summation of current out and seg2
        out = torch.add(F.leaky_relu(self.segNorm3(self.seg3(out)), self.negative_slope), seg2)
        # softmax
        out = self.softmax(out)
        return out