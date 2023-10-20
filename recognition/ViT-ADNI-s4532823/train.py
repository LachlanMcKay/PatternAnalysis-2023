"""
Train the model and perform testing.
"""

from dataset import get_dataloader
import torch
import time
from modules import ViT, VisionTransformer
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader


def plot_metric(stopping_epoch: int, metric_type: str, train_data: list, val_data: list):
    """
    Helper function to plot a given metric
    """
    plt.figure()
    plt.plot(range(1, stopping_epoch+1), train_data, label = f"Training {metric_type}")
    plt.plot(range(1, stopping_epoch+1), val_data, label=f"Validation {metric_type}", color='orange')
    plt.xlabel('Epoch')
    plt.ylabel(metric_type)
    plt.legend()
    plt.title(f"Training {metric_type} vs validation {metric_type}")
    plt.savefig(f"Training_vs_validation_{metric_type}_{int(time.time())}.png")


def train_val_epoch(device,
                    model, 
                    train_loader: DataLoader,
                    val_loader: DataLoader, 
                    criterion: torch.nn.CrossEntropyLoss,
                    optimizer: torch.optim.Adam,
                    scheduler: torch.optim.lr_scheduler.StepLR,
                    epoch,
                    epochs):
    """
    Function to run an epoch of training and validation
    """
    # Training metrics
    train_correct = 0
    train_total = 0
    tl = []
    strt = time.time()
    # Do training
    for images, labels in train_loader:
        images = images.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        # Forward pass
        outputs = model(images)
        #losses
        loss = criterion(outputs, labels)
        tl.append(loss.item())
        _, predicted = torch.max(outputs, 1)
        train_total += labels.size(0)
        train_correct += (predicted == labels).sum().item()
        # Backward and optimize
        loss.backward()
        optimizer.step()

    print (f"Training epoch [{epoch+1}/{epochs}]: mean loss {sum(tl)/len(tl):.5f}, accuracy {(train_correct/train_total)*100:.2f}%. Time elapsed {time.time()-strt:.3f}.")
    # Validation metrics
    val_correct = 0
    val_total = 0
    vl = []
    strt = time.time()

    # Do validation
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)
            # Forward pass
            outputs = model(images)
            #losses
            loss = criterion(outputs, labels)
            vl.append(loss.item())
            _, predicted = torch.max(outputs, 1)
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    print (f"Validation epoch [{epoch+1}/{epochs}]: mean loss {sum(vl)/len(vl):.5f}, accuracy {(val_correct/val_total)*100:.2f}%.")
    scheduler.step()
    return sum(tl)/len(tl), sum(vl)/len(vl), train_correct/train_total, val_correct/val_total


def run_training(device, 
                 model, 
                 train_loader: DataLoader, 
                 val_loader: DataLoader,
                 epochs: int,
                 lr: float):
    """
    Function to run training on the dataset.
    """
    # Initialise criterion, optimizer and LR scheduler
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 1, 0.5)
    # Metrics tracking
    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []
    stopping_epoch = epochs
    # Run through epochs
    strt = time.time()
    for epoch in range(epochs):
        tl, vl, ta, va = train_val_epoch(device, model, train_loader, val_loader, criterion, optimizer, scheduler, epoch, epochs)
        train_losses.append(tl); val_losses.append(vl); train_accs.append(ta); val_accs.append(va)
        # Stop training early if validation accuracy decreases for two epochs in a row
        if epoch+1 > 2 and val_accs[-3] > val_accs[-2] and val_accs[-2] > val_accs[-1]:
            stopping_epoch = epoch+1
            break
        if val_accs[-1] == max(val_accs):
            # save best model
            torch.save(model, "adni_vit.pt")

    print(f"Training & validation took {time.time()-strt:.3f} secs or {(time.time()-strt)/60:.2f} mins in total")
    print("")
    plot_metric(stopping_epoch, 'loss', train_losses, val_losses)
    plot_metric(stopping_epoch, 'accuracy', train_accs, val_accs)


def run_testing(device, model, test_loader: DataLoader):
    """
    Function to run testing on the trained model.
    """
    test_correct = 0
    test_total = 0
    start = time.time()
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)
            # Forward pass
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            test_total += labels.size(0)
            test_correct += (predicted == labels).sum().item()

    print(f"Test accuracy {(test_correct/test_total)*100:.2f}, time elapsed {time.time()-start:.3f} secs or {(time.time()-start)/60:.2f} mins in total")


def main():
    """
    Main execution function.
    """
    # Device configuration
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    if not torch.cuda.is_available():
        print("Warning CUDA not found. Using CPU")
    # Initialise hyperparameters
    BATCH_SIZE = 64
    EPOCHS = 10
    LR = 2e-5
    # Initialise data loaders & model
    train_loader, val_loader = get_dataloader(batch_size=BATCH_SIZE, train=True)
    test_loader = get_dataloader(batch_size=BATCH_SIZE, train=False)
    model = ViT()
    model = model.to(device)
    # Run training and testing
    run_training(device, model, train_loader, val_loader, epochs=EPOCHS, lr=LR)
    run_testing(device, model, test_loader)


if __name__ == "__main__":
    main()
