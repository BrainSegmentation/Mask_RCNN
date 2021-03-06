"""
Mask R-CNN

Licensed under the MIT License (see LICENSE for details)
Written by Waleed Abdulla


Copied from Mask_RCNN/samples/nucleus/nucleus.py
and modified for BrainSegmentation by @bgrassy @atikinf @niklasschmitz

------------------------------------------------------------

Usage: import the module (see Jupyter notebooks for examples), or run from
       the command line as such:

    # Train a new model starting from ImageNet weights
    python3 Braintissue.py train --dataset=/path/to/dataset --subset=train --weights=imagenet

    # Train a new model starting from specific weights file
    python3 Braintissue.py train --dataset=/path/to/dataset --subset=train --weights=/path/to/weights.h5

    # Resume training a model that you had trained earlier
    python3 Braintissue.py train --dataset=/path/to/dataset --subset=train --weights=last

    # Generate submission file
    python3 Braintissue.py detect --dataset=/path/to/dataset --subset=train --weights=<last or /path/to/weights.h5>
"""

# Set matplotlib backend
# This has to be done before other import that might
# set it, but only if we're running in script mode
# rather than being imported.
if __name__ == '__main__':
    import matplotlib
    # Agg backend runs without a display
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

import os
import sys
import json
import datetime
import time
import numpy as np
import skimage
import skimage.io
import pickle
from imgaug import augmenters as iaa
from shutil import copyfile
import re

# Root directory of the project
ROOT_DIR = os.path.abspath("../../")

# Import Mask RCNN
sys.path.append(ROOT_DIR)  # To find local version of the library
from mrcnn.config import Config
from mrcnn import utils
from mrcnn import model as modellib
from mrcnn import visualize

from braintissue_config import *

############################################################
#  Dataset
############################################################

class BraintissueDataset(utils.Dataset):

    def load_braintissue(self, dataset_dir, subset):
        """Load a subset of the nuclei dataset.

        dataset_dir: Root directory of the dataset
        subset: Subset to load. Either the name of the sub-directory,
                such as stage1_train, stage1_test, ...etc. or, one of:
                * train: stage1_train excluding validation images
                * val: validation images from VAL_IMAGE_IDS
        """
        # Add classes. We have two classes: magnetic part and braintissue part
        # Naming the dataset Braintissue, and the class Braintissue
        self.add_class("Braintissue", 1, "Braintissue")
        self.add_class("Braintissue", 2, "Magnet")

        # Which subset?
        # "val": use hard-coded list above
        # "train": use data from train minus the hard-coded list above
        # "train_artificial" : use data from train_artificial minus val
        # else: use the data from the specified sub-directory
        assert subset in ["train", "val", "train_artificial", "partitions"]
        subset_dir = "train" if subset in ["train", "val"] else subset
        dataset_dir = os.path.join(dataset_dir, subset_dir)
        if subset == "val":
            image_ids = VAL_IMAGE_IDS
        else:
            # Get image ids from directory names
            image_ids = next(os.walk(dataset_dir))[1]
            if subset == "train" or "train_artificial" or "partitions":
                image_ids = list(set(image_ids) - set(VAL_IMAGE_IDS))

        # Add images
        for image_id in image_ids:
            self.add_image(
                "Braintissue",
                image_id=image_id,
                path=os.path.join(dataset_dir, image_id, "images")
            )

    def load_mask(self, image_id):
        """Generate instance masks for an image
       Returns:
        masks: A bool array of shape [height, width, instance count] with
            one mask per instance.
        class_ids: a 1D array of class IDs of the instance masks.
        """
        info = self.image_info[image_id]
        # Get mask directory from image path
        tissue_mask_dir = os.path.join(os.path.dirname(info['path']), "tissue_masks")
        magnetic_mask_dir = os.path.join(os.path.dirname(info['path']), "magnetic_masks")

        # Read mask files from .tif image
        tissue_masks = []
        magnetic_masks = []

        # collect tissue part masks
        for f in next(os.walk(tissue_mask_dir))[2]:
            if f.endswith(".tif"):
                m = skimage.io.imread(os.path.join(tissue_mask_dir, f), as_gray=True).astype(np.bool)
                tissue_masks.append(m)
        class_ids_tissue = np.zeros(len(tissue_masks), dtype=np.int32) + 1  # braintissue has id 1

        # collect magnetic part masks
        for f in next(os.walk(magnetic_mask_dir))[2]:
            if f.endswith(".tif"):
                m = skimage.io.imread(os.path.join(magnetic_mask_dir, f), as_gray=True).astype(np.bool)
                magnetic_masks.append(m)
        class_ids_magnetic = np.zeros(len(magnetic_masks), dtype=np.int32) + 2  # magnetic part has id 2

        # collect both
        mask = tissue_masks + magnetic_masks
        mask = np.stack(mask, axis=-1)
        class_ids = np.r_[class_ids_tissue, class_ids_magnetic]

        # Return mask, and array of class IDs of each instance.
        return mask, class_ids

    def load_image(self, image_id):
        """ Load a given image, convert to grayscale, add fluo channel
        Returns:
            image: the loaded image as array of shape (HEIGHT, WIDTH, NUM_CHANNELS)
        """

        info = self.image_info[image_id]

        # this is the path to the images/ folder containing both channels as seperate images
        path = info['path']

        path_base_channel = os.path.join(path, "{}.tif".format(info["id"]))
        path_fluo_channel = os.path.join(path, "{}_fluo.tif".format(info["id"]))
        
        base_channel = skimage.io.imread(path_base_channel, as_gray=True)
        base_channel = skimage.img_as_ubyte(base_channel)

        fluo_channel = skimage.io.imread(path_fluo_channel, as_gray=True)
        fluo_channel = skimage.img_as_ubyte(fluo_channel)

        # stack both channels together
        image = [base_channel, fluo_channel]
        image = np.stack(image, axis=-1)

        return image

    def image_reference(self, image_id):
        """Return the path of the image."""
        info = self.image_info[image_id]
        if info["source"] == "Braintissue":
            return info["id"]
        else:
            super(self.__class__, self).image_reference(image_id)


