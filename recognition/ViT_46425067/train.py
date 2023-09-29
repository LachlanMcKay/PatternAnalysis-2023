import torch
import torch.nn as nn
import torch.optim as optim
from modules import ViT
from dataset import load_data
from types import SimpleNamespace

#setup random seeds
torch.manual_seed(42)
torch.cuda.manual_seed(42)
#device agnostic code
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#hyperparmeters
config = SimpleNamespace(
    batch_size=32,
    img_size=(224, 224),
    patch_size=16,
    img_channel=1,
    num_classes=2,
    embed_dim=768,
    depth=1,
    num_heads=3,
    mlp_ratio=4,
    qkv_bias=True,
    drop_prob=0.1,
    lr=1e-3
)

#load dataloaders
train_loader, test_load, _, _ = load_data(config.batch_size, config.img_size)

#create model
model = ViT(img_size=config.img_size[0],
            patch_size=config.patch_size,
            img_channels=config.img_channel,
            num_classes=config.num_classes,
            embed_dim=config.embed_dim,
            depth=config.depth,
            num_heads=config.num_heads,
            mlp_ratio=config.mlp_ratio,
            qkv_bias=config.qkv_bias,
            drop_prob=config.drop_prob).to(device)

#loss function + optimiser
loss_fn = nn.CrossEntropyLoss()
optimiser = optim.AdamW(model.parameters(), lr=config.lr)


def train_epoch(model: nn.Module, 
                data_loader: torch.utils.data.DataLoader,
                loss_fn: nn.Module,
                optimiser: optim.Optimizer,
                device: str):
    train_loss, train_acc = 0, 0
    model.train()
    for batch, (X, y) in enumerate(data_loader):
        X, y = X.to(device), y.to(device)
        y_pred = model(X)
        loss = loss_fn(y_pred, y)
        train_loss += loss.item()
        train_acc += accuracy(y_pred, y)
        #backpropagation
        optimiser.zero_grad()
        loss.backward()
        optimiser.step()

    train_acc = train_acc / len(data_loader)
    train_loss = train_loss / len(data_loader)
    return train_acc, train_loss


def accuracy(y_pred, y):
    y_pred_class = torch.argmax(torch.softmax(y_pred, dim=1), dim=1)
    train_acc = (y_pred_class == y).sum().item() / len(y_pred)
    return train_acc