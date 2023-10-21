# training, validating, testing and saving the model
import datetime
import argparse
from dataset import *
from modules import *
from utils import plot_losses, plot_test_loss, plot_embeddings, save_embeddings
import torch
from torch import optim

def train(model: TripletNetwork, criterion: TripletLoss, optimiser: optim.Optimizer,
          train_loader: DataLoader, valid_loader: DataLoader, epochs: int):
    losses = {
        "train": [],
        "valid": []
    }
    train_set_size = len(train_loader) # no of batches
    valid_set_size = len(valid_loader)
    print(f"Training images: {train_set_size*BATCH_SIZE}")
    print(f"Number of training batches: {train_set_size}")
    try:
        for epoch in range(epochs):
            print(f"Epoch {epoch + 1}")
            # training
            epoch_train_loss = 0
            model.train()
            for batch_no, (a_t, label, p_t, n_t) in enumerate(train_loader):
                # move the data to the GPU
                a_t, p_t, n_t = a_t.to(device), p_t.to(device), n_t.to(device)
                # zero the gradients
                optimiser.zero_grad()
                # input triplet images into model
                a_out_t, p_out_t, n_out_t = model(a_t, p_t, n_t)
                # calculate the loss
                loss_t = criterion(a_out_t, p_out_t, n_out_t)
                # backpropagate
                loss_t.backward()
                # step the optimiser
                optimiser.step()
                # add the loss
                epoch_train_loss += loss_t.item()

                print(f"Training Batch {batch_no + 1}, Loss: {loss_t.item()}")
                # if batch_no > 0:
                #     break 

            # record average training loss over epoch
            losses["train"].append(epoch_train_loss/train_set_size)

            # validation
            epoch_valid_loss = 0
            model.eval()
            for batch_no, (a_v, label, p_v, n_v) in enumerate(valid_loader):
                # move the data to the GPU
                a_v, p_v, n_v = a_v.to(device), p_v.to(device), n_v.to(device)
                # input triplet images into model
                a_out_v, p_out_v, n_out_v = model(a_v, p_v, n_v)
                # calculate the loss
                loss_v = criterion(a_out_v, p_out_v, n_out_v)
                # add the loss
                epoch_valid_loss += loss_v.item()

                print(f"Validation Batch {batch_no + 1}, Loss: {loss_v.item()}")
                # if batch_no > 0:
                #     break 

            # record average training loss over epoch
            losses["valid"].append(epoch_valid_loss/valid_set_size)

    except Exception as e:
        print(f"Failed at epoch {epoch}")
        print(e)
        
    return losses


def test(chkpt_path, model: TripletNetwork, criterion: TripletLoss,
            test_loader: DataLoader):
    model.load_state_dict(torch.load(chkpt_path))
    model.eval()
    losses = []
    embeddings = []
    total_loss = 0
    print(f"Total batches: {len(test_loader)}")
    try:
        for batch_no, (a, label, p, n) in enumerate(test_loader):
            # move the data to the GPU
            a, p, n = a.to(device), p.to(device), n.to(device)
            # input triplet images into model
            a_out, p_out, n_out = model(a, p, n)
            # calculate the loss
            loss = criterion(a_out, p_out, n_out)
            # record the loss
            losses.append(loss.item())
            total_loss += loss.item()
            # record embedding
            embeddings.append((label.cpu().detach().numpy(),
                              a_out.cpu().detach().numpy()))

            print(f"Test Batch {batch_no + 1}, Loss: {loss.item()}")
            # if batch_no > 10:
            #     break

    except Exception as e:
        print(e)

    average_loss = total_loss / batch_no + 1

    return losses, average_loss, embeddings


def parse_user_args():
    """Parse user CLI args"""
    parser = argparse.ArgumentParser(description="Training/testing model")

    test_or_train = parser.add_mutually_exclusive_group(required=True)

    test_or_train.add_argument(
        "--train",
        action="store_true",
        help="Train new model"
    )

    test_or_train.add_argument(
        "--test",
        type=str,
        help="Path to saved model to test",
        metavar="FILE_PATH"
    )

    args = parser.parse_args()

    return args.train, args.test


if __name__ == '__main__':
    is_training, saved_model_path = parse_user_args()

    # setup the transforms for the images
    transform = transforms.Compose([
        transforms.Resize((256, 240)),
        transforms.ToTensor(),
        OneChannel()
    ])

    # set up network and hyperparameters
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = TripletNetwork().to(device)
    # criterion = TripletLoss()
    criterion = torch.nn.TripletMarginLoss()
    optimiser = optim.Adam(model.parameters(), lr=1e-3)
    epochs = 3

    print(model)

    if is_training:
        # set up the datasets
        train_set = TripletDataset(root="data/train", transform=transform)
        valid_set = TripletDataset(root="data/valid", transform=transform)

        # set up the dataloaders
        train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
        valid_loader = DataLoader(valid_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)

        # train the model
        losses = train(model, criterion, optimiser, train_loader, valid_loader, epochs)
        save_path = f"./checkpoints/cp_{datetime.datetime.now().strftime('%m-%d_%H-%M-%S')}"
        torch.save(model.state_dict(), save_path)
        # print(losses)
        
        plot_losses(losses["train"], losses["valid"])
        saved_model_path = save_path

    test_set = TripletDataset(root="data/test", transform=transform)
    test_loader = DataLoader(test_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)

    test_losses, average_test_loss, embeddings = test(saved_model_path, model, 
                                                      criterion, test_loader)
    plot_test_loss(test_losses)
    save_embeddings(embeddings)
    if False:
        plot_embeddings(embeddings)