############################################################
#  Training
############################################################

def train(model, dataset_dir, subset):
    """Train the model."""
    # Training dataset.
    dataset_train = BraintissueDataset()
    dataset_train.load_braintissue(dataset_dir, subset)
    dataset_train.prepare()

    # Validation dataset
    dataset_val = BraintissueDataset()
    dataset_val.load_braintissue(dataset_dir, "val")
    dataset_val.prepare()

    # Image augmentation
    # http://imgaug.readthedocs.io/en/latest/source/augmenters.html
    augmentation = iaa.SomeOf((0, 2), [
        iaa.Fliplr(0.5),
        iaa.Flipud(0.5),
        iaa.OneOf([iaa.Affine(rotate=90),
                   iaa.Affine(rotate=180),
                   iaa.Affine(rotate=270)]),
        #iaa.Multiply((0.9, 1.1)),
    ])

    # *** This training schedule is an example. Update to your needs ***

    # If starting from imagenet, train heads only for a bit
    # since they have random weights
    print(time.strftime('%x %X'))
    print("Train network heads")
    model.train(dataset_train, dataset_val,
                learning_rate=config.LEARNING_RATE,
                epochs=2,
                augmentation=augmentation,
                layers='heads+conv1')

    print(time.strftime('%x %X'))
    print("Train all layers")
    model.train(dataset_train, dataset_val,
                learning_rate=config.LEARNING_RATE,
                epochs=80,
                augmentation=augmentation,
                layers='all')

############################################################
#  RLE Encoding
############################################################

def rle_encode(mask):
    """Encodes a mask in Run Length Encoding (RLE).
    Returns a string of space-separated values.
    """
    assert mask.ndim == 2, "Mask must be of shape [Height, Width]"
    # Flatten it column wise
    m = mask.T.flatten()
    # Compute gradient. Equals 1 or -1 at transition points
    g = np.diff(np.concatenate([[0], m, [0]]), n=1)
    # 1-based indicies of transition points (where gradient != 0)
    rle = np.where(g != 0)[0].reshape([-1, 2]) + 1
    # Convert second index in each pair to lenth
    rle[:, 1] = rle[:, 1] - rle[:, 0]
    return " ".join(map(str, rle.flatten()))


def rle_decode(rle, shape):
    """Decodes an RLE encoded list of space separated
    numbers and returns a binary mask."""
    rle = list(map(int, rle.split()))
    rle = np.array(rle, dtype=np.int32).reshape([-1, 2])
    rle[:, 1] += rle[:, 0]
    rle -= 1
    mask = np.zeros([shape[0] * shape[1]], np.bool)
    for s, e in rle:
        assert 0 <= s < mask.shape[0]
        assert 1 <= e <= mask.shape[0], "shape: {}  s {}  e {}".format(shape, s, e)
        mask[s:e] = 1
    # Reshape and transpose
    mask = mask.reshape([shape[1], shape[0]]).T
    return mask


def mask_to_rle(image_id, mask, scores):
    "Encodes instance masks to submission format."
    assert mask.ndim == 3, "Mask must be [H, W, count]"
    # If mask is empty, return line with image ID only
    if mask.shape[-1] == 0:
        return "{},".format(image_id)
    # Remove mask overlaps
    # Multiply each instance mask by its score order
    # then take the maximum across the last dimension
    order = np.argsort(scores)[::-1] + 1  # 1-based descending
    mask = np.max(mask * np.reshape(order, [1, 1, -1]), -1)
    # Loop over instance masks
    lines = []
    for o in order:
        m = np.where(mask == o, 1, 0)
        # Skip if empty
        if m.sum() == 0.0:
            continue
        rle = rle_encode(m)
        lines.append("{}, {}".format(image_id, rle))
    return "\n".join(lines)


############################################################
#  Detection
############################################################

