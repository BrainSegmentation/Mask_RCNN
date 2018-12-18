"""
Mask R-CNN
Base Configurations class.

Copyright (c) 2017 Matterport, Inc.
Licensed under the MIT License (see LICENSE for details)
Written by Waleed Abdulla

Modified by @bgrassy @atikinf @niklasschmitz
"""

import numpy as np
import sys
import os

# Root directory of the project
ROOT_DIR = os.path.abspath("../../")

# Import Mask RCNN
sys.path.append(ROOT_DIR)  # To find local version of the library
from mrcnn.config import Config

# Path to trained coco weights file
COCO_WEIGHTS_PATH = os.path.join(ROOT_DIR, "weights/mask_rcnn_coco.h5")

# Directory to save logs and model checkpoints, if not provided
# through the command line argument --logs
DEFAULT_LOGS_DIR = os.path.join(ROOT_DIR, "logs")

# Results directory
# Save submission files here
RESULTS_DIR = os.path.join(ROOT_DIR, "results/braintissue")

# The dataset doesn't have a standard train/val split, so I picked
# a variety of images to serve as a validation set.
VAL_IMAGE_IDS = ["artif1_0_crop1", "artif1_6_crop4", "artif1_2_crop8"]

############################################################
#  Configurations
############################################################

class BraintissueConfig(Config):
    """Configuration for training on the Braintissue segmentation dataset."""
    # Give the configuration a recognizable name
    NAME = "Braintissue"

    # Adjust depending on your GPU memory
    IMAGES_PER_GPU = 1

    # Number of classes (including background)
    NUM_CLASSES = 1 + 1 + 1 # Background + Braintissue + magnetic part

    # Number of training and validation steps per epoch
    STEPS_PER_EPOCH = (100 - len(VAL_IMAGE_IDS)) // IMAGES_PER_GPU
    VALIDATION_STEPS = 3 # max(1, len(VAL_IMAGE_IDS) // IMAGES_PER_GPU)

    # Backbone network architecture
    # Supported values are: resnet50, resnet101
    BACKBONE = "resnet50"

    # Input image resizing
    IMAGE_RESIZE_MODE = "square"
    IMAGE_MIN_DIM = 512
    IMAGE_MAX_DIM = 512
    IMAGE_MIN_SCALE = 0

    # Length of square anchor side in pixels
    RPN_ANCHOR_SCALES = (32, 64, 128, 256) # (8, 16, 32, 64, 128)

    # ROIs kept after non-maximum supression (training and inference)
    POST_NMS_ROIS_TRAINING = 128
    POST_NMS_ROIS_INFERENCE = 128

    # Non-max suppression threshold to filter RPN proposals.
    # You can increase this during training to generate more proposals.
    RPN_NMS_THRESHOLD = 0.9

    # How many anchors per image to use for RPN training
    RPN_TRAIN_ANCHORS_PER_IMAGE = 64

    # Grayscale adjustments
    IMAGE_CHANNEL_COUNT = 1
    MEAN_PIXEL = np.array([184])
    

    # If enabled, resizes instance masks to a smaller size to reduce
    # memory load. Recommended when using high-resolution images.
    USE_MINI_MASK = True
    MINI_MASK_SHAPE = (56, 56)  # (height, width) of the mini-mask

    # Number of ROIs per image to feed to classifier/mask heads
    # The Mask RCNN paper uses 512 but often the RPN doesn't generate
    # enough positive proposals to fill this and keep a positive:negative
    # ratio of 1:3. You can increase the number of proposals by adjusting
    # the RPN NMS threshold.
    TRAIN_ROIS_PER_IMAGE = 128

    # Maximum number of ground truth instances to use in one image
    MAX_GT_INSTANCES = 1000	

    # Max number of final detections per image
    DETECTION_MAX_INSTANCES = 100

    # Loss weights for more precise optimization.
    # Can be used for R-CNN training setup.
    LOSS_WEIGHTS = {
        "rpn_class_loss": 1.,
        "rpn_bbox_loss": 2.,
        "mrcnn_class_loss": 1.,
        "mrcnn_bbox_loss": 1.,
        "mrcnn_mask_loss": 2.
    }


class BraintissueInferenceConfig(BraintissueConfig):
    # Set batch size to 1 to run one image at a time
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    # Don't resize imager for inferencing
    IMAGE_RESIZE_MODE = "square"
    # Non-max suppression threshold to filter RPN proposals.
    # You can increase this during training to generate more proposals.
    RPN_NMS_THRESHOLD = 0.7
