import glob
from functools import partial
from pathlib import Path

import pytorch_lightning as pl
from metavision_ml.data import SequentialDataLoader
from metavision_ml.data import box_processing as box_api


class Gen4DetectionDataset(pl.LightningDataModule):
    """Pytorch Lightning DataModule for Gen4 pre-computed dataset The default parameters are set
    for the Gen4 Histograms dataset, which can be downloaded from
    https://docs.prophesee.ai/stable/datasets.html#precomputed-datasets but you can change that
    easily by downloading one of the other pre-computed datasets and changing the
    preprocess_function_name and channels parameters accordingly.

    Once downloaded, extract the zip folder and set the dataset_path parameter to the path of the extracted folder.

    Parameters:
        dataset_path: path to the dataset folder
        label_map_path: path to the label_map_dictionary.json file
        batch_size: batch size
        num_tbins: number of time bins in a mini batch
        preprocess_function_name: name of the preprocessing function to use, 'histo' by default. Can be that are listed under https://docs.prophesee.ai/stable/metavision_sdk/modules/ml/python_api/preprocessing.html#module-metavision_ml.preprocessing.event_to_tensor
        delta_t: time interval between two consecutive frames
        channels: number of channels in the input data, 2 by default for histograms
        height: height of the input data
        width: width of the input data
        max_incr_per_pixel: maximum number of events per pixel
        class_selection: list of classes to use
        num_workers: number of workers for the dataloader
    """

    def __init__(
        self,
        dataset_path="data/Gen 4 Histograms",
        label_map_path="label_map_dictionary.json",
        batch_size: int = 4,
        num_tbins: int = 12,
        preprocess_function_name="histo",
        delta_t=50000,
        channels=2,  # histograms have two channels
        height=360,
        width=640,
        max_incr_per_pixel=5,
        class_selection=["pedestrian", "two wheeler", "car"],
        num_workers=4,
    ):
        super().__init__()
        self.dataset_path = Path(dataset_path)
        self.channels = channels
        self.height = height
        self.width = width
        self.class_selection = class_selection
        class_lookup = box_api.create_class_lookup(label_map_path, class_selection)

        self.kw_args = dict(
            delta_t=delta_t,
            preprocess_function_name=preprocess_function_name,
            array_dim=[num_tbins, channels, height, width],
            load_labels=partial(
                box_api.load_boxes,
                num_tbins=num_tbins,
                class_lookup=class_lookup,
                min_box_diag_network=60,
            ),
            batch_size=batch_size,
            num_workers=num_workers,
            padding=True,
            preprocess_kwargs={"max_incr_per_pixel": max_incr_per_pixel},
        )
        print(f"Initialized batch size: {self.kw_args['batch_size']}")
        


    def setup(self, stage=None):
        self.files_train = glob.glob(str(self.dataset_path / "train" / "*.h5"))
        self.files_val = glob.glob(str(self.dataset_path / "val" / "*.h5"))
        self.files_test = glob.glob(str(self.dataset_path / "test" / "*.h5"))
        # print("Testing hello")
        # print(self.files_train)

    def train_dataloader(self):
        return SequentialDataLoader(self.files_train, **self.kw_args)

    def val_dataloader(self):
        return SequentialDataLoader(self.files_val, **self.kw_args)

    def test_dataloader(self):
        return SequentialDataLoader(self.files_test, **self.kw_args)
