import decord

decord.bridge.set_bridge('torch')
from torch.utils.data import Dataset
from einops import rearrange
import os
from PIL import Image
import numpy as np


class VideoDataset(Dataset):
    def __init__(
            self,
            video_path: str,
            prompt: str,
            width: int = 512,
            height: int = 512,
            n_sample_frames: int = 8,
            sample_start_idx: int = 0,
            sample_frame_rate: int = 1,
    ):
        self.video_path = video_path
        self.prompt = prompt
        self.prompt_ids = None
        self.width = width
        self.height = height
        self.n_sample_frames = n_sample_frames
        self.sample_start_idx = sample_start_idx
        self.sample_frame_rate = sample_frame_rate
        if not self.video_path.endswith('mp4'):
            self.images = []
            for file in sorted(os.listdir(self.video_path), key=lambda x: int(x[:-4])):
                self.images.append(np.asarray(
                    Image.open(os.path.join(self.video_path, file)).convert('RGB').resize((self.width, self.height))))
            self.images = np.stack(self.images)

    def __len__(self):
        return 1

    def __getitem__(self, index):
        # load and sample video frames
        if self.video_path.endswith('mp4'):
            vr = decord.VideoReader(self.video_path, width=self.width, height=self.height)
            sample_frame_rate = len(vr) // self.n_sample_frames
            print(('sample-frame-rate', sample_frame_rate, len(vr), self.n_sample_frames))
            sample_index = list(range(self.sample_start_idx, len(vr), sample_frame_rate))[:self.n_sample_frames]
            video = vr.get_batch(sample_index)
            control = video

        else:
            video = self.images[:self.n_sample_frames]
            control = video
        video = rearrange(video, "f h w c -> f c h w")

        example = {
            "pixel_values": (video / 127.5 - 1.0),  # [-1,1] with shape [f c h w ]
            "prompt_ids": self.prompt_ids,
            "control": control,  # {0,1,……,255} with shape [f h w c]
        }
        return example