def detect(model, dataset_dir, subset):
    """Run detection on images in the given directory."""
    print("Running on {}".format(dataset_dir))

    # Create directory
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    submit_dir = "submit_{:%Y%m%dT%H%M%S}".format(datetime.datetime.now())
    submit_dir = os.path.join(RESULTS_DIR, submit_dir)
    os.makedirs(submit_dir)

    # Read dataset
    dataset = BraintissueDataset()
    dataset.load_braintissue(dataset_dir, subset)
    dataset.prepare()
    # Load over images
    submission = []
    for image_id in dataset.image_ids:
        # Load image and run detection
        image = dataset.load_image(image_id)
        # Detect objects
        r = model.detect([image], verbose=0)[0]
        # Encode image to RLE. Returns a string of multiple lines
        source_id = dataset.image_info[image_id]["id"]
        rle = mask_to_rle(source_id, r["masks"], r["scores"])
        submission.append(rle)
        # Save image with masks
        visualize.display_instances(
            image, r['rois'], r['masks'], r['class_ids'],
            dataset.class_names, r['scores'],
            show_bbox=False, show_mask=False,
            title="Predictions")
        plt.savefig("{}/{}.png".format(submit_dir, dataset.image_info[image_id]["id"]))

    # Save to csv file
    submission = "ImageId,EncodedPixels\n" + "\n".join(submission)
    file_path = os.path.join(submit_dir, "submit.csv")
    with open(file_path, "w") as f:
        f.write(submission)
    print("Saved to ", submit_dir)

############################################################
#  Config saving
############################################################

def save_config(logs_path):
    """ saves the braintissue config to the log dir, to have it next to the weights """

    now = datetime.datetime.now()

    # TODO: model.py 2335 possible conflict, if minute differs
    log_dir = os.path.join(logs_path, 
                            "config_{}{:%Y%m%dT%H%M}".format(config.NAME.lower(), now))

    # Create log_dir if it does not exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    dest = os.path.join(log_dir, "braintissue_config.py")

    # Copy braintissue config to log dir
    copyfile("braintissue_config.py", dest)


############################################################
#  Command Line
############################################################

if __name__ == '__main__':
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Mask R-CNN for braintissue wafer segmentation')
    parser.add_argument("command",
                        metavar="<command>",
                        help="'train' or 'detect'")
    parser.add_argument('--dataset', required=False,
                        metavar="/path/to/dataset/",
                        help='Root directory of the dataset')
    parser.add_argument('--weights', required=True,
                        metavar="/path/to/weights.h5",
                        help="Path to weights .h5 file or 'coco'")
    parser.add_argument('--logs', required=False,
                        default=DEFAULT_LOGS_DIR,
                        metavar="/path/to/logs/",
                        help='Logs and checkpoints directory (default=logs/)')
    parser.add_argument('--subset', required=False,
                        metavar="Dataset sub-directory",
                        help="Subset of dataset to run prediction on")
    args = parser.parse_args()

    # Validate arguments
    if args.command == "train":
        assert args.dataset, "Argument --dataset is required for training"
    elif args.command == "detect":
        assert args.subset, "Provide --subset to run prediction on"

    print("Weights: ", args.weights)
    print("Dataset: ", args.dataset)
    if args.subset:
        print("Subset: ", args.subset)
    print("Logs: ", args.logs)

    # Configurations
    if args.command == "train":
        config = BraintissueConfig()

        # Copy the used config file to the log dir for reproducibility after training
        save_config(args.logs)
    else:
        config = BraintissueInferenceConfig()
    config.display()

    # Create model
    if args.command == "train":
        model = modellib.MaskRCNN(mode="training", config=config,
                                  model_dir=args.logs)
    else:
        model = modellib.MaskRCNN(mode="inference", config=config,
                                  model_dir=args.logs)

    # Select weights file to load
    if args.weights.lower() == "coco":
        weights_path = COCO_WEIGHTS_PATH
        # Download weights file
        if not os.path.exists(weights_path):
            utils.download_trained_weights(weights_path)
    elif args.weights.lower() == "last":
        # Find last trained weights
        weights_path = model.find_last()
    elif args.weights.lower() == "imagenet":
        # Start from ImageNet trained weights
        weights_path = model.get_imagenet_weights()
    else:
        weights_path = args.weights

    # Load weights
    print("Loading weights ", weights_path)
    if args.weights.lower() == "coco":
        # Exclude the last layers because they require a matching
        # number of classes
        model.load_weights(weights_path, by_name=True, exclude=[
            "mrcnn_class_logits", "mrcnn_bbox_fc",
            "mrcnn_bbox", "mrcnn_mask", "conv1"])
    else:
        model.load_weights(weights_path, by_name=True)

    # Train or evaluate
    if args.command == "train":
        train(model, args.dataset, args.subset)
    elif args.command == "detect":
        detect(model, args.dataset, args.subset)
    else:
        print("'{}' is not recognized. "
              "Use 'train' or 'detect'".format(args.command))

